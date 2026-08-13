"""
High-level ParameterOptimization interface for PyHelios.

This module provides a user-friendly interface to the parameter optimization
plugin, which calibrates named model parameters against a user-supplied
objective function using either population-based search (genetic algorithm,
Bayesian optimization, CMA-ES) or local optimization (Adam, L-BFGS, BOBYQA).

Example:
    >>> from pyhelios import ParameterOptimization, Parameter, GeneticAlgorithm
    >>>
    >>> def objective(p):
    ...     return (p["x"] - 3.0) ** 2 + (p["y"] + 1.0) ** 2
    >>>
    >>> with ParameterOptimization() as opt:
    ...     opt.setAlgorithm(GeneticAlgorithm(generations=100, random_seed=1))
    ...     result = opt.run(objective, {
    ...         "x": Parameter.continuous(0.0, -5.0, 5.0),
    ...         "y": Parameter.continuous(0.0, -5.0, 5.0),
    ...     })
    >>> round(result["x"], 1), round(result["y"], 1)
    (3.0, -1.0)
"""

import logging
import math
from dataclasses import dataclass, field
from enum import IntEnum
from typing import Callable, Dict, Mapping, Optional, Sequence, Union

from .plugins.registry import get_plugin_registry
from .wrappers import UParameterOptimizationWrapper as paramopt_wrapper
from .exceptions import HeliosError

logger = logging.getLogger(__name__)


class ParameterOptimizationError(HeliosError):
    """Exception raised for ParameterOptimization-specific errors."""
    pass


class ParameterType(IntEnum):
    """Kind of an optimizable parameter."""

    FLOAT = paramopt_wrapper.PARAM_FLOAT           #: Continuous
    INTEGER = paramopt_wrapper.PARAM_INTEGER       #: Rounded to the nearest whole number
    CATEGORICAL = paramopt_wrapper.PARAM_CATEGORICAL  #: Chosen from an explicit set


@dataclass
class Parameter:
    """
    A single optimizable parameter.

    Args:
        value: Initial value
        min: Lower bound. Ignored for CATEGORICAL parameters.
        max: Upper bound. Ignored for CATEGORICAL parameters.
        type: Parameter kind
        categories: Allowed values, required for CATEGORICAL parameters
    """

    value: float
    min: float = 0.0
    max: float = 0.0
    type: ParameterType = ParameterType.FLOAT
    categories: Sequence[float] = ()

    @classmethod
    def continuous(cls, value: float, min: float, max: float) -> "Parameter":
        """Create a continuous parameter bounded by [min, max]."""
        return cls(value=value, min=min, max=max, type=ParameterType.FLOAT)

    @classmethod
    def integer(cls, value: float, min: float, max: float) -> "Parameter":
        """Create an integer parameter bounded by [min, max]."""
        return cls(value=value, min=min, max=max, type=ParameterType.INTEGER)

    @classmethod
    def categorical(cls, value: float, categories: Sequence[float]) -> "Parameter":
        """Create a parameter restricted to an explicit set of values."""
        return cls(value=value, min=0.0, max=0.0,
                   type=ParameterType.CATEGORICAL, categories=tuple(categories))


#=============================================================================
# Genetic algorithm operators
#=============================================================================

@dataclass(frozen=True)
class BLXAlphaCrossover:
    """Component-wise blend crossover."""
    alpha: float = 0.5


@dataclass(frozen=True)
class BLXPCACrossover:
    """Blend crossover in PCA-transformed space, for non-separable problems."""
    alpha: float = 0.5
    pca_update_interval: int = 5


@dataclass(frozen=True)
class PerGeneMutation:
    """Per-gene Gaussian mutation."""
    rate: float = 0.1


@dataclass(frozen=True)
class IsotropicMutation:
    """Isotropic Gaussian mutation applied to all genes together."""
    rate: float = 0.1


@dataclass(frozen=True)
class HybridMutation:
    """Mixture of PCA-Gaussian, PCA-Cauchy, and random-direction mutation."""
    rate: float = 0.15
    pca_update_interval: int = 5
    sigma_pca: float = 0.25
    gamma_cauchy: float = 0.1
    sigma_random: float = 0.3
    pca_gaussian_prob: float = 0.70
    pca_cauchy_prob: float = 0.20


CrossoverOperator = Union[BLXAlphaCrossover, BLXPCACrossover]
MutationOperator = Union[PerGeneMutation, IsotropicMutation, HybridMutation]


#=============================================================================
# Algorithm settings
#
# Presets are read from the native library rather than transcribed here, so
# they cannot drift from helios-core when it is updated.
#=============================================================================

@dataclass
class GeneticAlgorithm:
    """
    Genetic algorithm settings.

    Handles continuous, integer, and categorical parameters, and needs no
    gradient. A good default when the search space is large or poorly behaved.
    """

    generations: int = 100
    population_size: int = 20
    crossover_rate: float = 0.5
    elitism_rate: float = 0.05
    random_seed: int = 0  #: 0 selects a nondeterministic seed
    crossover: CrossoverOperator = field(default_factory=BLXAlphaCrossover)
    mutation: MutationOperator = field(default_factory=PerGeneMutation)

    @classmethod
    def _from_struct(cls, struct) -> "GeneticAlgorithm":
        if struct.crossover_kind == paramopt_wrapper.CROSSOVER_BLX_PCA:
            crossover: CrossoverOperator = BLXPCACrossover(
                alpha=struct.crossover_alpha,
                pca_update_interval=struct.crossover_pca_update_interval)
        else:
            crossover = BLXAlphaCrossover(alpha=struct.crossover_alpha)

        if struct.mutation_kind == paramopt_wrapper.MUTATION_ISOTROPIC:
            mutation: MutationOperator = IsotropicMutation(rate=struct.mutation_rate)
        elif struct.mutation_kind == paramopt_wrapper.MUTATION_HYBRID:
            mutation = HybridMutation(
                rate=struct.mutation_rate,
                pca_update_interval=struct.mutation_pca_update_interval,
                sigma_pca=struct.mutation_sigma_pca,
                gamma_cauchy=struct.mutation_gamma_cauchy,
                sigma_random=struct.mutation_sigma_random,
                pca_gaussian_prob=struct.mutation_pca_gaussian_prob,
                pca_cauchy_prob=struct.mutation_pca_cauchy_prob)
        else:
            mutation = PerGeneMutation(rate=struct.mutation_rate)

        return cls(
            generations=struct.generations,
            population_size=struct.population_size,
            crossover_rate=struct.crossover_rate,
            elitism_rate=struct.elitism_rate,
            random_seed=struct.random_seed,
            crossover=crossover,
            mutation=mutation)

    @classmethod
    def explore(cls) -> "GeneticAlgorithm":
        """Exploration-biased preset: large population, high mutation."""
        return cls._from_struct(paramopt_wrapper.getGeneticAlgorithmExplore())

    @classmethod
    def exploit(cls) -> "GeneticAlgorithm":
        """Exploitation-biased preset: smaller population, low mutation."""
        return cls._from_struct(paramopt_wrapper.getGeneticAlgorithmExploit())

    def _to_struct(self):
        struct = paramopt_wrapper.PyHeliosGeneticAlgorithm()
        struct.generations = self.generations
        struct.population_size = self.population_size
        struct.crossover_rate = self.crossover_rate
        struct.elitism_rate = self.elitism_rate
        struct.random_seed = self.random_seed

        if isinstance(self.crossover, BLXPCACrossover):
            struct.crossover_kind = paramopt_wrapper.CROSSOVER_BLX_PCA
            struct.crossover_alpha = self.crossover.alpha
            struct.crossover_pca_update_interval = self.crossover.pca_update_interval
        elif isinstance(self.crossover, BLXAlphaCrossover):
            struct.crossover_kind = paramopt_wrapper.CROSSOVER_BLX_ALPHA
            struct.crossover_alpha = self.crossover.alpha
            struct.crossover_pca_update_interval = 5
        else:
            raise ValueError(
                f"crossover must be BLXAlphaCrossover or BLXPCACrossover, "
                f"got {type(self.crossover).__name__}")

        # Defaults for the fields the selected mutation does not carry.
        struct.mutation_pca_update_interval = 5
        struct.mutation_sigma_pca = 0.25
        struct.mutation_gamma_cauchy = 0.1
        struct.mutation_sigma_random = 0.3
        struct.mutation_pca_gaussian_prob = 0.70
        struct.mutation_pca_cauchy_prob = 0.20

        if isinstance(self.mutation, HybridMutation):
            struct.mutation_kind = paramopt_wrapper.MUTATION_HYBRID
            struct.mutation_rate = self.mutation.rate
            struct.mutation_pca_update_interval = self.mutation.pca_update_interval
            struct.mutation_sigma_pca = self.mutation.sigma_pca
            struct.mutation_gamma_cauchy = self.mutation.gamma_cauchy
            struct.mutation_sigma_random = self.mutation.sigma_random
            struct.mutation_pca_gaussian_prob = self.mutation.pca_gaussian_prob
            struct.mutation_pca_cauchy_prob = self.mutation.pca_cauchy_prob
        elif isinstance(self.mutation, IsotropicMutation):
            struct.mutation_kind = paramopt_wrapper.MUTATION_ISOTROPIC
            struct.mutation_rate = self.mutation.rate
        elif isinstance(self.mutation, PerGeneMutation):
            struct.mutation_kind = paramopt_wrapper.MUTATION_PER_GENE
            struct.mutation_rate = self.mutation.rate
        else:
            raise ValueError(
                f"mutation must be PerGeneMutation, IsotropicMutation, or HybridMutation, "
                f"got {type(self.mutation).__name__}")

        return struct


@dataclass
class BayesianOptimization:
    """
    Bayesian optimization with a Gaussian process surrogate.

    Suited to expensive objectives where the evaluation budget is small.
    """

    max_evaluations: int = 100
    initial_samples: int = 0  #: 0 selects 2*num_params
    ucb_kappa: float = 2.0
    max_gp_samples: int = 200
    acquisition_samples: int = 1000
    random_seed: int = 0  #: 0 selects a nondeterministic seed

    @classmethod
    def _from_struct(cls, struct) -> "BayesianOptimization":
        return cls(
            max_evaluations=struct.max_evaluations,
            initial_samples=struct.initial_samples,
            ucb_kappa=struct.ucb_kappa,
            max_gp_samples=struct.max_gp_samples,
            acquisition_samples=struct.acquisition_samples,
            random_seed=struct.random_seed)

    @classmethod
    def explore(cls) -> "BayesianOptimization":
        """Exploration-biased preset: high kappa, many acquisition samples."""
        return cls._from_struct(paramopt_wrapper.getBayesianExplore())

    @classmethod
    def exploit(cls) -> "BayesianOptimization":
        """Exploitation-biased preset: low kappa."""
        return cls._from_struct(paramopt_wrapper.getBayesianExploit())

    def _to_struct(self):
        struct = paramopt_wrapper.PyHeliosBayesianOptimization()
        struct.max_evaluations = self.max_evaluations
        struct.initial_samples = self.initial_samples
        struct.ucb_kappa = self.ucb_kappa
        struct.max_gp_samples = self.max_gp_samples
        struct.acquisition_samples = self.acquisition_samples
        struct.random_seed = self.random_seed
        return struct


@dataclass
class CMAES:
    """
    Covariance Matrix Adaptation Evolution Strategy.

    Strong general-purpose choice for continuous, non-separable problems.
    """

    max_evaluations: int = 200
    lambda_: int = 0  #: Population size; 0 selects 4+floor(3*ln(n))
    sigma: float = 0.3
    random_seed: int = 0  #: 0 selects a nondeterministic seed

    @classmethod
    def _from_struct(cls, struct) -> "CMAES":
        return cls(
            max_evaluations=struct.max_evaluations,
            lambda_=struct.lambda_,
            sigma=struct.sigma,
            random_seed=struct.random_seed)

    @classmethod
    def explore(cls) -> "CMAES":
        """Exploration-biased preset: large initial step size."""
        return cls._from_struct(paramopt_wrapper.getCMAESExplore())

    @classmethod
    def exploit(cls) -> "CMAES":
        """Exploitation-biased preset: small initial step size."""
        return cls._from_struct(paramopt_wrapper.getCMAESExploit())

    def _to_struct(self):
        struct = paramopt_wrapper.PyHeliosCMAES()
        struct.max_evaluations = self.max_evaluations
        struct.lambda_ = self.lambda_
        struct.sigma = self.sigma
        struct.random_seed = self.random_seed
        return struct


@dataclass
class Adam:
    """
    AdamW gradient-based optimization.

    Noise-tolerant and dependency-free. Requires a gradient, either supplied
    directly or estimated with ``finite_difference=True``.
    """

    max_iterations: int = 200
    learning_rate: float = 0.01
    beta1: float = 0.9
    beta2: float = 0.999
    epsilon: float = 1e-8
    weight_decay: float = 0.0  #: 0 gives standard Adam
    ftol_rel: float = 1e-6
    xtol_rel: float = 1e-6

    def _to_struct(self):
        struct = paramopt_wrapper.PyHeliosAdam()
        struct.max_iterations = self.max_iterations
        struct.learning_rate = self.learning_rate
        struct.beta1 = self.beta1
        struct.beta2 = self.beta2
        struct.epsilon = self.epsilon
        struct.weight_decay = self.weight_decay
        struct.ftol_rel = self.ftol_rel
        struct.xtol_rel = self.xtol_rel
        return struct


@dataclass
class LBFGS:
    """
    L-BFGS gradient-based optimization.

    Requires an NLopt build that includes the LGPL Luksan solvers. PyHelios
    builds without them by default to keep the distributed library MIT-licensed,
    so this is typically unavailable -- use :class:`Adam` or :class:`BOBYQA`.
    """

    max_iterations: int = 200
    ftol_rel: float = 1e-6
    xtol_rel: float = 1e-6
    verify_gradients: bool = False
    fd_step: float = 1e-5

    def _to_struct(self):
        struct = paramopt_wrapper.PyHeliosLBFGS()
        struct.max_iterations = self.max_iterations
        struct.ftol_rel = self.ftol_rel
        struct.xtol_rel = self.xtol_rel
        struct.verify_gradients = 1 if self.verify_gradients else 0
        struct.fd_step = self.fd_step
        return struct


@dataclass
class BOBYQA:
    """
    BOBYQA derivative-free local optimization. Requires NLopt.

    Builds a local quadratic model from function values alone -- a good choice
    for polishing a population-based result or for noisy black-box objectives.
    """

    max_iterations: int = 200
    ftol_rel: float = 1e-6
    xtol_rel: float = 1e-6
    initial_step: float = 0.0  #: 0 selects 10% of the parameter range

    def _to_struct(self):
        struct = paramopt_wrapper.PyHeliosBOBYQA()
        struct.max_iterations = self.max_iterations
        struct.ftol_rel = self.ftol_rel
        struct.xtol_rel = self.xtol_rel
        struct.initial_step = self.initial_step
        return struct


@dataclass
class SLSQP:
    """
    SLSQP gradient-based optimization. Requires NLopt and a gradient.

    Note that PyHelios does not currently expose the plugin's nonlinear
    constraint support, so this behaves as an unconstrained local optimizer.
    """

    max_iterations: int = 200
    ftol_rel: float = 1e-6
    xtol_rel: float = 1e-6

    def _to_struct(self):
        struct = paramopt_wrapper.PyHeliosSLSQP()
        struct.max_iterations = self.max_iterations
        struct.ftol_rel = self.ftol_rel
        struct.xtol_rel = self.xtol_rel
        return struct


AlgorithmSettings = Union[GeneticAlgorithm, BayesianOptimization, CMAES,
                          Adam, LBFGS, BOBYQA, SLSQP]

# Maps each settings type to its short native name, its wrapper setter, whether
# it needs a gradient, and whether it understands INTEGER/CATEGORICAL parameters.
#
# Only the genetic algorithm handles discrete parameters. Every other algorithm
# searches a continuous space and would treat a discrete parameter as a plain
# float, so passing one is rejected rather than silently answered -- see
# _validate_parameter_types_for_algorithm.
_ALGORITHM_INFO = {
    GeneticAlgorithm: ("GA", paramopt_wrapper.setGeneticAlgorithm, False, True),
    BayesianOptimization: ("BO", paramopt_wrapper.setBayesianOptimization, False, False),
    CMAES: ("CMAES", paramopt_wrapper.setCMAES, False, False),
    Adam: ("ADAM", paramopt_wrapper.setAdam, True, False),
    LBFGS: ("LBFGS", paramopt_wrapper.setLBFGS, True, False),
    BOBYQA: ("BOBYQA", paramopt_wrapper.setBOBYQA, False, False),
    SLSQP: ("SLSQP", paramopt_wrapper.setSLSQP, True, False),
}


@dataclass(frozen=True)
class ConstrainedResult:
    """
    One evaluation of a constrained simulation.

    Returned by the callable passed to :meth:`ParameterOptimization.runConstrained`,
    which computes the objective, the constraints, and every gradient in a single
    pass. The optimizer caches this per parameter point, so a simulation that runs a
    full Helios scene is evaluated once rather than once per constraint.

    Args:
        objective: Scalar cost to minimize
        objective_gradient: Partial derivative of the objective for every parameter
        constraints: Constraint values; constraint i is satisfied when its value is <= 0
        constraint_gradients: One gradient mapping per constraint, in the same order
    """

    objective: float
    objective_gradient: Dict[str, float]
    constraints: Sequence[float]
    constraint_gradients: Sequence[Dict[str, float]]


@dataclass(frozen=True)
class OptimizationResult:
    """
    Outcome of an optimization run.

    Holds full :class:`Parameter` objects rather than bare floats so a result
    can be fed straight back into another run, e.g. refining a CMA-ES result
    with BOBYQA.
    """

    parameters: Dict[str, Parameter]
    fitness: float

    @property
    def values(self) -> Dict[str, float]:
        """The optimized values, as a plain name-to-value mapping."""
        return {name: parameter.value for name, parameter in self.parameters.items()}

    def __getitem__(self, name: str) -> float:
        """Get one optimized value by parameter name."""
        return self.parameters[name].value


def make_constrained_simulation(
        objective: Callable[[Dict[str, float]], float],
        objective_gradient: Callable[[Dict[str, float]], Dict[str, float]],
        constraints: Sequence[tuple]) -> Callable[[Dict[str, float]], ConstrainedResult]:
    """
    Compose separate objective and constraint callables into one simulation.

    A convenience for problems whose constraints really are independent functions.
    Note that it calls every function at each parameter point, so it forfeits the
    single-pass advantage of writing one combined simulation: if computing the
    objective and the constraints shares expensive work -- as it does when they come
    from one Helios simulation -- write a :class:`ConstrainedResult` directly instead.

    Args:
        objective: Callable receiving ``{name: value}`` and returning a scalar cost
        objective_gradient: Callable returning ``{name: partial derivative}``
        constraints: Sequence of ``(function, gradient)`` pairs, each satisfied when
                     ``function(params) <= 0``

    Returns:
        A callable suitable for :meth:`ParameterOptimization.runConstrained`

    Example:
        >>> simulation = make_constrained_simulation(
        ...     lambda p: p["x"] ** 2,
        ...     lambda p: {"x": 2 * p["x"]},
        ...     [(lambda p: 1.0 - p["x"], lambda p: {"x": -1.0})])
    """
    if not callable(objective):
        raise TypeError(f"objective must be callable, got {type(objective).__name__}")
    if not callable(objective_gradient):
        raise TypeError(
            f"objective_gradient must be callable, got {type(objective_gradient).__name__}")

    pairs = list(constraints)
    for index, pair in enumerate(pairs):
        if not isinstance(pair, tuple) or len(pair) != 2:
            raise TypeError(
                f"constraints[{index}] must be a (function, gradient) tuple, "
                f"got {type(pair).__name__}")
        if not all(callable(item) for item in pair):
            raise TypeError(f"Both entries of constraints[{index}] must be callable")

    def simulation(params: Dict[str, float]) -> ConstrainedResult:
        return ConstrainedResult(
            objective=objective(params),
            objective_gradient=objective_gradient(params),
            constraints=[function(params) for function, _ in pairs],
            constraint_gradients=[gradient(params) for _, gradient in pairs],
        )

    return simulation


class ParameterOptimization:
    """
    Optimize named model parameters against an objective function.

    The objective receives a ``{name: value}`` dict and returns a scalar cost to
    minimize. It may close over a :class:`~pyhelios.Context` and run a full
    Helios simulation; the plugin itself takes no Context.

    This class requires the native Helios library built with the
    ``parameteroptimization`` plugin. Use it as a context manager so the C++
    instance is released promptly.

    Example:
        >>> with ParameterOptimization() as opt:
        ...     opt.setAlgorithm(CMAES(max_evaluations=200, random_seed=1))
        ...     result = opt.run(objective, {"x": Parameter.continuous(0.0, -5.0, 5.0)})
        ...     print(result.fitness, result["x"])
    """

    def __init__(self):
        """
        Create a ParameterOptimization instance.

        Raises:
            ParameterOptimizationError: If the plugin is unavailable in this build
        """
        self.optimizer = None
        self._running = False

        registry = get_plugin_registry()
        if not registry.is_plugin_available('parameteroptimization'):
            available_plugins = registry.get_available_plugins()
            raise ParameterOptimizationError(
                "ParameterOptimization requires the 'parameteroptimization' plugin "
                "which is not available.\n\n"
                "To enable parameter optimization:\n"
                "1. Rebuild PyHelios with all plugins:\n"
                "   build_scripts/build_helios --clean\n"
                "2. Or select the plugin explicitly:\n"
                "   build_scripts/build_helios --plugins parameteroptimization\n\n"
                "System requirements:\n"
                "  - Platforms: Windows, Linux, macOS\n"
                "  - Dependencies: none (NLopt is bundled)\n"
                "  - GPU: not required\n\n"
                f"Currently available plugins: {available_plugins}"
            )

        try:
            self.optimizer = paramopt_wrapper.createParameterOptimization()
            if not self.optimizer:
                raise ParameterOptimizationError(
                    "Failed to create ParameterOptimization instance.")
        except ParameterOptimizationError:
            raise
        except Exception as e:
            raise ParameterOptimizationError(
                f"Failed to initialize ParameterOptimization: {e}")

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        """Context manager exit with proper cleanup."""
        if self.optimizer is not None:
            try:
                paramopt_wrapper.destroyParameterOptimization(self.optimizer)
                logger.debug("ParameterOptimization destroyed successfully")
            except Exception as e:
                logger.warning(f"Error destroying ParameterOptimization: {e}")
            finally:
                self.optimizer = None

    def __del__(self):
        """Destructor to ensure C++ resources freed even without 'with' statement."""
        if hasattr(self, 'optimizer') and self.optimizer is not None:
            try:
                paramopt_wrapper.destroyParameterOptimization(self.optimizer)
                self.optimizer = None
            except Exception as e:
                import warnings
                warnings.warn(f"Error in ParameterOptimization.__del__: {e}")

    def getNativePtr(self):
        """Get the native pointer for advanced operations."""
        return self.optimizer

    def _check_alive(self) -> None:
        """Raise if this instance has already been destroyed."""
        if self.optimizer is None:
            raise ParameterOptimizationError(
                "ParameterOptimization has been destroyed and can no longer be used.")

    #=========================================================================
    # Algorithm selection
    #=========================================================================

    @staticmethod
    def availableAlgorithms() -> Dict[str, bool]:
        """
        Report which algorithms can run in this build.

        L-BFGS, BOBYQA and SLSQP depend on NLopt, and L-BFGS additionally on the
        LGPL Luksan solvers, which PyHelios disables by default.

        Returns:
            Mapping of algorithm name to availability
        """
        names = ["GA", "BO", "CMAES", "ADAM", "LBFGS", "BOBYQA", "SLSQP"]
        return {name: paramopt_wrapper.isAlgorithmAvailable(name) for name in names}

    def setAlgorithm(self, algorithm: AlgorithmSettings) -> None:
        """
        Select the optimization algorithm and its hyperparameters.

        If never called, the plugin picks a default based on the parameter types
        and whether a gradient was supplied.

        Args:
            algorithm: One of the algorithm settings dataclasses

        Raises:
            TypeError: If algorithm is not a recognized settings type
            ParameterOptimizationError: If the algorithm is unavailable in this build
        """
        self._check_alive()

        info = _ALGORITHM_INFO.get(type(algorithm))
        if info is None:
            raise TypeError(
                f"algorithm must be one of "
                f"{', '.join(cls.__name__ for cls in _ALGORITHM_INFO)}, "
                f"got {type(algorithm).__name__}")

        native_name, setter, _, _ = info

        # Checked here rather than left to fail inside run(), so the user finds
        # out before waiting through a long optimization.
        if not paramopt_wrapper.isAlgorithmAvailable(native_name):
            raise ParameterOptimizationError(
                f"The {type(algorithm).__name__} algorithm is not available in this build.\n\n"
                f"{native_name} is provided by NLopt. PyHelios builds NLopt without the "
                f"LGPL-licensed Luksan solvers so the distributed library stays "
                f"MIT-licensed, which makes L-BFGS unavailable.\n\n"
                f"Alternatives that are always available:\n"
                f"  - Adam: gradient-based, noise-tolerant\n"
                f"  - BOBYQA: derivative-free local optimization (needs NLopt)\n"
                f"  - CMAES / GeneticAlgorithm: population-based global search\n\n"
                f"To enable it anyway, rebuild helios-core with -DHELIOS_NLOPT_LUKSAN=ON.")

        try:
            setter(self.optimizer, algorithm._to_struct())
        except (ParameterOptimizationError, ValueError, TypeError):
            raise
        except Exception as e:
            raise ParameterOptimizationError(f"Failed to set algorithm: {e}")

        self._algorithm = algorithm

    #=========================================================================
    # I/O configuration
    #=========================================================================

    def setPrintProgress(self, enable: bool) -> None:
        """
        Enable or disable the plugin's progress printout to stdout.

        Args:
            enable: True to print progress during optimization
        """
        self._check_alive()
        paramopt_wrapper.setPrintProgress(self.optimizer, bool(enable))

    def setResultFile(self, path: Optional[str]) -> None:
        """
        Write the final result to a CSV file.

        Args:
            path: Output path ending in .csv or .txt; None disables writing
        """
        self._check_alive()
        paramopt_wrapper.setResultFile(self.optimizer, path)

    def setProgressFile(self, path: Optional[str]) -> None:
        """
        Write per-generation progress to a CSV file.

        Args:
            path: Output path ending in .csv or .txt; None disables writing
        """
        self._check_alive()
        paramopt_wrapper.setProgressFile(self.optimizer, path)

    def setInputFile(self, path: Optional[str]) -> None:
        """
        Read the initial parameter set from a file.

        Only the genetic algorithm consults this file.

        Args:
            path: Headerless CSV of "name,value,min,max" rows; None disables reading
        """
        self._check_alive()
        paramopt_wrapper.setInputFile(self.optimizer, path)

    #=========================================================================
    # Run
    #=========================================================================

    def run(self,
            objective: Callable[[Dict[str, float]], float],
            parameters: Mapping[str, Parameter],
            gradient: Optional[Callable[[Dict[str, float]], Dict[str, float]]] = None,
            *,
            finite_difference: bool = False,
            fd_step: float = 0.0) -> OptimizationResult:
        """
        Run the optimization.

        Args:
            objective: Callable receiving {name: value} and returning a scalar cost
                       to minimize. Invoked once per candidate parameter set.
            parameters: Parameters to optimize, keyed by name
            gradient: Optional callable receiving {name: value} and returning
                      {name: partial derivative} for every parameter. Required by
                      Adam, L-BFGS, and SLSQP unless finite_difference is used.
            finite_difference: Estimate the gradient by centered finite differences
                               instead of supplying one. Costs 2N extra objective
                               evaluations per gradient.
            fd_step: Relative perturbation for finite differences; 0 uses the default

        Returns:
            The optimized parameters and the objective value at the optimum

        Raises:
            ValueError: If the arguments are invalid
            TypeError: If objective or gradient is not callable
            ParameterOptimizationError: If the optimization fails

        Note:
            An exception raised inside the objective aborts the run and is
            re-raised here with its original traceback. Partial results are not
            recoverable.
        """
        self._check_alive()

        if not callable(objective):
            raise TypeError(f"objective must be callable, got {type(objective).__name__}")
        if gradient is not None and not callable(gradient):
            raise TypeError(f"gradient must be callable, got {type(gradient).__name__}")
        if gradient is not None and finite_difference:
            raise ValueError(
                "Pass either a gradient function or finite_difference=True, not both.")

        specs = self._validate_parameters(parameters)

        algorithm = getattr(self, '_algorithm', None)
        if algorithm is not None:
            _, _, needs_gradient, _ = _ALGORITHM_INFO[type(algorithm)]
            self._validate_parameter_types_for_algorithm(parameters, algorithm)
            if needs_gradient and gradient is None and not finite_difference:
                raise ValueError(
                    f"{type(algorithm).__name__} is a gradient-based algorithm and requires "
                    f"a gradient. Either pass gradient=<callable>, or pass "
                    f"finite_difference=True to estimate it numerically.")

        # The objective must not re-enter this same instance: the C++ optimizer
        # is stateful and not reentrant.
        if self._running:
            raise ParameterOptimizationError(
                "ParameterOptimization.run() was called from inside its own objective "
                "function. The optimizer is not reentrant; use a separate instance.")

        self._running = True
        try:
            if gradient is not None:
                values, fitness = paramopt_wrapper.runOptimizationWithGradient(
                    self.optimizer, specs, objective, gradient)
            elif finite_difference:
                values, fitness = paramopt_wrapper.runOptimizationWithFDGradient(
                    self.optimizer, specs, objective, fd_step)
            else:
                values, fitness = paramopt_wrapper.runOptimization(
                    self.optimizer, specs, objective)
        finally:
            self._running = False

        # Bounds and types are untouched by the optimizer, so they carry over
        # from the inputs and only the values are replaced.
        optimized = {
            name: Parameter(value=values[name], min=parameter.min, max=parameter.max,
                            type=parameter.type, categories=parameter.categories)
            for name, parameter in parameters.items()
        }
        return OptimizationResult(parameters=optimized, fitness=fitness)

    def runConstrained(self,
                       simulation: Callable[[Dict[str, float]], ConstrainedResult],
                       parameters: Mapping[str, Parameter],
                       *,
                       constraint_count: int) -> OptimizationResult:
        """
        Run a constrained optimization: minimize f(x) subject to c_i(x) <= 0.

        Requires ``setAlgorithm(SLSQP(...))``. SLSQP is the only algorithm in the
        plugin that handles nonlinear inequality constraints, and it needs every
        parameter to be ``FLOAT``.

        The simulation returns the objective, the constraints, and all gradients
        together. The optimizer caches each result, so the simulation runs once per
        parameter point no matter how many constraints there are -- which is what
        makes this practical for objectives that run a full Helios simulation.

        Args:
            simulation: Callable receiving ``{name: value}`` and returning a
                        :class:`ConstrainedResult`
            parameters: Parameters to optimize, keyed by name
            constraint_count: Number of constraints. Required, and fixed for the whole
                              run: the buffers the simulation writes into are sized
                              before the first call, so the count cannot be discovered
                              by calling it.

        Returns:
            The optimized parameters and the objective value at the optimum

        Raises:
            ValueError: If the arguments are invalid, or the selected algorithm is
                        not SLSQP
            TypeError: If simulation is not callable
            ParameterOptimizationError: If the optimization fails

        Note:
            Constraints are satisfied to the plugin's tolerance rather than exactly.
            Check feasibility of the returned parameters if it matters.

        Example:
            >>> # minimize x^2 + y^2 subject to x + y >= 1
            >>> def simulation(p):
            ...     return ConstrainedResult(
            ...         objective=p["x"] ** 2 + p["y"] ** 2,
            ...         objective_gradient={"x": 2 * p["x"], "y": 2 * p["y"]},
            ...         constraints=[1.0 - p["x"] - p["y"]],
            ...         constraint_gradients=[{"x": -1.0, "y": -1.0}],
            ...     )
            >>> with ParameterOptimization() as opt:
            ...     opt.setAlgorithm(SLSQP())
            ...     result = opt.runConstrained(
            ...         simulation,
            ...         {"x": Parameter.continuous(0.0, -5.0, 5.0),
            ...          "y": Parameter.continuous(0.0, -5.0, 5.0)},
            ...         constraint_count=1)
        """
        self._check_alive()

        if not callable(simulation):
            raise TypeError(
                f"simulation must be callable, got {type(simulation).__name__}")
        if not isinstance(constraint_count, int) or isinstance(constraint_count, bool):
            raise TypeError(
                f"constraint_count must be an int, got {type(constraint_count).__name__}")
        if constraint_count < 1:
            raise ValueError(
                f"constraint_count must be at least 1, got {constraint_count}. "
                f"Use run() when there are no constraints.")

        specs = self._validate_parameters(parameters)

        # Checked before the run rather than left to C++, which raises the same
        # requirement from inside the optimizer once work is already underway.
        algorithm = getattr(self, '_algorithm', None)
        if not isinstance(algorithm, SLSQP):
            selected = type(algorithm).__name__ if algorithm is not None else "none"
            raise ValueError(
                f"Constrained optimization requires SLSQP, but the selected algorithm is "
                f"{selected}. Call setAlgorithm(SLSQP(...)) first.\n\n"
                f"SLSQP is the only algorithm in the plugin that supports nonlinear "
                f"inequality constraints. For the others, fold the constraint into the "
                f"objective as a penalty term and use run().")

        self._validate_parameter_types_for_algorithm(parameters, algorithm)

        if self._running:
            raise ParameterOptimizationError(
                "ParameterOptimization.runConstrained() was called from inside its own "
                "simulation function. The optimizer is not reentrant; use a separate "
                "instance.")

        self._running = True
        try:
            values, fitness = paramopt_wrapper.runOptimizationConstrained(
                self.optimizer, specs, simulation, constraint_count)
        finally:
            self._running = False

        optimized = {
            name: Parameter(value=values[name], min=parameter.min, max=parameter.max,
                            type=parameter.type, categories=parameter.categories)
            for name, parameter in parameters.items()
        }
        return OptimizationResult(parameters=optimized, fitness=fitness)

    @staticmethod
    def _validate_parameters(parameters: Mapping[str, Parameter]) -> list:
        """
        Check the parameter mapping and flatten it for the wrapper.

        Only conditions that are memory-safety preconditions, or that produce a
        materially better message here than from C++, are checked. Bound
        consistency (min == max, min > max, NaN bounds, empty categories) is left
        to the plugin's own validation so the two cannot drift apart.
        """
        if not isinstance(parameters, Mapping):
            raise TypeError(
                f"parameters must be a mapping of name to Parameter, "
                f"got {type(parameters).__name__}")
        if not parameters:
            raise ValueError("parameters cannot be empty")

        specs = []
        for name, parameter in parameters.items():
            if not isinstance(name, str):
                raise TypeError(
                    f"Parameter names must be strings, got {type(name).__name__}: {name!r}")
            if not name:
                raise ValueError("Parameter names cannot be empty")
            if "\x00" in name:
                # Would silently truncate the C string and misalign every
                # subsequent name lookup.
                raise ValueError(f"Parameter name {name!r} cannot contain a null character")
            if not isinstance(parameter, Parameter):
                raise TypeError(
                    f"Parameter '{name}' must be a Parameter, "
                    f"got {type(parameter).__name__}")

            for attribute in ("value", "min", "max"):
                attr_value = getattr(parameter, attribute)
                if not isinstance(attr_value, (int, float)) or isinstance(attr_value, bool):
                    raise TypeError(
                        f"Parameter '{name}' field '{attribute}' must be numeric, "
                        f"got {type(attr_value).__name__}")

            categories = tuple(parameter.categories or ())
            if parameter.type == ParameterType.CATEGORICAL and not categories:
                raise ValueError(
                    f"Parameter '{name}' is CATEGORICAL and must define at least one "
                    f"allowed value via 'categories'")
            for category in categories:
                if not isinstance(category, (int, float)) or isinstance(category, bool):
                    raise TypeError(
                        f"Parameter '{name}' has a non-numeric category: {category!r}")
                if not math.isfinite(float(category)):
                    raise ValueError(
                        f"Parameter '{name}' has a non-finite category: {category!r}")

            specs.append({
                "name": name,
                "value": float(parameter.value),
                "min": float(parameter.min),
                "max": float(parameter.max),
                "type": int(parameter.type),
                "categories": [float(c) for c in categories],
            })

        return specs

    @staticmethod
    def _validate_parameter_types_for_algorithm(
            parameters: Mapping[str, "Parameter"],
            algorithm: "AlgorithmSettings") -> None:
        """
        Reject discrete parameters given to an algorithm that cannot handle them.

        Only the genetic algorithm implements INTEGER and CATEGORICAL parameters.
        The rest search a continuous space, so a discrete parameter would be
        optimized as a plain float and the result would not be a whole number, or
        not one of the allowed categories.

        helios-core enforces this for L-BFGS, Adam, BOBYQA and SLSQP, but not for
        CMA-ES or Bayesian optimization, where a CATEGORICAL parameter instead
        collapses to 0.0 with no diagnostic: its min and max are documented as
        ignored and so are conventionally left at zero, which those two algorithms
        read as the bounds [0, 0]. Checking here covers that gap on every core
        version, and reports the parameter and the remedy rather than leaving the
        message to the layer that happens to catch it first.
        """
        info = _ALGORITHM_INFO.get(type(algorithm))
        if info is None or info[3]:
            return

        discrete = [
            (name, ParameterType(parameter.type).name)
            for name, parameter in parameters.items()
            if isinstance(parameter, Parameter)
            and parameter.type != ParameterType.FLOAT
        ]
        if not discrete:
            return

        listed = ", ".join(f"'{name}' is {type_name}" for name, type_name in discrete)
        raise ValueError(
            f"{type(algorithm).__name__} requires every parameter to be FLOAT, "
            f"but {listed}.\n\n"
            f"GeneticAlgorithm is the only algorithm that supports INTEGER and "
            f"CATEGORICAL parameters. Either switch to it, or make the parameter "
            f"continuous with Parameter.continuous(...).")

    def is_available(self) -> bool:
        """Check if the parameteroptimization plugin is available in this build."""
        return get_plugin_registry().is_plugin_available('parameteroptimization')
