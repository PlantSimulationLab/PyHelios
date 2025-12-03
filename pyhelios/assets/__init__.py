"""
Dynamic Asset Path Resolution for PyHelios

This module provides working-directory-independent asset path resolution
for PyHelios plugins. It automatically locates assets in the helios-core
source directory and sets up environment variables for C++ plugins.

The key principle is NO MANUAL COPYING - all assets are referenced directly
from their source locations to ensure they stay synchronized with the
helios-core repository.
"""

import os
import logging
from pathlib import Path
from typing import Optional, Dict, Any

# Configure logging
logger = logging.getLogger(__name__)


class AssetPathManager:
    """Manages dynamic resolution of asset paths for PyHelios plugins."""

    def __init__(self):
        self._helios_core_path: Optional[Path] = None
        self._initialized = False

    def _find_helios_core(self) -> Optional[Path]:
        """
        Find the helios-core directory relative to PyHelios package.

        Returns:
            Path to helios-core directory, or None if not found
        """
        if self._helios_core_path is not None:
            return self._helios_core_path

        # Start from the PyHelios package directory
        pyhelios_root = Path(__file__).parent.parent.parent

        # Look for helios-core as a subdirectory
        helios_core_candidates = [
            pyhelios_root / 'helios-core',
            pyhelios_root.parent / 'helios-core',  # In case PyHelios is in a subdirectory
        ]

        for candidate in helios_core_candidates:
            if candidate.exists() and candidate.is_dir():
                # Verify it's actually the helios-core by checking for key directories
                if (candidate / 'core').exists() and (candidate / 'plugins').exists():
                    self._helios_core_path = candidate
                    logger.info(f"Found helios-core at: {candidate}")
                    return candidate

        # In wheel installations, helios-core directory is not expected to exist
        # Assets are packaged separately in wheel distributions
        if not self._is_wheel_install():
            # Check if we have packaged assets available before warning
            package_root = Path(__file__).parent
            packaged_build = package_root / 'build'
            if packaged_build.exists() and (packaged_build / 'lib' / 'images').exists():
                logger.debug("helios-core directory not found, but packaged assets are available")
            else:
                logger.warning("helios-core directory not found - asset paths may not work correctly")
        return None

    def get_helios_core_path(self) -> Optional[Path]:
        """Get the path to the helios-core directory."""
        return self._find_helios_core()

    def _is_wheel_install(self) -> bool:
        """
        Detect if we're running from an installed wheel package.

        Returns:
            True if running from wheel installation, False otherwise
        """
        package_root = Path(__file__).parent
        pyhelios_parent = package_root.parent.parent  # Go up to site-packages level

        # Look for .dist-info directory which indicates wheel installation
        # The package is distributed as 'pyhelios3d' but the Python module is 'pyhelios'
        return any(pyhelios_parent.glob('pyhelios3d-*.dist-info')) or any(pyhelios_parent.glob('pyhelios-*.dist-info'))

    def _get_helios_build_path(self) -> Optional[Path]:
        """
        Find the HELIOS_BUILD directory containing assets.

        This searches for the directory structure that Helios C++ expects:
        - lib/images/ (core textures)
        - plugins/ (plugin assets)

        Search priority ensures pip-installed users get the correct packaged assets
        even if they have incomplete development directories.

        Returns:
            Path to build directory, or None if not found
        """
        package_root = Path(__file__).parent
        packaged_build = package_root / 'build'  # pyhelios/assets/build/

        # Check if we're in a wheel installation
        is_wheel_install = self._is_wheel_install()

        if is_wheel_install:
            # WHEEL INSTALL: Only check packaged assets location
            if (packaged_build.exists() and
                (packaged_build / 'lib' / 'images').exists() and
                len(list((packaged_build / 'lib' / 'images').glob('*'))) > 0):
                logger.debug(f"Using wheel-installed assets: {packaged_build}")
                return packaged_build
            else:
                # This is a critical packaging error for wheels
                raise RuntimeError(
                    f"Wheel installation detected but assets not found at {packaged_build}. "
                    f"This indicates a packaging error. Expected structure:\n"
                    f"  {packaged_build / 'lib' / 'images'} with image files"
                )

        # DEVELOPMENT INSTALL: Check packaged assets first, then development paths

        # PRIORITY 1: Check for packaged assets (even in development)
        if (packaged_build.exists() and
            (packaged_build / 'lib' / 'images').exists() and
            len(list((packaged_build / 'lib' / 'images').glob('*'))) > 0):
            logger.debug(f"Using development packaged assets: {packaged_build}")
            return packaged_build

        # Log diagnostic information if packaged assets are missing or incomplete
        if packaged_build.exists():
            logger.debug(f"Packaged assets directory exists but incomplete: {packaged_build}")
            if not (packaged_build / 'lib' / 'images').exists():
                logger.debug("  Missing lib/images directory")
            else:
                image_count = len(list((packaged_build / 'lib' / 'images').glob('*')))
                logger.debug(f"  Found {image_count} images (need > 0 for validation)")
        else:
            logger.debug(f"Packaged assets directory does not exist: {packaged_build}")

        # PRIORITY 2: For development, look for pyhelios_build/build directory
        # Only used if pip-installed assets are not available
        helios_core = self.get_helios_core_path()
        if helios_core:
            project_root = helios_core.parent
            dev_build_paths = [
                project_root / 'pyhelios_build' / 'build',
                project_root / 'build',  # Alternative build location
            ]

            for build_path in dev_build_paths:
                if (build_path.exists() and
                    (build_path / 'lib' / 'images').exists() and
                    len(list((build_path / 'lib' / 'images').glob('*'))) > 0):
                    logger.debug(f"Using development build assets: {build_path}")
                    return build_path

        # PRIORITY 3: Fallback to helios-core source directory
        # This works for some assets but may not have all compiled assets
        if helios_core and (helios_core / 'core' / 'lib' / 'images').exists():
            logger.debug("Using helios-core directory as fallback HELIOS_BUILD path")
            return helios_core

        return None

    def get_weberpenntree_assets_path(self) -> Optional[str]:
        """
        Get the path to WeberPennTree plugin assets.

        Returns:
            Absolute path to weberpenntree assets directory, or None if not found
        """
        # First try packaged assets (for wheel installations)
        build_path = self._get_helios_build_path()
        if build_path:
            wpt_path = build_path / 'plugins' / 'weberpenntree'
            if wpt_path.exists():
                return str(wpt_path)

        # Fallback to helios-core directory (for development)
        helios_core = self.get_helios_core_path()
        if helios_core:
            wpt_path = helios_core / 'plugins' / 'weberpenntree'
            if wpt_path.exists():
                return str(wpt_path)

            if not self._is_wheel_install():
                logger.warning(f"WeberPennTree assets not found at: {wpt_path}")

        return None

    def get_visualizer_assets_path(self) -> Optional[str]:
        """
        Get the path to Visualizer plugin assets.

        Returns:
            Absolute path to visualizer assets directory, or None if not found
        """
        # First try packaged assets (for wheel installations)
        build_path = self._get_helios_build_path()
        if build_path:
            visualizer_path = build_path / 'plugins' / 'visualizer'
            if visualizer_path.exists():
                return str(visualizer_path)

        # Fallback to helios-core directory (for development)
        helios_core = self.get_helios_core_path()
        if helios_core:
            visualizer_path = helios_core / 'plugins' / 'visualizer'
            if visualizer_path.exists():
                return str(visualizer_path)

            if not self._is_wheel_install():
                logger.warning(f"Visualizer assets not found at: {visualizer_path}")

        return None


    def get_radiation_assets_path(self) -> Optional[str]:
        """
        Get the path to Radiation plugin assets.

        Returns:
            Absolute path to radiation assets directory, or None if not found
        """
        # First try packaged assets (for wheel installations)
        build_path = self._get_helios_build_path()
        if build_path:
            radiation_path = build_path / 'plugins' / 'radiation'
            if radiation_path.exists():
                return str(radiation_path)

        # Fallback to helios-core directory (for development)
        helios_core = self.get_helios_core_path()
        if helios_core:
            radiation_path = helios_core / 'plugins' / 'radiation'
            if radiation_path.exists():
                return str(radiation_path)

            if not self._is_wheel_install():
                logger.warning(f"Radiation assets not found at: {radiation_path}")

        return None

    def get_solarposition_assets_path(self) -> Optional[str]:
        """
        Get the path to SolarPosition plugin assets.

        Returns:
            Absolute path to solarposition assets directory, or None if not found
        """
        # First try packaged assets (for wheel installations)
        build_path = self._get_helios_build_path()
        if build_path:
            solarposition_path = build_path / 'plugins' / 'solarposition'
            if solarposition_path.exists():
                return str(solarposition_path)

        # Fallback to helios-core directory (for development)
        helios_core = self.get_helios_core_path()
        if helios_core:
            solarposition_path = helios_core / 'plugins' / 'solarposition'
            if solarposition_path.exists():
                return str(solarposition_path)

            if not self._is_wheel_install():
                logger.warning(f"SolarPosition assets not found at: {solarposition_path}")

        return None

    def get_all_asset_paths(self) -> Dict[str, Optional[str]]:
        """
        Get all available plugin asset paths.

        Returns:
            Dictionary mapping plugin names to their asset directory paths
        """
        return {
            'weberpenntree': self.get_weberpenntree_assets_path(),
            'visualizer': self.get_visualizer_assets_path(),
            'radiation': self.get_radiation_assets_path(),
            'solarposition': self.get_solarposition_assets_path(),
        }

    def set_environment_variables(self) -> None:
        """
        Set environment variables for C++ plugins to find their assets.

        This method sets the following environment variables:
        - HELIOS_BUILD: Path to build directory with assets (REQUIRED by Helios C++)
        - HELIOS_ASSET_ROOT: Path to helios-core directory
        - HELIOS_WEBERPENNTREE_PATH: Path to WeberPennTree assets
        - HELIOS_VISUALIZER_PATH: Path to Visualizer assets
        - HELIOS_RADIATION_PATH: Path to Radiation assets
        """
        helios_core = self.get_helios_core_path()
        if helios_core:
            os.environ['HELIOS_ASSET_ROOT'] = str(helios_core)
            logger.debug(f"Set HELIOS_ASSET_ROOT = {helios_core}")

            # CRITICAL: Set HELIOS_BUILD environment variable
            # This is REQUIRED by Helios C++ core for asset discovery
            helios_build_path = self._get_helios_build_path()
            if helios_build_path and helios_build_path.exists():
                os.environ['HELIOS_BUILD'] = str(helios_build_path)
                logger.debug(f"Set HELIOS_BUILD = {helios_build_path}")
            else:
                self._log_helios_build_error()

        asset_paths = self.get_all_asset_paths()

        for plugin_name, path in asset_paths.items():
            if path is not None:
                env_var = f"HELIOS_{plugin_name.upper()}_PATH"
                os.environ[env_var] = path
                logger.debug(f"Set {env_var} = {path}")
            else:
                logger.warning(f"Could not set asset path for plugin: {plugin_name}")

    def initialize(self) -> bool:
        """
        Initialize the asset path manager and set up environment variables.

        Returns:
            True if initialization was successful, False otherwise
        """
        if self._initialized:
            return True

        try:
            self.set_environment_variables()
            self._initialized = True
            logger.info("Asset path manager initialized successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to initialize asset path manager: {e}")
            return False

    def validate_assets(self) -> Dict[str, Dict[str, Any]]:
        """
        Validate that all expected asset directories and files exist.

        Returns:
            Dictionary with validation results for each plugin
        """
        results = {}
        asset_paths = self.get_all_asset_paths()

        for plugin_name, base_path in asset_paths.items():
            result = {
                'base_path': base_path,
                'exists': False,
                'subdirectories': {},
                'files_found': 0
            }

            if base_path and Path(base_path).exists():
                result['exists'] = True
                base_dir = Path(base_path)

                # Check for expected subdirectories based on plugin
                expected_subdirs = self._get_expected_subdirectories(plugin_name)

                for subdir in expected_subdirs:
                    subdir_path = base_dir / subdir
                    result['subdirectories'][subdir] = {
                        'exists': subdir_path.exists(),
                        'files': list(subdir_path.glob('*')) if subdir_path.exists() else []
                    }

                    if subdir_path.exists():
                        result['files_found'] += len(list(subdir_path.glob('*')))

            results[plugin_name] = result

        return results

    def _get_expected_subdirectories(self, plugin_name: str) -> list:
        """Get expected subdirectories for a given plugin."""
        subdirs_map = {
            'weberpenntree': ['leaves', 'wood', 'xml'],
            'visualizer': ['shaders', 'textures', 'fonts'],
            'radiation': ['spectral_data'],
            'solarposition': ['ssolar_goa']
        }
        return subdirs_map.get(plugin_name, [])

    def _log_helios_build_error(self) -> None:
        """Log actionable error message when HELIOS_BUILD directory is not found."""
        # Try to determine installation context for better error messages
        package_root = Path(__file__).parent
        packaged_build = package_root / 'build'
        helios_core = self.get_helios_core_path()

        if packaged_build.exists():
            # Assets directory exists but missing required structure
            logger.error(
                "HELIOS_BUILD directory found but missing required assets. "
                f"Expected lib/images/ directory not found in {packaged_build}. "
                "This indicates a packaging issue - please report this as a bug."
            )
        elif helios_core:
            # In development environment
            logger.error(
                "HELIOS_BUILD directory not found. This will cause asset-dependent "
                "features to fail. Please build native libraries using:\n"
                "  python build_scripts/build_helios.py"
            )
        else:
            # Pip-installed or broken environment
            logger.error(
                "HELIOS_BUILD directory not found and no helios-core directory detected. "
                "If you installed PyHelios via pip, this is a packaging bug - please report it. "
                "If you're in a development environment, ensure helios-core submodule is properly "
                "initialized and build libraries using: python build_scripts/build_helios.py"
            )


# Global asset path manager instance
_asset_manager: Optional[AssetPathManager] = None


def get_asset_manager() -> AssetPathManager:
    """Get the global asset path manager instance."""
    global _asset_manager
    if _asset_manager is None:
        _asset_manager = AssetPathManager()
    return _asset_manager


def initialize_asset_paths() -> bool:
    """
    Initialize asset paths for all PyHelios plugins.

    This function should be called during PyHelios package initialization
    to set up environment variables that C++ plugins can use to find their assets.

    Returns:
        True if initialization was successful, False otherwise
    """
    manager = get_asset_manager()
    return manager.initialize()


def get_weberpenntree_assets() -> Optional[str]:
    """Get the path to WeberPennTree plugin assets."""
    return get_asset_manager().get_weberpenntree_assets_path()


def get_visualizer_assets() -> Optional[str]:
    """Get the path to Visualizer plugin assets."""
    return get_asset_manager().get_visualizer_assets_path()


def get_radiation_assets() -> Optional[str]:
    """Get the path to Radiation plugin assets."""
    return get_asset_manager().get_radiation_assets_path()


def get_solarposition_assets() -> Optional[str]:
    """Get the path to SolarPosition plugin assets."""
    return get_asset_manager().get_solarposition_assets_path()


def get_all_asset_paths() -> Dict[str, Optional[str]]:
    """Get all available plugin asset paths."""
    return get_asset_manager().get_all_asset_paths()


def validate_assets() -> Dict[str, Dict[str, Any]]:
    """Validate that all expected asset directories and files exist."""
    return get_asset_manager().validate_assets()


def print_asset_status():
    """Print comprehensive asset status information."""
    manager = get_asset_manager()

    print("PyHelios Asset Status")
    print("=" * 21)

    helios_core = manager.get_helios_core_path()
    if helios_core:
        print(f"Helios Core: {helios_core}")
    else:
        print("Helios Core: NOT FOUND")
        print("⚠️  Asset paths may not work correctly")
        return

    print()
    validation_results = manager.validate_assets()

    for plugin_name, result in validation_results.items():
        status_icon = "✓" if result['exists'] else "✗"
        print(f"{status_icon} {plugin_name.title()}: {result['base_path']}")

        if result['exists']:
            print(f"  Files found: {result['files_found']}")
            for subdir, info in result['subdirectories'].items():
                subdir_icon = "✓" if info['exists'] else "✗"
                file_count = len(info['files']) if info['exists'] else 0
                print(f"  {subdir_icon} {subdir}/: {file_count} files")
        else:
            print("  Directory not found")
        print()

    # Print environment variables
    print("Environment Variables:")
    print("-" * 21)
    env_vars = ['HELIOS_ASSET_ROOT', 'HELIOS_WEBERPENNTREE_PATH',
                'HELIOS_VISUALIZER_PATH', 'HELIOS_RADIATION_PATH',
                'HELIOS_SOLARPOSITION_PATH']

    for var in env_vars:
        value = os.environ.get(var, 'Not set')
        print(f"{var}: {value}")