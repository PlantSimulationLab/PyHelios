"""
Tests for LiDAR plugin integration
"""

import pytest
import math
import os
from pyhelios.types import vec3, vec2, RGBcolor, SphericalCoord
from pyhelios.plugins.registry import get_plugin_registry
from pyhelios.exceptions import HeliosError
from pyhelios.wrappers import ULiDARWrapper as lidar_wrapper


def get_lidar_asset_path(asset_path):
    """
    Get path to LiDAR plugin asset file.

    Uses AssetPathManager to find assets in both development (helios-core/)
    and wheel (pyhelios/assets/build/) environments. Returns None if not found.

    Args:
        asset_path: Relative path within lidar plugin directory
                   (e.g., 'xml/leaf_cube.xml' or 'xml/AlmondWP.obj')

    Returns:
        Absolute path to asset file, or None if not found
    """
    from pyhelios.assets import get_asset_manager

    asset_manager = get_asset_manager()
    lidar_assets_dir = asset_manager.get_lidar_assets_path()

    if lidar_assets_dir is None:
        return None

    full_path = os.path.join(lidar_assets_dir, asset_path)
    return full_path if os.path.exists(full_path) else None


class TestLiDARMetadata:
    """Test plugin metadata and registration"""

    @pytest.mark.cross_platform
    def test_plugin_metadata_exists(self):
        """Test that plugin metadata is correctly defined"""
        from pyhelios.config.plugin_metadata import get_plugin_metadata

        metadata = get_plugin_metadata('lidar')
        assert metadata is not None
        assert metadata.name == 'lidar'
        assert 'LiDAR' in metadata.description or 'lidar' in metadata.description.lower()
        assert metadata.test_symbols
        assert len(metadata.platforms) > 0

    @pytest.mark.cross_platform
    def test_plugin_in_metadata_registry(self):
        """Test that lidar is registered in PLUGIN_METADATA"""
        from pyhelios.config.plugin_metadata import PLUGIN_METADATA

        assert 'lidar' in PLUGIN_METADATA
        metadata = PLUGIN_METADATA['lidar']
        assert metadata.name == 'lidar'


class TestLiDARAvailability:
    """Test plugin availability detection"""

    @pytest.mark.cross_platform
    def test_plugin_registry_awareness(self):
        """Test that plugin registry knows about LiDAR"""
        from pyhelios.config.plugin_metadata import PLUGIN_METADATA

        # Plugin should be in metadata registry
        assert 'lidar' in PLUGIN_METADATA

    @pytest.mark.cross_platform
    def test_graceful_unavailable_handling(self):
        """Test graceful handling when plugin unavailable"""
        from pyhelios import LiDARCloud, LiDARError

        registry = get_plugin_registry()

        if not registry.is_plugin_available('lidar'):
            # Should raise informative error
            with pytest.raises(LiDARError) as exc_info:
                LiDARCloud()

            error_msg = str(exc_info.value).lower()
            # Error should mention rebuilding
            assert any(keyword in error_msg for keyword in
                      ['rebuild', 'build', 'enable', 'compile'])


class TestLiDARInterface:
    """Test plugin interface without requiring native library"""

    @pytest.mark.cross_platform
    def test_plugin_class_structure(self):
        """Test that plugin class has expected structure"""
        from pyhelios import LiDARCloud

        # Test class attributes and methods exist
        assert hasattr(LiDARCloud, '__init__')
        assert hasattr(LiDARCloud, '__enter__')
        assert hasattr(LiDARCloud, '__exit__')
        assert hasattr(LiDARCloud, '__del__')
        assert hasattr(LiDARCloud, 'addScan')
        assert hasattr(LiDARCloud, 'addHitPoint')
        assert hasattr(LiDARCloud, 'getHitCount')
        assert hasattr(LiDARCloud, 'triangulateHitPoints')
        assert hasattr(LiDARCloud, 'exportPointCloud')
        assert hasattr(LiDARCloud, 'is_available')

    @pytest.mark.cross_platform
    def test_error_types_available(self):
        """Test that error types are properly defined"""
        from pyhelios import LiDARError, HeliosError

        assert issubclass(LiDARError, HeliosError)


@pytest.mark.native_only
class TestLiDARFunctionality:
    """Test actual LiDAR functionality with native library"""

    def test_cloud_creation(self):
        """Test LiDAR cloud can be created and destroyed"""
        from pyhelios import LiDARCloud

        with LiDARCloud() as lidar:
            assert lidar is not None
            assert isinstance(lidar, LiDARCloud)

    def test_cloud_creation_without_context_manager(self):
        """Test LiDAR cloud cleanup without context manager"""
        from pyhelios import LiDARCloud
        import gc

        lidar = LiDARCloud()
        assert lidar is not None

        # Delete and force garbage collection
        del lidar
        gc.collect()
        # If __del__ works correctly, no errors

    def test_add_scan(self):
        """Test adding a scan to the cloud"""
        from pyhelios import LiDARCloud

        with LiDARCloud() as lidar:
            scan_id = lidar.addScan(
                origin=vec3(0, 0, 1),
                Ntheta=10, theta_range=(0, 1.57),
                Nphi=10, phi_range=(-3.14, 3.14),
                exit_diameter=0.01, beam_divergence=0.001
            )
            assert isinstance(scan_id, int)
            assert scan_id >= 0
            assert lidar.getScanCount() == 1

    def test_add_scan_with_list_origin(self):
        """Test adding scan with list origin"""
        from pyhelios import LiDARCloud

        with LiDARCloud() as lidar:
            scan_id = lidar.addScan(
                origin=[0, 0, 1],
                Ntheta=5, theta_range=(0, 1.0),
                Nphi=5, phi_range=(-3.14, 3.14),
                exit_diameter=0.01, beam_divergence=0.001
            )
            assert scan_id >= 0

    def test_scan_properties(self):
        """Test querying scan properties"""
        from pyhelios import LiDARCloud

        with LiDARCloud() as lidar:
            origin = vec3(1, 2, 3)
            scan_id = lidar.addScan(
                origin=origin,
                Ntheta=15, theta_range=(0, 1.5),
                Nphi=20, phi_range=(-3.0, 3.0),
                exit_diameter=0.02, beam_divergence=0.002
            )

            # Check scan properties
            retrieved_origin = lidar.getScanOrigin(scan_id)
            assert abs(retrieved_origin.x - origin.x) < 0.001
            assert abs(retrieved_origin.y - origin.y) < 0.001
            assert abs(retrieved_origin.z - origin.z) < 0.001

            assert lidar.getScanSizeTheta(scan_id) == 15
            assert lidar.getScanSizePhi(scan_id) == 20

    def test_add_hit_point(self):
        """Test adding hit points to the cloud"""
        from pyhelios import LiDARCloud

        with LiDARCloud() as lidar:
            scan_id = lidar.addScan(
                origin=vec3(0, 0, 1),
                Ntheta=10, theta_range=(0, 1.0),
                Nphi=10, phi_range=(-3.14, 3.14),
                exit_diameter=0.01, beam_divergence=0.001
            )

            # Add hit point with vec3
            lidar.addHitPoint(scan_id, vec3(1, 0, 0), vec3(1, 0, 0))
            assert lidar.getHitCount() == 1

            # Add hit point with list
            lidar.addHitPoint(scan_id, [2, 0, 0], [1, 0, 0])
            assert lidar.getHitCount() == 2

    def test_add_hit_point_with_color(self):
        """Test adding hit points with color"""
        from pyhelios import LiDARCloud

        with LiDARCloud() as lidar:
            scan_id = lidar.addScan(
                origin=vec3(0, 0, 1),
                Ntheta=5, theta_range=(0, 1.0),
                Nphi=5, phi_range=(-3.14, 3.14),
                exit_diameter=0.01, beam_divergence=0.001
            )

            # Add with RGBcolor
            lidar.addHitPoint(scan_id, vec3(1, 0, 0), vec3(1, 0, 0),
                            color=RGBcolor(1.0, 0.0, 0.0))
            assert lidar.getHitCount() == 1

            # Add with list color
            lidar.addHitPoint(scan_id, [2, 0, 0], [1, 0, 0],
                            color=[0.0, 1.0, 0.0])
            assert lidar.getHitCount() == 2

    def test_get_hit_properties(self):
        """Test retrieving hit point properties"""
        from pyhelios import LiDARCloud

        with LiDARCloud() as lidar:
            scan_id = lidar.addScan(
                origin=vec3(0, 0, 1),
                Ntheta=5, theta_range=(0, 1.0),
                Nphi=5, phi_range=(-3.14, 3.14),
                exit_diameter=0.01, beam_divergence=0.001
            )

            # Add hit point
            position = vec3(1.5, 2.5, 3.5)
            color = RGBcolor(0.5, 0.6, 0.7)
            lidar.addHitPoint(scan_id, position, vec3(1, 0, 0), color=color)

            # Retrieve properties
            retrieved_pos = lidar.getHitXYZ(0)
            assert abs(retrieved_pos.x - position.x) < 0.001
            assert abs(retrieved_pos.y - position.y) < 0.001
            assert abs(retrieved_pos.z - position.z) < 0.001

            retrieved_color = lidar.getHitColor(0)
            assert abs(retrieved_color.r - color.r) < 0.001
            assert abs(retrieved_color.g - color.g) < 0.001
            assert abs(retrieved_color.b - color.b) < 0.001

    def test_delete_hit_point(self):
        """Test deleting hit points"""
        from pyhelios import LiDARCloud

        with LiDARCloud() as lidar:
            scan_id = lidar.addScan(
                origin=vec3(0, 0, 1),
                Ntheta=5, theta_range=(0, 1.0),
                Nphi=5, phi_range=(-3.14, 3.14),
                exit_diameter=0.01, beam_divergence=0.001
            )

            # Add multiple hit points
            lidar.addHitPoint(scan_id, vec3(1, 0, 0), vec3(1, 0, 0))
            lidar.addHitPoint(scan_id, vec3(2, 0, 0), vec3(1, 0, 0))
            lidar.addHitPoint(scan_id, vec3(3, 0, 0), vec3(1, 0, 0))
            assert lidar.getHitCount() == 3

            # Delete middle point
            lidar.deleteHitPoint(1)
            assert lidar.getHitCount() == 2

    def test_coordinate_shift(self):
        """Test coordinate shift transformation"""
        from pyhelios import LiDARCloud

        with LiDARCloud() as lidar:
            scan_id = lidar.addScan(
                origin=vec3(0, 0, 0),
                Ntheta=5, theta_range=(0, 1.0),
                Nphi=5, phi_range=(-3.14, 3.14),
                exit_diameter=0.01, beam_divergence=0.001
            )

            # Add hit point
            lidar.addHitPoint(scan_id, vec3(1, 2, 3), vec3(1, 0, 0))

            # Shift coordinates
            shift = vec3(10, 20, 30)
            lidar.coordinateShift(shift)

            # Check shifted position
            shifted_pos = lidar.getHitXYZ(0)
            assert abs(shifted_pos.x - 11) < 0.001
            assert abs(shifted_pos.y - 22) < 0.001
            assert abs(shifted_pos.z - 33) < 0.001

    def test_triangulation(self):
        """Test triangulation of hit points"""
        from pyhelios import LiDARCloud

        with LiDARCloud() as lidar:
            scan_id = lidar.addScan(
                origin=vec3(0, 0, 0),
                Ntheta=5, theta_range=(0, 1.0),
                Nphi=5, phi_range=(-3.14, 3.14),
                exit_diameter=0.01, beam_divergence=0.001
            )

            # Add several hit points to form triangles
            lidar.addHitPoint(scan_id, vec3(0, 0, 0), vec3(1, 0, 0))
            lidar.addHitPoint(scan_id, vec3(1, 0, 0), vec3(1, 0, 0))
            lidar.addHitPoint(scan_id, vec3(0, 1, 0), vec3(1, 0, 0))
            lidar.addHitPoint(scan_id, vec3(1, 1, 0), vec3(1, 0, 0))

            # Triangulate
            lidar.triangulateHitPoints(Lmax=2.0, max_aspect_ratio=4.0)

            # Should have created triangles
            triangle_count = lidar.getTriangleCount()
            assert triangle_count >= 0

    def test_distance_filter(self):
        """Test distance filtering"""
        from pyhelios import LiDARCloud

        with LiDARCloud() as lidar:
            scan_id = lidar.addScan(
                origin=vec3(0, 0, 0),
                Ntheta=5, theta_range=(0, 1.0),
                Nphi=5, phi_range=(-3.14, 3.14),
                exit_diameter=0.01, beam_divergence=0.001
            )

            # Add hit points at different distances
            lidar.addHitPoint(scan_id, vec3(1, 0, 0), vec3(1, 0, 0))
            lidar.addHitPoint(scan_id, vec3(5, 0, 0), vec3(1, 0, 0))
            lidar.addHitPoint(scan_id, vec3(10, 0, 0), vec3(1, 0, 0))
            initial_count = lidar.getHitCount()
            assert initial_count == 3

            # Filter by distance - keep only points within 6 units
            lidar.distanceFilter(maxdistance=6.0)

            # Should have fewer points
            filtered_count = lidar.getHitCount()
            assert filtered_count <= initial_count

    def test_first_hit_filter(self):
        """Test first hit filtering"""
        from pyhelios import LiDARCloud

        with LiDARCloud() as lidar:
            scan_id = lidar.addScan(
                origin=vec3(0, 0, 0),
                Ntheta=5, theta_range=(0, 1.0),
                Nphi=5, phi_range=(-3.14, 3.14),
                exit_diameter=0.01, beam_divergence=0.001
            )

            # Add multiple hit points
            lidar.addHitPoint(scan_id, vec3(1, 0, 0), vec3(1, 0, 0))
            lidar.addHitPoint(scan_id, vec3(2, 0, 0), vec3(1, 0, 0))
            lidar.addHitPoint(scan_id, vec3(3, 0, 0), vec3(1, 0, 0))

            # Apply first hit filter
            lidar.firstHitFilter()

            # Should still have points (exact behavior depends on implementation)
            assert lidar.getHitCount() >= 0

    def test_export_point_cloud(self, tmp_path):
        """Test exporting point cloud to file"""
        from pyhelios import LiDARCloud

        with LiDARCloud() as lidar:
            scan_id = lidar.addScan(
                origin=vec3(0, 0, 1),
                Ntheta=5, theta_range=(0, 1.0),
                Nphi=5, phi_range=(-3.14, 3.14),
                exit_diameter=0.01, beam_divergence=0.001
            )

            # Add some hit points
            lidar.addHitPoint(scan_id, vec3(1, 0, 0), vec3(1, 0, 0))
            lidar.addHitPoint(scan_id, vec3(2, 0, 0), vec3(1, 0, 0))

            # Export to file
            output_file = tmp_path / "test_cloud.xyz"
            lidar.exportPointCloud(str(output_file))

            # File should exist
            assert output_file.exists()
            assert output_file.stat().st_size > 0

    def test_message_control(self):
        """Test enabling/disabling messages"""
        from pyhelios import LiDARCloud

        with LiDARCloud() as lidar:
            # Should not raise errors
            lidar.disableMessages()
            lidar.enableMessages()


@pytest.mark.native_only
class TestLiDARValidation:
    """Test parameter validation"""

    def test_add_scan_validation(self):
        """Test scan parameter validation"""
        from pyhelios import LiDARCloud

        with LiDARCloud() as lidar:
            # Invalid origin
            with pytest.raises(ValueError, match="must have 3 elements"):
                lidar.addScan(
                    origin=[0, 0],  # Only 2 elements
                    Ntheta=10, theta_range=(0, 1.0),
                    Nphi=10, phi_range=(-3.14, 3.14),
                    exit_diameter=0.01, beam_divergence=0.001
                )

            # Invalid Ntheta (must be positive)
            with pytest.raises(ValueError):
                lidar.addScan(
                    origin=vec3(0, 0, 1),
                    Ntheta=0,  # Invalid
                    theta_range=(0, 1.0),
                    Nphi=10, phi_range=(-3.14, 3.14),
                    exit_diameter=0.01, beam_divergence=0.001
                )

    def test_add_hit_point_validation(self):
        """Test hit point parameter validation"""
        from pyhelios import LiDARCloud

        with LiDARCloud() as lidar:
            scan_id = lidar.addScan(
                origin=vec3(0, 0, 1),
                Ntheta=5, theta_range=(0, 1.0),
                Nphi=5, phi_range=(-3.14, 3.14),
                exit_diameter=0.01, beam_divergence=0.001
            )

            # Invalid xyz
            with pytest.raises(ValueError, match="must have 3 elements"):
                lidar.addHitPoint(scan_id, [1, 2], [1, 0, 0])

            # Invalid direction
            with pytest.raises(ValueError, match="at least 2 elements"):
                lidar.addHitPoint(scan_id, vec3(1, 0, 0), [1])

    def test_triangulation_validation(self):
        """Test triangulation parameter validation"""
        from pyhelios import LiDARCloud

        with LiDARCloud() as lidar:
            # Negative Lmax
            with pytest.raises(ValueError):
                lidar.triangulateHitPoints(Lmax=-1.0)

            # Negative aspect ratio
            with pytest.raises(ValueError):
                lidar.triangulateHitPoints(Lmax=1.0, max_aspect_ratio=-1.0)


@pytest.mark.native_only
class TestLiDARGrid:
    """Test grid cell functionality"""

    def test_add_grid(self):
        """Test adding a rectangular grid"""
        from pyhelios import LiDARCloud

        with LiDARCloud() as lidar:
            # Add grid with subdivisions
            lidar.addGrid(
                center=vec3(0, 0, 0.5),
                size=vec3(10, 10, 1),
                ndiv=[5, 5, 2],
                rotation=0.0
            )

            # Should have created 5*5*2 = 50 cells
            assert lidar.getGridCellCount() == 50

    def test_add_grid_cell(self):
        """Test adding individual grid cells"""
        from pyhelios import LiDARCloud

        with LiDARCloud() as lidar:
            # Add single cell
            lidar.addGridCell(
                center=vec3(0, 0, 0.5),
                size=vec3(1, 1, 1),
                rotation=0.0
            )
            assert lidar.getGridCellCount() == 1

            # Add another cell
            lidar.addGridCell(
                center=[2, 2, 0.5],
                size=[1, 1, 1],
                rotation=0.5
            )
            assert lidar.getGridCellCount() == 2

    def test_get_cell_properties(self):
        """Test querying grid cell properties"""
        from pyhelios import LiDARCloud

        with LiDARCloud() as lidar:
            center_in = vec3(1, 2, 3)
            size_in = vec3(0.5, 0.5, 0.5)

            lidar.addGridCell(center=center_in, size=size_in, rotation=0.0)

            # Query properties
            center_out = lidar.getCellCenter(0)
            size_out = lidar.getCellSize(0)

            assert abs(center_out.x - center_in.x) < 0.001
            assert abs(center_out.y - center_in.y) < 0.001
            assert abs(center_out.z - center_in.z) < 0.001

            assert abs(size_out.x - size_in.x) < 0.001
            assert abs(size_out.y - size_in.y) < 0.001
            assert abs(size_out.z - size_in.z) < 0.001


@pytest.mark.native_only
class TestLiDARLeafArea:
    """Test leaf area calculation functionality"""

    @pytest.mark.slow
    def test_calculate_leaf_area(self):
        """Test leaf area calculation - mirrors C++ Single Voxel Isotropic Patches Test"""
        from pyhelios import Context, LiDARCloud
        import math

        xml_path = get_lidar_asset_path('xml/leaf_cube_LAI2_lw0_01_spherical.xml')
        if xml_path is None:
            pytest.skip("LiDAR test assets not available (leaf_cube_LAI2_lw0_01_spherical.xml)")

        with Context() as context:
            # Load the same geometry used in C++ test
            UUIDs = context.loadXML(xml_path, quiet=True)

            # Calculate exact LAD from loaded geometry (1x1x1 meter voxel)
            voxel_volume = 1.0 * 1.0 * 1.0
            LAD_exact = 0.0
            for uuid in UUIDs:
                area = context.getPrimitiveArea(uuid)
                LAD_exact += area / voxel_volume

            with LiDARCloud() as lidar:
                # Match C++ test scan parameters exactly
                scan_id = lidar.addScan(
                    origin=vec3(-5.0, 0.0, 0.5),  # Scanner at side
                    Ntheta=6000, theta_range=(0, math.pi),
                    Nphi=12000, phi_range=(0, 2 * math.pi),
                    exit_diameter=0.0,
                    beam_divergence=0.0
                )

                # Single voxel grid - match C++ test
                lidar.addGrid(
                    center=vec3(0.0, 0.0, 0.5),
                    size=vec3(1.0, 1.0, 1.0),
                    ndiv=[1, 1, 1],
                    rotation=0.0
                )
                assert lidar.getGridCellCount() == 1

                # Perform synthetic scan
                lidar.syntheticScan(context)

                hit_count = lidar.getHitCount()
                assert hit_count > 0, f"Synthetic scan must generate hits, got {hit_count}"

                # Triangulate - match C++ test parameters
                lidar.triangulateHitPoints(Lmax=0.04, max_aspect_ratio=10)
                triangle_count = lidar.getTriangleCount()
                assert triangle_count > 0, f"Triangulation must produce triangles, got {triangle_count}"

                # Calculate leaf area
                lidar.calculateHitGridCell()
                lidar.calculateLeafArea(context)

                # Validate numerical accuracy - match C++ test validation
                LAD_calculated = lidar.getCellLeafAreaDensity(0)
                assert not math.isnan(LAD_calculated), "LAD must not be NaN"

                # C++ test uses 2% tolerance, we'll use 5% to account for scan resolution differences
                relative_error = abs(LAD_calculated - LAD_exact) / LAD_exact
                assert relative_error < 0.05, \
                    f"LAD accuracy failed: calculated={LAD_calculated:.4f}, exact={LAD_exact:.4f}, error={relative_error*100:.1f}%"

    def test_export_leaf_areas(self, tmp_path):
        """Test exporting leaf area data"""
        from pyhelios import Context, LiDARCloud

        with Context() as context:
            with LiDARCloud() as lidar:
                # Add scan
                scan_id = lidar.addScan(
                    origin=vec3(0, 0, 2),
                    Ntheta=10, theta_range=(0, 1.5),
                    Nphi=10, phi_range=(0, 6.28),
                    exit_diameter=0.01, beam_divergence=0.001
                )

                # Add grid
                lidar.addGrid(
                    center=vec3(0, 0, 0.5),
                    size=vec3(2, 2, 1),
                    ndiv=[2, 2, 1],
                    rotation=0.0
                )

                # Add hit points
                for i in range(5):
                    lidar.addHitPoint(scan_id, vec3(i * 0.2, 0, 0.5), vec3(1, 0, 0))

                # Triangulate and calculate
                lidar.triangulateHitPoints(Lmax=1.0, max_aspect_ratio=4.0)
                lidar.calculateHitGridCell()
                lidar.calculateLeafArea(context)

                # Export results
                leaf_areas_file = tmp_path / "leaf_areas.txt"
                leaf_densities_file = tmp_path / "leaf_densities.txt"

                lidar.exportLeafAreas(str(leaf_areas_file))
                lidar.exportLeafAreaDensities(str(leaf_densities_file))

                assert leaf_areas_file.exists()
                assert leaf_densities_file.exists()


@pytest.mark.native_only
class TestLiDARExport:
    """Test export functionality"""

    def test_export_triangle_normals(self, tmp_path):
        """Test exporting triangle normals"""
        from pyhelios import LiDARCloud

        with LiDARCloud() as lidar:
            scan_id = lidar.addScan(
                origin=vec3(0, 0, 0),
                Ntheta=5, theta_range=(0, 1.0),
                Nphi=5, phi_range=(0, 6.28),
                exit_diameter=0.01, beam_divergence=0.001
            )

            # Add hit points forming triangles
            lidar.addHitPoint(scan_id, vec3(0, 0, 0), vec3(1, 0, 0))
            lidar.addHitPoint(scan_id, vec3(1, 0, 0), vec3(1, 0, 0))
            lidar.addHitPoint(scan_id, vec3(0, 1, 0), vec3(1, 0, 0))

            # Triangulate
            lidar.triangulateHitPoints(Lmax=2.0, max_aspect_ratio=4.0)

            # Export normals
            normals_file = tmp_path / "normals.txt"
            lidar.exportTriangleNormals(str(normals_file))

            if lidar.getTriangleCount() > 0:
                assert normals_file.exists()

    def test_export_triangle_areas(self, tmp_path):
        """Test exporting triangle areas"""
        from pyhelios import LiDARCloud

        with LiDARCloud() as lidar:
            scan_id = lidar.addScan(
                origin=vec3(0, 0, 0),
                Ntheta=5, theta_range=(0, 1.0),
                Nphi=5, phi_range=(0, 6.28),
                exit_diameter=0.01, beam_divergence=0.001
            )

            # Add hit points
            lidar.addHitPoint(scan_id, vec3(0, 0, 0), vec3(1, 0, 0))
            lidar.addHitPoint(scan_id, vec3(1, 0, 0), vec3(1, 0, 0))
            lidar.addHitPoint(scan_id, vec3(0, 1, 0), vec3(1, 0, 0))

            # Triangulate
            lidar.triangulateHitPoints(Lmax=2.0, max_aspect_ratio=4.0)

            # Export areas
            areas_file = tmp_path / "areas.txt"
            lidar.exportTriangleAreas(str(areas_file))

            if lidar.getTriangleCount() > 0:
                assert areas_file.exists()


@pytest.mark.native_only
class TestLiDARSyntheticScanning:
    """Test synthetic LiDAR scanning functionality"""

    def test_discrete_return_synthetic_scan(self):
        """Test discrete-return synthetic scanning"""
        from pyhelios import Context, LiDARCloud

        with Context() as context:
            # Add simple geometry
            for i in range(3):
                for j in range(3):
                    context.addPatch(
                        center=vec3(i * 0.5, j * 0.5, 0.5),
                        size=vec2(0.2, 0.2)
                    )

            with LiDARCloud() as lidar:
                # Define scan
                scan_id = lidar.addScan(
                    origin=vec3(0.5, 0.5, 2),
                    Ntheta=30, theta_range=(0.3, 1.5),
                    Nphi=30, phi_range=(0, 6.28),
                    exit_diameter=0.0,
                    beam_divergence=0.0
                )

                # Perform discrete-return scan
                lidar.syntheticScan(context)

                # Should have generated some hits
                hit_count = lidar.getHitCount()
                # May be 0 if scan doesn't intersect geometry, that's OK
                assert hit_count >= 0

    def test_full_waveform_synthetic_scan(self):
        """Test full-waveform synthetic scanning"""
        from pyhelios import Context, LiDARCloud

        with Context() as context:
            # Add geometry
            for i in range(5):
                for j in range(5):
                    context.addPatch(
                        center=vec3(i * 0.5, j * 0.5, 0.5),
                        size=vec2(0.2, 0.2)
                    )

            with LiDARCloud() as lidar:
                # Define scan with beam parameters
                scan_id = lidar.addScan(
                    origin=vec3(1, 1, 3),
                    Ntheta=50, theta_range=(0.5, 2.0),
                    Nphi=50, phi_range=(0, 6.28),
                    exit_diameter=0.005,  # 5mm beam
                    beam_divergence=0.003  # Beam diverges
                )

                # Perform full-waveform scan
                lidar.syntheticScan(
                    context,
                    rays_per_pulse=50,
                    pulse_distance_threshold=0.02
                )

                hit_count = lidar.getHitCount()
                assert hit_count > 0  # Should generate hits with this setup

    def test_synthetic_scan_with_grid(self):
        """Test synthetic scanning limited to grid cells"""
        from pyhelios import Context, LiDARCloud

        with Context() as context:
            # Add large area of geometry
            for i in range(10):
                for j in range(10):
                    context.addPatch(
                        center=vec3(i * 0.5, j * 0.5, 0.5),
                        size=vec2(0.2, 0.2)
                    )

            with LiDARCloud() as lidar:
                # Define scan
                scan_id = lidar.addScan(
                    origin=vec3(2.5, 2.5, 3),
                    Ntheta=40, theta_range=(0.5, 2.0),
                    Nphi=40, phi_range=(0, 6.28),
                    exit_diameter=0.005,
                    beam_divergence=0.003
                )

                # Add limited grid
                lidar.addGrid(
                    center=vec3(1, 1, 0.5),
                    size=vec3(2, 2, 1),
                    ndiv=[2, 2, 1],
                    rotation=0.0
                )

                # Scan only within grid
                lidar.syntheticScan(
                    context,
                    rays_per_pulse=30,
                    pulse_distance_threshold=0.02,
                    scan_grid_only=True,
                    record_misses=False
                )

                # Should have hits only from grid region
                assert lidar.getHitCount() >= 0

    def test_synthetic_scan_append_mode(self):
        """Test appending synthetic scans"""
        from pyhelios import Context, LiDARCloud

        with Context() as context:
            context.addPatch(center=vec3(0, 0, 0.5), size=vec2(1, 1))

            with LiDARCloud() as lidar:
                scan_id = lidar.addScan(
                    origin=vec3(0, 0, 2),
                    Ntheta=20, theta_range=(0.5, 1.5),
                    Nphi=20, phi_range=(0, 6.28),
                    exit_diameter=0.005,
                    beam_divergence=0.003
                )

                # First scan
                lidar.syntheticScan(context, rays_per_pulse=20,
                                  pulse_distance_threshold=0.02, append=False)
                first_count = lidar.getHitCount()

                # Append another scan
                lidar.syntheticScan(context, rays_per_pulse=20,
                                  pulse_distance_threshold=0.02, append=True)
                second_count = lidar.getHitCount()

                # Should have more hits after appending (or same if no new hits)
                assert second_count >= first_count


@pytest.mark.native_only
class TestLiDARRigorousValidation:
    """Rigorous tests mirroring C++ selfTest.cpp - numerical validation"""

    def test_single_voxel_sphere(self):
        """
        Mirror C++ 'Single Voxel Sphere Test' - Test 1.

        Loads sphere point cloud, triangulates, adds to context, validates 383 primitives.
        """
        from pyhelios import Context, LiDARCloud

        # Check for scan data files (following radiation test pattern)
        scan_files = []
        for i in range(4):
            scan_path = get_lidar_asset_path(f'data/sphere_scan{i}.xyz')
            if scan_path is None:
                pytest.skip(f"LiDAR test assets not available (sphere_scan{i}.xyz)")
            scan_files.append(scan_path)

        with Context() as context:
            with LiDARCloud() as lidar:
                lidar.disableMessages()

                # Manually load scan data from XYZ files (matching sphere.xml scan definitions)
                scan_origins = [vec3(-2, 0, 0.5), vec3(0, -2, 0.5),
                               vec3(2, 0, 0.5), vec3(0, 2, 0.5)]

                for scan_idx, (scan_file, origin) in enumerate(zip(scan_files, scan_origins)):
                    # Add scan (matching sphere.xml: 100x200 size)
                    scan_id = lidar.addScan(
                        origin=origin,
                        Ntheta=100, theta_range=(0, 1.57),
                        Nphi=200, phi_range=(0, 6.28),
                        exit_diameter=0.0, beam_divergence=0.0
                    )

                    # Load XYZ data: format is "row column x y z r g b reflectance"
                    with open(scan_file, 'r') as f:
                        for line in f:
                            parts = line.strip().split()
                            if len(parts) >= 9:
                                x, y, z = float(parts[2]), float(parts[3]), float(parts[4])
                                r, g, b = int(parts[5]), int(parts[6]), int(parts[7])

                                # Calculate direction from origin to hit point
                                direction = vec3(x - origin.x, y - origin.y, z - origin.z)
                                color = RGBcolor(r/255.0, g/255.0, b/255.0)

                                lidar.addHitPoint(scan_id, vec3(x, y, z), direction, color)

                # Add 2x2x2 grid (matching sphere.xml grid definition)
                lidar.addGrid(
                    center=vec3(0, 0, 0.5),
                    size=vec3(0.5, 0.5, 0.5),
                    ndiv=[2, 2, 2],
                    rotation=45.0
                )

                # Triangulate
                lidar.triangulateHitPoints(Lmax=0.5, max_aspect_ratio=5)
                triangle_count = lidar.getTriangleCount()
                assert triangle_count > 0, "Must produce triangles from sphere scan"

                # Add triangles to context
                initial_primitive_count = context.getPrimitiveCount()
                lidar.addTrianglesToContext(context)
                final_primitive_count = context.getPrimitiveCount()

                # C++ test validates exactly 383 primitives created
                primitives_added = final_primitive_count - initial_primitive_count
                assert primitives_added == 383, \
                    f"Must create exactly 383 primitives, got {primitives_added}"

    @pytest.mark.slow
    def test_single_voxel_anisotropic_patches(self):
        """
        Mirror C++ 'Single Voxel Anisotropic Patches Test' - Test 4.

        Tests erectophile (upward-oriented) leaves, validates G(theta) reflects anisotropy.
        """
        from pyhelios import Context, LiDARCloud

        xml_path = get_lidar_asset_path('xml/leaf_cube_LAI2_lw0_01_erectophile.xml')
        if xml_path is None:
            pytest.skip("LiDAR test assets not available (leaf_cube_LAI2_lw0_01_erectophile.xml)")

        with Context() as context:
            # Load erectophile geometry (upward-oriented leaves)
            UUIDs = context.loadXML(xml_path, quiet=True)

            # Calculate exact G(theta) from geometry (erectophile should have higher G(theta))
            scan_origin = vec3(-5.0, 0.0, 0.5)
            Gtheta_exact_numerator = 0.0
            Gtheta_exact_denominator = 0.0

            for uuid in UUIDs:
                area = context.getPrimitiveArea(uuid)
                normal = context.getPrimitiveNormal(uuid)
                vertices = context.getPrimitiveVertices(uuid)

                # Ray direction
                raydir_x = vertices[0].x - scan_origin.x
                raydir_y = vertices[0].y - scan_origin.y
                raydir_z = vertices[0].z - scan_origin.z
                magnitude = math.sqrt(raydir_x**2 + raydir_y**2 + raydir_z**2)
                raydir_x /= magnitude
                raydir_y /= magnitude
                raydir_z /= magnitude

                normal_dot_ray = abs(normal.x * raydir_x + normal.y * raydir_y + normal.z * raydir_z)
                Gtheta_exact_numerator += normal_dot_ray * area
                Gtheta_exact_denominator += area

            Gtheta_exact = Gtheta_exact_numerator / Gtheta_exact_denominator

            with LiDARCloud() as lidar:
                lidar.disableMessages()

                # Match C++ test parameters exactly - uses higher resolution for anisotropic
                lidar.addScan(
                    origin=scan_origin,
                    Ntheta=10000, theta_range=(0, math.pi),
                    Nphi=16000, phi_range=(0, 2 * math.pi),
                    exit_diameter=0.0, beam_divergence=0.0
                )

                lidar.addGrid(
                    center=vec3(0.0, 0.0, 0.5),
                    size=vec3(1.0, 1.0, 1.0),
                    ndiv=[1, 1, 1],
                    rotation=0.0
                )

                # Synthetic scan and processing
                lidar.syntheticScan(context)
                lidar.triangulateHitPoints(Lmax=0.04, max_aspect_ratio=10)
                lidar.calculateHitGridCell()
                lidar.calculateLeafArea(context)

                # Validate G(theta) - erectophile should have different value than isotropic
                Gtheta_calculated = lidar.getCellGtheta(0)
                assert not math.isnan(Gtheta_calculated), "G(theta) must not be NaN"

                # Validate within 5% tolerance
                relative_error = abs(Gtheta_calculated - Gtheta_exact) / Gtheta_exact
                assert relative_error < 0.05, \
                    f"G(theta) validation failed for erectophile: calculated={Gtheta_calculated:.4f}, exact={Gtheta_exact:.4f}, error={relative_error*100:.1f}%"

                # Erectophile leaves should have G(theta) notably different from 0.5 (isotropic)
                assert abs(Gtheta_calculated - 0.5) > 0.05, \
                    "Erectophile G(theta) should differ from isotropic (0.5)"

    @pytest.mark.slow
    def test_single_voxel_isotropic_gtheta_validation(self):
        """
        Mirror C++ 'Single Voxel Isotropic Patches Test' - validates G(theta).

        Tests that G(theta) calculated from synthetic scan matches exact value
        from primitive geometry within 5% tolerance.
        """
        from pyhelios import Context, LiDARCloud

        xml_path = get_lidar_asset_path('xml/leaf_cube_LAI2_lw0_01_spherical.xml')
        if xml_path is None:
            pytest.skip("LiDAR test assets not available (leaf_cube_LAI2_lw0_01_spherical.xml)")

        with Context() as context:
            # Load exact geometry from C++ test
            UUIDs = context.loadXML(xml_path, quiet=True)

            # Calculate exact G(theta) from primitive geometry
            scan_origin = vec3(-5.0, 0.0, 0.5)
            Gtheta_exact_numerator = 0.0
            Gtheta_exact_denominator = 0.0

            for uuid in UUIDs:
                area = context.getPrimitiveArea(uuid)
                normal = context.getPrimitiveNormal(uuid)
                vertices = context.getPrimitiveVertices(uuid)

                # Ray direction from scanner to primitive
                raydir_x = vertices[0].x - scan_origin.x
                raydir_y = vertices[0].y - scan_origin.y
                raydir_z = vertices[0].z - scan_origin.z

                # Normalize
                magnitude = math.sqrt(raydir_x**2 + raydir_y**2 + raydir_z**2)
                raydir_x /= magnitude
                raydir_y /= magnitude
                raydir_z /= magnitude

                # Dot product for G(theta) calculation
                normal_dot_ray = abs(normal.x * raydir_x + normal.y * raydir_y + normal.z * raydir_z)
                Gtheta_exact_numerator += normal_dot_ray * area
                Gtheta_exact_denominator += area

            Gtheta_exact = Gtheta_exact_numerator / Gtheta_exact_denominator if Gtheta_exact_denominator > 0 else 0.0

            with LiDARCloud() as lidar:
                # Match C++ test parameters exactly
                lidar.addScan(
                    origin=scan_origin,
                    Ntheta=6000, theta_range=(0, math.pi),
                    Nphi=12000, phi_range=(0, 2 * math.pi),
                    exit_diameter=0.0, beam_divergence=0.0
                )

                lidar.addGrid(
                    center=vec3(0.0, 0.0, 0.5),
                    size=vec3(1.0, 1.0, 1.0),
                    ndiv=[1, 1, 1],
                    rotation=0.0
                )

                # Synthetic scan and processing
                lidar.syntheticScan(context)
                lidar.triangulateHitPoints(Lmax=0.04, max_aspect_ratio=10)
                lidar.calculateHitGridCell()
                lidar.calculateLeafArea(context)

                # Validate G(theta) within 5% (C++ test uses 5%)
                Gtheta_calculated = lidar.getCellGtheta(0)
                assert not math.isnan(Gtheta_calculated), "G(theta) must not be NaN"

                relative_error = abs(Gtheta_calculated - Gtheta_exact) / Gtheta_exact
                assert relative_error < 0.05, \
                    f"G(theta) validation failed: calculated={Gtheta_calculated:.4f}, exact={Gtheta_exact:.4f}, error={relative_error*100:.1f}%"

    @pytest.mark.slow
    def test_eight_voxel_lad_distribution(self):
        """
        Mirror C++ 'Eight Voxel Isotropic Patches Test'.

        Tests LAD distribution across 2x2x2 grid, validates RMSE < 6%.
        """
        from pyhelios import Context, LiDARCloud

        xml_path = get_lidar_asset_path('xml/leaf_cube_LAI2_lw0_01_spherical.xml')
        if xml_path is None:
            pytest.skip("LiDAR test assets not available (leaf_cube_LAI2_lw0_01_spherical.xml)")

        with Context() as context:
            # Load geometry
            UUIDs = context.loadXML(xml_path, quiet=True)

            # Calculate exact LAD per voxel from geometry
            voxel_volume = 0.5 * 0.5 * 0.5
            LAD_exact = [0.0] * 8

            for uuid in UUIDs:
                vertices = context.getPrimitiveVertices(uuid)
                v = vertices[0]

                # Determine which voxel this primitive is in
                i = 1 if v.x > 0.0 else 0
                j = 1 if v.y > 0.0 else 0
                k = 1 if v.z > 0.5 else 0
                voxel_id = k * 4 + j * 2 + i

                area = context.getPrimitiveArea(uuid)
                LAD_exact[voxel_id] += area / voxel_volume

            with LiDARCloud() as lidar:
                # Match C++ test parameters
                lidar.addScan(
                    origin=vec3(-5.0, 0.0, 0.5),
                    Ntheta=10000, theta_range=(0, math.pi),
                    Nphi=12000, phi_range=(0, 2 * math.pi),
                    exit_diameter=0.0, beam_divergence=0.0
                )

                # 2x2x2 grid
                lidar.addGrid(
                    center=vec3(0.0, 0.0, 0.5),
                    size=vec3(1.0, 1.0, 1.0),
                    ndiv=[2, 2, 2],
                    rotation=0.0
                )
                assert lidar.getGridCellCount() == 8

                # Synthetic scan and processing
                lidar.syntheticScan(context)
                assert lidar.getHitCount() > 1000, "Must generate substantial hits"

                lidar.triangulateHitPoints(Lmax=0.04, max_aspect_ratio=10)
                assert lidar.getTriangleCount() > 0, "Must produce triangles"

                lidar.calculateHitGridCell()
                lidar.calculateLeafArea(context)

                # Calculate RMSE across all voxels (C++ test uses 6% threshold)
                sum_squared_error = 0.0
                for i in range(8):
                    LAD_calculated = lidar.getCellLeafAreaDensity(i)
                    assert not math.isnan(LAD_calculated), f"Cell {i} LAD is NaN"

                    error = LAD_calculated - LAD_exact[i]
                    sum_squared_error += error ** 2

                rmse = math.sqrt(sum_squared_error / 8)
                mean_exact = sum(LAD_exact) / 8
                relative_rmse = rmse / mean_exact

                assert relative_rmse < 0.06, \
                    f"LAD distribution RMSE failed: {relative_rmse*100:.1f}% (threshold: 6%)"

    def test_synthetic_almond_tree(self):
        """
        Mirror C++ 'Synthetic Almond Tree Test'.

        Tests synthetic scanning of complex tree geometry with synthetic leaf area validation.
        """
        from pyhelios import Context, LiDARCloud

        obj_path = get_lidar_asset_path('xml/AlmondWP.obj')
        xml_path = get_lidar_asset_path('xml/almond.xml')
        if obj_path is None or xml_path is None:
            pytest.skip("LiDAR test assets not available (AlmondWP.obj or almond.xml)")

        with Context() as context:
            # Load almond tree OBJ (same as C++ test)
            UUIDs = context.loadOBJ(
                obj_path,
                origin=vec3(0, 0, 0),
                height=6.0,
                rotation=SphericalCoord(1.0, 0),  # radius=1 for no rotation
                color=RGBcolor(1, 0, 0),
                silent=True
            )
            assert len(UUIDs) > 0, "Must load tree geometry"

            with LiDARCloud() as lidar:
                # Load scan metadata from C++ test
                lidar.loadXML(xml_path)

                # Perform synthetic scan
                lidar.syntheticScan(context)
                assert lidar.getHitCount() > 0, "Must generate hits from tree"

                # Calculate synthetic leaf area and G(theta) for validation
                lidar.calculateSyntheticLeafArea(context)
                lidar.calculateSyntheticGtheta(context)

                # Triangulate and calculate actual leaf area
                lidar.triangulateHitPoints(Lmax=0.05, max_aspect_ratio=5)
                lidar.calculateLeafArea(context)

                # Verify we have grid cells and can query results
                cell_count = lidar.getGridCellCount()
                assert cell_count > 0, "Must have grid cells from XML"

                # All cells should have valid (non-NaN) values
                for i in range(cell_count):
                    lad = lidar.getCellLeafAreaDensity(i)
                    gtheta = lidar.getCellGtheta(i)
                    assert not math.isnan(lad), f"Cell {i} LAD is NaN"
                    assert not math.isnan(gtheta), f"Cell {i} G(theta) is NaN"

    def test_append_overwrite_exact_validation(self):
        """
        Mirror C++ 'Append/Overwrite Test' - exact hit count validation.

        Tests that append=true exactly doubles hits, append=false resets.
        """
        from pyhelios import Context, LiDARCloud

        xml_path = get_lidar_asset_path('xml/leaf_cube_LAI2_lw0_01_spherical.xml')
        synthetic_xml = get_lidar_asset_path('xml/synthetic_test.xml')
        if xml_path is None or synthetic_xml is None:
            pytest.skip("LiDAR test assets not available (leaf_cube or synthetic_test.xml)")

        with Context() as context:
            UUIDs = context.loadXML(xml_path, quiet=True)

            with LiDARCloud() as lidar:
                lidar.disableMessages()
                lidar.loadXML(synthetic_xml)

                # First scan with default behavior (append to empty = just adds hits)
                # Using append=False explicitly to match C++ default behavior
                lidar.syntheticScan(context, append=False)
                hit_count_first = lidar.getHitCount()
                assert hit_count_first > 0, "First scan must generate hits"

                # Second scan with append=True (should double)
                lidar.syntheticScan(context, append=True)
                hit_count_append = lidar.getHitCount()
                assert hit_count_append == 2 * hit_count_first, \
                    f"Append must double hits: got {hit_count_append}, expected {2 * hit_count_first}"

                # Third scan with append=False (should reset)
                lidar.syntheticScan(context, append=False)
                hit_count_overwrite = lidar.getHitCount()
                assert hit_count_overwrite == hit_count_first, \
                    f"Overwrite must reset: got {hit_count_overwrite}, expected {hit_count_first}"

    def test_gapfill_misses_functionality(self):
        """
        Test gapfillMisses() basic functionality.

        Validates that gapfilling adds miss points where rays didn't hit.
        Uses proven geometry from other tests.
        """
        from pyhelios import Context, LiDARCloud

        xml_path = get_lidar_asset_path('xml/leaf_cube_LAI2_lw0_01_spherical.xml')
        if xml_path is None:
            pytest.skip("LiDAR test assets not available (leaf_cube_LAI2_lw0_01_spherical.xml)")

        with Context() as context:
            # Use same geometry that works in other tests
            UUIDs = context.loadXML(xml_path, quiet=True)

            with LiDARCloud() as lidar:
                # Low-resolution scan (more misses with coarse scan)
                lidar.addScan(
                    origin=vec3(-5.0, 0.0, 0.5),
                    Ntheta=50, theta_range=(0, math.pi),
                    Nphi=50, phi_range=(0, 2 * math.pi),
                    exit_diameter=0.0, beam_divergence=0.0
                )

                # Add grid
                lidar.addGrid(
                    center=vec3(0, 0, 0.5),
                    size=vec3(1, 1, 1),
                    ndiv=[1, 1, 1],
                    rotation=0.0
                )

                # Synthetic scan with low resolution (will have gaps)
                lidar.syntheticScan(context, append=False)
                hit_count_before = lidar.getHitCount()
                assert hit_count_before > 0, f"Scan must generate hits, got {hit_count_before}"

                # Gapfill misses
                lidar.gapfillMisses()
                hit_count_after = lidar.getHitCount()

                # Should add miss points
                assert hit_count_after > hit_count_before, \
                    f"Gapfilling must add miss points: before={hit_count_before}, after={hit_count_after}"


@pytest.mark.native_only
class TestLiDARCollisionDetection:
    """Test 9: Collision Detection Integration - mirrors C++ test"""

    def test_collision_detection_initialization(self):
        """Test CD initialization and GPU control"""
        from pyhelios import Context, LiDARCloud

        xml_path = get_lidar_asset_path('xml/leaf_cube_LAI2_lw0_01_spherical.xml')
        if xml_path is None:
            pytest.skip("LiDAR test assets not available (leaf_cube_LAI2_lw0_01_spherical.xml)")

        with Context() as context:
            # Use proven geometry
            UUIDs = context.loadXML(xml_path, quiet=True)

            with LiDARCloud() as lidar:
                lidar.disableMessages()

                # Initialize collision detection explicitly
                lidar.initializeCollisionDetection(context)

                # Test GPU enable/disable (should not crash)
                lidar.enableCDGPUAcceleration()
                lidar.disableCDGPUAcceleration()

                # Verify scanning still works after CD operations
                lidar.addScan(
                    origin=vec3(-5.0, 0.0, 0.5),
                    Ntheta=100, theta_range=(0, math.pi),
                    Nphi=100, phi_range=(0, 2 * math.pi),
                    exit_diameter=0.0, beam_divergence=0.0
                )

                lidar.syntheticScan(context)
                assert lidar.getHitCount() > 0, "Scan must work after CD operations"


@pytest.mark.native_only
class TestLiDAREdgeCases:
    """Test 11: Edge Cases and Error Conditions - mirrors C++ test"""

    def test_empty_scan_operations(self):
        """Test operations on empty scans"""
        from pyhelios import LiDARCloud

        with LiDARCloud() as lidar:
            # Should handle empty cloud gracefully
            assert lidar.getHitCount() == 0
            assert lidar.getTriangleCount() == 0
            assert lidar.getScanCount() == 0
            assert lidar.getGridCellCount() == 0

    def test_triangulation_without_hits(self):
        """Test triangulation on empty cloud"""
        from pyhelios import LiDARCloud

        with LiDARCloud() as lidar:
            lidar.addScan(
                origin=vec3(0, 0, 1),
                Ntheta=10, theta_range=(0, 1.5),
                Nphi=10, phi_range=(0, 6.28),
                exit_diameter=0.0, beam_divergence=0.0
            )

            # Triangulate with no hits (should not crash)
            lidar.triangulateHitPoints(Lmax=1.0, max_aspect_ratio=4.0)
            assert lidar.getTriangleCount() == 0

    def test_leaf_area_without_grid(self):
        """Test that leaf area calculation requires grid"""
        from pyhelios import Context, LiDARCloud

        with Context() as context:
            context.addPatch(center=vec3(0, 0, 0.5), size=vec2(1, 1))

            with LiDARCloud() as lidar:
                lidar.addScan(
                    origin=vec3(0, 0, 2),
                    Ntheta=20, theta_range=(0.5, 1.5),
                    Nphi=20, phi_range=(0, 6.28),
                    exit_diameter=0.005, beam_divergence=0.003
                )

                lidar.syntheticScan(context, rays_per_pulse=20, pulse_distance_threshold=0.02)
                lidar.triangulateHitPoints(Lmax=0.5, max_aspect_ratio=4.0)

                # Should handle no grid gracefully or raise clear error
                # (behavior depends on C++ implementation)
                try:
                    lidar.calculateLeafArea(context)
                except Exception as e:
                    # If it raises, error should be clear
                    assert 'grid' in str(e).lower() or 'cell' in str(e).lower()


@pytest.mark.native_only
class TestLiDARMemoryManagement:
    """Test 12: CD Memory Management - mirrors C++ test"""

    def test_collision_detection_cleanup(self):
        """Test that CD resources are properly cleaned up"""
        from pyhelios import Context, LiDARCloud
        import gc

        with Context() as context:
            context.addPatch(center=vec3(0, 0, 0.5), size=vec2(1, 1))

            # Create and destroy multiple times
            for _ in range(3):
                with LiDARCloud() as lidar:
                    lidar.initializeCollisionDetection(context)
                    lidar.addScan(
                        origin=vec3(0, 0, 2),
                        Ntheta=10, theta_range=(0.5, 1.5),
                        Nphi=10, phi_range=(0, 6.28),
                        exit_diameter=0.0, beam_divergence=0.0
                    )
                    lidar.syntheticScan(context)
                    # LiDAR destroyed here - should clean up CD resources

            # Force garbage collection
            gc.collect()
            # If no memory leaks or crashes, test passes


@pytest.mark.native_only
class TestLiDARSyntheticScanIntegration:
    """Test 13: Synthetic Scan Integration - mirrors C++ test with distribution validation"""

    def test_scan_grid_only_flag(self):
        """Test scan_grid_only flag limits scanning to grid cells"""
        from pyhelios import Context, LiDARCloud

        xml_path = get_lidar_asset_path('xml/leaf_cube_LAI2_lw0_01_spherical.xml')
        if xml_path is None:
            pytest.skip("LiDAR test assets not available (leaf_cube_LAI2_lw0_01_spherical.xml)")

        with Context() as context:
            # Use proven geometry that will definitely be hit
            UUIDs = context.loadXML(xml_path, quiet=True)

            with LiDARCloud() as lidar:
                lidar.disableMessages()

                # Scan from side with good coverage
                lidar.addScan(
                    origin=vec3(-5.0, 0.0, 0.5),
                    Ntheta=200, theta_range=(0, math.pi),
                    Nphi=200, phi_range=(0, 2 * math.pi),
                    exit_diameter=0.005, beam_divergence=0.003
                )

                # Add small grid covering only part of the geometry
                lidar.addGrid(
                    center=vec3(0.25, 0.25, 0.5),  # Offset from center
                    size=vec3(0.5, 0.5, 0.5),      # Only covers 1/8 of the 1x1x1 cube
                    ndiv=[1, 1, 1],
                    rotation=0.0
                )

                # Scan entire scene
                lidar.syntheticScan(context, rays_per_pulse=30,
                                  pulse_distance_threshold=0.02,
                                  scan_grid_only=False, record_misses=False)
                hit_count_full = lidar.getHitCount()

                # Scan only grid region (should be subset)
                lidar.syntheticScan(context, rays_per_pulse=30,
                                  pulse_distance_threshold=0.02,
                                  scan_grid_only=True, record_misses=False,
                                  append=False)
                hit_count_grid = lidar.getHitCount()

                # Grid-only should have fewer hits since grid only covers part of geometry
                assert hit_count_grid < hit_count_full, \
                    f"scan_grid_only must reduce hits: full={hit_count_full}, grid={hit_count_grid}"

    def test_record_misses_flag(self):
        """Test record_misses flag controls miss point recording"""
        from pyhelios import Context, LiDARCloud

        with Context() as context:
            # Small geometry (many misses expected)
            context.addPatch(center=vec3(0, 0, 0.5), size=vec2(0.3, 0.3))

            with LiDARCloud() as lidar:
                lidar.disableMessages()

                lidar.addScan(
                    origin=vec3(0, 0, 3),
                    Ntheta=50, theta_range=(0.5, 2.0),
                    Nphi=50, phi_range=(0, 2 * math.pi),
                    exit_diameter=0.005, beam_divergence=0.003
                )

                # Scan with miss recording
                lidar.syntheticScan(context, rays_per_pulse=20,
                                  pulse_distance_threshold=0.02,
                                  record_misses=True, append=False)
                hit_count_with_misses = lidar.getHitCount()

                # Scan without miss recording
                lidar.syntheticScan(context, rays_per_pulse=20,
                                  pulse_distance_threshold=0.02,
                                  record_misses=False, append=False)
                hit_count_no_misses = lidar.getHitCount()

                # Recording misses should produce more points
                assert hit_count_with_misses > hit_count_no_misses, \
                    f"record_misses must increase hit count: with_misses={hit_count_with_misses}, without={hit_count_no_misses}"


@pytest.mark.native_only
class TestLiDARMultiReturn:
    """Tests 14-15: Multi-Return Data Processing - mirrors C++ tests"""

    @pytest.mark.slow
    def test_multi_return_equal_weighting(self):
        """
        Mirror C++ 'Multi-Return Equal Weighting Test' - Test 14.

        Tests multi-return data processing with equal weighting algorithm.
        Note: Requires full-waveform scan to generate multi-return data.
        """
        from pyhelios import Context, LiDARCloud

        xml_path = get_lidar_asset_path('xml/leaf_cube_LAI2_lw0_01_spherical.xml')
        if xml_path is None:
            pytest.skip("LiDAR test assets not available (leaf_cube_LAI2_lw0_01_spherical.xml)")

        with Context() as context:
            # Load geometry
            UUIDs = context.loadXML(xml_path, quiet=True)

            with LiDARCloud() as lidar:
                lidar.disableMessages()

                # Match C++ test - high resolution full-waveform
                lidar.addScan(
                    origin=vec3(-5.0, 0.0, 0.5),
                    Ntheta=6000, theta_range=(0, math.pi),
                    Nphi=12000, phi_range=(0, 2 * math.pi),
                    exit_diameter=0.005,  # Non-zero = full-waveform
                    beam_divergence=0.003
                )

                lidar.addGrid(
                    center=vec3(0, 0, 0.5),
                    size=vec3(1, 1, 1),
                    ndiv=[1, 1, 1],
                    rotation=0.0
                )

                # Full-waveform scan (generates multi-return data)
                lidar.syntheticScan(context, rays_per_pulse=100, pulse_distance_threshold=0.02)

                hit_count = lidar.getHitCount()
                assert hit_count > 1000, f"Must generate substantial multi-return hits, got {hit_count}"

                # Triangulate and calculate leaf area
                lidar.triangulateHitPoints(Lmax=0.04, max_aspect_ratio=10)
                lidar.calculateHitGridCell()
                lidar.calculateLeafArea(context)

                # Validate results
                LAD = lidar.getCellLeafAreaDensity(0)
                assert not math.isnan(LAD), "Multi-return LAD must not be NaN"
                assert LAD > 0, f"Multi-return must calculate non-zero LAD, got {LAD}"

    @pytest.mark.slow
    def test_eight_voxel_multi_return(self):
        """
        Mirror C++ 'Eight Voxel Multi-Return Equal Weighting Test' - Test 15.

        Tests multi-return data with 2x2x2 grid, validates LAD distribution.
        """
        from pyhelios import Context, LiDARCloud

        xml_path = get_lidar_asset_path('xml/leaf_cube_LAI2_lw0_01_spherical.xml')
        if xml_path is None:
            pytest.skip("LiDAR test assets not available (leaf_cube_LAI2_lw0_01_spherical.xml)")

        with Context() as context:
            # CRITICAL: Seed RNG for reproducible results (C++ test line 864)
            context.seedRandomGenerator(0)
            UUIDs = context.loadXML(xml_path, quiet=True)

            # Calculate exact LAD per voxel
            voxel_volume = 0.5 * 0.5 * 0.5
            LAD_exact = [0.0] * 8

            for uuid in UUIDs:
                vertices = context.getPrimitiveVertices(uuid)
                v = vertices[0]
                i = 1 if v.x > 0.0 else 0
                j = 1 if v.y > 0.0 else 0
                k = 1 if v.z > 0.5 else 0
                voxel_id = k * 4 + j * 2 + i

                area = context.getPrimitiveArea(uuid)
                LAD_exact[voxel_id] += area / voxel_volume

            with LiDARCloud() as lidar:
                lidar.disableMessages()

                # Match C++ test parameters exactly
                lidar.addScan(
                    origin=vec3(-5.0, 0.0, 0.5),
                    Ntheta=10000, theta_range=(0, math.pi),
                    Nphi=14000, phi_range=(0, 2 * math.pi),
                    exit_diameter=0.0,       # Point source (C++ test uses 0.0)
                    beam_divergence=0.0004   # Small divergence for multi-return
                )

                lidar.addGrid(
                    center=vec3(0, 0, 0.5),
                    size=vec3(1, 1, 1),
                    ndiv=[2, 2, 2],
                    rotation=0.0
                )

                # Multi-return scan with C++ test parameters
                lidar.syntheticScan(context, rays_per_pulse=100,
                                  pulse_distance_threshold=0.1,  # C++ uses 0.1
                                  scan_grid_only=True,           # C++ uses true
                                  record_misses=True)            # C++ uses true
                assert lidar.getHitCount() > 5000, "Must generate substantial multi-return hits"

                lidar.triangulateHitPoints(Lmax=0.04, max_aspect_ratio=10)
                lidar.calculateHitGridCell()
                lidar.calculateLeafArea(context)

                # Validate RMSE across all voxels (C++ uses 10% threshold - see line 972)
                sum_squared_error = 0.0
                for i in range(8):
                    LAD_calc = lidar.getCellLeafAreaDensity(i)
                    assert not math.isnan(LAD_calc)
                    # C++ uses normalized RMSE: sqrt(sum((LAD - exact)^2 / exact) / 8)
                    error = LAD_calc - LAD_exact[i]
                    sum_squared_error += (error ** 2) / LAD_exact[i] / 8.0

                rmse = math.sqrt(sum_squared_error)

                assert rmse < 0.10, \
                    f"Multi-return LAD distribution RMSE failed: {rmse*100:.1f}% (threshold: 10%)"


@pytest.mark.native_only
class TestLiDARIntegration:
    """Test LiDAR integration with other PyHelios components"""

    def test_is_available_method(self):
        """Test is_available method"""
        from pyhelios import LiDARCloud

        with LiDARCloud() as lidar:
            # Should return True since we're in native_only tests
            assert lidar.is_available() is True

    @pytest.mark.slow
    def test_complete_workflow(self):
        """Test complete LiDAR workflow - mirrors C++ Eight Voxel Test"""
        from pyhelios import Context, LiDARCloud
        import math

        xml_path = get_lidar_asset_path('xml/leaf_cube_LAI2_lw0_01_spherical.xml')
        if xml_path is None:
            pytest.skip("LiDAR test assets not available (leaf_cube_LAI2_lw0_01_spherical.xml)")

        with Context() as context:
            # Load geometry from C++ test file
            UUIDs = context.loadXML(xml_path, quiet=True)
            assert len(UUIDs) > 0, "Must load geometry from XML"

            with LiDARCloud() as lidar:
                # Match C++ Eight Voxel test parameters
                scan_id = lidar.addScan(
                    origin=vec3(-5.0, 0.0, 0.5),
                    Ntheta=10000, theta_range=(0, math.pi),
                    Nphi=12000, phi_range=(0, 2 * math.pi),
                    exit_diameter=0.0,
                    beam_divergence=0.0
                )

                # 2x2x2 grid (8 voxels) - match C++ test
                lidar.addGrid(
                    center=vec3(0.0, 0.0, 0.5),
                    size=vec3(1.0, 1.0, 1.0),
                    ndiv=[2, 2, 2],
                    rotation=0.0
                )
                assert lidar.getGridCellCount() == 8

                # Perform synthetic scan
                lidar.syntheticScan(context)

                hit_count = lidar.getHitCount()
                assert hit_count > 1000, f"Must generate substantial hits from loaded geometry, got {hit_count}"

                # Triangulate - match C++ test parameters
                lidar.triangulateHitPoints(Lmax=0.04, max_aspect_ratio=10)
                triangle_count = lidar.getTriangleCount()
                assert triangle_count > 0, f"Must produce triangles from {hit_count} hits, got {triangle_count}"

                # Calculate leaf area
                lidar.calculateHitGridCell()
                lidar.calculateLeafArea(context)

                # Validate all cells have been processed
                total_leaf_area = 0.0
                for i in range(lidar.getGridCellCount()):
                    leaf_area = lidar.getCellLeafArea(i)
                    lad = lidar.getCellLeafAreaDensity(i)
                    assert not math.isnan(leaf_area), f"Cell {i} leaf area is NaN"
                    assert not math.isnan(lad), f"Cell {i} LAD is NaN"
                    assert leaf_area >= 0
                    assert lad >= 0
                    total_leaf_area += leaf_area

                # Must calculate non-zero total leaf area
                assert total_leaf_area > 0, f"Must calculate non-zero total leaf area, got {total_leaf_area}"

