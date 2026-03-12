from setuptools import setup, find_packages, Extension
from setuptools.command.build_py import build_py
import os
import platform
import glob
import shutil
from pathlib import Path

# Read development requirements
def read_dev_requirements():
    try:
        with open('requirements-dev.txt', 'r') as f:
            return [line.strip() for line in f if line.strip() and not line.startswith('#')]
    except FileNotFoundError:
        return []

def get_platform_libraries():
    """Get platform-specific library files for packaging from build directory."""
    # Look in build directory where prepare_wheel.py leaves them
    build_lib_dir = os.path.join('pyhelios_build', 'build', 'lib')
    if not os.path.exists(build_lib_dir):
        return []

    system = platform.system()
    if system == 'Windows':
        patterns = ['*.dll']
    elif system == 'Darwin':  # macOS
        patterns = ['*.dylib']
    elif system == 'Linux':
        patterns = ['*.so', '*.so.*']
    else:
        # Include all possible library types
        patterns = ['*.dll', '*.dylib', '*.so', '*.so.*']

    library_files = []
    for pattern in patterns:
        found_files = glob.glob(os.path.join(build_lib_dir, pattern))
        # Only include files that exist and have non-zero size
        for f in found_files:
            if os.path.exists(f) and os.path.getsize(f) > 0:
                library_files.append(f)

    # Return paths relative to project root for data_files
    return library_files

def get_asset_files():
    """Get asset files for packaging in wheels from build directory."""
    # Look for assets in the build directory where prepare_wheel.py organizes them
    assets_dir = os.path.join('pyhelios_build', 'build', 'assets_for_wheel')

    asset_patterns = []

    if os.path.exists(assets_dir):
        build_dir = assets_dir
        if os.path.exists(build_dir):
            # Core assets
            core_images = os.path.join(build_dir, 'lib', 'images')
            if os.path.exists(core_images):
                asset_patterns.append(os.path.join(assets_dir, 'lib', 'images', '*'))

            # Plugin assets - comprehensive patterns matching prepare_wheel.py
            plugins_dir = os.path.join(build_dir, 'plugins')
            if os.path.exists(plugins_dir):
                # Base patterns for all platforms (relative to build directory)
                base_patterns = [
                    # Shader files - all graphics shader types
                    'plugins/*/shaders/*.glsl',
                    'plugins/*/shaders/*.vert',
                    'plugins/*/shaders/*.frag',
                    'plugins/*/shaders/*.geom',
                    'plugins/*/shaders/*.comp',
                    # Font files - all font formats
                    'plugins/*/fonts/*.ttf',
                    'plugins/*/fonts/*.otf',
                    'plugins/*/fonts/*.woff',
                    'plugins/*/fonts/*.woff2',
                    # Texture files - all image formats
                    'plugins/*/textures/*.png',
                    'plugins/*/textures/*.jpg',
                    'plugins/*/textures/*.jpeg',
                    'plugins/*/textures/*.tiff',
                    'plugins/*/textures/*.bmp',
                    # WeberPennTree assets - leaves and wood
                    'plugins/*/leaves/*.xml',
                    'plugins/*/leaves/*.obj',
                    'plugins/*/leaves/*.ply',
                    'plugins/*/wood/*.xml',
                    'plugins/*/wood/*.obj',
                    'plugins/*/wood/*.ply',
                    # XML configuration files
                    'plugins/*/xml/*.xml',
                    # Generic data files
                    'plugins/*/data/*.csv',
                    'plugins/*/data/*.txt',
                    'plugins/*/data/*.dat',
                    'plugins/*/data/*.json',
                    # Camera and light models
                    'plugins/*/camera_light_models/*.xml',
                    'plugins/*/camera_light_models/*.json',
                    # Subdirectories recursively for complex asset structures
                    'plugins/*/shaders/**/*',
                    'plugins/*/fonts/**/*',
                    'plugins/*/textures/**/*',
                    'plugins/*/data/**/*',
                ]
                # Prepend the build directory path to each pattern
                asset_patterns.extend([os.path.join(assets_dir, p) for p in base_patterns])

            # Platform-specific assets: Radiation spectral data only on Windows/Linux
            # Exclude radiation assets on macOS (consistent with prepare_wheel.py)
            if platform.system() != 'Darwin':
                radiation_patterns = [
                    # Spectral data - all data formats (radiation plugin)
                    'plugins/*/spectral_data/*.csv',
                    'plugins/*/spectral_data/*.txt',
                    'plugins/*/spectral_data/*.dat',
                    'plugins/*/spectral_data/**/*',
                ]
                asset_patterns.extend([os.path.join(assets_dir, p) for p in radiation_patterns])

    return asset_patterns

def get_long_description():
    """Read long description from README."""
    try:
        with open('README.md', 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        return 'Python bindings for Helios 3D plant simulation library'

def get_extensions():
    """
    Create a stub extension to force setuptools to create platform-specific wheels.

    This is necessary because setuptools only creates platform-specific wheels when
    it detects compiled extensions. Since PyHelios includes pre-built native libraries
    via CustomBuildPy, we need this stub to signal that the wheel is platform-specific.
    """
    # Check if we have actual binary libraries in the build directory
    build_lib_dir = os.path.join('pyhelios_build', 'build', 'lib')
    has_binaries = False

    if os.path.exists(build_lib_dir):
        system = platform.system()
        if system == 'Windows':
            has_binaries = bool(glob.glob(os.path.join(build_lib_dir, '*.dll')))
        elif system == 'Darwin':
            has_binaries = bool(glob.glob(os.path.join(build_lib_dir, '*.dylib')))
        else:  # Linux
            has_binaries = bool(glob.glob(os.path.join(build_lib_dir, '*.so*')))

    if has_binaries:
        # Create a minimal stub extension that signals binary content
        stub_extension = Extension(
            name='pyhelios._stub',
            sources=['pyhelios/_stub.c'],  # Minimal C extension
            optional=True,  # Won't fail build if compilation fails
        )
        return [stub_extension]
    else:
        # No binaries found - allow pure Python wheel
        return []

class CustomBuildPy(build_py):
    """
    Custom build_py command that copies libraries and assets from build directory
    into the package structure during wheel creation.

    This keeps the source tree clean while ensuring wheels contain all necessary files.
    """
    def run(self):
        # Run standard build_py first
        super().run()

        # Copy libraries from pyhelios_build/build/lib/ to build/lib/pyhelios/plugins/
        build_lib_dir = Path('pyhelios_build') / 'build' / 'lib'
        if build_lib_dir.exists():
            # Determine target directory in build output
            target_plugins_dir = Path(self.build_lib) / 'pyhelios' / 'plugins'
            target_plugins_dir.mkdir(parents=True, exist_ok=True)

            # Platform-specific library extensions
            system = platform.system()
            if system == 'Windows':
                patterns = ['*.dll']
            elif system == 'Darwin':
                patterns = ['*.dylib']
            else:
                patterns = ['*.so', '*.so.*']

            # Copy all matching libraries
            copied = 0
            for pattern in patterns:
                for lib_file in build_lib_dir.glob(pattern):
                    dest = target_plugins_dir / lib_file.name
                    shutil.copy2(lib_file, dest)
                    print(f"Copied library: {lib_file.name} -> {dest}")
                    copied += 1

            if copied > 0:
                print(f"Copied {copied} libraries from build directory")

        # Copy assets from pyhelios_build/build/assets_for_wheel/ to build/lib/pyhelios/assets/build/
        assets_src_dir = Path('pyhelios_build') / 'build' / 'assets_for_wheel'
        if assets_src_dir.exists():
            target_assets_dir = Path(self.build_lib) / 'pyhelios' / 'assets' / 'build'

            # Remove existing assets directory in build if it exists
            if target_assets_dir.exists():
                shutil.rmtree(target_assets_dir)

            # Copy entire assets directory
            shutil.copytree(assets_src_dir, target_assets_dir)
            print(f"Copied assets from {assets_src_dir} to {target_assets_dir}")

# Get platform-appropriate library files and assets for validation
library_files = get_platform_libraries()
asset_files = get_asset_files()

# Package data now includes patterns for files that will be copied during build
# These patterns match what CustomBuildPy will copy
package_data = {
    'pyhelios': [
        'plugins/*.dll',
        'plugins/*.so',
        'plugins/*.so.*',
        'plugins/*.dylib',
        'assets/build/lib/images/*',
        'assets/build/plugins/*/shaders/*',
        'assets/build/plugins/*/textures/*',
        'assets/build/plugins/*/fonts/*',
        'assets/build/plugins/*/leaves/*',
        'assets/build/plugins/*/wood/*',
        'assets/build/plugins/*/xml/*',
        'assets/build/plugins/*/data/*',
        'assets/build/plugins/*/spectral_data/*',
        'assets/build/plugins/*/camera_light_models/*',
        'assets/build/plugins/*/*',  # Nested structures
        'assets/build/plugins/*/*/*',  # Deeply nested
    ]
}

setup(
    name='pyhelios3d',
    use_scm_version=True,
    description='Cross-platform Python bindings for Helios 3D plant simulation',
    long_description=get_long_description(),
    long_description_content_type='text/markdown',
    author='Brian Bailey',
    author_email='bnbailey@ucdavis.edu',
    url='https://github.com/PlantSimulationLab/PyHelios',
    packages=find_packages(exclude=('tests', 'docs', 'build_scripts', 'pyhelios_build*')),
    package_data=package_data,
    include_package_data=True,
    ext_modules=get_extensions(),  # Force platform-specific wheels
    cmdclass={
        'build_py': CustomBuildPy,  # Custom build to copy files from pyhelios_build/
    },
    
    # Platform support
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Science/Research',
        'License :: OSI Approved :: GNU General Public License v2 (GPLv2)',
        'Operating System :: Microsoft :: Windows',
        'Operating System :: POSIX :: Linux', 
        'Operating System :: MacOS',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Programming Language :: Python :: 3.12',
        'Programming Language :: Python :: 3.13',
        'Programming Language :: Python :: 3.14',
        'Topic :: Scientific/Engineering',
        'Topic :: Scientific/Engineering :: Physics',
        'Topic :: Scientific/Engineering :: Visualization',
    ],
    
    # Dependencies
    install_requires=[
        'numpy>=1.19.0',  # Core dependency for PyHelios data structures
        'pyyaml>=5.0.0',  # Configuration file parsing for plugin system
    ],
    setup_requires=[
        'setuptools-scm',
    ],
    extras_require={
        'dev': read_dev_requirements(),
        'test': [
            'pytest>=7.0.0',
            'pytest-cov>=4.0.0',
            'pytest-mock>=3.10.0',
            'pytest-xdist>=3.0.0',
            'pytest-timeout>=2.1.0',
            'pytest-forked>=1.6.0',  # required for --forked flag in pytest config
        ],
        'build': [
            'cmake',
        ],
    },
    
    # Entry points for build utilities
    entry_points={
        'console_scripts': [
            'pyhelios-build=build_scripts.build_helios:main',
        ],
    },
    
    python_requires='>=3.10',
    
    # Additional metadata
    keywords='helios, plant simulation, 3d modeling, ray tracing, photosynthesis, plant architecture',
    project_urls={
        'Documentation': 'https://baileylab.ucdavis.edu/software/helios',
        'Source': 'https://github.com/PlantSimulationLab/PyHelios',
        'Tracker': 'https://github.com/PlantSimulationLab/PyHelios/issues',
        'Helios Core': 'https://github.com/PlantSimulationLab/Helios',
    },
)