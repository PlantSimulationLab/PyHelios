"""
High-level EnergyBalance interface for PyHelios.

This module provides a user-friendly interface to the energy balance modeling
capabilities with graceful plugin handling and informative error messages.
"""

import logging
from typing import List, Optional, Union
from contextlib import contextmanager

from .plugins.registry import get_plugin_registry
from .wrappers import UEnergyBalanceWrapper as energy_wrapper
from .Context import Context
from .exceptions import HeliosError
from .validation.plugin_decorators import (
    validate_energy_run_params, validate_energy_band_params, validate_air_energy_params,
    validate_evaluate_air_energy_params, validate_output_data_params, validate_print_report_params
)

logger = logging.getLogger(__name__)


class EnergyBalanceModelError(HeliosError):
    """Exception raised for EnergyBalance-specific errors."""
    pass


class EnergyBalanceModel:
    """
    High-level interface for energy balance modeling and thermal calculations.
    
    This class provides a user-friendly wrapper around the native Helios
    energy balance plugin with automatic plugin availability checking and
    graceful error handling.
    
    The energy balance model computes surface temperatures based on local energy
    balance equations, including radiation absorption, convection, and transpiration.
    It supports both steady-state and dynamic (time-stepping) calculations.
    
    System requirements:
        - NVIDIA GPU with CUDA support
        - CUDA Toolkit installed
        - Energy balance plugin compiled into PyHelios
    
    Example:
        >>> with Context() as context:
        ...     # Add some geometry
        ...     patch_uuid = context.addPatch(center=[0, 0, 1], size=[1, 1])
        ...     
        ...     with EnergyBalanceModel(context) as energy_balance:
        ...         # Add radiation band for flux calculations
        ...         energy_balance.addRadiationBand("SW")
        ...         
        ...         # Run steady-state energy balance
        ...         energy_balance.run()
        ...         
        ...         # Or run dynamic simulation with timestep
        ...         energy_balance.run(dt=60.0)  # 60 second timestep
    """
    
    def __init__(self, context: Context):
        """
        Initialize EnergyBalanceModel with graceful plugin handling.
        
        Args:
            context: Helios Context instance
            
        Raises:
            TypeError: If context is not a Context instance
            EnergyBalanceModelError: If energy balance plugin is not available
        """
        # Validate context type
        if not isinstance(context, Context):
            raise TypeError(f"EnergyBalanceModel requires a Context instance, got {type(context).__name__}")
        
        self.context = context
        self.energy_model = None
        
        # Check plugin availability using registry
        registry = get_plugin_registry()
        
        if not registry.is_plugin_available('energybalance'):
            # Get helpful information about the missing plugin
            plugin_info = registry.get_plugin_capabilities()
            available_plugins = registry.get_available_plugins()
            
            error_msg = (
                "EnergyBalanceModel requires the 'energybalance' plugin which is not available.\n\n"
                "The energy balance plugin provides GPU-accelerated thermal modeling and surface temperature calculations.\n"
                "System requirements:\n"
                "- NVIDIA GPU with CUDA support\n"
                "- CUDA Toolkit installed\n"
                "- Energy balance plugin compiled into PyHelios\n\n"
                "To enable energy balance modeling:\n"
                "1. Build PyHelios with energy balance plugin:\n"
                "   build_scripts/build_helios --plugins energybalance\n"
                "2. Or build with multiple plugins:\n"
                "   build_scripts/build_helios --plugins energybalance,visualizer,weberpenntree\n"
                f"\nCurrently available plugins: {available_plugins}"
            )
            
            # Suggest alternatives if available
            alternatives = registry.suggest_alternatives('energybalance')
            if alternatives:
                error_msg += f"\n\nAlternative plugins available: {alternatives}"
                error_msg += "\nConsider using radiation or photosynthesis for related thermal modeling."
            
            raise EnergyBalanceModelError(error_msg)
        
        # Plugin is available - create energy balance model
        try:
            self.energy_model = energy_wrapper.createEnergyBalanceModel(context.getNativePtr())
            if self.energy_model is None:
                raise EnergyBalanceModelError(
                    "Failed to create EnergyBalanceModel instance. "
                    "This may indicate a problem with the native library or CUDA initialization."
                )
            logger.info("EnergyBalanceModel created successfully")
            
        except Exception as e:
            raise EnergyBalanceModelError(f"Failed to initialize EnergyBalanceModel: {e}")
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_value, traceback):
        """Context manager exit with proper cleanup."""
        if self.energy_model is not None:
            try:
                energy_wrapper.destroyEnergyBalanceModel(self.energy_model)
                logger.debug("EnergyBalanceModel destroyed successfully")
            except Exception as e:
                logger.warning(f"Error destroying EnergyBalanceModel: {e}")
            finally:
                self.energy_model = None

    def __del__(self):
        """Destructor to ensure C++ resources freed even without 'with' statement."""
        if hasattr(self, 'energy_model') and self.energy_model is not None:
            try:
                energy_wrapper.destroyEnergyBalanceModel(self.energy_model)
                self.energy_model = None
            except Exception as e:
                import warnings
                warnings.warn(f"Error in EnergyBalanceModel.__del__: {e}")

    def getNativePtr(self):
        """Get the native pointer for advanced operations."""
        return self.energy_model
    
    def enableMessages(self) -> None:
        """
        Enable console output messages from the energy balance model.
        
        Raises:
            EnergyBalanceModelError: If operation fails
        """
        try:
            energy_wrapper.enableMessages(self.energy_model)
        except Exception as e:
            raise EnergyBalanceModelError(f"Failed to enable messages: {e}")
    
    def disableMessages(self) -> None:
        """
        Disable console output messages from the energy balance model.
        
        Raises:
            EnergyBalanceModelError: If operation fails
        """
        try:
            energy_wrapper.disableMessages(self.energy_model)
        except Exception as e:
            raise EnergyBalanceModelError(f"Failed to disable messages: {e}")
    
    @validate_energy_run_params
    def run(self, uuids: Optional[List[int]] = None, dt: Optional[float] = None) -> None:
        """
        Run the energy balance model.
        
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
            EnergyBalanceModelError: If energy balance calculation fails
            
        Example:
            >>> # Steady state for all primitives
            >>> energy_balance.run()
            
            >>> # Dynamic simulation with 60-second timestep
            >>> energy_balance.run(dt=60.0)
            
            >>> # Steady state for specific patches
            >>> energy_balance.run(uuids=[patch1_uuid, patch2_uuid])
            
            >>> # Dynamic simulation for specific patches
            >>> energy_balance.run(uuids=[patch1_uuid, patch2_uuid], dt=30.0)
        """
        try:
            if uuids is None and dt is None:
                # Steady state for all primitives
                energy_wrapper.run(self.energy_model)
            elif uuids is None and dt is not None:
                # Dynamic with timestep for all primitives
                energy_wrapper.runDynamic(self.energy_model, dt)
            elif uuids is not None and dt is None:
                # Steady state for specific primitives
                energy_wrapper.runForUUIDs(self.energy_model, uuids)
            else:
                # Dynamic with timestep for specific primitives
                energy_wrapper.runForUUIDsDynamic(self.energy_model, uuids, dt)
                
        except Exception as e:
            raise EnergyBalanceModelError(f"Energy balance calculation failed: {e}")
    
    @validate_energy_band_params
    def addRadiationBand(self, band: Union[str, List[str]]) -> None:
        """
        Add a radiation band or bands for absorbed flux calculations.
        
        The energy balance model uses radiation bands from the RadiationModel
        plugin to calculate absorbed radiation flux for each primitive.
        
        Args:
            band: Name of radiation band (e.g., "SW", "PAR", "NIR", "LW")
                  or list of band names
            
        Raises:
            ValueError: If band name is invalid
            EnergyBalanceModelError: If operation fails
            
        Example:
            >>> energy_balance.addRadiationBand("SW")  # Single band
            >>> energy_balance.addRadiationBand(["SW", "LW", "PAR"])  # Multiple bands
        """
        if isinstance(band, str):
            if not band:
                raise ValueError("Band name must be a non-empty string")
            try:
                energy_wrapper.addRadiationBand(self.energy_model, band)
            except Exception as e:
                raise EnergyBalanceModelError(f"Failed to add radiation band '{band}': {e}")
        elif isinstance(band, list):
            if not band:
                raise ValueError("Bands list cannot be empty")
            for b in band:
                if not isinstance(b, str) or not b:
                    raise ValueError("All band names must be non-empty strings")
            try:
                energy_wrapper.addRadiationBands(self.energy_model, band)
            except Exception as e:
                raise EnergyBalanceModelError(f"Failed to add radiation bands {band}: {e}")
        else:
            raise ValueError("Band must be a string or list of strings")
    
    @validate_air_energy_params
    def enableAirEnergyBalance(self, canopy_height_m: Optional[float] = None, 
                             reference_height_m: Optional[float] = None) -> None:
        """
        Enable air energy balance model for canopy-scale thermal calculations.
        
        The air energy balance computes average air temperature and water vapor
        mole fraction based on the energy balance of the air layer in the canopy.
        
        Args:
            canopy_height_m: Optional canopy height in meters. If not provided,
                           computed automatically from primitive bounding box.
            reference_height_m: Optional reference height in meters where ambient
                              conditions are measured. If not provided, assumes
                              reference height is at canopy top.
                              
        Raises:
            ValueError: If parameters are invalid
            EnergyBalanceModelError: If operation fails
            
        Example:
            >>> # Automatic canopy height detection
            >>> energy_balance.enable_air_energy_balance()
            
            >>> # Manual canopy and reference heights
            >>> energy_balance.enable_air_energy_balance(canopy_height_m=5.0, reference_height_m=10.0)
        """
        if canopy_height_m is not None and canopy_height_m <= 0:
            raise ValueError("Canopy height must be positive")
        if reference_height_m is not None and reference_height_m <= 0:
            raise ValueError("Reference height must be positive")
        
        try:
            if canopy_height_m is None and reference_height_m is None:
                energy_wrapper.enableAirEnergyBalance(self.energy_model)
            elif canopy_height_m is not None and reference_height_m is not None:
                energy_wrapper.enableAirEnergyBalanceWithParameters(
                    self.energy_model, canopy_height_m, reference_height_m)
            else:
                raise ValueError("Both canopy_height_m and reference_height_m must be provided together, or both None")
                
        except Exception as e:
            raise EnergyBalanceModelError(f"Failed to enable air energy balance: {e}")
    
    @validate_evaluate_air_energy_params
    def evaluateAirEnergyBalance(self, dt_sec: float, time_advance_sec: float,
                               UUIDs: Optional[List[int]] = None) -> None:
        """
        Advance the air energy balance over time.
        
        This method advances the air energy balance model by integrating over
        multiple timesteps to reach the target time advancement.
        
        Args:
            dt_sec: Timestep in seconds for integration
            time_advance_sec: Total time to advance in seconds (must be >= dt_sec)
            UUIDs: Optional list of primitive UUIDs. If None, processes all primitives.
            
        Raises:
            ValueError: If parameters are invalid
            EnergyBalanceModelError: If operation fails
            
        Example:
            >>> # Advance air energy balance by 1 hour using 60-second timesteps
            >>> energy_balance.evaluate_air_energy_balance(dt_sec=60.0, time_advance_sec=3600.0)
            
            >>> # Advance for specific primitives
            >>> energy_balance.evaluate_air_energy_balance(
            ...     dt_sec=30.0, time_advance_sec=1800.0, uuids=[patch1_uuid, patch2_uuid])
        """
        if dt_sec <= 0:
            raise ValueError("Time step must be positive")
        if time_advance_sec < dt_sec:
            raise ValueError("Total time advance must be greater than or equal to time step")
        
        try:
            if UUIDs is None:
                energy_wrapper.evaluateAirEnergyBalance(self.energy_model, dt_sec, time_advance_sec)
            else:
                energy_wrapper.evaluateAirEnergyBalanceForUUIDs(
                    self.energy_model, UUIDs, dt_sec, time_advance_sec)
                    
        except Exception as e:
            raise EnergyBalanceModelError(f"Failed to evaluate air energy balance: {e}")
    
    @validate_output_data_params
    def optionalOutputPrimitiveData(self, label: str) -> None:
        """
        Add optional output primitive data to the Context.
        
        This method adds additional data fields to primitives that will be
        calculated and stored during energy balance execution.
        
        Args:
            label: Name of the data field to add (e.g., "vapor_pressure_deficit",
                  "boundary_layer_conductance", "net_radiation")
                  
        Raises:
            ValueError: If label is invalid
            EnergyBalanceModelError: If operation fails
            
        Example:
            >>> energy_balance.add_optional_output_data("vapor_pressure_deficit")
            >>> energy_balance.add_optional_output_data("net_radiation")
        """
        if not label or not isinstance(label, str):
            raise ValueError("Label must be a non-empty string")
        
        try:
            energy_wrapper.optionalOutputPrimitiveData(self.energy_model, label)
        except Exception as e:
            raise EnergyBalanceModelError(f"Failed to add optional output data '{label}': {e}")
    
    @validate_print_report_params
    def printDefaultValueReport(self, UUIDs: Optional[List[int]] = None) -> None:
        """
        Print a report detailing usage of default input values.
        
        This diagnostic method prints information about which primitives are
        using default values for energy balance parameters, helping identify
        where additional parameter specification might be needed.
        
        Args:
            UUIDs: Optional list of primitive UUIDs to report on. If None,
                   reports on all primitives.
                  
        Raises:
            EnergyBalanceModelError: If operation fails
            
        Example:
            >>> # Report on all primitives
            >>> energy_balance.print_default_value_report()
            
            >>> # Report on specific primitives
            >>> energy_balance.print_default_value_report(uuids=[patch1_uuid, patch2_uuid])
        """
        try:
            if UUIDs is None:
                energy_wrapper.printDefaultValueReport(self.energy_model)
            else:
                energy_wrapper.printDefaultValueReportForUUIDs(self.energy_model, UUIDs)
                
        except Exception as e:
            raise EnergyBalanceModelError(f"Failed to print default value report: {e}")
    
    def is_available(self) -> bool:
        """
        Check if EnergyBalanceModel is available in current build.

        Returns:
            True if plugin is available, False otherwise
        """
        registry = get_plugin_registry()
        return registry.is_plugin_available('energybalance')

    def enableGPUAcceleration(self) -> None:
        """
        Enable GPU acceleration for energy balance calculations.

        Attempts to enable GPU acceleration using CUDA. If GPU is not available at runtime,
        this will raise an error. The energy balance model will use three-tier execution:
        GPU (CUDA), OpenMP (parallel CPU), or serial CPU fallback.

        Raises:
            NotImplementedError: If library not compiled with CUDA support
            EnergyBalanceModelError: If GPU acceleration cannot be enabled

        Example:
            >>> with EnergyBalanceModel(context) as energy_balance:
            ...     try:
            ...         energy_balance.enableGPUAcceleration()
            ...         print("GPU acceleration enabled")
            ...     except NotImplementedError:
            ...         print("GPU not available - using CPU mode")

        Note:
            Only available when PyHelios is compiled with CUDA support.
            OpenMP CPU mode is recommended for most workloads without GPU.
        """
        try:
            energy_wrapper.enableGPUAcceleration(self.energy_model)
        except NotImplementedError:
            raise
        except Exception as e:
            raise EnergyBalanceModelError(f"Failed to enable GPU acceleration: {e}")

    def disableGPUAcceleration(self) -> None:
        """
        Disable GPU acceleration and force CPU mode.

        Forces the use of OpenMP CPU implementation even if GPU is available.
        Useful for testing, benchmarking, or when CPU performance is preferred.

        Raises:
            EnergyBalanceModelError: If operation fails

        Example:
            >>> energy_balance.disableGPUAcceleration()

        Note:
            Only available when PyHelios is compiled with CUDA support.
            Has no effect if GPU support is not compiled in.
        """
        try:
            energy_wrapper.disableGPUAcceleration(self.energy_model)
        except Exception as e:
            raise EnergyBalanceModelError(f"Failed to disable GPU acceleration: {e}")

    def isGPUAccelerationEnabled(self) -> bool:
        """
        Check if GPU acceleration is currently enabled.

        Returns:
            True if GPU acceleration is enabled and available, False otherwise

        Example:
            >>> if energy_balance.isGPUAccelerationEnabled():
            ...     print("Using GPU acceleration")
            ... else:
            ...     print("Using CPU mode")

        Note:
            Returns False if library not compiled with CUDA support.
        """
        try:
            return energy_wrapper.isGPUAccelerationEnabled(self.energy_model)
        except NotImplementedError:
            return False
        except Exception as e:
            raise EnergyBalanceModelError(f"Failed to check GPU acceleration status: {e}")

    @staticmethod
    def isGPUAccelerationAvailable() -> bool:
        """
        Check if GPU acceleration functions are available in this build.

        Returns:
            True if GPU acceleration support is compiled in, False otherwise

        Example:
            >>> if EnergyBalanceModel.isGPUAccelerationAvailable():
            ...     print("GPU acceleration supported")
            ... else:
            ...     print("GPU acceleration not compiled in - CPU mode only")
        """
        return energy_wrapper.isGPUAccelerationAvailable()


# Convenience function
def create_energy_balance_model(context: Context) -> EnergyBalanceModel:
    """
    Create EnergyBalanceModel instance with context.
    
    Args:
        context: Helios Context
        
    Returns:
        EnergyBalanceModel instance
    """
    return EnergyBalanceModel(context)