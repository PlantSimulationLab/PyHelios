from .Global import Global
from .Logger import Logger
from .Context import Context, PrimitiveType

# Initialize asset paths for C++ plugins
try:
    from .assets import initialize_asset_paths
    initialize_asset_paths()
except Exception as e:
    import logging
    logging.getLogger(__name__).warning(f"Failed to initialize asset paths: {e}")

# Optional plugin imports - only load if the native functions are available
try:
    from .WeberPennTree import WeberPennTree, WPTType
except (AttributeError, ImportError):
    # WeberPennTree functions not available in current library
    WeberPennTree = None
    WPTType = None

try:
    from .RadiationModel import RadiationModel
except (AttributeError, ImportError):
    # RadiationModel functions not available in current library
    RadiationModel = None

try:
    from .EnergyBalance import EnergyBalanceModel, EnergyBalanceModelError
except (AttributeError, ImportError):
    # EnergyBalanceModel functions not available in current library
    EnergyBalanceModel = None
    EnergyBalanceModelError = None

try:
    from .Visualizer import Visualizer, VisualizerError
except (AttributeError, ImportError):
    # Visualizer functions not available in current library
    Visualizer = None
    VisualizerError = None
from .wrappers import DataTypes as DataTypes
from . import dev_utils
from .exceptions import (
    HeliosError,
    HeliosRuntimeError,
    HeliosInvalidArgumentError,
    HeliosUUIDNotFoundError,
    HeliosFileIOError,
    HeliosMemoryAllocationError,
    HeliosGPUInitializationError,
    HeliosPluginNotAvailableError,
    HeliosUnknownError
)