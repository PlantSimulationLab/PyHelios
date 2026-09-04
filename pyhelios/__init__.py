from .Global import Global
from .Logger import Logger
from .Context import Context, PrimitiveType, VertexNormalSource, VertexWeldMode

# Version information with robust fallback strategies
def _get_version():
    """Get version with multiple fallback strategies."""
    try:
        from ._version import version
        return version
    except ImportError:
        pass
    
    try:
        # Try setuptools-scm directly for development installs
        from setuptools_scm import get_version
        from pathlib import Path
        return get_version(root=Path(__file__).parent.parent)
    except (ImportError, LookupError):
        pass
    
    try:
        # Try pkg_resources/importlib.metadata as final fallback
        try:
            from importlib.metadata import version
        except ImportError:
            # Python < 3.8 fallback
            from importlib_metadata import version
        return version('pyhelios')
    except Exception:
        pass
    
    return "unknown"

__version__ = _get_version()

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
    from .RadiationModel import (
        RadiationModel,
        RadiationModelError,
        CameraProperties,
        CameraMetadata,
        SIFCameraProperties,
    )
except (AttributeError, ImportError):
    # RadiationModel functions not available in current library
    RadiationModel = None
    CameraProperties = None
    CameraMetadata = None
    RadiationModelError = None
    SIFCameraProperties = None

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

try:
    from .SolarPosition import SolarPosition, SolarPositionError
except (AttributeError, ImportError):
    # SolarPosition functions not available in current library
    SolarPosition = None
    SolarPositionError = None

try:
    from .StomatalConductance import (
        StomatalConductanceModel,
        StomatalConductanceModelError,
        BWBCoefficients,
        BBLCoefficients,
        MOPTCoefficients,
        BMFCoefficients,
        BBCoefficients
    )
except (AttributeError, ImportError):
    # StomatalConductanceModel functions not available in current library
    StomatalConductanceModel = None
    StomatalConductanceModelError = None
    BWBCoefficients = None
    BBLCoefficients = None
    MOPTCoefficients = None
    BMFCoefficients = None
    BBCoefficients = None

try:
    from .BoundaryLayerConductance import (
        BoundaryLayerConductanceModel,
        BoundaryLayerConductanceModelError
    )
except (AttributeError, ImportError):
    # BoundaryLayerConductanceModel functions not available in current library
    BoundaryLayerConductanceModel = None
    BoundaryLayerConductanceModelError = None

try:
    from .PhotosynthesisModel import (
        PhotosynthesisModel,
        PhotosynthesisModelError,
        AVAILABLE_C4_SPECIES,
    )
except (AttributeError, ImportError):
    # PhotosynthesisModel functions not available in current library
    PhotosynthesisModel = None
    PhotosynthesisModelError = None
    AVAILABLE_C4_SPECIES = []

try:
    from .PlantArchitecture import PlantArchitecture, PlantArchitectureError
except (AttributeError, ImportError):
    # PlantArchitecture functions not available in current library
    PlantArchitecture = None
    PlantArchitectureError = None

# Typed plant architecture parameter model (pure Python, always importable)
from .plant_architecture_params import (
    RandomParameter,
    RandomParameterFloat,
    RandomParameterInt,
    LeafPrototype,
    InternodeParameters,
    PetioleParameters,
    LeafParameters,
    PeduncleParameters,
    InflorescenceParameters,
    PhytomerParameters,
    ShootParameters,
    CarbohydrateParameters,
    NitrogenParameters,
)

try:
    from .LeafOptics import LeafOptics, LeafOpticsError, LeafOpticsProperties
except (AttributeError, ImportError):
    # LeafOptics functions not available in current library
    LeafOptics = None
    LeafOpticsError = None
    LeafOpticsProperties = None

try:
    from .LiDARCloud import (
        LiDARCloud, LiDARError, ScanPattern,
        ScanMode, ReturnMode, SingleReturnSelection, RisleyPrism,
    )
except (AttributeError, ImportError):
    # LiDARCloud functions not available in current library
    LiDARCloud = None
    LiDARError = None
    ScanPattern = None
    ScanMode = None
    ReturnMode = None
    SingleReturnSelection = None
    RisleyPrism = None

try:
    from .ParameterOptimization import (
        ParameterOptimization, ParameterOptimizationError, OptimizationResult,
        ConstrainedResult, make_constrained_simulation,
        Parameter, ParameterType,
        GeneticAlgorithm, BayesianOptimization, CMAES, Adam, LBFGS, BOBYQA, SLSQP,
        BLXAlphaCrossover, BLXPCACrossover,
        PerGeneMutation, IsotropicMutation, HybridMutation,
    )
except (AttributeError, ImportError):
    # ParameterOptimization functions not available in current library
    ParameterOptimization = None
    ParameterOptimizationError = None
    OptimizationResult = None
    ConstrainedResult = None
    make_constrained_simulation = None
    Parameter = None
    ParameterType = None
    GeneticAlgorithm = None
    BayesianOptimization = None
    CMAES = None
    Adam = None
    LBFGS = None
    BOBYQA = None
    SLSQP = None
    BLXAlphaCrossover = None
    BLXPCACrossover = None
    PerGeneMutation = None
    IsotropicMutation = None
    HybridMutation = None

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