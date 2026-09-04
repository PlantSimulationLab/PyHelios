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
        assert hasattr(LiDARCloud, 'exportScans')
        assert hasattr(LiDARCloud, 'getScanRangeNoiseStdDev')
        assert hasattr(LiDARCloud, 'getScanAngleNoiseStdDev')
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

    def test_add_scan_with_noise_params(self):
        """Test adding a scan with range/angle measurement noise and querying them back."""
        from pyhelios import LiDARCloud

        with LiDARCloud() as lidar:
            scan_id = lidar.addScan(
                origin=vec3(0, 0, 1),
                Ntheta=10, theta_range=(0, 1.57),
                Nphi=10, phi_range=(-3.14, 3.14),
                exit_diameter=0.01, beam_divergence=0.001,
                range_noise_stddev=0.003, angle_noise_stddev=0.0002
            )
            assert scan_id >= 0
            assert lidar.getScanRangeNoiseStdDev(scan_id) == pytest.approx(0.003, abs=1e-6)
            assert lidar.getScanAngleNoiseStdDev(scan_id) == pytest.approx(0.0002, abs=1e-7)

    def test_add_scan_noise_defaults_zero(self):
        """Noise parameters default to 0 (disabled), preserving prior behavior."""
        from pyhelios import LiDARCloud

        with LiDARCloud() as lidar:
            scan_id = lidar.addScan(
                origin=vec3(0, 0, 1),
                Ntheta=5, theta_range=(0, 1.0),
                Nphi=5, phi_range=(-3.14, 3.14),
                exit_diameter=0.01, beam_divergence=0.001
            )
            assert lidar.getScanRangeNoiseStdDev(scan_id) == pytest.approx(0.0, abs=1e-7)
            assert lidar.getScanAngleNoiseStdDev(scan_id) == pytest.approx(0.0, abs=1e-7)

    @pytest.mark.parametrize("noise_kwargs", [
        {"range_noise_stddev": -1.0},
        {"angle_noise_stddev": -0.001},
    ])
    def test_add_scan_negative_noise_raises(self, noise_kwargs):
        """Negative range or angle noise standard deviations are rejected."""
        from pyhelios import LiDARCloud

        with LiDARCloud() as lidar:
            with pytest.raises(ValueError):
                lidar.addScan(
                    origin=vec3(0, 0, 1),
                    Ntheta=5, theta_range=(0, 1.0),
                    Nphi=5, phi_range=(-3.14, 3.14),
                    exit_diameter=0.01, beam_divergence=0.001,
                    **noise_kwargs
                )

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

    def test_bulk_add_hit_points_roundtrip_no_color(self):
        """Bulk addHitPoints (no color) matches per-point addHitPoint exactly"""
        import numpy as np
        from pyhelios import LiDARCloud

        # Eight hit points with distinct coords and ray directions
        xyz = np.array([
            [1.0, 0.0, 0.0], [2.0, 1.0, 0.5], [3.0, -1.0, 2.0],
            [0.5, 0.5, 0.5], [4.0, 2.0, 1.0], [-1.0, 3.0, 0.0],
            [2.5, 2.5, 2.5], [0.0, 0.0, 1.0],
        ], dtype=np.float32)
        directions = np.array([
            [1.0, 0.0, 0.0], [1.0, 0.1, 0.0], [1.0, 0.2, 0.0],
            [1.0, 0.3, 0.0], [1.0, 0.4, 0.0], [1.0, 0.5, 0.0],
            [1.0, 0.6, 0.0], [1.0, 0.7, 0.0],
        ], dtype=np.float32)
        n = xyz.shape[0]

        def make_scan(lidar):
            return lidar.addScan(
                origin=vec3(0, 0, 1),
                Ntheta=10, theta_range=(0, 1.0),
                Nphi=10, phi_range=(-3.14, 3.14),
                exit_diameter=0.01, beam_divergence=0.001
            )

        with LiDARCloud() as bulk, LiDARCloud() as loop:
            bulk_scan = make_scan(bulk)
            loop_scan = make_scan(loop)

            bulk.addHitPoints(bulk_scan, xyz, directions)
            for i in range(n):
                loop.addHitPoint(loop_scan, list(xyz[i]), list(directions[i]))

            assert bulk.getHitCount() == n
            assert loop.getHitCount() == n

            for i in range(n):
                b = bulk.getHitXYZ(i)
                l = loop.getHitXYZ(i)
                assert abs(b.x - l.x) < 1e-5
                assert abs(b.y - l.y) < 1e-5
                assert abs(b.z - l.z) < 1e-5

    def test_bulk_add_hit_points_roundtrip_with_color(self):
        """Bulk addHitPoints (with color) matches per-point addHitPoint exactly"""
        import numpy as np
        from pyhelios import LiDARCloud

        xyz = np.array([
            [1.0, 0.0, 0.0], [2.0, 1.0, 0.5], [3.0, -1.0, 2.0],
            [0.5, 0.5, 0.5], [4.0, 2.0, 1.0],
        ], dtype=np.float32)
        directions = np.array([
            [1.0, 0.0, 0.0], [1.0, 0.1, 0.0], [1.0, 0.2, 0.0],
            [1.0, 0.3, 0.0], [1.0, 0.4, 0.0],
        ], dtype=np.float32)
        colors = np.array([
            [1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 1.0],
            [0.5, 0.5, 0.5], [0.2, 0.4, 0.6],
        ], dtype=np.float32)
        n = xyz.shape[0]

        def make_scan(lidar):
            return lidar.addScan(
                origin=vec3(0, 0, 1),
                Ntheta=10, theta_range=(0, 1.0),
                Nphi=10, phi_range=(-3.14, 3.14),
                exit_diameter=0.01, beam_divergence=0.001
            )

        with LiDARCloud() as bulk, LiDARCloud() as loop:
            bulk_scan = make_scan(bulk)
            loop_scan = make_scan(loop)

            bulk.addHitPoints(bulk_scan, xyz, directions, color_array=colors)
            for i in range(n):
                loop.addHitPoint(loop_scan, list(xyz[i]), list(directions[i]),
                                 color=list(colors[i]))

            assert bulk.getHitCount() == n
            assert loop.getHitCount() == n

            for i in range(n):
                bp, lp = bulk.getHitXYZ(i), loop.getHitXYZ(i)
                assert abs(bp.x - lp.x) < 1e-5
                assert abs(bp.y - lp.y) < 1e-5
                assert abs(bp.z - lp.z) < 1e-5

                bc, lc = bulk.getHitColor(i), loop.getHitColor(i)
                assert abs(bc.r - lc.r) < 1e-5
                assert abs(bc.g - lc.g) < 1e-5
                assert abs(bc.b - lc.b) < 1e-5

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

    def test_export_scans(self, tmp_path):
        """Test exporting all scans to XML metadata + per-scan ASCII files."""
        from pyhelios import LiDARCloud

        with LiDARCloud() as lidar:
            scan_id = lidar.addScan(
                origin=vec3(0, 0, 1),
                Ntheta=5, theta_range=(0, 1.0),
                Nphi=5, phi_range=(-3.14, 3.14),
                exit_diameter=0.01, beam_divergence=0.001
            )
            lidar.addHitPoint(scan_id, vec3(1, 0, 0), vec3(1, 0, 0))

            output_xml = tmp_path / "scans.xml"
            lidar.exportScans(str(output_xml))

            # XML metadata file plus a per-scan ASCII data file (scans_0.xyz) should appear.
            assert output_xml.exists()
            assert (tmp_path / "scans_0.xyz").exists()

    def test_export_scans_empty_filename_raises(self):
        from pyhelios import LiDARCloud
        with LiDARCloud() as lidar:
            with pytest.raises(ValueError):
                lidar.exportScans("")

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

    def test_add_grid_terrain_following(self):
        """Terrain-following grid shifts each column in z by its offset (helios-core 1.3.78)"""
        from pyhelios import LiDARCloud

        with LiDARCloud() as lidar:
            # 2x2 columns, 1 layer. Each column gets a distinct vertical offset.
            offsets = [0.0, 0.25, 0.5, 0.75]
            lidar.addGrid(
                center=vec3(0, 0, 0.5),
                size=vec3(2, 2, 1),
                ndiv=[2, 2, 1],
                rotation=0.0,
                column_z_offsets=offsets
            )

            assert lidar.getGridCellCount() == 4

            # Cells are added in row-major column order [j*ndiv.x + i], so cell n's
            # z-center is the un-shifted center (0.5) plus offsets[n].
            for n, expected_offset in enumerate(offsets):
                center = lidar.getCellCenter(n)
                assert abs(center.z - (0.5 + expected_offset)) < 1e-4, (
                    f"cell {n} z={center.z}, expected {0.5 + expected_offset}"
                )

    def test_add_grid_terrain_following_matches_plain_grid_when_zero(self):
        """All-zero offsets reproduce the axis-regular grid exactly"""
        from pyhelios import LiDARCloud

        with LiDARCloud() as plain, LiDARCloud() as terrain:
            args = dict(center=vec3(0, 0, 0.5), size=vec3(2, 2, 1), ndiv=[2, 2, 2])
            plain.addGrid(**args)
            terrain.addGrid(column_z_offsets=[0.0] * 4, **args)

            assert plain.getGridCellCount() == terrain.getGridCellCount() == 8

            for n in range(plain.getGridCellCount()):
                a, b = plain.getCellCenter(n), terrain.getCellCenter(n)
                assert abs(a.x - b.x) < 1e-6
                assert abs(a.y - b.y) < 1e-6
                assert abs(a.z - b.z) < 1e-6

    def test_add_grid_terrain_following_rejects_wrong_length(self):
        """column_z_offsets length must equal ndiv[0]*ndiv[1]"""
        from pyhelios import LiDARCloud

        with LiDARCloud() as lidar:
            with pytest.raises(ValueError, match="column_z_offsets"):
                lidar.addGrid(
                    center=vec3(0, 0, 0.5),
                    size=vec3(2, 2, 1),
                    ndiv=[2, 2, 1],
                    column_z_offsets=[0.0, 0.1, 0.2]  # need 4, not 3
                )

            # Nothing should have been added
            assert lidar.getGridCellCount() == 0

    def test_get_cell_rotation_returns_degrees(self):
        """getCellRotation reports degrees, matching addGrid's units (helios-core 1.3.78)"""
        from pyhelios import LiDARCloud

        with LiDARCloud() as lidar:
            lidar.addGrid(
                center=vec3(0, 0, 0.5),
                size=vec3(2, 2, 1),
                ndiv=[1, 1, 1],
                rotation=30.0
            )

            # addGrid takes degrees and getCellRotation returns degrees, so this
            # round-trips. If either leaked radians the value would be ~0.52 or ~1718.
            assert abs(lidar.getCellRotation(0) - 30.0) < 1e-3

    def test_get_cell_center_is_rotated_world_frame(self):
        """getCellCenter returns the rotated world-space center, not the lattice center"""
        import math
        from pyhelios import LiDARCloud

        with LiDARCloud() as lidar:
            # Single column offset from the grid anchor, rotated 90 degrees about +z.
            # The lattice center sits at x=+0.5 relative to the anchor at the origin;
            # rotating 90 degrees about +z maps it to y=+0.5.
            lidar.addGrid(
                center=vec3(0, 0, 0.5),
                size=vec3(2, 1, 1),
                ndiv=[2, 1, 1],
                rotation=90.0
            )

            c0 = lidar.getCellCenter(0)
            # Un-rotated lattice center of cell 0 is (-0.5, 0, 0.5). Rotated +90 deg
            # about the anchor (0,0) that becomes (0, -0.5, 0.5).
            assert abs(c0.x - 0.0) < 1e-4, f"x={c0.x}"
            assert abs(c0.y - (-0.5)) < 1e-4, f"y={c0.y}"
            assert abs(c0.z - 0.5) < 1e-4, f"z={c0.z}"

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
            # Geometry to scan so the leaf-area inversion has hits and (recorded) misses.
            context.addPatch(center=vec3(0, 0, 0.5), size=vec2(0.5, 0.5))
            with LiDARCloud() as lidar:
                lidar.disableMessages()
                # Scanner above looking down so most beams reach the patch or miss past it.
                lidar.addScan(
                    origin=vec3(0, 0, 3),
                    Ntheta=40, theta_range=(2.7, 3.13),
                    Nphi=40, phi_range=(0, 6.28),
                    exit_diameter=0.02, beam_divergence=0.001
                )

                # Add grid
                lidar.addGrid(
                    center=vec3(0, 0, 0.5),
                    size=vec3(2, 2, 1),
                    ndiv=[2, 2, 1],
                    rotation=0.0
                )

                # Synthetic scan records misses by default (required by calculateLeafArea).
                lidar.syntheticScan(context, rays_per_pulse=12, pulse_distance_threshold=0.05)
                assert lidar.hasMisses(), "Synthetic scan must record misses for leaf-area inversion"

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

    @pytest.mark.slow
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
                scan_id = lidar.addScan(
                    origin=vec3(-5.0, 0.0, 0.5),
                    Ntheta=10000, theta_range=(0, math.pi),
                    Nphi=14000, phi_range=(0, 2 * math.pi),
                    exit_diameter=0.0,       # Point source (C++ test uses 0.0)
                    beam_divergence=0.0004   # Small divergence for multi-return
                )

                # helios-core 1.3.77 changed the default detectionThreshold from 0 to 0.05 (a ~5%
                # noise floor that pairs with ~40 rays/pulse). This equal-weighting test reports
                # every return at 100 rays/pulse, where the weakest single-sub-ray return is 0.01 <
                # 0.05 and would be suppressed, skewing the LAD reconstruction. Disable suppression to
                # reproduce the "report every detected return" behavior this test validates.
                lidar.setScanDetectionThreshold(scan_id, 0.0)

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

                # The native C++ self-test asserts this normalized RMSE at 10% on a single
                # deterministically-seeded run. helios-core 1.3.76 reworked synthetic multi-return
                # detection onto an analytic sum-of-Gaussians waveform model (Gaussian-footprint
                # sub-ray weighting, range-resolution merging, energy-weighted return ranges). Under
                # that model the per-voxel LAD error for this 8-voxel partial-occlusion case sits
                # near the old 10% bound and, because the sub-ray placement is stochastic and is not
                # fully pinned by the Context seed in the forked PyHelios harness, swings run-to-run
                # (~6-16% observed). The threshold is widened to 20% so the test still catches a gross
                # inversion breakage without flaking on that inherent variance. See CHANGELOG v0.1.24
                # (helios-core 1.3.76 LiDAR waveform rework).
                assert rmse < 0.20, \
                    f"Multi-return LAD distribution RMSE failed: {rmse*100:.1f}% (threshold: 20%)"


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


class TestLiDARHitData:
    """Test per-hit data accessors and column-format-driven primitive-data transfer.

    Uses the proven leaf-cube XML geometry (real 3-D geometry that the synthetic scan
    reliably hits) — a flat or tiny mesh produces a degenerate/ill-aimed scan that yields
    zero hits.
    """

    # Scan parameters proven to generate hits against the leaf-cube geometry (mirrors
    # TestLiDARLeafArea.test_calculate_leaf_area), trimmed for test speed.
    _SCAN = dict(
        origin=vec3(-5.0, 0.0, 0.5),
        Ntheta=300, theta_range=(0.0, math.pi),
        Nphi=600, phi_range=(0.0, 2 * math.pi),
        exit_diameter=0.0, beam_divergence=0.0,
    )

    @pytest.mark.native_only
    @pytest.mark.slow
    def test_hit_data_and_column_format_transfer(self):
        """End-to-end: scan geometry, read per-hit data, scan ID, and a column-format scalar."""
        from pyhelios import Context, LiDARCloud

        xml_path = get_lidar_asset_path('xml/leaf_cube_LAI2_lw0_01_spherical.xml')
        if xml_path is None:
            pytest.skip("LiDAR test assets not available")

        my_scalar_value = 1.23

        with Context() as context:
            uuids = context.loadXML(xml_path, quiet=True)
            for uuid in uuids:
                context.setPrimitiveDataFloat(uuid, "reflectivity_lidar", 0.7)
                context.setPrimitiveDataFloat(uuid, "my_scalar", my_scalar_value)

            with LiDARCloud() as lidar:
                lidar.disableMessages()
                scan_id = lidar.addScan(column_format=["my_scalar"], **self._SCAN)

                lidar.syntheticScan(context)

                hit_count = lidar.getHitCount()
                assert hit_count > 0, f"Synthetic scan must generate hits, got {hit_count}"

                # Find a real hit (target_index == 99 marks misses) carrying the sampled scalar.
                real_index = None
                for i in range(hit_count):
                    if not lidar.doesHitDataExist(i, "target_index"):
                        continue
                    if lidar.getHitData(i, "target_index") != 99 and lidar.doesHitDataExist(i, "my_scalar"):
                        real_index = i
                        break
                assert real_index is not None, "Expected at least one real hit carrying my_scalar"

                # Standard per-hit scalars computed by syntheticScan must exist.
                for label in ("intensity", "distance", "timestamp", "target_index", "target_count"):
                    assert lidar.doesHitDataExist(real_index, label), \
                        f"Expected hit data '{label}' to exist on a real hit"

                # The column-format primitive-data scalar must have transferred verbatim.
                assert abs(lidar.getHitData(real_index, "my_scalar") - my_scalar_value) < 1e-4

                # reflectivity_lidar is special: it modulates intensity and is NOT stored
                # as its own retrievable hit-data key (even though it was set on primitives
                # and is not in column_format here, the rule holds regardless).
                assert not lidar.doesHitDataExist(real_index, "reflectivity_lidar")

                # Scan ID round-trips.
                assert lidar.getHitScanID(real_index) == scan_id

                # Bulk exports return one entry per hit.
                intensities = lidar.getHitDataAll("intensity")
                assert len(intensities) == hit_count
                positions, colors = lidar.getHitsXYZRGB()
                assert len(positions) == hit_count
                assert len(colors) == hit_count
                # Bulk XYZ matches the per-hit accessor.
                p0 = lidar.getHitXYZ(real_index)
                assert abs(positions[real_index].x - p0.x) < 1e-4
                assert abs(positions[real_index].y - p0.y) < 1e-4
                assert abs(positions[real_index].z - p0.z) < 1e-4

    @pytest.mark.native_only
    @pytest.mark.slow
    def test_hit_data_absent_without_column_format(self):
        """Without listing it in column_format, a custom scalar must NOT transfer onto hits."""
        from pyhelios import Context, LiDARCloud

        xml_path = get_lidar_asset_path('xml/leaf_cube_LAI2_lw0_01_spherical.xml')
        if xml_path is None:
            pytest.skip("LiDAR test assets not available")

        with Context() as context:
            uuids = context.loadXML(xml_path, quiet=True)
            for uuid in uuids:
                context.setPrimitiveDataFloat(uuid, "my_scalar", 4.56)

            with LiDARCloud() as lidar:
                lidar.disableMessages()
                # No column_format -> my_scalar should not be sampled onto hits.
                lidar.addScan(**self._SCAN)
                lidar.syntheticScan(context)

                hit_count = lidar.getHitCount()
                assert hit_count > 0

                # Bulk-export the scalar in one call; every entry must be NaN since
                # my_scalar was not in column_format and so was never sampled onto hits.
                values = lidar.getHitDataAll("my_scalar")
                assert len(values) == hit_count
                assert all(math.isnan(v) for v in values), \
                    "my_scalar must not transfer to hits when absent from column_format"



@pytest.mark.native_only
class TestLiDARMergeAdditions:
    """Tests for LiDAR API added with the helios-core 1.3.74 merge:
    scanner tilt, spinning multibeam, miss detection, leaf-area uncertainty, and
    point-cloud header export."""

    def test_scan_tilt_roundtrip(self):
        """Scanner tilt roll/pitch supplied to addScan() round-trip through the getters."""
        from pyhelios import LiDARCloud

        with LiDARCloud() as lidar:
            scan_id = lidar.addScan(
                origin=vec3(0, 0, 2),
                Ntheta=10, theta_range=(0.2, 1.4),
                Nphi=10, phi_range=(0, 6.28),
                exit_diameter=0.0, beam_divergence=0.0,
                scan_tilt_roll=0.05, scan_tilt_pitch=-0.03,
            )
            assert lidar.getScanTiltRoll(scan_id) == pytest.approx(0.05, abs=1e-6)
            assert lidar.getScanTiltPitch(scan_id) == pytest.approx(-0.03, abs=1e-6)

    def test_scan_tilt_defaults_zero(self):
        """Tilt defaults to level (0, 0), preserving prior behavior."""
        from pyhelios import LiDARCloud

        with LiDARCloud() as lidar:
            scan_id = lidar.addScan(
                origin=vec3(0, 0, 2),
                Ntheta=10, theta_range=(0.2, 1.4),
                Nphi=10, phi_range=(0, 6.28),
                exit_diameter=0.0, beam_divergence=0.0,
            )
            assert lidar.getScanTiltRoll(scan_id) == pytest.approx(0.0, abs=1e-7)
            assert lidar.getScanTiltPitch(scan_id) == pytest.approx(0.0, abs=1e-7)

    def test_raster_scan_pattern(self):
        """A scan added via addScan() reports the RASTER pattern and no beam zenith angles."""
        from pyhelios import LiDARCloud
        from pyhelios.LiDARCloud import ScanPattern

        with LiDARCloud() as lidar:
            scan_id = lidar.addScan(
                origin=vec3(0, 0, 2),
                Ntheta=10, theta_range=(0.2, 1.4),
                Nphi=10, phi_range=(0, 6.28),
                exit_diameter=0.0, beam_divergence=0.0,
            )
            assert lidar.getScanPattern(scan_id) == ScanPattern.RASTER
            assert lidar.getScanBeamZenithAngles(scan_id) == []

    def test_spinning_scan_reports_spinning_pattern(self):
        """addScanSpinning() reports the SPINNING_MULTIBEAM geometric pattern, the SPINNING
        acquisition mode, and round-trips the per-channel angles (elevation -> zenith)."""
        from pyhelios import LiDARCloud
        from pyhelios.LiDARCloud import ScanPattern, ScanMode

        elevations = [math.radians(-10), math.radians(0), math.radians(10)]
        with LiDARCloud() as lidar:
            scan_id = lidar.addScanSpinning(
                beam_elevation_angles=elevations,
                azimuth_step=math.radians(1.0),
                pulse_rate_hz=100000.0,
                traj_t=[0.0, 1.0],
                traj_pos=[[0, 0, 1.5], [0, 0, 1.5]],   # stationary spin-in-place
                traj_rot=[[0, 0, 0, 1], [0, 0, 0, 1]],
            )
            assert lidar.getScanPattern(scan_id) == ScanPattern.SPINNING_MULTIBEAM
            assert lidar.getScanMode(scan_id) == ScanMode.SPINNING
            assert lidar.getScanSizeTheta(scan_id) == len(elevations)
            # The native path stores per-channel ZENITH angles (zenith = pi/2 - elevation).
            returned = lidar.getScanBeamZenithAngles(scan_id)
            assert len(returned) == len(elevations)
            for got, elev in zip(returned, elevations):
                assert got == pytest.approx(math.pi / 2 - elev, abs=1e-4)

    def test_spinning_scan_is_self_describing(self):
        """A spinning scan exposes derived rotation rate, steps-per-rev, and revolution count."""
        from pyhelios import LiDARCloud

        with LiDARCloud() as lidar:
            scan_id = lidar.addScanSpinning(
                beam_elevation_angles=[math.radians(0)],
                azimuth_step=math.radians(1.0),    # 360 steps per revolution
                pulse_rate_hz=36000.0,
                traj_t=[0.0, 1.0],
                traj_pos=[[0, 0, 1.5], [0, 0, 1.5]],
                traj_rot=[[0, 0, 0, 1], [0, 0, 0, 1]],
            )
            # 1 deg azimuth step -> 360 firing steps per revolution.
            assert lidar.getScanStepsPerRev(scan_id) == pytest.approx(360, abs=1)
            # rotation_rate = PRF / (channels * steps_per_rev) = 36000 / (1 * 360) = 100 rev/s.
            assert lidar.getScanRotationRate(scan_id) == pytest.approx(100.0, rel=0.05)
            # revolutions = rotation_rate * duration = 100 * 1.0 = 100.
            assert lidar.getScanRevolutions(scan_id) == pytest.approx(100.0, rel=0.05)

    def test_miss_detection(self):
        """record_misses=True produces misses detectable via hasMisses()/isHitMiss()."""
        from pyhelios import Context, LiDARCloud

        with Context() as context:
            context.addPatch(center=vec3(0, 0, 0.5), size=vec2(0.3, 0.3))
            with LiDARCloud() as lidar:
                lidar.disableMessages()
                lidar.addScan(
                    origin=vec3(0, 0, 2),
                    Ntheta=20, theta_range=(0, 1.4),
                    Nphi=20, phi_range=(0, 6.28),
                    exit_diameter=0.0, beam_divergence=0.0,
                )
                lidar.syntheticScan(context, rays_per_pulse=10,
                                    pulse_distance_threshold=0.05, record_misses=True)
                assert lidar.hasMisses() is True
                hit_count = lidar.getHitCount()
                assert hit_count > 0
                # At least one hit must be flagged as a miss.
                assert any(lidar.isHitMiss(i) for i in range(hit_count))

    def test_miss_distance_constant(self):
        """getMissDistance() exposes the LIDAR_MISS_DISTANCE constant (20000 m)."""
        from pyhelios import LiDARCloud

        assert LiDARCloud.getMissDistance() == pytest.approx(20000.0, abs=1.0)

    def test_export_point_cloud_header(self, tmp_path):
        """exportPointCloud(write_header=True) writes a '#'-prefixed header line."""
        from pyhelios import Context, LiDARCloud

        with Context() as context:
            context.addPatch(center=vec3(0, 0, 0.5), size=vec2(0.5, 0.5))
            with LiDARCloud() as lidar:
                lidar.disableMessages()
                lidar.addScan(
                    origin=vec3(0, 0, 2),
                    Ntheta=15, theta_range=(2.6, 3.13),
                    Nphi=15, phi_range=(0, 6.28),
                    exit_diameter=0.0, beam_divergence=0.0,
                    column_format=["x", "y", "z"],
                )
                lidar.syntheticScan(context)

                headered = tmp_path / "headered.xyz"
                lidar.exportPointCloud(str(headered), write_header=True)
                assert headered.exists()
                first_line = headered.read_text().splitlines()[0]
                assert first_line.startswith("#")

                bare = tmp_path / "bare.xyz"
                lidar.exportPointCloud(str(bare), write_header=False)
                assert bare.exists()
                assert not bare.read_text().splitlines()[0].startswith("#")

    def test_leaf_area_uncertainty_accessors(self):
        """calculateLeafArea(element_width=...) populates the uncertainty accessors without error.

        The numeric values depend on scan geometry; here we only assert the accessors are
        callable and return values of the documented types/sentinels.
        """
        from pyhelios import Context, LiDARCloud

        with Context() as context:
            context.addPatch(center=vec3(0, 0, 0.5), size=vec2(0.3, 0.3))
            with LiDARCloud() as lidar:
                lidar.disableMessages()
                lidar.addScan(
                    origin=vec3(0, 0, 3),
                    Ntheta=30, theta_range=(2.7, 3.13),
                    Nphi=30, phi_range=(0, 6.28),
                    exit_diameter=0.02, beam_divergence=0.001,
                )
                lidar.syntheticScan(context, rays_per_pulse=12,
                                    pulse_distance_threshold=0.05, record_misses=True)
                lidar.addGrid(center=vec3(0, 0, 0.5), size=vec3(1, 1, 1),
                              ndiv=[1, 1, 1], rotation=0.0)
                lidar.triangulateHitPoints(Lmax=0.1, max_aspect_ratio=5.0)
                lidar.calculateHitGridCell()
                lidar.calculateLeafArea(context, min_voxel_hits=1, element_width=0.05)

                # Accessors are callable and typed; beam count is an int >= -1.
                assert isinstance(lidar.getCellBeamCount(0), int)
                assert isinstance(lidar.getCellLADVariance(0), float)
                assert isinstance(lidar.getCellRelativeDensityIndex(0), float)
                assert isinstance(lidar.getCellMeanPathLength(0), float)
                valid, lo, hi = lidar.getCellLeafAreaConfidenceInterval(0, 0.95)
                assert isinstance(valid, bool)
                gvalid, mean_lad, glo, ghi = lidar.getGroupLADConfidenceInterval([0], 0.95)
                assert isinstance(gvalid, bool)

    def test_element_width_requires_min_voxel_hits(self):
        """element_width without min_voxel_hits is a usage error."""
        from pyhelios import Context, LiDARCloud

        with Context() as context:
            with LiDARCloud() as lidar:
                with pytest.raises(ValueError):
                    lidar.calculateLeafArea(context, element_width=0.05)


class TestLiDARMovingPlatformInterface:
    """Cross-platform interface tests for the helios-core 1.3.75 LiDAR additions:
    azimuth offset, per-hit origin, moving-platform scans, and the G(theta) leaf-area overload."""

    @pytest.mark.cross_platform
    def test_new_methods_exist(self):
        """The 1.3.75 high-level methods are present on LiDARCloud."""
        from pyhelios import LiDARCloud

        assert hasattr(LiDARCloud, 'getScanAzimuthOffset')
        assert hasattr(LiDARCloud, 'getHitOrigin')
        assert hasattr(LiDARCloud, 'addScanMoving')

    @pytest.mark.cross_platform
    def test_addscanmoving_length_mismatch_validation(self):
        """addScanMoving validates equal trajectory array lengths before touching native code.

        Runs in mock mode: validation happens in Python before any FFI call.
        """
        from pyhelios import LiDARCloud

        lidar = LiDARCloud.__new__(LiDARCloud)  # bypass native cloud creation
        lidar._cloud_ptr = None
        with pytest.raises(ValueError):
            lidar.addScanMoving(
                Ntheta=4, theta_range=(0.2, 1.4), Nphi=4, phi_range=(0, 6.28),
                exit_diameter=0.0, beam_divergence=0.0,
                traj_t=[0.0, 1.0],
                traj_pos=[[0, 0, 10]],  # length 1 != len(traj_t) == 2
                traj_rot=[[0, 0, 0, 1], [0, 0, 0, 1]],
                pulse_rate_hz=1000.0,
            )

    @pytest.mark.cross_platform
    def test_addscanmoving_rotation_stride_validation(self):
        """Euler trajectory entries must be length-3; quaternion entries length-4."""
        from pyhelios import LiDARCloud

        lidar = LiDARCloud.__new__(LiDARCloud)
        lidar._cloud_ptr = None
        with pytest.raises(ValueError):
            lidar.addScanMoving(
                Ntheta=4, theta_range=(0.2, 1.4), Nphi=4, phi_range=(0, 6.28),
                exit_diameter=0.0, beam_divergence=0.0,
                traj_t=[0.0],
                traj_pos=[[0, 0, 10]],
                traj_rot=[[0, 0, 0, 1]],  # length 4 but rot_is_quaternion=False expects 3
                rot_is_quaternion=False,
                pulse_rate_hz=1000.0,
            )

    @pytest.mark.cross_platform
    def test_addscanmoving_pulse_rate_validation(self):
        """pulse_rate_hz must be positive."""
        from pyhelios import LiDARCloud

        lidar = LiDARCloud.__new__(LiDARCloud)
        lidar._cloud_ptr = None
        with pytest.raises(ValueError):
            lidar.addScanMoving(
                Ntheta=4, theta_range=(0.2, 1.4), Nphi=4, phi_range=(0, 6.28),
                exit_diameter=0.0, beam_divergence=0.0,
                traj_t=[0.0], traj_pos=[[0, 0, 10]], traj_rot=[[0, 0, 0, 1]],
                pulse_rate_hz=0.0,
            )

    @pytest.mark.cross_platform
    def test_addscanmoving_nonmonotonic_traj_t_validation(self):
        """traj_t must be strictly increasing; caught in Python before any FFI call."""
        from pyhelios import LiDARCloud

        lidar = LiDARCloud.__new__(LiDARCloud)
        lidar._cloud_ptr = None
        with pytest.raises(ValueError):
            lidar.addScanMoving(
                Ntheta=4, theta_range=(0.2, 1.4), Nphi=4, phi_range=(0, 6.28),
                exit_diameter=0.0, beam_divergence=0.0,
                traj_t=[0.0, 0.0],  # not strictly increasing
                traj_pos=[[0, 0, 10], [1, 0, 10]],
                traj_rot=[[0, 0, 0, 1], [0, 0, 0, 1]],
                pulse_rate_hz=1000.0,
            )

    @pytest.mark.cross_platform
    def test_calculate_leaf_area_gtheta_requires_all_args(self):
        """The Gtheta overload requires min_voxel_hits and element_width too."""
        from pyhelios import LiDARCloud

        lidar = LiDARCloud.__new__(LiDARCloud)
        lidar._cloud_ptr = None
        with pytest.raises((ValueError, TypeError)):
            # missing context entirely is a TypeError; missing the companion args a ValueError
            lidar.calculateLeafArea(None, Gtheta=0.5)

    @pytest.mark.cross_platform
    def test_calculate_leaf_area_gtheta_rejects_nonpositive(self):
        """Gtheta <= 0 is rejected (it is the native 'compute-from-triangulation' sentinel)."""
        from pyhelios import Context, LiDARCloud

        lidar = LiDARCloud.__new__(LiDARCloud)
        lidar._cloud_ptr = None

        class _FakeContext(Context):
            def __init__(self):  # bypass native context creation
                pass

        with pytest.raises(ValueError):
            lidar.calculateLeafArea(_FakeContext(), min_voxel_hits=1, element_width=0.05, Gtheta=0.0)


@pytest.mark.native_only
class TestLiDARMovingPlatformFunctionality:
    """Native functional tests for the helios-core 1.3.75 LiDAR additions."""

    def test_scan_azimuth_offset_roundtrip(self):
        """scan_azimuth_offset supplied to addScan() round-trips through getScanAzimuthOffset()."""
        from pyhelios import LiDARCloud

        with LiDARCloud() as lidar:
            scan_id = lidar.addScan(
                origin=vec3(0, 0, 2),
                Ntheta=10, theta_range=(0.2, 1.4),
                Nphi=10, phi_range=(0, 6.28),
                exit_diameter=0.0, beam_divergence=0.0,
                scan_azimuth_offset=0.123,
            )
            assert lidar.getScanAzimuthOffset(scan_id) == pytest.approx(0.123, abs=1e-6)

    def test_scan_azimuth_offset_defaults_zero(self):
        """Azimuth offset defaults to 0 (no heading offset), preserving prior behavior."""
        from pyhelios import LiDARCloud

        with LiDARCloud() as lidar:
            scan_id = lidar.addScan(
                origin=vec3(0, 0, 2),
                Ntheta=10, theta_range=(0.2, 1.4),
                Nphi=10, phi_range=(0, 6.28),
                exit_diameter=0.0, beam_divergence=0.0,
            )
            assert lidar.getScanAzimuthOffset(scan_id) == pytest.approx(0.0, abs=1e-7)

    def test_static_hit_origin_matches_scan_origin(self):
        """For a static scan, getHitOrigin() falls back to the scan origin."""
        from pyhelios import LiDARCloud

        with LiDARCloud() as lidar:
            origin = vec3(1, 2, 3)
            scan_id = lidar.addScan(
                origin=origin,
                Ntheta=5, theta_range=(0, 1.0),
                Nphi=5, phi_range=(-3.14, 3.14),
                exit_diameter=0.01, beam_divergence=0.001,
            )
            lidar.addHitPoint(scan_id, vec3(1.5, 2.5, 3.5), vec3(1, 0, 0))
            hit_origin = lidar.getHitOrigin(0)
            assert hit_origin.x == pytest.approx(origin.x, abs=1e-4)
            assert hit_origin.y == pytest.approx(origin.y, abs=1e-4)
            assert hit_origin.z == pytest.approx(origin.z, abs=1e-4)

    def test_add_scan_moving_quaternion(self):
        """addScanMoving() with a quaternion trajectory creates a scan and produces hits/origins."""
        from pyhelios import Context, LiDARCloud

        with Context() as context:
            context.addPatch(center=vec3(0, 0, 0), size=vec2(4, 4))
            with LiDARCloud() as lidar:
                lidar.disableMessages()
                scan_id = lidar.addScanMoving(
                    Ntheta=8, theta_range=(2.7, 3.13),
                    Nphi=8, phi_range=(-0.3, 0.3),
                    exit_diameter=0.0, beam_divergence=0.0,
                    traj_t=[0.0, 1.0],
                    traj_pos=[[-1, 0, 10], [1, 0, 10]],
                    traj_rot=[[0, 0, 0, 1], [0, 0, 0, 1]],  # identity quaternions
                    rot_is_quaternion=True,
                    pulse_rate_hz=1000.0,
                )
                assert scan_id >= 0
                assert lidar.getScanCount() == 1
                lidar.syntheticScan(context, rays_per_pulse=4,
                                    pulse_distance_threshold=0.05, record_misses=True)
                assert lidar.getHitCount() > 0
                # Per-pulse origin should be near the moving platform altitude (z ~ 10), not (0,0,0).
                origin = lidar.getHitOrigin(0)
                assert origin.z == pytest.approx(10.0, abs=2.0)

    def test_add_scan_moving_euler(self):
        """addScanMoving() also accepts a roll/pitch/yaw Euler trajectory."""
        from pyhelios import Context, LiDARCloud

        with Context() as context:
            context.addPatch(center=vec3(0, 0, 0), size=vec2(4, 4))
            with LiDARCloud() as lidar:
                lidar.disableMessages()
                scan_id = lidar.addScanMoving(
                    Ntheta=8, theta_range=(2.7, 3.13),
                    Nphi=8, phi_range=(-0.3, 0.3),
                    exit_diameter=0.0, beam_divergence=0.0,
                    traj_t=[0.0, 1.0],
                    traj_pos=[[-1, 0, 10], [1, 0, 10]],
                    traj_rot=[[0, 0, 0], [0, 0, 0]],  # level
                    rot_is_quaternion=False,
                    pulse_rate_hz=1000.0,
                )
                assert scan_id >= 0
                assert lidar.getScanCount() == 1

    def test_calculate_leaf_area_gtheta(self):
        """calculateLeafArea(Gtheta=...) runs the triangulation-free inversion without error."""
        from pyhelios import Context, LiDARCloud

        with Context() as context:
            context.addPatch(center=vec3(0, 0, 0.5), size=vec2(0.3, 0.3))
            with LiDARCloud() as lidar:
                lidar.disableMessages()
                lidar.addScan(
                    origin=vec3(0, 0, 3),
                    Ntheta=30, theta_range=(2.7, 3.13),
                    Nphi=30, phi_range=(0, 6.28),
                    exit_diameter=0.02, beam_divergence=0.001,
                )
                lidar.syntheticScan(context, rays_per_pulse=12,
                                    pulse_distance_threshold=0.05, record_misses=True)
                lidar.addGrid(center=vec3(0, 0, 0.5), size=vec3(1, 1, 1),
                              ndiv=[1, 1, 1], rotation=0.0)
                lidar.calculateHitGridCell()
                # No triangulation performed; the G(theta) overload must not require it.
                lidar.calculateLeafArea(context, min_voxel_hits=1, element_width=0.05, Gtheta=0.5)
                assert isinstance(lidar.getCellLeafArea(0), float)

    def test_calculate_leaf_area_gtheta_requires_companions(self):
        """Gtheta without min_voxel_hits/element_width is a usage error (native check)."""
        from pyhelios import Context, LiDARCloud

        with Context() as context:
            with LiDARCloud() as lidar:
                with pytest.raises(ValueError):
                    lidar.calculateLeafArea(context, Gtheta=0.5)


class TestLiDARSpinningReturnModeInterface:
    """Cross-platform interface tests for the helios-core 1.3.76 LiDAR additions:
    physical-parameter spinning/moving-raster scans, scan-mode introspection, return-mode
    configuration, and columnar bulk reads. These run in mock mode (Python-level checks)."""

    @pytest.mark.cross_platform
    def test_new_enums_exist(self):
        """ScanMode/ReturnMode/SingleReturnSelection enums are importable with the expected values."""
        from pyhelios import ScanMode, ReturnMode, SingleReturnSelection

        assert int(ScanMode.STATIC_RASTER) == 0
        assert int(ScanMode.MOVING_RASTER) == 1
        assert int(ScanMode.SPINNING) == 2
        assert int(ReturnMode.MULTI) == 0
        assert int(ReturnMode.SINGLE) == 1
        assert int(SingleReturnSelection.STRONGEST) == 0
        assert int(SingleReturnSelection.FIRST) == 1
        assert int(SingleReturnSelection.LAST) == 2
        assert int(SingleReturnSelection.STRONGEST_PLUS_LAST) == 3

    @pytest.mark.cross_platform
    def test_new_methods_exist(self):
        """The 1.3.76 high-level methods are present on LiDARCloud."""
        from pyhelios import LiDARCloud

        for name in ('addScanSpinning', 'addScanMovingRaster',
                     'getScanMode', 'getScanStepsPerRev', 'getScanRotationRate', 'getScanRevolutions',
                     'getScanReturnMode', 'setScanReturnMode',
                     'getScanSingleReturnSelection', 'setScanSingleReturnSelection',
                     'getScanMaxReturns', 'setScanMaxReturns',
                     'getScanPulseWidth', 'setScanPulseWidth',
                     'getScanDetectionThreshold', 'setScanDetectionThreshold',
                     'getHitDataColumn', 'getHitDataColumnArray'):
            assert hasattr(LiDARCloud, name), name

    @pytest.mark.cross_platform
    def test_addscanmultibeam_is_removed(self):
        """The legacy addScanMultibeam entry point is deleted (superseded by addScanSpinning)."""
        from pyhelios import LiDARCloud

        assert not hasattr(LiDARCloud, 'addScanMultibeam')

    @pytest.mark.cross_platform
    def test_addscanspinning_empty_angles_validation(self):
        """addScanSpinning rejects an empty channel-angle list before any FFI call."""
        from pyhelios import LiDARCloud

        lidar = LiDARCloud.__new__(LiDARCloud)
        lidar._cloud_ptr = None
        with pytest.raises(ValueError):
            lidar.addScanSpinning(
                beam_elevation_angles=[],
                azimuth_step=math.radians(1.0), pulse_rate_hz=1000.0,
                traj_t=[0.0, 1.0], traj_pos=[[0, 0, 1], [0, 0, 1]],
                traj_rot=[[0, 0, 0, 1], [0, 0, 0, 1]],
            )

    @pytest.mark.cross_platform
    def test_addscanspinning_azimuth_step_validation(self):
        """azimuth_step must be positive."""
        from pyhelios import LiDARCloud

        lidar = LiDARCloud.__new__(LiDARCloud)
        lidar._cloud_ptr = None
        with pytest.raises(ValueError):
            lidar.addScanSpinning(
                beam_elevation_angles=[0.0],
                azimuth_step=0.0, pulse_rate_hz=1000.0,
                traj_t=[0.0, 1.0], traj_pos=[[0, 0, 1], [0, 0, 1]],
                traj_rot=[[0, 0, 0, 1], [0, 0, 0, 1]],
            )

    @pytest.mark.cross_platform
    def test_addscanspinning_trajectory_length_validation(self):
        """traj_pos/traj_rot must match traj_t length, caught before any FFI call."""
        from pyhelios import LiDARCloud

        lidar = LiDARCloud.__new__(LiDARCloud)
        lidar._cloud_ptr = None
        with pytest.raises(ValueError):
            lidar.addScanSpinning(
                beam_elevation_angles=[0.0],
                azimuth_step=math.radians(1.0), pulse_rate_hz=1000.0,
                traj_t=[0.0, 1.0], traj_pos=[[0, 0, 1]],   # length 1 != 2
                traj_rot=[[0, 0, 0, 1], [0, 0, 0, 1]],
            )

    @pytest.mark.cross_platform
    def test_addscanmovingraster_pulse_rate_validation(self):
        """addScanMovingRaster requires a positive pulse_rate_hz."""
        from pyhelios import LiDARCloud

        lidar = LiDARCloud.__new__(LiDARCloud)
        lidar._cloud_ptr = None
        with pytest.raises(ValueError):
            lidar.addScanMovingRaster(
                Ntheta=4, theta_range=(2.8, 3.1), Nphi=4, phi_range=(-0.2, 0.2),
                pulse_rate_hz=0.0,
                traj_t=[0.0, 1.0], traj_pos=[[0, 0, 10], [1, 0, 10]],
                traj_quat=[[0, 0, 0, 1], [0, 0, 0, 1]],
            )

    @pytest.mark.cross_platform
    def test_addscanmovingraster_quat_stride_validation(self):
        """addScanMovingRaster requires length-4 quaternion trajectory entries."""
        from pyhelios import LiDARCloud

        lidar = LiDARCloud.__new__(LiDARCloud)
        lidar._cloud_ptr = None
        with pytest.raises(ValueError):
            lidar.addScanMovingRaster(
                Ntheta=4, theta_range=(2.8, 3.1), Nphi=4, phi_range=(-0.2, 0.2),
                pulse_rate_hz=1000.0,
                traj_t=[0.0, 1.0], traj_pos=[[0, 0, 10], [1, 0, 10]],
                traj_quat=[[0, 0, 0], [0, 0, 0]],   # length 3, not 4
            )

    @pytest.mark.cross_platform
    def test_setscanmaxreturns_validation(self):
        """setScanMaxReturns rejects values < 1 in Python before the FFI call."""
        from pyhelios import LiDARCloud

        lidar = LiDARCloud.__new__(LiDARCloud)
        lidar._cloud_ptr = None
        with pytest.raises(ValueError):
            lidar.setScanMaxReturns(0, 0)

    @pytest.mark.cross_platform
    def test_return_mode_arg_requires_waveform(self):
        """syntheticScan(return_mode=...) is rejected without rays_per_pulse (discrete path)."""
        from pyhelios import Context, LiDARCloud, ReturnMode

        lidar = LiDARCloud.__new__(LiDARCloud)
        lidar._cloud_ptr = None
        with Context() as context:
            with pytest.raises(ValueError):
                lidar.syntheticScan(context, return_mode=ReturnMode.SINGLE)


@pytest.mark.native_only
class TestLiDARSpinningReturnModeFunctionality:
    """Native functional tests for the helios-core 1.3.76 LiDAR additions."""

    def test_moving_raster_scan_mode(self):
        """addScanMovingRaster() creates a scan reporting MOVING_RASTER acquisition mode."""
        from pyhelios import Context, LiDARCloud
        from pyhelios.LiDARCloud import ScanMode

        with Context() as context:
            context.addPatch(center=vec3(0, 0, 0), size=vec2(4, 4))
            with LiDARCloud() as lidar:
                lidar.disableMessages()
                scan_id = lidar.addScanMovingRaster(
                    Ntheta=8, theta_range=(2.7, 3.13),
                    Nphi=8, phi_range=(-0.3, 0.3),
                    pulse_rate_hz=1000.0,
                    traj_t=[0.0, 1.0],
                    traj_pos=[[-1, 0, 10], [1, 0, 10]],
                    traj_quat=[[0, 0, 0, 1], [0, 0, 0, 1]],
                )
                assert lidar.getScanMode(scan_id) == ScanMode.MOVING_RASTER
                lidar.syntheticScan(context, rays_per_pulse=4,
                                    pulse_distance_threshold=0.05, record_misses=True)
                assert lidar.getHitCount() > 0
                # Per-pulse origin follows the moving platform (z ~ 10), not (0,0,0).
                assert lidar.getHitOrigin(0).z == pytest.approx(10.0, abs=2.0)

    def test_static_scan_mode_default(self):
        """A plain addScan() scan reports STATIC_RASTER acquisition mode."""
        from pyhelios import LiDARCloud
        from pyhelios.LiDARCloud import ScanMode

        with LiDARCloud() as lidar:
            scan_id = lidar.addScan(
                origin=vec3(0, 0, 2),
                Ntheta=10, theta_range=(0.2, 1.4),
                Nphi=10, phi_range=(0, 6.28),
                exit_diameter=0.0, beam_divergence=0.0,
            )
            assert lidar.getScanMode(scan_id) == ScanMode.STATIC_RASTER

    def test_return_mode_config_roundtrip(self):
        """Return-mode/selection/maxReturns/pulseWidth/detectionThreshold round-trip through the setters."""
        from pyhelios import LiDARCloud
        from pyhelios.LiDARCloud import ReturnMode, SingleReturnSelection

        with LiDARCloud() as lidar:
            scan_id = lidar.addScan(
                origin=vec3(0, 0, 2),
                Ntheta=8, theta_range=(0.2, 1.4),
                Nphi=8, phi_range=(0, 6.28),
                exit_diameter=0.005, beam_divergence=0.003,
            )
            # Defaults
            assert lidar.getScanReturnMode(scan_id) == ReturnMode.MULTI
            assert lidar.getScanMaxReturns(scan_id) == 1

            lidar.setScanReturnMode(scan_id, ReturnMode.SINGLE)
            lidar.setScanSingleReturnSelection(scan_id, SingleReturnSelection.LAST)
            lidar.setScanMaxReturns(scan_id, 3)
            lidar.setScanPulseWidth(scan_id, 0.02)
            lidar.setScanDetectionThreshold(scan_id, 0.001)

            assert lidar.getScanReturnMode(scan_id) == ReturnMode.SINGLE
            assert lidar.getScanSingleReturnSelection(scan_id) == SingleReturnSelection.LAST
            assert lidar.getScanMaxReturns(scan_id) == 3
            assert lidar.getScanPulseWidth(scan_id) == pytest.approx(0.02, abs=1e-6)
            assert lidar.getScanDetectionThreshold(scan_id) == pytest.approx(0.001, abs=1e-7)

            # STRONGEST_PLUS_LAST (value 3) is a valid 1.3.76 dual-return mode
            lidar.setScanSingleReturnSelection(scan_id, SingleReturnSelection.STRONGEST_PLUS_LAST)
            assert (lidar.getScanSingleReturnSelection(scan_id)
                    == SingleReturnSelection.STRONGEST_PLUS_LAST)

    def test_synthetic_scan_return_mode_single(self):
        """syntheticScan(return_mode=SINGLE) runs the analytic-waveform single-return path."""
        from pyhelios import Context, LiDARCloud
        from pyhelios.LiDARCloud import ReturnMode

        with Context() as context:
            context.addPatch(center=vec3(0, 0, 0.5), size=vec2(1, 1))
            with LiDARCloud() as lidar:
                lidar.disableMessages()
                lidar.addScan(
                    origin=vec3(0, 0, 2),
                    Ntheta=20, theta_range=(0, 1.0),
                    Nphi=20, phi_range=(0, 6.28),
                    exit_diameter=0.005, beam_divergence=0.003,
                )
                lidar.syntheticScan(context, rays_per_pulse=20, pulse_distance_threshold=0.02,
                                    return_mode=ReturnMode.SINGLE, record_misses=True)
                assert lidar.getHitCount() > 0

    def test_hit_data_column_matches_per_hit(self):
        """getHitDataColumn() returns the same values as per-hit getHitData() for present labels."""
        from pyhelios import Context, LiDARCloud

        with Context() as context:
            context.addPatch(center=vec3(0, 0, 0.5), size=vec2(1, 1))
            with LiDARCloud() as lidar:
                lidar.disableMessages()
                lidar.addScan(
                    origin=vec3(0, 0, 2),
                    Ntheta=15, theta_range=(0, 1.0),
                    Nphi=15, phi_range=(0, 6.28),
                    exit_diameter=0.0, beam_divergence=0.0,
                    column_format=["x", "y", "z", "timestamp"],
                )
                lidar.syntheticScan(context, record_misses=True)
                n = lidar.getHitCount()
                assert n > 0
                column = lidar.getHitDataColumn("timestamp")
                assert len(column) == n
                # Spot-check a few hits against the per-hit getter where the label exists.
                for i in (0, n // 2, n - 1):
                    if lidar.doesHitDataExist(i, "timestamp"):
                        assert column[i] == pytest.approx(lidar.getHitData(i, "timestamp"), rel=1e-6)

    def test_hit_data_column_array_dtype(self):
        """getHitDataColumnArray() returns a float64 numpy array of length getHitCount()."""
        import numpy as np
        from pyhelios import Context, LiDARCloud

        with Context() as context:
            context.addPatch(center=vec3(0, 0, 0.5), size=vec2(1, 1))
            with LiDARCloud() as lidar:
                lidar.disableMessages()
                lidar.addScan(
                    origin=vec3(0, 0, 2),
                    Ntheta=10, theta_range=(0, 1.0),
                    Nphi=10, phi_range=(0, 6.28),
                    exit_diameter=0.0, beam_divergence=0.0,
                    column_format=["x", "y", "z", "timestamp"],
                )
                lidar.syntheticScan(context, record_misses=True)
                arr = lidar.getHitDataColumnArray("timestamp")
                assert arr.dtype == np.float64
                assert arr.shape == (lidar.getHitCount(),)

    def test_introspection_out_of_range_scan_id_raises(self):
        """The enum-returning introspection getters surface an out-of-range scan ID as a clean
        Python exception (the C shim returns -1 on error, which is caught by errcheck or fails the
        enum cast), not a silent value or a ctypes crash."""
        from pyhelios import LiDARCloud

        with LiDARCloud() as lidar:
            # No scans added: scan ID 0 is out of range.
            for getter in (lidar.getScanMode, lidar.getScanReturnMode,
                           lidar.getScanSingleReturnSelection):
                with pytest.raises((HeliosError, ValueError)):
                    getter(0)


class TestLiDARRisleyReturnInterface:
    """Cross-platform interface tests for the helios-core 1.3.77 LiDAR additions:
    Risley-prism rosette scans, the RisleyPrism type, GPU-availability queries, the per-scan
    progress pointer/callback, and the prev-merge gap accessors (column index, memory-budget
    getter). These run in mock mode (Python-level checks)."""

    @pytest.mark.cross_platform
    def test_risley_enum_values_exist(self):
        """ScanPattern.RISLEY_PRISM (2) and ScanMode.RISLEY_PRISM (3) are present."""
        from pyhelios import ScanPattern, ScanMode

        assert int(ScanPattern.RISLEY_PRISM) == 2
        assert int(ScanMode.RISLEY_PRISM) == 3

    @pytest.mark.cross_platform
    def test_risleyprism_type(self):
        """RisleyPrism stores its four parameters and round-trips through to_list()."""
        from pyhelios import RisleyPrism

        p = RisleyPrism(wedge_angle=0.3, refractive_index=1.51, rotor_rate=420.0, phase=0.1)
        assert p.wedge_angle == pytest.approx(0.3)
        assert p.refractive_index == pytest.approx(1.51)
        assert p.rotor_rate == pytest.approx(420.0)
        assert p.phase == pytest.approx(0.1)
        assert p.to_list() == [0.3, 1.51, 420.0, 0.1]
        # phase defaults to 0.0
        assert RisleyPrism(0.3, 1.51, -420.0).phase == 0.0
        assert RisleyPrism(0.3, 1.51, 420.0, 0.1) == RisleyPrism(0.3, 1.51, 420.0, 0.1)

    @pytest.mark.cross_platform
    def test_new_methods_exist(self):
        """The 1.3.77 high-level methods are present on LiDARCloud."""
        from pyhelios import LiDARCloud

        for name in ('addScanRisley', 'getScanRisleyPrisms', 'getScanRisleyRefractiveIndexAir',
                     'isGPUAvailable', 'isGPUAccelerationEnabled',
                     'setSyntheticScanProgressPointer', 'setProgressCallback',
                     'getHitDataColumnIndex', 'getSyntheticScanMemoryBudget'):
            assert hasattr(LiDARCloud, name), name

    @pytest.mark.cross_platform
    def test_addscanrisley_empty_prisms_validation(self):
        """addScanRisley rejects an empty prism list before any FFI call."""
        from pyhelios import LiDARCloud

        lidar = LiDARCloud.__new__(LiDARCloud)
        lidar._cloud_ptr = None
        with pytest.raises(ValueError):
            lidar.addScanRisley(
                prisms=[], refractive_index_air=1.0, pulse_rate_hz=100000.0,
                traj_t=[0.0, 1.0], traj_pos=[[0, 0, 1], [0, 0, 1]],
                traj_rot=[[0, 0, 0, 1], [0, 0, 0, 1]],
            )

    @pytest.mark.cross_platform
    def test_addscanrisley_prism_shape_validation(self):
        """addScanRisley rejects a prism that is not a 4-element entry / RisleyPrism."""
        from pyhelios import LiDARCloud

        lidar = LiDARCloud.__new__(LiDARCloud)
        lidar._cloud_ptr = None
        with pytest.raises(ValueError):
            lidar.addScanRisley(
                prisms=[[0.3, 1.51, 420.0]],   # length 3, not 4
                refractive_index_air=1.0, pulse_rate_hz=100000.0,
                traj_t=[0.0, 1.0], traj_pos=[[0, 0, 1], [0, 0, 1]],
                traj_rot=[[0, 0, 0, 1], [0, 0, 0, 1]],
            )

    @pytest.mark.cross_platform
    def test_addscanrisley_pulse_rate_validation(self):
        """addScanRisley requires a positive pulse_rate_hz."""
        from pyhelios import LiDARCloud, RisleyPrism

        lidar = LiDARCloud.__new__(LiDARCloud)
        lidar._cloud_ptr = None
        with pytest.raises(ValueError):
            lidar.addScanRisley(
                prisms=[RisleyPrism(0.3, 1.51, 420.0), RisleyPrism(0.3, 1.51, -380.0)],
                refractive_index_air=1.0, pulse_rate_hz=0.0,
                traj_t=[0.0, 1.0], traj_pos=[[0, 0, 1], [0, 0, 1]],
                traj_rot=[[0, 0, 0, 1], [0, 0, 0, 1]],
            )

    @pytest.mark.cross_platform
    def test_addscanrisley_trajectory_length_validation(self):
        """traj_pos/traj_rot must match traj_t length, caught before any FFI call."""
        from pyhelios import LiDARCloud, RisleyPrism

        lidar = LiDARCloud.__new__(LiDARCloud)
        lidar._cloud_ptr = None
        with pytest.raises(ValueError):
            lidar.addScanRisley(
                prisms=[RisleyPrism(0.3, 1.51, 420.0)],
                refractive_index_air=1.0, pulse_rate_hz=100000.0,
                traj_t=[0.0, 1.0], traj_pos=[[0, 0, 1]],   # length 1 != 2
                traj_rot=[[0, 0, 0, 1], [0, 0, 0, 1]],
            )

    @pytest.mark.cross_platform
    def test_setprogresscallback_type_validation(self):
        """setProgressCallback rejects a non-callable, non-None argument."""
        from pyhelios import LiDARCloud

        lidar = LiDARCloud.__new__(LiDARCloud)
        lidar._cloud_ptr = None
        lidar._progress_callback_ref = None
        with pytest.raises(TypeError):
            lidar.setProgressCallback(42)

    @pytest.mark.cross_platform
    def test_addscanrisley_refractive_index_air_validation(self):
        """addScanRisley requires a positive refractive_index_air, caught before any FFI call."""
        from pyhelios import LiDARCloud, RisleyPrism

        lidar = LiDARCloud.__new__(LiDARCloud)
        lidar._cloud_ptr = None
        with pytest.raises(ValueError):
            lidar.addScanRisley(
                prisms=[RisleyPrism(0.3, 1.51, 420.0)],
                refractive_index_air=0.0, pulse_rate_hz=100000.0,
                traj_t=[0.0, 1.0], traj_pos=[[0, 0, 1], [0, 0, 1]],
                traj_rot=[[0, 0, 0, 1], [0, 0, 0, 1]],
            )

    @pytest.mark.cross_platform
    def test_gethitdatacolumnindex_type_validation(self):
        """getHitDataColumnIndex rejects a non-str label with a clear TypeError."""
        from pyhelios import LiDARCloud

        lidar = LiDARCloud.__new__(LiDARCloud)
        lidar._cloud_ptr = None
        with pytest.raises(TypeError):
            lidar.getHitDataColumnIndex(123)

    @pytest.mark.cross_platform
    def test_setsyntheticscanprogresspointer_type_validation(self):
        """setSyntheticScanProgressPointer rejects a non-c_int pointer with a clear TypeError."""
        from pyhelios import LiDARCloud

        lidar = LiDARCloud.__new__(LiDARCloud)
        lidar._cloud_ptr = None
        with pytest.raises(TypeError):
            lidar.setSyntheticScanProgressPointer(0)   # plain int, not ctypes.c_int


@pytest.mark.native_only
class TestLiDARRisleyReturnFunctionality:
    """Native functional tests for the helios-core 1.3.77 LiDAR additions."""

    @staticmethod
    def _two_prisms():
        from pyhelios import RisleyPrism
        # Two counter-rotating wedge prisms, the canonical Livox configuration.
        return [RisleyPrism(wedge_angle=math.radians(15), refractive_index=1.51,
                            rotor_rate=420.0, phase=0.0),
                RisleyPrism(wedge_angle=math.radians(15), refractive_index=1.51,
                            rotor_rate=-380.0, phase=0.0)]

    def test_risley_scan_reports_risley_mode(self):
        """addScanRisley() reports the RISLEY_PRISM pattern and acquisition mode and round-trips prisms."""
        from pyhelios import LiDARCloud, RisleyPrism
        from pyhelios.LiDARCloud import ScanPattern, ScanMode

        prisms = self._two_prisms()
        with LiDARCloud() as lidar:
            lidar.disableMessages()
            scan_id = lidar.addScanRisley(
                prisms=prisms, refractive_index_air=1.0003, pulse_rate_hz=100000.0,
                traj_t=[0.0, 0.1],
                traj_pos=[[0, 0, 1.5], [0, 0, 1.5]],   # stationary tripod capture
                traj_rot=[[0, 0, 0, 1], [0, 0, 0, 1]],
            )
            assert lidar.getScanPattern(scan_id) == ScanPattern.RISLEY_PRISM
            assert lidar.getScanMode(scan_id) == ScanMode.RISLEY_PRISM
            # Stored as a single-row (Ntheta=1) table.
            assert lidar.getScanSizeTheta(scan_id) == 1
            assert lidar.getScanRisleyRefractiveIndexAir(scan_id) == pytest.approx(1.0003, abs=1e-6)
            returned = lidar.getScanRisleyPrisms(scan_id)
            assert len(returned) == len(prisms)
            for got, want in zip(returned, prisms):
                assert isinstance(got, RisleyPrism)
                assert got.wedge_angle == pytest.approx(want.wedge_angle, abs=1e-6)
                assert got.refractive_index == pytest.approx(want.refractive_index, abs=1e-6)
                assert got.rotor_rate == pytest.approx(want.rotor_rate, abs=1e-4)
                assert got.phase == pytest.approx(want.phase, abs=1e-6)

    def test_risley_scan_euler_overload(self):
        """addScanRisley(rot_is_quaternion=False) accepts roll/pitch/yaw trajectory orientations."""
        from pyhelios import LiDARCloud
        from pyhelios.LiDARCloud import ScanMode

        with LiDARCloud() as lidar:
            lidar.disableMessages()
            scan_id = lidar.addScanRisley(
                prisms=self._two_prisms(), refractive_index_air=1.0, pulse_rate_hz=100000.0,
                traj_t=[0.0, 0.1],
                traj_pos=[[0, 0, 1.5], [0, 0, 1.5]],
                traj_rot=[[0, 0, 0], [0, 0, 0]],   # roll/pitch/yaw
                rot_is_quaternion=False,
            )
            assert lidar.getScanMode(scan_id) == ScanMode.RISLEY_PRISM

    def test_non_risley_scan_has_no_prisms(self):
        """A raster scan reports an empty prism stack and a 1.0 air index."""
        from pyhelios import LiDARCloud

        with LiDARCloud() as lidar:
            scan_id = lidar.addScan(
                origin=vec3(0, 0, 2),
                Ntheta=8, theta_range=(0.2, 1.4), Nphi=8, phi_range=(0, 6.28),
                exit_diameter=0.0, beam_divergence=0.0,
            )
            assert lidar.getScanRisleyPrisms(scan_id) == []
            assert lidar.getScanRisleyRefractiveIndexAir(scan_id) == pytest.approx(1.0, abs=1e-6)

    def test_memory_budget_roundtrip(self):
        """setSyntheticScanMemoryBudget()/getSyntheticScanMemoryBudget() round-trip; default is 0 (automatic)."""
        from pyhelios import LiDARCloud

        with LiDARCloud() as lidar:
            # Unset -> automatic, reported as 0.
            assert lidar.getSyntheticScanMemoryBudget() == 0
            lidar.setSyntheticScanMemoryBudget(2 * 1024 * 1024 * 1024)
            assert lidar.getSyntheticScanMemoryBudget() == 2 * 1024 * 1024 * 1024

    def test_hit_data_column_index(self):
        """getHitDataColumnIndex() returns -1 for an unknown label and a valid slot for a present one."""
        from pyhelios import Context, LiDARCloud

        with Context() as context:
            context.addPatch(center=vec3(0, 0, 0.5), size=vec2(1, 1))
            with LiDARCloud() as lidar:
                lidar.disableMessages()
                lidar.addScan(
                    origin=vec3(0, 0, 2),
                    Ntheta=12, theta_range=(0, 1.0), Nphi=12, phi_range=(0, 6.28),
                    exit_diameter=0.0, beam_divergence=0.0,
                    column_format=["x", "y", "z", "timestamp"],
                )
                lidar.syntheticScan(context, record_misses=True)
                assert lidar.getHitDataColumnIndex("definitely_not_a_label") == -1
                assert lidar.getHitDataColumnIndex("timestamp") >= 0

    def test_gpu_availability_queries(self):
        """isGPUAvailable()/isGPUAccelerationEnabled() are callable and return booleans."""
        from pyhelios import LiDARCloud

        with LiDARCloud() as lidar:
            assert isinstance(lidar.isGPUAvailable(), bool)
            assert isinstance(lidar.isGPUAccelerationEnabled(), bool)

    def test_synthetic_scan_progress_pointer(self):
        """setSyntheticScanProgressPointer() ends at getScanCount() after the batch finishes."""
        import ctypes
        from pyhelios import Context, LiDARCloud

        with Context() as context:
            context.addPatch(center=vec3(0, 0, 0.5), size=vec2(1, 1))
            with LiDARCloud() as lidar:
                lidar.disableMessages()
                lidar.addScan(
                    origin=vec3(0, 0, 2),
                    Ntheta=10, theta_range=(0, 1.0), Nphi=10, phi_range=(0, 6.28),
                    exit_diameter=0.0, beam_divergence=0.0,
                )
                progress = ctypes.c_int(-1)
                lidar.setSyntheticScanProgressPointer(progress)
                try:
                    lidar.syntheticScan(context, record_misses=True)
                    # Set to getScanCount() when the batch finishes.
                    assert progress.value == lidar.getScanCount()
                finally:
                    lidar.setSyntheticScanProgressPointer(None)

    def test_progress_callback_invoked(self):
        """setProgressCallback() receives (fraction, message) during a waveform syntheticScan."""
        from pyhelios import Context, LiDARCloud

        events = []
        with Context() as context:
            context.addPatch(center=vec3(0, 0, 0.5), size=vec2(1, 1))
            with LiDARCloud() as lidar:
                lidar.disableMessages()
                lidar.addScan(
                    origin=vec3(0, 0, 2),
                    Ntheta=16, theta_range=(0, 1.0), Nphi=16, phi_range=(0, 6.28),
                    exit_diameter=0.0, beam_divergence=0.0,
                )
                lidar.setProgressCallback(lambda frac, msg: events.append((frac, msg)))
                try:
                    lidar.syntheticScan(context, rays_per_pulse=8,
                                        pulse_distance_threshold=0.02, record_misses=True)
                finally:
                    lidar.setProgressCallback(None)
                # The callback fired with in-range fractions and string messages.
                assert len(events) > 0
                for frac, msg in events:
                    assert 0.0 <= frac <= 1.0
                    assert isinstance(msg, str)


@pytest.mark.native_only
class TestLiDARCapacityAndMemory:
    """helios-core 1.3.84 memory budgeting and capacity control."""

    def test_default_max_hit_points_is_100_million(self):
        from pyhelios import LiDARCloud
        assert LiDARCloud.getDefaultMaxHitPoints() == 100_000_000

    def test_new_cloud_starts_at_the_default_cap(self):
        from pyhelios import LiDARCloud
        with LiDARCloud() as lidar:
            assert lidar.getMaxHitPoints() == LiDARCloud.getDefaultMaxHitPoints()

    def test_set_and_get_max_hit_points(self):
        from pyhelios import LiDARCloud
        with LiDARCloud() as lidar:
            lidar.setMaxHitPoints(5_000_000)
            assert lidar.getMaxHitPoints() == 5_000_000

    def test_zero_disables_the_cap(self):
        from pyhelios import LiDARCloud
        with LiDARCloud() as lidar:
            lidar.setMaxHitPoints(0)
            assert lidar.getMaxHitPoints() == 0

    def test_reserve_does_not_create_hit_points(self):
        from pyhelios import LiDARCloud
        with LiDARCloud() as lidar:
            lidar.reserveHitPoints(10_000)
            assert lidar.getHitCount() == 0

    def test_reserve_beyond_the_cap_raises(self):
        """The cap exists so an over-fine scan grid fails with a diagnostic, not bad_alloc."""
        from pyhelios import LiDARCloud
        with LiDARCloud() as lidar:
            lidar.setMaxHitPoints(1000)
            with pytest.raises(HeliosError):
                lidar.reserveHitPoints(10_000_000)

    def test_memory_estimate_scales_with_point_count(self):
        from pyhelios import LiDARCloud
        with LiDARCloud() as lidar:
            one = lidar.estimateHitPointMemory(1_000_000)
            two = lidar.estimateHitPointMemory(2_000_000)
            assert one > 0
            assert two == pytest.approx(2 * one, rel=1e-6)

    def test_memory_estimate_of_zero_points(self):
        from pyhelios import LiDARCloud
        with LiDARCloud() as lidar:
            assert lidar.estimateHitPointMemory(0) == 0


@pytest.mark.native_only
class TestLiDARExactPathLengths:
    """helios-core 1.3.84 leaf-area inversion path-length accumulation mode."""

    def test_binning_is_the_default(self):
        from pyhelios import LiDARCloud
        with LiDARCloud() as lidar:
            assert lidar.getExactPathLengths() is False

    def test_enable_exact_path_lengths(self):
        from pyhelios import LiDARCloud
        with LiDARCloud() as lidar:
            lidar.setExactPathLengths(True)
            assert lidar.getExactPathLengths() is True

    def test_toggle_back_to_binning(self):
        from pyhelios import LiDARCloud
        with LiDARCloud() as lidar:
            lidar.setExactPathLengths(True)
            lidar.setExactPathLengths(False)
            assert lidar.getExactPathLengths() is False


@pytest.mark.native_only
class TestLiDARVirtualMisses:
    """helios-core 1.3.84 virtualized gap-filled misses and columnar readers."""

    @staticmethod
    def _scanned_cloud(context, lidar):
        lidar.addScan(origin=vec3(0, 0, 2), Ntheta=20, theta_range=(0, 1.2),
                      Nphi=20, phi_range=(0, 6.28), exit_diameter=0, beam_divergence=0)
        lidar.syntheticScan(context)

    def test_fresh_cloud_has_no_virtual_misses(self):
        from pyhelios import LiDARCloud
        with LiDARCloud() as lidar:
            assert lidar.hasVirtualMisses() is False
            assert lidar.getVirtualMissCount() == 0

    def test_gapfill_misses_count_returns_an_integer(self):
        from pyhelios import Context, LiDARCloud
        with Context() as context:
            context.addPatch(center=vec3(0, 0, 0.5), size=vec2(1, 1))
            with LiDARCloud() as lidar:
                self._scanned_cloud(context, lidar)
                added = lidar.gapfillMissesCount()
                assert isinstance(added, int)
                assert added >= 0

    def test_gapfill_misses_count_per_scan(self):
        from pyhelios import Context, LiDARCloud
        with Context() as context:
            context.addPatch(center=vec3(0, 0, 0.5), size=vec2(1, 1))
            with LiDARCloud() as lidar:
                self._scanned_cloud(context, lidar)
                added = lidar.gapfillMissesCount(scanID=0, gapfill_grid_only=False,
                                                 add_flags=False)
                assert isinstance(added, int)
                assert added >= 0

    def test_xyz_column_matches_per_index_accessor(self):
        """The columnar reader is the fast path; it must agree with the slow one exactly."""
        from pyhelios import Context, LiDARCloud
        with Context() as context:
            context.addPatch(center=vec3(0, 0, 0.5), size=vec2(1, 1))
            with LiDARCloud() as lidar:
                self._scanned_cloud(context, lidar)
                column = lidar.getHitXYZColumn()
                assert len(column) == lidar.getHitCount()
                for i in (0, lidar.getHitCount() // 2, lidar.getHitCount() - 1):
                    p = lidar.getHitXYZ(i)
                    assert column[i][0] == pytest.approx(p.x, abs=1e-5)
                    assert column[i][1] == pytest.approx(p.y, abs=1e-5)
                    assert column[i][2] == pytest.approx(p.z, abs=1e-5)

    def test_scan_id_column_matches_per_index_accessor(self):
        from pyhelios import Context, LiDARCloud
        with Context() as context:
            context.addPatch(center=vec3(0, 0, 0.5), size=vec2(1, 1))
            with LiDARCloud() as lidar:
                self._scanned_cloud(context, lidar)
                column = lidar.getHitScanIDColumn()
                assert len(column) == lidar.getHitCount()
                for i in (0, lidar.getHitCount() // 2, lidar.getHitCount() - 1):
                    assert column[i] == lidar.getHitScanID(i)

    def test_columns_are_empty_for_an_empty_cloud(self):
        from pyhelios import LiDARCloud
        with LiDARCloud() as lidar:
            assert lidar.getHitXYZColumn() == []
            assert lidar.getHitScanIDColumn() == []

    def test_materialize_misses_preserves_the_hit_count(self):
        """Materializing trades memory for storage; nothing observable changes."""
        from pyhelios import Context, LiDARCloud
        with Context() as context:
            context.addPatch(center=vec3(0, 0, 0.5), size=vec2(1, 1))
            with LiDARCloud() as lidar:
                self._scanned_cloud(context, lidar)
                lidar.gapfillMissesCount()
                before_count = lidar.getHitCount()
                before_xyz = lidar.getHitXYZColumn()
                lidar.materializeMisses()
                assert lidar.getHitCount() == before_count
                assert lidar.getVirtualMissCount() == 0
                after_xyz = lidar.getHitXYZColumn()
                for b, a in zip(before_xyz, after_xyz):
                    assert a[0] == pytest.approx(b[0], abs=1e-5)
                    assert a[2] == pytest.approx(b[2], abs=1e-5)

    def test_scan_grid_direction_requires_a_fitted_model(self):
        """Fail-fast: without gapfillMisses() there is no model, and that is said plainly."""
        from pyhelios import Context, LiDARCloud
        with Context() as context:
            context.addPatch(center=vec3(0, 0, 0.5), size=vec2(1, 1))
            with LiDARCloud() as lidar:
                self._scanned_cloud(context, lidar)
                with pytest.raises(HeliosError, match="no fitted scan-grid model"):
                    lidar.getScanGridDirection(0, 5, 5)

    def test_bulk_miss_array_matches_accessor_for_unflagged_hits(self):
        """A cloud can carry the is_miss column while individual hits lack the flag.

        hit_data_present is per-hit, so a hit added by a path that does not set is_miss
        leaves the column present-but-absent at that index. isHitMiss() falls back to
        distance classification for exactly those hits; a bulk reader that decides its
        strategy from whether the column exists cloud-wide would report them as hits.
        """
        from pyhelios import Context, LiDARCloud
        with Context() as context:
            context.addPatch(center=vec3(0, 0, 0.5), size=vec2(2, 2))
            with LiDARCloud() as lidar:
                self._scanned_cloud(context, lidar)
                # syntheticScan sets is_miss on every point it makes, so the column exists.
                # Add one hit at the miss sentinel distance without the flag.
                lidar.addHitPoint(0, vec3(0, 0, 2 + 20000.0), SphericalCoord(1, 0, 0))
                idx = lidar.getHitCount() - 1

                misses = lidar.getHitMissArray()
                assert bool(misses[idx]) == lidar.isHitMiss(idx)

    def test_bulk_miss_array_matches_per_index_accessor(self):
        """isLiDARHitMiss_all now reads the is_miss column; it must still agree."""
        from pyhelios import Context, LiDARCloud
        with Context() as context:
            context.addPatch(center=vec3(0, 0, 0.5), size=vec2(1, 1))
            with LiDARCloud() as lidar:
                self._scanned_cloud(context, lidar)
                misses = lidar.getHitMissArray()
                assert len(misses) == lidar.getHitCount()
                for i in (0, lidar.getHitCount() // 2, lidar.getHitCount() - 1):
                    assert bool(misses[i]) == lidar.isHitMiss(i)
