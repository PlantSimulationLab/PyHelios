"""
High-level LeafOptics interface for PyHelios.

This module provides a user-friendly interface to the PROSPECT leaf optical model
for computing spectral reflectance and transmittance of plant leaves.
"""

import logging
import os
from contextlib import contextmanager
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional, Tuple

from .plugins.registry import get_plugin_registry
from .wrappers import ULeafOpticsWrapper as leafoptics_wrapper
from .Context import Context
from .exceptions import HeliosError
from .assets import get_asset_manager

logger = logging.getLogger(__name__)


class LeafOpticsError(HeliosError):
    """Exception raised for LeafOptics-specific errors."""
    pass


# Available species in the built-in library
AVAILABLE_SPECIES = [
    "default",
    "garden_lettuce",
    "alfalfa",
    "corn",
    "sunflower",
    "english_walnut",
    "rice",
    "soybean",
    "wine_grape",
    "tomato",
    "common_bean",
    "cowpea"
]


@dataclass
class LeafOpticsProperties:
    """
    Data class for PROSPECT leaf optical model parameters.

    These parameters define the physical and biochemical properties of a leaf
    that determine its spectral reflectance and transmittance.

    Attributes:
        numberlayers: Number of mesophyll layers in the leaf (typically 1-3)
        brownpigments: Brown pigment content (arbitrary units, typically 0)
        chlorophyllcontent: Chlorophyll a+b content in micrograms per square cm
        carotenoidcontent: Carotenoid content in micrograms per square cm
        anthocyancontent: Anthocyanin content in micrograms per square cm
        watermass: Equivalent water thickness in grams per square cm
        drymass: Dry matter content (leaf mass per area) in grams per square cm
        protein: Protein content in grams per square cm (PROSPECT-PRO mode)
        carbonconstituents: Carbon-based constituents in grams per square cm (PROSPECT-PRO mode)

    Note:
        - If protein > 0 OR carbonconstituents > 0, the model uses PROSPECT-PRO mode
          which ignores drymass and uses protein + carbonconstituents instead.
        - Otherwise, the model uses PROSPECT-D mode which uses drymass.
    """
    numberlayers: float = 1.5
    brownpigments: float = 0.0
    chlorophyllcontent: float = 30.0  # micrograms/cm^2
    carotenoidcontent: float = 7.0    # micrograms/cm^2
    anthocyancontent: float = 1.0     # micrograms/cm^2
    watermass: float = 0.015          # g/cm^2
    drymass: float = 0.09             # g/cm^2
    protein: float = 0.0              # g/cm^2 (PROSPECT-PRO mode)
    carbonconstituents: float = 0.0   # g/cm^2 (PROSPECT-PRO mode)

    def to_list(self) -> List[float]:
        """Convert properties to a list in the order expected by the C++ interface."""
        return [
            self.numberlayers,
            self.brownpigments,
            self.chlorophyllcontent,
            self.carotenoidcontent,
            self.anthocyancontent,
            self.watermass,
            self.drymass,
            self.protein,
            self.carbonconstituents
        ]

    @classmethod
    def from_list(cls, values: List[float]) -> 'LeafOpticsProperties':
        """Create LeafOpticsProperties from a list of values."""
        if len(values) != 9:
            raise ValueError(f"Expected 9 values, got {len(values)}")
        return cls(
            numberlayers=values[0],
            brownpigments=values[1],
            chlorophyllcontent=values[2],
            carotenoidcontent=values[3],
            anthocyancontent=values[4],
            watermass=values[5],
            drymass=values[6],
            protein=values[7],
            carbonconstituents=values[8]
        )


@contextmanager
def _leafoptics_working_directory():
    """
    Context manager that temporarily changes working directory to where LeafOptics assets are located.

    LeafOptics C++ code uses relative paths like "plugins/leafoptics/spectral_data/"
    expecting assets relative to working directory. This manager temporarily changes to the build
    directory where assets are actually located.
    """
    # Find the build directory containing LeafOptics assets
    asset_manager = get_asset_manager()
    working_dir = asset_manager._get_helios_build_path()

    if working_dir and working_dir.exists():
        leafoptics_assets = working_dir / 'plugins' / 'leafoptics' / 'spectral_data'
    else:
        # Fallback to development paths
        current_dir = Path(__file__).parent
        repo_root = current_dir.parent
        build_lib_dir = repo_root / 'pyhelios_build' / 'build' / 'lib'
        working_dir = build_lib_dir.parent
        leafoptics_assets = working_dir / 'plugins' / 'leafoptics' / 'spectral_data'

        if not build_lib_dir.exists():
            raise LeafOpticsError(
                f"PyHelios build directory not found at {build_lib_dir}. "
                f"LeafOptics requires native libraries to be built. "
                f"Run: build_scripts/build_helios --plugins leafoptics"
            )

    # Validate spectral data file exists
    spectral_file = leafoptics_assets / 'prospect_spectral_library.xml'
    if not spectral_file.exists():
        raise LeafOpticsError(
            f"LeafOptics spectral data not found at {spectral_file}. "
            f"Build system failed to copy LeafOptics assets. "
            f"Run: build_scripts/build_helios --clean --plugins leafoptics"
        )

    # Validate file size (should be ~475KB)
    file_size = spectral_file.stat().st_size
    if file_size < 400000:  # Less than 400KB indicates corruption
        raise LeafOpticsError(
            f"LeafOptics spectral data file appears corrupted (size: {file_size} bytes, expected ~475KB). "
            f"Run: build_scripts/build_helios --clean --plugins leafoptics"
        )

    # Change to the build directory temporarily
    original_dir = os.getcwd()
    try:
        os.chdir(working_dir)
        logger.debug(f"Changed working directory to {working_dir} for LeafOptics asset access")
        yield working_dir
    finally:
        os.chdir(original_dir)
        logger.debug(f"Restored working directory to {original_dir}")


class LeafOptics:
    """
    High-level interface for PROSPECT leaf optical model.

    This class provides a user-friendly wrapper around the native Helios
    LeafOptics plugin for computing spectral reflectance and transmittance
    of plant leaves based on their biochemical properties.

    The PROSPECT model computes spectral optical properties for wavelengths
    from 400 nm to 2500 nm at 1 nm resolution (2101 data points).

    System requirements:
        - Cross-platform support (Windows, Linux, macOS)
        - No GPU required
        - Requires spectral_data assets (~475KB XML file)
        - LeafOptics plugin compiled into PyHelios

    Example:
        >>> from pyhelios import Context, LeafOptics, LeafOpticsProperties
        >>>
        >>> with Context() as context:
        ...     with LeafOptics(context) as leafoptics:
        ...         # Get properties for a known species
        ...         props = leafoptics.getPropertiesFromLibrary("sunflower")
        ...         print(f"Sunflower chlorophyll: {props.chlorophyllcontent} ug/cm^2")
        ...
        ...         # Compute spectra
        ...         wavelengths, reflectance, transmittance = leafoptics.getLeafSpectra(props)
        ...         print(f"Spectral range: {wavelengths[0]}-{wavelengths[-1]} nm")
        ...
        ...         # Apply to geometry
        ...         leaf_uuid = context.addPatch(center=[0, 0, 1], size=[0.1, 0.1])
        ...         leafoptics.run([leaf_uuid], props, "sunflower_leaf")
    """

    def __init__(self, context: Context):
        """
        Initialize LeafOptics with graceful plugin handling.

        Args:
            context: Helios Context instance

        Raises:
            TypeError: If context is not a Context instance
            LeafOpticsError: If LeafOptics plugin is not available or spectral data missing
        """
        # Validate context type - use duck typing to handle import state issues during testing
        if not (hasattr(context, '__class__') and
                (isinstance(context, Context) or
                 context.__class__.__name__ == 'Context')):
            raise TypeError(f"LeafOptics requires a Context instance, got {type(context).__name__}")

        self.context = context
        self._leafoptics_ptr = None

        # Check plugin availability using registry
        registry = get_plugin_registry()

        if not registry.is_plugin_available('leafoptics'):
            # Get helpful information about the missing plugin
            available_plugins = registry.get_available_plugins()

            error_msg = (
                "LeafOptics requires the 'leafoptics' plugin which is not available.\n\n"
                "The LeafOptics plugin implements the PROSPECT leaf optical model which computes:\n"
                "- Spectral reflectance (400-2500 nm at 1 nm resolution)\n"
                "- Spectral transmittance\n"
                "- Based on leaf biochemical properties (chlorophyll, water, dry matter, etc.)\n\n"
                "Features:\n"
                "- Cross-platform support (Windows, Linux, macOS)\n"
                "- No GPU required\n"
                "- Built-in species library with 12 plant species\n"
                "- Supports both PROSPECT-D and PROSPECT-PRO modes\n\n"
                "To enable LeafOptics modeling:\n"
                "1. Build PyHelios with LeafOptics plugin:\n"
                "   build_scripts/build_helios --plugins leafoptics\n"
                "2. Or build with radiation plugins for full spectral modeling:\n"
                "   build_scripts/build_helios --plugins leafoptics,radiation\n"
                f"\nCurrently available plugins: {available_plugins}"
            )

            raise LeafOpticsError(error_msg)

        # Plugin is available - create LeafOptics with asset-aware working directory
        try:
            with _leafoptics_working_directory():
                self._leafoptics_ptr = leafoptics_wrapper.createLeafOptics(context.getNativePtr())
                if self._leafoptics_ptr is None:
                    raise LeafOpticsError(
                        "Failed to create LeafOptics instance. "
                        "This may indicate a problem with the spectral data files."
                    )
            logger.info("LeafOptics created successfully")

        except LeafOpticsError:
            raise
        except Exception as e:
            raise LeafOpticsError(f"Failed to initialize LeafOptics: {e}")

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        """Context manager exit with proper cleanup."""
        if self._leafoptics_ptr is not None:
            try:
                leafoptics_wrapper.destroyLeafOptics(self._leafoptics_ptr)
                logger.debug("LeafOptics destroyed successfully")
            except Exception as e:
                logger.warning(f"Error destroying LeafOptics: {e}")
            finally:
                self._leafoptics_ptr = None

    def __del__(self):
        """Destructor to ensure C++ resources freed even without 'with' statement."""
        if hasattr(self, '_leafoptics_ptr') and self._leafoptics_ptr is not None:
            try:
                leafoptics_wrapper.destroyLeafOptics(self._leafoptics_ptr)
                self._leafoptics_ptr = None
            except Exception as e:
                import warnings
                warnings.warn(f"Error in LeafOptics.__del__: {e}")

    def run(self, UUIDs: List[int], leafproperties: LeafOpticsProperties, label: str) -> None:
        """
        Run the LeafOptics model to generate spectra and assign to primitives.

        This method computes reflectance and transmittance spectra based on the given
        leaf properties, creates global data entries, and assigns them to the specified
        primitives.

        Args:
            UUIDs: List of primitive UUIDs to assign spectra to
            leafproperties: LeafOpticsProperties with biochemical parameters
            label: Label for the spectra (appended to "leaf_reflectivity_" and "leaf_transmissivity_")

        Raises:
            ValueError: If parameters are invalid
            LeafOpticsError: If computation fails

        Example:
            >>> props = LeafOpticsProperties(chlorophyllcontent=40.0, watermass=0.02)
            >>> leafoptics.run([leaf_uuid], props, "my_leaf")
            >>> # Creates: "leaf_reflectivity_my_leaf" and "leaf_transmissivity_my_leaf"
        """
        if not UUIDs:
            raise ValueError("UUIDs list cannot be empty")
        if not isinstance(leafproperties, LeafOpticsProperties):
            raise ValueError("leafproperties must be a LeafOpticsProperties instance")
        if not label:
            raise ValueError("Label cannot be empty")

        try:
            leafoptics_wrapper.leafOpticsRun(
                self._leafoptics_ptr,
                UUIDs,
                leafproperties.to_list(),
                label
            )
        except Exception as e:
            raise LeafOpticsError(f"Failed to run LeafOptics model: {e}")

    def runNoUUIDs(self, leafproperties: LeafOpticsProperties, label: str) -> None:
        """
        Run the LeafOptics model without assigning to primitives.

        This method computes reflectance and transmittance spectra based on the given
        leaf properties and creates global data entries, but does not assign them to
        any primitives.

        Args:
            leafproperties: LeafOpticsProperties with biochemical parameters
            label: Label for the spectra (appended to "leaf_reflectivity_" and "leaf_transmissivity_")

        Raises:
            ValueError: If parameters are invalid
            LeafOpticsError: If computation fails
        """
        if not isinstance(leafproperties, LeafOpticsProperties):
            raise ValueError("leafproperties must be a LeafOpticsProperties instance")
        if not label:
            raise ValueError("Label cannot be empty")

        try:
            leafoptics_wrapper.leafOpticsRunNoUUIDs(
                self._leafoptics_ptr,
                leafproperties.to_list(),
                label
            )
        except Exception as e:
            raise LeafOpticsError(f"Failed to run LeafOptics model: {e}")

    def getLeafSpectra(self, leafproperties: LeafOpticsProperties) -> Tuple[List[float], List[float], List[float]]:
        """
        Compute leaf reflectance and transmittance spectra.

        This method computes spectral properties without creating global data entries
        or assigning to primitives.

        Args:
            leafproperties: LeafOpticsProperties with biochemical parameters

        Returns:
            Tuple of (wavelengths, reflectivities, transmissivities):
            - wavelengths: List of wavelengths in nm (400-2500 at 1nm resolution, 2101 points)
            - reflectivities: List of reflectance values (0-1) at each wavelength
            - transmissivities: List of transmittance values (0-1) at each wavelength

        Raises:
            ValueError: If parameters are invalid
            LeafOpticsError: If computation fails

        Example:
            >>> props = LeafOpticsProperties(chlorophyllcontent=40.0)
            >>> wavelengths, refl, trans = leafoptics.getLeafSpectra(props)
            >>> # Find reflectance at 550 nm (green peak)
            >>> idx_550 = wavelengths.index(550.0)
            >>> print(f"Reflectance at 550 nm: {refl[idx_550]:.3f}")
        """
        if not isinstance(leafproperties, LeafOpticsProperties):
            raise ValueError("leafproperties must be a LeafOpticsProperties instance")

        try:
            return leafoptics_wrapper.leafOpticsGetLeafSpectra(
                self._leafoptics_ptr,
                leafproperties.to_list()
            )
        except Exception as e:
            raise LeafOpticsError(f"Failed to get leaf spectra: {e}")

    def setProperties(self, UUIDs: List[int], leafproperties: LeafOpticsProperties) -> None:
        """
        Set leaf optical properties for primitives as Context primitive data.

        This assigns the biochemical properties as primitive data using labels:
        "chlorophyll", "carotenoid", "anthocyanin", "brown", "water", "drymass"
        (or "protein" + "cellulose" in PROSPECT-PRO mode).

        Args:
            UUIDs: List of primitive UUIDs
            leafproperties: LeafOpticsProperties with biochemical parameters

        Raises:
            ValueError: If parameters are invalid
            LeafOpticsError: If operation fails
        """
        if not UUIDs:
            raise ValueError("UUIDs list cannot be empty")
        if not isinstance(leafproperties, LeafOpticsProperties):
            raise ValueError("leafproperties must be a LeafOpticsProperties instance")

        try:
            leafoptics_wrapper.leafOpticsSetProperties(
                self._leafoptics_ptr,
                UUIDs,
                leafproperties.to_list()
            )
        except Exception as e:
            raise LeafOpticsError(f"Failed to set properties: {e}")

    def getPropertiesFromSpectrum(self, UUIDs: List[int]) -> None:
        """
        Get PROSPECT parameters from reflectivity spectrum for primitives.

        This method retrieves the "reflectivity_spectrum" primitive data for each
        primitive and checks if it matches a spectrum generated by this LeafOptics
        instance. If a match is found, the corresponding PROSPECT model parameters
        are assigned as primitive data.

        Args:
            UUIDs: List of primitive UUIDs to query

        Note:
            Primitives without matching spectra are silently skipped.
        """
        if not UUIDs:
            raise ValueError("UUIDs list cannot be empty")

        try:
            leafoptics_wrapper.leafOpticsGetPropertiesFromSpectrum(
                self._leafoptics_ptr,
                UUIDs
            )
        except Exception as e:
            raise LeafOpticsError(f"Failed to get properties from spectrum: {e}")

    def getPropertiesFromLibrary(self, species: str) -> LeafOpticsProperties:
        """
        Get leaf optical properties from the built-in species library.

        The library contains PROSPECT-D parameters fitted from the LOPEX93 dataset
        for common plant species.

        Args:
            species: Name of the species (case-insensitive). Available species:
                     "default", "garden_lettuce", "alfalfa", "corn", "sunflower",
                     "english_walnut", "rice", "soybean", "wine_grape", "tomato",
                     "common_bean", "cowpea"

        Returns:
            LeafOpticsProperties populated with the species-specific parameters

        Raises:
            ValueError: If species name is empty

        Note:
            If species is not found, default properties are used and a warning is issued.

        Example:
            >>> props = leafoptics.getPropertiesFromLibrary("sunflower")
            >>> print(f"Chlorophyll: {props.chlorophyllcontent} ug/cm^2")
        """
        if not species:
            raise ValueError("Species name cannot be empty")

        try:
            properties_list = leafoptics_wrapper.leafOpticsGetPropertiesFromLibrary(
                self._leafoptics_ptr,
                species
            )
            return LeafOpticsProperties.from_list(properties_list)
        except Exception as e:
            raise LeafOpticsError(f"Failed to get properties from library: {e}")

    def disableMessages(self) -> None:
        """Disable command-line output messages from LeafOptics."""
        try:
            leafoptics_wrapper.leafOpticsDisableMessages(self._leafoptics_ptr)
        except Exception as e:
            raise LeafOpticsError(f"Failed to disable messages: {e}")

    def enableMessages(self) -> None:
        """Enable command-line output messages from LeafOptics."""
        try:
            leafoptics_wrapper.leafOpticsEnableMessages(self._leafoptics_ptr)
        except Exception as e:
            raise LeafOpticsError(f"Failed to enable messages: {e}")

    def optionalOutputPrimitiveData(self, label: str) -> None:
        """
        Selectively output specific biochemical properties as primitive data.

        By default, LeafOptics writes all biochemical properties to primitive data.
        Use this method to specify only the properties you need for improved performance.

        Args:
            label: Biochemical property to output. Valid values:
                   - "chlorophyll": Chlorophyll content
                   - "carotenoid": Carotenoid content
                   - "anthocyanin": Anthocyanin content
                   - "brown": Brown pigment content
                   - "water": Water content
                   - "drymass": Dry mass content
                   - "protein": Protein content
                   - "cellulose": Cellulose content

        Raises:
            ValueError: If label is empty or invalid
            LeafOpticsError: If operation fails

        Note:
            Added in helios-core v1.3.59 for performance optimization when only
            specific biochemical properties are needed for analysis.

        Example:
            >>> with LeafOptics(context) as leaf:
            ...     # Only output chlorophyll and water content
            ...     leaf.optionalOutputPrimitiveData("chlorophyll")
            ...     leaf.optionalOutputPrimitiveData("water")
            ...     leaf.run(uuids, properties, "leaf_spectra")
        """
        if not label:
            raise ValueError("Label cannot be empty")

        valid_labels = ["chlorophyll", "carotenoid", "anthocyanin", "brown",
                       "water", "drymass", "protein", "cellulose"]
        if label not in valid_labels:
            raise ValueError(f"Invalid label '{label}'. Must be one of: {', '.join(valid_labels)}")

        try:
            leafoptics_wrapper.leafOpticsOptionalOutputPrimitiveData(self._leafoptics_ptr, label)
        except Exception as e:
            raise LeafOpticsError(f"Failed to set optional output for '{label}': {e}")

    @staticmethod
    def getAvailableSpecies() -> List[str]:
        """
        Get list of available species in the built-in library.

        Returns:
            List of species names that can be used with getPropertiesFromLibrary()
        """
        return AVAILABLE_SPECIES.copy()

    @staticmethod
    def isAvailable() -> bool:
        """
        Check if LeafOptics plugin is available in the current build.

        Returns:
            True if LeafOptics is available, False otherwise
        """
        return leafoptics_wrapper.is_leafoptics_available()
