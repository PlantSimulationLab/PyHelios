"""
High-level BoundaryLayerConductanceModel interface for PyHelios.

This module provides a user-friendly interface to the boundary layer conductance modeling
capabilities with graceful plugin handling and informative error messages.
"""

import logging
from typing import List, Optional

from .plugins.registry import get_plugin_registry
from .wrappers import UBoundaryLayerConductanceWrapper as bl_wrapper
from .Context import Context
from .exceptions import HeliosError

logger = logging.getLogger(__name__)


class BoundaryLayerConductanceModelError(HeliosError):
    """Exception raised for BoundaryLayerConductanceModel-specific errors."""
    pass


class BoundaryLayerConductanceModel:
    """
    High-level interface for boundary layer conductance modeling and heat/mass transfer calculations.

    This class provides a user-friendly wrapper around the native Helios
    boundary layer conductance plugin with automatic plugin availability checking and
    graceful error handling.

    The boundary layer conductance model implements four different boundary-layer models:
    - Pohlhausen: Laminar flat plate, forced convection (default)
    - InclinedPlate: Mixed free-forced convection for inclined plates
    - Sphere: Laminar flow around a sphere
    - Ground: Flow over bare ground surface

    System requirements:
        - Cross-platform support (Windows, Linux, macOS)
        - No GPU required
        - No special dependencies
        - Boundary layer conductance plugin compiled into PyHelios

    Example:
        >>> from pyhelios import Context, BoundaryLayerConductanceModel
        >>>
        >>> with Context() as context:
        ...     # Add leaf geometry
        ...     leaf_uuid = context.addPatch(center=[0, 0, 1], size=[0.1, 0.1])
        ...
        ...     with BoundaryLayerConductanceModel(context) as bl_model:
        ...         # Set model for all primitives (default is Pohlhausen)
        ...         bl_model.setBoundaryLayerModel("InclinedPlate")
        ...
        ...         # Run calculation
        ...         bl_model.run()
        ...
        ...         # Or set different models for different primitives
        ...         bl_model.setBoundaryLayerModel("Sphere", uuids=[leaf_uuid])
        ...         bl_model.run(uuids=[leaf_uuid])
    """

    def __init__(self, context: Context):
        """
        Initialize BoundaryLayerConductanceModel with graceful plugin handling.

        Args:
            context: Helios Context instance

        Raises:
            TypeError: If context is not a Context instance
            BoundaryLayerConductanceModelError: If boundary layer conductance plugin is not available
        """
        # Validate context type - use duck typing to handle import state issues during testing
        if not (hasattr(context, '__class__') and
                (isinstance(context, Context) or
                 context.__class__.__name__ == 'Context')):
            raise TypeError(f"BoundaryLayerConductanceModel requires a Context instance, got {type(context).__name__}")

        self.context = context
        self.bl_model = None

        # Check plugin availability using registry
        registry = get_plugin_registry()

        if not registry.is_plugin_available('boundarylayerconductance'):
            # Get helpful information about the missing plugin
            available_plugins = registry.get_available_plugins()

            error_msg = (
                "BoundaryLayerConductanceModel requires the 'boundarylayerconductance' plugin which is not available.\n\n"
                "The boundary layer conductance plugin provides heat and mass transfer calculations using four validated models:\n"
                "- Pohlhausen: Laminar flat plate, forced convection\n"
                "- InclinedPlate: Mixed free-forced convection for inclined surfaces\n"
                "- Sphere: Laminar flow around spherical objects\n"
                "- Ground: Convective transfer over bare ground\n\n"
                "Features:\n"
                "- Cross-platform support (Windows, Linux, macOS)\n"
                "- No GPU or special dependencies required\n"
                "- Applicable to plant leaves, fruits, and soil surfaces\n\n"
                "To enable boundary layer conductance modeling:\n"
                "1. Build PyHelios with boundary layer conductance plugin:\n"
                "   build_scripts/build_helios --plugins boundarylayerconductance\n"
                "2. Or build with multiple physics plugins:\n"
                "   build_scripts/build_helios --plugins boundarylayerconductance,energybalance,stomatalconductance\n"
                f"\nCurrently available plugins: {available_plugins}"
            )

            # Suggest alternatives if available
            alternatives = registry.suggest_alternatives('boundarylayerconductance')
            if alternatives:
                error_msg += f"\n\nAlternative plugins available: {alternatives}"
                error_msg += "\nConsider using energybalance or stomatalconductance for related plant physiology modeling."

            raise BoundaryLayerConductanceModelError(error_msg)

        # Plugin is available - create boundary layer conductance model
        try:
            self.bl_model = bl_wrapper.createBoundaryLayerConductanceModel(context.getNativePtr())
            if self.bl_model is None:
                raise BoundaryLayerConductanceModelError(
                    "Failed to create BoundaryLayerConductanceModel instance. "
                    "This may indicate a problem with the native library."
                )
            logger.info("BoundaryLayerConductanceModel created successfully")

        except Exception as e:
            raise BoundaryLayerConductanceModelError(f"Failed to initialize BoundaryLayerConductanceModel: {e}")

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        """Context manager exit with proper cleanup."""
        if self.bl_model is not None:
            try:
                bl_wrapper.destroyBoundaryLayerConductanceModel(self.bl_model)
                logger.debug("BoundaryLayerConductanceModel destroyed successfully")
            except Exception as e:
                logger.warning(f"Error destroying BoundaryLayerConductanceModel: {e}")
            finally:
                self.bl_model = None

    def __del__(self):
        """Destructor to ensure C++ resources freed even without 'with' statement."""
        if hasattr(self, 'bl_model') and self.bl_model is not None:
            try:
                bl_wrapper.destroyBoundaryLayerConductanceModel(self.bl_model)
                self.bl_model = None
            except Exception as e:
                import warnings
                warnings.warn(f"Error in BoundaryLayerConductanceModel.__del__: {e}")

    def getNativePtr(self):
        """Get the native pointer for advanced operations."""
        return self.bl_model

    def enableMessages(self) -> None:
        """
        Enable console output messages from the boundary layer conductance model.

        Raises:
            BoundaryLayerConductanceModelError: If operation fails
        """
        try:
            bl_wrapper.enableMessages(self.bl_model)
        except Exception as e:
            raise BoundaryLayerConductanceModelError(f"Failed to enable messages: {e}")

    def disableMessages(self) -> None:
        """
        Disable console output messages from the boundary layer conductance model.

        Raises:
            BoundaryLayerConductanceModelError: If operation fails
        """
        try:
            bl_wrapper.disableMessages(self.bl_model)
        except Exception as e:
            raise BoundaryLayerConductanceModelError(f"Failed to disable messages: {e}")

    def setBoundaryLayerModel(self, model_name: str, uuids: Optional[List[int]] = None) -> None:
        """
        Set the boundary layer conductance model to be used.

        Four models are available:
        - "Pohlhausen": Laminar flat plate, forced convection (default)
        - "InclinedPlate": Mixed free-forced convection for inclined plates
        - "Sphere": Laminar flow around a sphere
        - "Ground": Flow over bare ground surface

        Args:
            model_name: Name of the boundary layer model to use.
                       Must be one of: "Pohlhausen", "InclinedPlate", "Sphere", "Ground"
            uuids: Optional list of primitive UUIDs to apply the model to.
                  If None, applies to all primitives in the Context.

        Raises:
            ValueError: If model_name is not valid
            BoundaryLayerConductanceModelError: If operation fails

        Example:
            >>> # Set Pohlhausen model for all primitives
            >>> bl_model.setBoundaryLayerModel("Pohlhausen")

            >>> # Set InclinedPlate model for specific leaves
            >>> bl_model.setBoundaryLayerModel("InclinedPlate", uuids=[uuid1, uuid2])

            >>> # Set Sphere model for fruit geometry
            >>> bl_model.setBoundaryLayerModel("Sphere", uuids=[fruit_uuid])

            >>> # Set Ground model for soil patches
            >>> bl_model.setBoundaryLayerModel("Ground", uuids=[ground_uuids])
        """
        # Validate model name
        valid_models = ["Pohlhausen", "InclinedPlate", "Sphere", "Ground"]
        if model_name not in valid_models:
            raise ValueError(
                f"Invalid boundary layer model '{model_name}'. "
                f"Must be one of: {', '.join(valid_models)}"
            )

        try:
            if uuids is None:
                # Apply to all primitives
                bl_wrapper.setBoundaryLayerModel(self.bl_model, model_name)
            elif len(uuids) == 1:
                # Single UUID - use UUID-specific function
                bl_wrapper.setBoundaryLayerModelForUUID(self.bl_model, uuids[0], model_name)
            else:
                # Multiple UUIDs
                bl_wrapper.setBoundaryLayerModelForUUIDs(self.bl_model, uuids, model_name)

        except Exception as e:
            raise BoundaryLayerConductanceModelError(f"Failed to set boundary layer model: {e}")

    def run(self, uuids: Optional[List[int]] = None) -> None:
        """
        Run the boundary layer conductance calculations.

        Calculates boundary-layer conductance values and stores results as
        primitive data "boundarylayer_conductance" (mol air/m²/s).

        Args:
            uuids: Optional list of primitive UUIDs to process.
                  If None, processes all primitives in the Context.

        Raises:
            BoundaryLayerConductanceModelError: If calculation fails

        Example:
            >>> # Calculate for all primitives
            >>> bl_model.run()

            >>> # Calculate for specific primitives
            >>> bl_model.run(uuids=[leaf1_uuid, leaf2_uuid])
        """
        try:
            if uuids is None:
                # Run for all primitives
                bl_wrapper.runBoundaryLayerModel(self.bl_model)
            else:
                # Run for specific UUIDs
                bl_wrapper.runBoundaryLayerModelForUUIDs(self.bl_model, uuids)

        except Exception as e:
            raise BoundaryLayerConductanceModelError(f"Failed to run boundary layer conductance calculation: {e}")

    @staticmethod
    def is_available() -> bool:
        """
        Check if BoundaryLayerConductanceModel plugin is available in current build.

        Returns:
            True if plugin is available, False otherwise

        Example:
            >>> if BoundaryLayerConductanceModel.is_available():
            ...     print("Boundary layer conductance modeling is available!")
        """
        registry = get_plugin_registry()
        return registry.is_plugin_available('boundarylayerconductance')
