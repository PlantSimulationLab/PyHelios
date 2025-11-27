"""
High-level StomatalConductance interface for PyHelios.

This module provides a user-friendly interface to the stomatal conductance modeling
capabilities with graceful plugin handling and informative error messages.
"""

import logging
from typing import List, Optional, Union, NamedTuple
from contextlib import contextmanager

from .plugins.registry import get_plugin_registry
from .wrappers import UStomatalConductanceWrapper as stomatal_wrapper
from .Context import Context
from .exceptions import HeliosError

logger = logging.getLogger(__name__)


class StomatalConductanceModelError(HeliosError):
    """Exception raised for StomatalConductance-specific errors."""
    pass


# Model Coefficient Classes for type safety and clarity
class BWBCoefficients(NamedTuple):
    """Ball-Woodrow-Berry model coefficients."""
    gs0: float  # mol/m²/s - minimum stomatal conductance
    a1: float   # dimensionless - sensitivity parameter


class BBLCoefficients(NamedTuple):
    """Ball-Berry-Leuning model coefficients."""
    gs0: float  # mol/m²/s - minimum stomatal conductance
    a1: float   # dimensionless - sensitivity parameter  
    D0: float   # mmol/mol - VPD parameter


class MOPTCoefficients(NamedTuple):
    """Medlyn et al. optimality model coefficients."""
    gs0: float  # mol/m²/s - minimum stomatal conductance
    g1: float   # (kPa)^0.5 - marginal water use efficiency


class BMFCoefficients(NamedTuple):
    """Buckley-Mott-Farquhar model coefficients."""
    Em: float   # mmol/m²/s - maximum transpiration rate
    i0: float   # μmol/m²/s - minimum radiation
    k: float    # μmol/m²/s·mmol/mol - light response parameter
    b: float    # mmol/mol - humidity response parameter


class BBCoefficients(NamedTuple):
    """Bailey model coefficients."""
    pi_0: float     # MPa - turgor pressure at full closure
    pi_m: float     # MPa - turgor pressure at full opening
    theta: float    # μmol/m²/s - light saturation parameter
    sigma: float    # dimensionless - shape parameter
    chi: float      # mol/m²/s/MPa - hydraulic conductance parameter


class StomatalConductanceModel:
    """
    High-level interface for stomatal conductance modeling and gas exchange calculations.
    
    This class provides a user-friendly wrapper around the native Helios
    stomatal conductance plugin with automatic plugin availability checking and
    graceful error handling.
    
    The stomatal conductance model implements five different stomatal response models:
    - BWB: Ball, Woodrow, Berry (1987) - original model
    - BBL: Ball, Berry, Leuning (1990, 1995) - includes VPD response  
    - MOPT: Medlyn et al. (2011) - optimality-based model
    - BMF: Buckley, Mott, Farquhar - simplified mechanistic model
    - BB: Bailey - hydraulic-based model
    
    The plugin includes a species library with pre-calibrated coefficients for
    common plant species (Almond, Apple, Avocado, Grape, Lemon, Olive, Walnut, etc.).
    
    Both steady-state and dynamic (time-stepping) calculations are supported,
    with configurable time constants for stomatal opening and closing dynamics.
    
    System requirements:
        - Cross-platform support (Windows, Linux, macOS)
        - No GPU required
        - No special dependencies
        - Stomatal conductance plugin compiled into PyHelios
    
    Example:
        >>> with Context() as context:
        ...     # Add leaf geometry
        ...     leaf_uuid = context.addPatch(center=[0, 0, 1], size=[0.1, 0.1])
        ...     
        ...     with StomatalConductanceModel(context) as stomatal:
        ...         # Set model coefficients using species library
        ...         stomatal.setBMFCoefficientsFromLibrary("Almond")
        ...         
        ...         # Run steady-state calculation
        ...         stomatal.run()
        ...         
        ...         # Or run dynamic simulation with timestep
        ...         stomatal.run(dt=60.0)  # 60 second timestep
        ...
        ...         # Set custom BMF coefficients for specific leaves
        ...         bmf_coeffs = BMFCoefficients(Em=258.25, i0=38.65, k=232916.82, b=609.67)
        ...         stomatal.setBMFCoefficients(bmf_coeffs, uuids=[leaf_uuid])
    """
    
    def __init__(self, context: Context):
        """
        Initialize StomatalConductanceModel with graceful plugin handling.
        
        Args:
            context: Helios Context instance
            
        Raises:
            TypeError: If context is not a Context instance
            StomatalConductanceModelError: If stomatal conductance plugin is not available
        """
        # Validate context type - use duck typing to handle import state issues during testing
        if not (hasattr(context, '__class__') and 
                (isinstance(context, Context) or 
                 context.__class__.__name__ == 'Context')):
            raise TypeError(f"StomatalConductanceModel requires a Context instance, got {type(context).__name__}")
        
        self.context = context
        self.stomatal_model = None
        
        # Check plugin availability using registry
        registry = get_plugin_registry()
        
        if not registry.is_plugin_available('stomatalconductance'):
            # Get helpful information about the missing plugin
            plugin_info = registry.get_plugin_capabilities()
            available_plugins = registry.get_available_plugins()
            
            error_msg = (
                "StomatalConductanceModel requires the 'stomatalconductance' plugin which is not available.\n\n"
                "The stomatal conductance plugin provides gas exchange calculations using five validated models:\n"
                "- Ball-Woodrow-Berry (BWB) - classic stomatal response\n"
                "- Ball-Berry-Leuning (BBL) - includes vapor pressure deficit\n" 
                "- Medlyn et al. optimality (MOPT) - optimal stomatal behavior\n"
                "- Buckley-Mott-Farquhar (BMF) - mechanistic approach\n"
                "- Bailey (BB) - hydraulic-based model\n\n"
                "Features:\n"
                "- Species library with pre-calibrated coefficients\n"
                "- Dynamic time-stepping with configurable time constants\n"
                "- No GPU or special dependencies required\n\n"
                "To enable stomatal conductance modeling:\n"
                "1. Build PyHelios with stomatal conductance plugin:\n"
                "   build_scripts/build_helios --plugins stomatalconductance\n"
                "2. Or build with multiple plugins:\n"
                "   build_scripts/build_helios --plugins stomatalconductance,energybalance,photosynthesis\n"
                f"\nCurrently available plugins: {available_plugins}"
            )
            
            # Suggest alternatives if available
            alternatives = registry.suggest_alternatives('stomatalconductance')
            if alternatives:
                error_msg += f"\n\nAlternative plugins available: {alternatives}"
                error_msg += "\nConsider using photosynthesis or energybalance for related plant physiology modeling."
            
            raise StomatalConductanceModelError(error_msg)
        
        # Plugin is available - create stomatal conductance model
        try:
            self.stomatal_model = stomatal_wrapper.createStomatalConductanceModel(context.getNativePtr())
            if self.stomatal_model is None:
                raise StomatalConductanceModelError(
                    "Failed to create StomatalConductanceModel instance. "
                    "This may indicate a problem with the native library."
                )
            logger.info("StomatalConductanceModel created successfully")
            
        except Exception as e:
            raise StomatalConductanceModelError(f"Failed to initialize StomatalConductanceModel: {e}")
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_value, traceback):
        """Context manager exit with proper cleanup."""
        if self.stomatal_model is not None:
            try:
                stomatal_wrapper.destroyStomatalConductanceModel(self.stomatal_model)
                logger.debug("StomatalConductanceModel destroyed successfully")
            except Exception as e:
                logger.warning(f"Error destroying StomatalConductanceModel: {e}")
            finally:
                self.stomatal_model = None

    def __del__(self):
        """Destructor to ensure C++ resources freed even without 'with' statement."""
        if hasattr(self, 'stomatal_model') and self.stomatal_model is not None:
            try:
                stomatal_wrapper.destroyStomatalConductanceModel(self.stomatal_model)
                self.stomatal_model = None
            except Exception as e:
                import warnings
                warnings.warn(f"Error in StomatalConductanceModel.__del__: {e}")

    def getNativePtr(self):
        """Get the native pointer for advanced operations."""
        return self.stomatal_model
    
    def enableMessages(self) -> None:
        """
        Enable console output messages from the stomatal conductance model.
        
        Raises:
            StomatalConductanceModelError: If operation fails
        """
        try:
            stomatal_wrapper.enableMessages(self.stomatal_model)
        except Exception as e:
            raise StomatalConductanceModelError(f"Failed to enable messages: {e}")
    
    def disableMessages(self) -> None:
        """
        Disable console output messages from the stomatal conductance model.
        
        Raises:
            StomatalConductanceModelError: If operation fails
        """
        try:
            stomatal_wrapper.disableMessages(self.stomatal_model)
        except Exception as e:
            raise StomatalConductanceModelError(f"Failed to disable messages: {e}")
    
    def run(self, uuids: Optional[List[int]] = None, dt: Optional[float] = None) -> None:
        """
        Run the stomatal conductance model.
        
        This method supports multiple execution modes:
        - Steady state for all primitives: run()
        - Dynamic with timestep for all primitives: run(dt=60.0)
        - Steady state for specific primitives: run(uuids=[1, 2, 3])
        - Dynamic with timestep for specific primitives: run(uuids=[1, 2, 3], dt=60.0)
        
        Args:
            uuids: Optional list of primitive UUIDs to process. If None, processes all primitives.
            dt: Optional timestep in seconds for dynamic simulation. If None, runs steady-state.
            
        Raises:
            ValueError: If parameters are invalid
            StomatalConductanceModelError: If calculation fails
            
        Example:
            >>> # Steady state for all primitives
            >>> stomatal.run()
            
            >>> # Dynamic simulation with 60-second timestep
            >>> stomatal.run(dt=60.0)
            
            >>> # Steady state for specific leaves
            >>> stomatal.run(uuids=[leaf1_uuid, leaf2_uuid])
            
            >>> # Dynamic simulation for specific leaves
            >>> stomatal.run(uuids=[leaf1_uuid, leaf2_uuid], dt=30.0)
        """
        try:
            if dt is not None and uuids is not None:
                # Dynamic simulation for specific UUIDs
                stomatal_wrapper.runForUUIDsDynamic(self.stomatal_model, uuids, dt)
            elif dt is not None:
                # Dynamic simulation for all primitives
                stomatal_wrapper.runDynamic(self.stomatal_model, dt)
            elif uuids is not None:
                # Steady state for specific UUIDs
                stomatal_wrapper.runForUUIDs(self.stomatal_model, uuids)
            else:
                # Steady state for all primitives
                stomatal_wrapper.run(self.stomatal_model)
                
        except Exception as e:
            raise StomatalConductanceModelError(f"Failed to run stomatal conductance model: {e}")

    # BWB Model Methods
    def setBWBCoefficients(self, coeffs: BWBCoefficients, uuids: Optional[List[int]] = None) -> None:
        """
        Set Ball-Woodrow-Berry model coefficients.
        
        Args:
            coeffs: BWB model coefficients (gs0, a1)
            uuids: Optional list of primitive UUIDs. If None, applies to all primitives.
            
        Raises:
            ValueError: If coefficients are invalid
            StomatalConductanceModelError: If operation fails
            
        Example:
            >>> bwb_coeffs = BWBCoefficients(gs0=0.0733, a1=9.422)
            >>> stomatal.setBWBCoefficients(bwb_coeffs)
        """
        if not isinstance(coeffs, BWBCoefficients):
            raise ValueError("coeffs must be a BWBCoefficients instance")
        if coeffs.gs0 < 0.0:
            raise ValueError("gs0 must be non-negative")
        if coeffs.a1 < 0.0:
            raise ValueError("a1 must be non-negative")
        
        try:
            if uuids is not None:
                stomatal_wrapper.setBWBCoefficientsForUUIDs(self.stomatal_model, coeffs.gs0, coeffs.a1, uuids)
            else:
                stomatal_wrapper.setBWBCoefficients(self.stomatal_model, coeffs.gs0, coeffs.a1)
        except Exception as e:
            raise StomatalConductanceModelError(f"Failed to set BWB coefficients: {e}")

    # BBL Model Methods
    def setBBLCoefficients(self, coeffs: BBLCoefficients, uuids: Optional[List[int]] = None) -> None:
        """
        Set Ball-Berry-Leuning model coefficients.
        
        Args:
            coeffs: BBL model coefficients (gs0, a1, D0)
            uuids: Optional list of primitive UUIDs. If None, applies to all primitives.
            
        Raises:
            ValueError: If coefficients are invalid
            StomatalConductanceModelError: If operation fails
            
        Example:
            >>> bbl_coeffs = BBLCoefficients(gs0=0.0743, a1=4.265, D0=14570.0)
            >>> stomatal.setBBLCoefficients(bbl_coeffs)
        """
        if not isinstance(coeffs, BBLCoefficients):
            raise ValueError("coeffs must be a BBLCoefficients instance")
        if coeffs.gs0 < 0.0:
            raise ValueError("gs0 must be non-negative")
        if coeffs.a1 < 0.0:
            raise ValueError("a1 must be non-negative")
        if coeffs.D0 <= 0.0:
            raise ValueError("D0 must be positive")
        
        try:
            if uuids is not None:
                stomatal_wrapper.setBBLCoefficientsForUUIDs(self.stomatal_model, coeffs.gs0, coeffs.a1, coeffs.D0, uuids)
            else:
                stomatal_wrapper.setBBLCoefficients(self.stomatal_model, coeffs.gs0, coeffs.a1, coeffs.D0)
        except Exception as e:
            raise StomatalConductanceModelError(f"Failed to set BBL coefficients: {e}")

    # MOPT Model Methods
    def setMOPTCoefficients(self, coeffs: MOPTCoefficients, uuids: Optional[List[int]] = None) -> None:
        """
        Set Medlyn et al. optimality model coefficients.
        
        Args:
            coeffs: MOPT model coefficients (gs0, g1)
            uuids: Optional list of primitive UUIDs. If None, applies to all primitives.
            
        Raises:
            ValueError: If coefficients are invalid
            StomatalConductanceModelError: If operation fails
            
        Example:
            >>> mopt_coeffs = MOPTCoefficients(gs0=0.0825, g1=2.637)
            >>> stomatal.setMOPTCoefficients(mopt_coeffs)
        """
        if not isinstance(coeffs, MOPTCoefficients):
            raise ValueError("coeffs must be a MOPTCoefficients instance")
        if coeffs.gs0 < 0.0:
            raise ValueError("gs0 must be non-negative")
        if coeffs.g1 <= 0.0:
            raise ValueError("g1 must be positive")
        
        try:
            if uuids is not None:
                stomatal_wrapper.setMOPTCoefficientsForUUIDs(self.stomatal_model, coeffs.gs0, coeffs.g1, uuids)
            else:
                stomatal_wrapper.setMOPTCoefficients(self.stomatal_model, coeffs.gs0, coeffs.g1)
        except Exception as e:
            raise StomatalConductanceModelError(f"Failed to set MOPT coefficients: {e}")

    # BMF Model Methods
    def setBMFCoefficients(self, coeffs: BMFCoefficients, uuids: Optional[List[int]] = None) -> None:
        """
        Set Buckley-Mott-Farquhar model coefficients.
        
        Args:
            coeffs: BMF model coefficients (Em, i0, k, b)
            uuids: Optional list of primitive UUIDs. If None, applies to all primitives.
            
        Raises:
            ValueError: If coefficients are invalid
            StomatalConductanceModelError: If operation fails
            
        Example:
            >>> bmf_coeffs = BMFCoefficients(Em=258.25, i0=38.65, k=232916.82, b=609.67)
            >>> stomatal.setBMFCoefficients(bmf_coeffs)
        """
        if not isinstance(coeffs, BMFCoefficients):
            raise ValueError("coeffs must be a BMFCoefficients instance")
        if coeffs.Em <= 0.0:
            raise ValueError("Em must be positive")
        if coeffs.i0 < 0.0:
            raise ValueError("i0 must be non-negative")
        if coeffs.k <= 0.0:
            raise ValueError("k must be positive")
        if coeffs.b <= 0.0:
            raise ValueError("b must be positive")
        
        try:
            if uuids is not None:
                stomatal_wrapper.setBMFCoefficientsForUUIDs(self.stomatal_model, coeffs.Em, coeffs.i0, coeffs.k, coeffs.b, uuids)
            else:
                stomatal_wrapper.setBMFCoefficients(self.stomatal_model, coeffs.Em, coeffs.i0, coeffs.k, coeffs.b)
        except Exception as e:
            raise StomatalConductanceModelError(f"Failed to set BMF coefficients: {e}")

    # BB Model Methods
    def setBBCoefficients(self, coeffs: BBCoefficients, uuids: Optional[List[int]] = None) -> None:
        """
        Set Bailey model coefficients.
        
        Args:
            coeffs: BB model coefficients (pi_0, pi_m, theta, sigma, chi)
            uuids: Optional list of primitive UUIDs. If None, applies to all primitives.
            
        Raises:
            ValueError: If coefficients are invalid
            StomatalConductanceModelError: If operation fails
            
        Example:
            >>> bb_coeffs = BBCoefficients(pi_0=1.0, pi_m=1.67, theta=211.22, sigma=0.4408, chi=2.076)
            >>> stomatal.setBBCoefficients(bb_coeffs)
        """
        if not isinstance(coeffs, BBCoefficients):
            raise ValueError("coeffs must be a BBCoefficients instance")
        if coeffs.pi_0 <= 0.0:
            raise ValueError("pi_0 must be positive")
        if coeffs.pi_m <= 0.0:
            raise ValueError("pi_m must be positive")
        if coeffs.theta <= 0.0:
            raise ValueError("theta must be positive")
        if coeffs.sigma <= 0.0:
            raise ValueError("sigma must be positive")
        if coeffs.chi <= 0.0:
            raise ValueError("chi must be positive")
        
        try:
            if uuids is not None:
                stomatal_wrapper.setBBCoefficientsForUUIDs(self.stomatal_model, coeffs.pi_0, coeffs.pi_m, coeffs.theta, coeffs.sigma, coeffs.chi, uuids)
            else:
                stomatal_wrapper.setBBCoefficients(self.stomatal_model, coeffs.pi_0, coeffs.pi_m, coeffs.theta, coeffs.sigma, coeffs.chi)
        except Exception as e:
            raise StomatalConductanceModelError(f"Failed to set BB coefficients: {e}")

    # Species Library Methods
    def setBMFCoefficientsFromLibrary(self, species: str, uuids: Optional[List[int]] = None) -> None:
        """
        Set BMF model coefficients using the built-in species library.
        
        Args:
            species: Species name from the library (e.g., "Almond", "Apple", "Grape", "Walnut")
            uuids: Optional list of primitive UUIDs. If None, applies to all primitives.
            
        Raises:
            ValueError: If species name is invalid
            StomatalConductanceModelError: If operation fails
            
        Example:
            >>> # Set coefficients for almond tree
            >>> stomatal.setBMFCoefficientsFromLibrary("Almond")
            
            >>> # Set coefficients for specific leaves only
            >>> stomatal.setBMFCoefficientsFromLibrary("Grape", uuids=[leaf1_uuid, leaf2_uuid])
        """
        if not species:
            raise ValueError("Species name cannot be empty")
        
        # Common species available in the library
        available_species = [
            "Almond", "Apple", "Avocado", "Cherry", "Grape", "Lemon", 
            "Olive", "Orange", "Peach", "Pear", "Plum", "Walnut"
        ]
        
        try:
            if uuids is not None:
                stomatal_wrapper.setBMFCoefficientsFromLibraryForUUIDs(self.stomatal_model, species, uuids)
            else:
                stomatal_wrapper.setBMFCoefficientsFromLibrary(self.stomatal_model, species)
        except Exception as e:
            error_msg = f"Failed to set BMF coefficients from library for species '{species}': {e}"
            if "species not found" in str(e).lower() or "invalid species" in str(e).lower():
                error_msg += f"\nAvailable species: {', '.join(available_species)}"
            raise StomatalConductanceModelError(error_msg)

    # Dynamic Time Constants
    def setDynamicTimeConstants(self, tau_open: float, tau_close: float, uuids: Optional[List[int]] = None) -> None:
        """
        Set time constants for dynamic stomatal opening and closing.
        
        Args:
            tau_open: Time constant (seconds) for stomatal opening
            tau_close: Time constant (seconds) for stomatal closing
            uuids: Optional list of primitive UUIDs. If None, applies to all primitives.
            
        Raises:
            ValueError: If time constants are invalid
            StomatalConductanceModelError: If operation fails
            
        Example:
            >>> # Set time constants for all leaves
            >>> stomatal.setDynamicTimeConstants(tau_open=120.0, tau_close=240.0)
            
            >>> # Set different time constants for specific leaves
            >>> stomatal.setDynamicTimeConstants(tau_open=60.0, tau_close=180.0, uuids=[leaf1_uuid])
        """
        if tau_open <= 0.0:
            raise ValueError("Opening time constant must be positive")
        if tau_close <= 0.0:
            raise ValueError("Closing time constant must be positive")
        
        try:
            if uuids is not None:
                stomatal_wrapper.setDynamicTimeConstantsForUUIDs(self.stomatal_model, tau_open, tau_close, uuids)
            else:
                stomatal_wrapper.setDynamicTimeConstants(self.stomatal_model, tau_open, tau_close)
        except Exception as e:
            raise StomatalConductanceModelError(f"Failed to set dynamic time constants: {e}")

    # Utility Methods
    def optionalOutputPrimitiveData(self, label: str) -> None:
        """
        Add optional output primitive data to the Context.
        
        Args:
            label: Name of primitive data to output (e.g., "Ci", "gs", "E")
            
        Raises:
            ValueError: If label is invalid
            StomatalConductanceModelError: If operation fails
            
        Example:
            >>> # Output stomatal conductance values
            >>> stomatal.optionalOutputPrimitiveData("gs")
            
            >>> # Output intercellular CO2 concentration
            >>> stomatal.optionalOutputPrimitiveData("Ci")
        """
        if not label:
            raise ValueError("Label cannot be empty")
        
        try:
            stomatal_wrapper.optionalOutputPrimitiveData(self.stomatal_model, label)
        except Exception as e:
            raise StomatalConductanceModelError(f"Failed to add optional output data '{label}': {e}")

    def printDefaultValueReport(self, uuids: Optional[List[int]] = None) -> None:
        """
        Print a report detailing usage of default input values.
        
        Args:
            uuids: Optional list of primitive UUIDs. If None, reports on all primitives.
            
        Raises:
            StomatalConductanceModelError: If operation fails
            
        Example:
            >>> # Print report for all primitives
            >>> stomatal.printDefaultValueReport()
            
            >>> # Print report for specific leaves
            >>> stomatal.printDefaultValueReport(uuids=[leaf1_uuid, leaf2_uuid])
        """
        try:
            if uuids is not None:
                stomatal_wrapper.printDefaultValueReportForUUIDs(self.stomatal_model, uuids)
            else:
                stomatal_wrapper.printDefaultValueReport(self.stomatal_model)
        except Exception as e:
            raise StomatalConductanceModelError(f"Failed to print default value report: {e}")

    def is_available(self) -> bool:
        """
        Check if StomatalConductanceModel is available in current build.
        
        Returns:
            True if plugin is available, False otherwise
        """
        registry = get_plugin_registry()
        return registry.is_plugin_available('stomatalconductance')


# Convenience function
def create_stomatal_conductance_model(context: Context) -> StomatalConductanceModel:
    """
    Create StomatalConductanceModel instance with context.
    
    Args:
        context: Helios Context
        
    Returns:
        StomatalConductanceModel instance
    """
    return StomatalConductanceModel(context)