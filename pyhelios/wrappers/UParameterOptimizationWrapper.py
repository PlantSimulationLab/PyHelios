"""
Ctypes wrapper for ParameterOptimization C++ bindings.

This module provides low-level ctypes bindings to interface with the native
Helios ParameterOptimization plugin via the C++ wrapper layer.

Unlike the other wrappers, this one passes Python callables into C++: the
objective is invoked once per candidate parameter set, potentially thousands of
times per run. Two mechanisms make that safe and are documented in detail at
their definitions below -- the exception stash (a Python exception cannot
propagate through C++ frames) and the callback keepalive (a garbage-collected
CFUNCTYPE object leaves C++ calling into freed memory).
"""

import ctypes
import math
import sys
from typing import Callable, Dict, List, Optional, Sequence, Tuple

from ..plugins import helios_lib
from ..exceptions import check_helios_error


# Define the UParameterOptimization struct
class UParameterOptimization(ctypes.Structure):
    """Opaque structure for ParameterOptimization C++ class"""
    pass


# Return codes from the native run() entry points. Must match the
# PYHELIOS_PARAMOPT_* macros in pyhelios_wrapper_parameteroptimization.h.
PARAMOPT_OK = 0
PARAMOPT_ERROR = -1
PARAMOPT_CALLBACK_FAILED = -2

# Parameter kinds. Must match PyHeliosParameterType.
PARAM_FLOAT = 0
PARAM_INTEGER = 1
PARAM_CATEGORICAL = 2

# Genetic algorithm operator selections. Must match PyHeliosCrossoverKind and
# PyHeliosMutationKind.
CROSSOVER_BLX_ALPHA = 0
CROSSOVER_BLX_PCA = 1
MUTATION_PER_GENE = 0
MUTATION_ISOTROPIC = 1
MUTATION_HYBRID = 2


# Error checking callback
def _check_error(result, func, args):
    """Automatic error checking for all parameter optimization functions"""
    check_helios_error(helios_lib.getLastErrorCode, helios_lib.getLastErrorMessage, helios_lib.clearError)
    return result


#=============================================================================
# Structure mirrors
#
# These mirror the POD structs in pyhelios_wrapper_parameteroptimization.h.
# _pack_ is deliberately not set: the C structs use natural alignment, so
# forcing a packed layout here would silently misread every field after the
# first padded one.
#=============================================================================

class PyHeliosParameterSpec(ctypes.Structure):
    """One optimizable parameter, flattened for the C ABI."""
    _fields_ = [
        ("name", ctypes.c_char_p),
        ("value", ctypes.c_float),
        ("min", ctypes.c_float),
        ("max", ctypes.c_float),
        ("type", ctypes.c_int),
        ("categories", ctypes.POINTER(ctypes.c_float)),
        ("category_count", ctypes.c_uint),
    ]


class PyHeliosGeneticAlgorithm(ctypes.Structure):
    """Genetic algorithm settings, with the variant members flattened."""
    _fields_ = [
        ("generations", ctypes.c_size_t),
        ("population_size", ctypes.c_size_t),
        ("crossover_rate", ctypes.c_float),
        ("elitism_rate", ctypes.c_float),
        ("random_seed", ctypes.c_uint),
        ("crossover_kind", ctypes.c_int),
        ("crossover_alpha", ctypes.c_float),
        ("crossover_pca_update_interval", ctypes.c_size_t),
        ("mutation_kind", ctypes.c_int),
        ("mutation_rate", ctypes.c_float),
        ("mutation_pca_update_interval", ctypes.c_size_t),
        ("mutation_sigma_pca", ctypes.c_float),
        ("mutation_gamma_cauchy", ctypes.c_float),
        ("mutation_sigma_random", ctypes.c_float),
        ("mutation_pca_gaussian_prob", ctypes.c_float),
        ("mutation_pca_cauchy_prob", ctypes.c_float),
    ]


class PyHeliosBayesianOptimization(ctypes.Structure):
    """Bayesian optimization settings."""
    _fields_ = [
        ("max_evaluations", ctypes.c_size_t),
        ("initial_samples", ctypes.c_size_t),
        ("ucb_kappa", ctypes.c_float),
        ("max_gp_samples", ctypes.c_size_t),
        ("acquisition_samples", ctypes.c_size_t),
        ("random_seed", ctypes.c_uint),
    ]


class PyHeliosCMAES(ctypes.Structure):
    """CMA-ES settings."""
    _fields_ = [
        ("max_evaluations", ctypes.c_size_t),
        ("lambda_", ctypes.c_size_t),
        ("sigma", ctypes.c_float),
        ("random_seed", ctypes.c_uint),
    ]


class PyHeliosLBFGS(ctypes.Structure):
    """L-BFGS settings."""
    _fields_ = [
        ("max_iterations", ctypes.c_int),
        ("ftol_rel", ctypes.c_double),
        ("xtol_rel", ctypes.c_double),
        ("verify_gradients", ctypes.c_int),
        ("fd_step", ctypes.c_double),
    ]


class PyHeliosAdam(ctypes.Structure):
    """AdamW settings."""
    _fields_ = [
        ("max_iterations", ctypes.c_int),
        ("learning_rate", ctypes.c_float),
        ("beta1", ctypes.c_float),
        ("beta2", ctypes.c_float),
        ("epsilon", ctypes.c_float),
        ("weight_decay", ctypes.c_float),
        ("ftol_rel", ctypes.c_double),
        ("xtol_rel", ctypes.c_double),
    ]


class PyHeliosBOBYQA(ctypes.Structure):
    """BOBYQA settings."""
    _fields_ = [
        ("max_iterations", ctypes.c_int),
        ("ftol_rel", ctypes.c_double),
        ("xtol_rel", ctypes.c_double),
        ("initial_step", ctypes.c_double),
    ]


class PyHeliosSLSQP(ctypes.Structure):
    """SLSQP settings."""
    _fields_ = [
        ("max_iterations", ctypes.c_int),
        ("ftol_rel", ctypes.c_double),
        ("xtol_rel", ctypes.c_double),
    ]


#=============================================================================
# Callback types
#
# CFUNCTYPE, never PYFUNCTYPE or WINFUNCTYPE. CFUNCTYPE acquires the GIL on
# entry (PyGILState_Ensure) and releases it on return, which is exactly what is
# needed when C++ -- running with the GIL released for the duration of the
# foreign call -- re-enters Python. PYFUNCTYPE assumes the GIL is already held
# and would crash if the optimizer ever evaluated candidates off the calling
# thread; WINFUNCTYPE is stdcall and would corrupt the stack.
#=============================================================================

ObjectiveCallback = ctypes.CFUNCTYPE(
    ctypes.c_float,                     # return: objective value
    ctypes.POINTER(ctypes.c_float),     # values, in sorted-name order
    ctypes.c_uint,                      # n
    ctypes.c_void_p,                    # user_data
    ctypes.POINTER(ctypes.c_int),       # error_flag (out)
)

GradientCallback = ctypes.CFUNCTYPE(
    None,
    ctypes.POINTER(ctypes.c_float),     # values, in sorted-name order
    ctypes.c_uint,                      # n
    ctypes.POINTER(ctypes.c_float),     # out_gradient
    ctypes.c_void_p,                    # user_data
    ctypes.POINTER(ctypes.c_int),       # error_flag (out)
)

ConstrainedCallback = ctypes.CFUNCTYPE(
    None,
    ctypes.POINTER(ctypes.c_float),     # values, in sorted-name order
    ctypes.c_uint,                      # n
    ctypes.POINTER(ctypes.c_float),     # out_objective
    ctypes.POINTER(ctypes.c_float),     # out_obj_gradient
    ctypes.POINTER(ctypes.c_float),     # out_constraints
    ctypes.POINTER(ctypes.c_float),     # out_con_gradients, row-major [i * n + j]
    ctypes.c_uint,                      # constraint_count
    ctypes.c_void_p,                    # user_data
    ctypes.POINTER(ctypes.c_int),       # error_flag (out)
)


#=============================================================================
# Function prototypes
#=============================================================================

try:
    helios_lib.createParameterOptimization.argtypes = []
    helios_lib.createParameterOptimization.restype = ctypes.POINTER(UParameterOptimization)
    helios_lib.createParameterOptimization.errcheck = _check_error

    helios_lib.destroyParameterOptimization.argtypes = [ctypes.POINTER(UParameterOptimization)]
    helios_lib.destroyParameterOptimization.restype = None
    # No errcheck: destructors do not fail.

    helios_lib.parameterOptimizationAlgorithmAvailable.argtypes = [ctypes.c_char_p]
    helios_lib.parameterOptimizationAlgorithmAvailable.restype = ctypes.c_int
    # No errcheck: this is a pure query that never sets error state.

    helios_lib.setParameterOptimizationGeneticAlgorithm.argtypes = [
        ctypes.POINTER(UParameterOptimization), ctypes.POINTER(PyHeliosGeneticAlgorithm)]
    helios_lib.setParameterOptimizationGeneticAlgorithm.restype = None
    helios_lib.setParameterOptimizationGeneticAlgorithm.errcheck = _check_error

    helios_lib.setParameterOptimizationBayesian.argtypes = [
        ctypes.POINTER(UParameterOptimization), ctypes.POINTER(PyHeliosBayesianOptimization)]
    helios_lib.setParameterOptimizationBayesian.restype = None
    helios_lib.setParameterOptimizationBayesian.errcheck = _check_error

    helios_lib.setParameterOptimizationCMAES.argtypes = [
        ctypes.POINTER(UParameterOptimization), ctypes.POINTER(PyHeliosCMAES)]
    helios_lib.setParameterOptimizationCMAES.restype = None
    helios_lib.setParameterOptimizationCMAES.errcheck = _check_error

    helios_lib.setParameterOptimizationAdam.argtypes = [
        ctypes.POINTER(UParameterOptimization), ctypes.POINTER(PyHeliosAdam)]
    helios_lib.setParameterOptimizationAdam.restype = None
    helios_lib.setParameterOptimizationAdam.errcheck = _check_error

    helios_lib.setParameterOptimizationLBFGS.argtypes = [
        ctypes.POINTER(UParameterOptimization), ctypes.POINTER(PyHeliosLBFGS)]
    helios_lib.setParameterOptimizationLBFGS.restype = None
    helios_lib.setParameterOptimizationLBFGS.errcheck = _check_error

    helios_lib.setParameterOptimizationBOBYQA.argtypes = [
        ctypes.POINTER(UParameterOptimization), ctypes.POINTER(PyHeliosBOBYQA)]
    helios_lib.setParameterOptimizationBOBYQA.restype = None
    helios_lib.setParameterOptimizationBOBYQA.errcheck = _check_error

    helios_lib.setParameterOptimizationSLSQP.argtypes = [
        ctypes.POINTER(UParameterOptimization), ctypes.POINTER(PyHeliosSLSQP)]
    helios_lib.setParameterOptimizationSLSQP.restype = None
    helios_lib.setParameterOptimizationSLSQP.errcheck = _check_error

    for _name, _struct in (
        ("getParameterOptimizationGADefaults", PyHeliosGeneticAlgorithm),
        ("getParameterOptimizationGAExplore", PyHeliosGeneticAlgorithm),
        ("getParameterOptimizationGAExploit", PyHeliosGeneticAlgorithm),
        ("getParameterOptimizationBayesianDefaults", PyHeliosBayesianOptimization),
        ("getParameterOptimizationBayesianExplore", PyHeliosBayesianOptimization),
        ("getParameterOptimizationBayesianExploit", PyHeliosBayesianOptimization),
        ("getParameterOptimizationCMAESDefaults", PyHeliosCMAES),
        ("getParameterOptimizationCMAESExplore", PyHeliosCMAES),
        ("getParameterOptimizationCMAESExploit", PyHeliosCMAES),
        ("getParameterOptimizationLBFGSDefaults", PyHeliosLBFGS),
        ("getParameterOptimizationAdamDefaults", PyHeliosAdam),
        ("getParameterOptimizationBOBYQADefaults", PyHeliosBOBYQA),
        ("getParameterOptimizationSLSQPDefaults", PyHeliosSLSQP),
    ):
        _fn = getattr(helios_lib, _name)
        _fn.argtypes = [ctypes.POINTER(_struct)]
        _fn.restype = None

    helios_lib.setParameterOptimizationPrintProgress.argtypes = [
        ctypes.POINTER(UParameterOptimization), ctypes.c_int]
    helios_lib.setParameterOptimizationPrintProgress.restype = None
    helios_lib.setParameterOptimizationPrintProgress.errcheck = _check_error

    for _name in ("setParameterOptimizationResultFile",
                  "setParameterOptimizationProgressFile",
                  "setParameterOptimizationInputFile"):
        _fn = getattr(helios_lib, _name)
        _fn.argtypes = [ctypes.POINTER(UParameterOptimization), ctypes.c_char_p]
        _fn.restype = None
        _fn.errcheck = _check_error

    # The run() entry points deliberately do NOT get an errcheck callback. They
    # signal a callback abort by returning PARAMOPT_CALLBACK_FAILED with the
    # native error state left clean, so the wrapper can re-raise the Python
    # exception the user's objective actually raised. An errcheck here would
    # inspect that clean state and mask the real failure.
    helios_lib.runParameterOptimization.argtypes = [
        ctypes.POINTER(UParameterOptimization),
        ctypes.POINTER(PyHeliosParameterSpec),
        ctypes.c_uint,
        ObjectiveCallback,
        ctypes.c_void_p,
        ctypes.POINTER(ctypes.c_float),
        ctypes.POINTER(ctypes.c_float),
    ]
    helios_lib.runParameterOptimization.restype = ctypes.c_int

    helios_lib.runParameterOptimizationWithGradient.argtypes = [
        ctypes.POINTER(UParameterOptimization),
        ctypes.POINTER(PyHeliosParameterSpec),
        ctypes.c_uint,
        ObjectiveCallback,
        GradientCallback,
        ctypes.c_void_p,
        ctypes.POINTER(ctypes.c_float),
        ctypes.POINTER(ctypes.c_float),
    ]
    helios_lib.runParameterOptimizationWithGradient.restype = ctypes.c_int

    helios_lib.runParameterOptimizationWithFDGradient.argtypes = [
        ctypes.POINTER(UParameterOptimization),
        ctypes.POINTER(PyHeliosParameterSpec),
        ctypes.c_uint,
        ObjectiveCallback,
        ctypes.c_float,
        ctypes.c_void_p,
        ctypes.POINTER(ctypes.c_float),
        ctypes.POINTER(ctypes.c_float),
    ]
    helios_lib.runParameterOptimizationWithFDGradient.restype = ctypes.c_int

    helios_lib.runParameterOptimizationConstrained.argtypes = [
        ctypes.POINTER(UParameterOptimization),
        ctypes.POINTER(PyHeliosParameterSpec),
        ctypes.c_uint,
        ConstrainedCallback,
        ctypes.c_uint,
        ctypes.c_void_p,
        ctypes.POINTER(ctypes.c_float),
        ctypes.POINTER(ctypes.c_float),
    ]
    helios_lib.runParameterOptimizationConstrained.restype = ctypes.c_int

    _PARAMETEROPTIMIZATION_FUNCTIONS_AVAILABLE = True

except AttributeError:
    _PARAMETEROPTIMIZATION_FUNCTIONS_AVAILABLE = False


def isParameterOptimizationAvailable() -> bool:
    """Check if ParameterOptimization functions are available in this build"""
    return _PARAMETEROPTIMIZATION_FUNCTIONS_AVAILABLE


def _require_available() -> None:
    """Raise an actionable error if the plugin was not built into the library."""
    if not _PARAMETEROPTIMIZATION_FUNCTIONS_AVAILABLE:
        raise NotImplementedError(
            "ParameterOptimization functions not available in current Helios library. "
            "Rebuild PyHelios with the parameteroptimization plugin enabled:\n"
            "  build_scripts/build_helios --clean"
        )


#=============================================================================
# Callback plumbing
#=============================================================================

class _CallbackState:
    """
    Carries a Python exception raised inside a callback back to the caller.

    A Python exception cannot propagate through the intervening C++ frames.
    Worse, ctypes does not even let it escape the callback: it prints the
    traceback via PyErr_WriteUnraisable and returns 0 to C++, and 0 is a
    perfectly plausible objective value, so the optimizer would carry on and
    return a confidently wrong answer.

    Instead the trampoline catches everything, stores it here, and raises the
    error flag. The native side unwinds and returns PARAMOPT_CALLBACK_FAILED,
    and the caller re-raises the stored exception with its original traceback.
    """

    __slots__ = ("exception",)

    def __init__(self):
        self.exception: Optional[Tuple] = None


def _make_objective_trampoline(objective: Callable[[Dict[str, float]], float],
                               names: Sequence[str],
                               state: _CallbackState) -> "ctypes._CFuncPtr":
    """Wrap a Python objective as a C callback."""

    def _impl(values_ptr, n, user_data, error_flag_ptr):
        # Once a failure has been recorded, do not re-enter user code: NLopt may
        # call back a further time or two before it observes its stop flag.
        if state.exception is not None:
            error_flag_ptr[0] = 1
            return 0.0
        try:
            params = {names[i]: values_ptr[i] for i in range(n)}
            # Coerce inside the try so a non-numeric return surfaces as the
            # user's own TypeError rather than a ctypes conversion failure.
            result = float(objective(params))
            if not math.isfinite(result):
                raise ValueError(
                    f"Objective function returned {result}, which is not a finite number. "
                    f"Non-finite objective values corrupt the optimizer's internal state "
                    f"without raising an error, so they are rejected here."
                )
            return result
        except BaseException:
            # BaseException, not Exception: a KeyboardInterrupt during a long
            # run must abort the optimization rather than be swallowed by ctypes.
            state.exception = sys.exc_info()
            error_flag_ptr[0] = 1
            return 0.0

    return ObjectiveCallback(_impl)


def _make_gradient_trampoline(gradient: Callable[[Dict[str, float]], Dict[str, float]],
                              names: Sequence[str],
                              state: _CallbackState) -> "ctypes._CFuncPtr":
    """Wrap a Python gradient function as a C callback."""

    def _impl(values_ptr, n, out_gradient_ptr, user_data, error_flag_ptr):
        if state.exception is not None:
            error_flag_ptr[0] = 1
            return
        try:
            params = {names[i]: values_ptr[i] for i in range(n)}
            result = gradient(params)

            if not isinstance(result, dict):
                raise TypeError(
                    f"Gradient function must return a dict mapping parameter name to "
                    f"partial derivative, got {type(result).__name__}"
                )

            # Checked here rather than left to C++ so the message names the
            # offending parameters and the traceback points at the user's own
            # gradient function.
            missing = set(names) - set(result)
            if missing:
                raise ValueError(
                    f"Gradient function omitted parameter(s) {sorted(missing)}. "
                    f"It must return a partial derivative for every parameter: {sorted(names)}"
                )
            extra = set(result) - set(names)
            if extra:
                raise ValueError(
                    f"Gradient function returned unknown parameter(s) {sorted(extra)}. "
                    f"Expected exactly: {sorted(names)}"
                )

            for i, name in enumerate(names):
                value = float(result[name])
                if not math.isfinite(value):
                    raise ValueError(
                        f"Gradient for parameter '{name}' is {value}, which is not a finite number."
                    )
                out_gradient_ptr[i] = value

        except BaseException:
            state.exception = sys.exc_info()
            error_flag_ptr[0] = 1

    return GradientCallback(_impl)


def _write_gradient_dict(result, names: Sequence[str], out_ptr, offset: int, label: str) -> None:
    """
    Validate a {name: partial derivative} mapping and write it out positionally.

    Shared by the objective and every constraint of a constrained simulation, so
    all of them report a missing or unknown parameter the same way. `offset` is the
    starting index in a flat row-major buffer.
    """
    if not isinstance(result, dict):
        raise TypeError(
            f"{label} must be a dict mapping parameter name to partial derivative, "
            f"got {type(result).__name__}"
        )

    missing = set(names) - set(result)
    if missing:
        raise ValueError(
            f"{label} omitted parameter(s) {sorted(missing)}. "
            f"It must return a partial derivative for every parameter: {sorted(names)}"
        )
    extra = set(result) - set(names)
    if extra:
        raise ValueError(
            f"{label} returned unknown parameter(s) {sorted(extra)}. "
            f"Expected exactly: {sorted(names)}"
        )

    for i, name in enumerate(names):
        value = float(result[name])
        if not math.isfinite(value):
            raise ValueError(
                f"{label} for parameter '{name}' is {value}, which is not a finite number."
            )
        out_ptr[offset + i] = value


def _make_constrained_trampoline(simulation: Callable[[Dict[str, float]], object],
                                 names: Sequence[str],
                                 constraint_count: int,
                                 state: _CallbackState) -> "ctypes._CFuncPtr":
    """Wrap a Python constrained simulation as a C callback."""

    def _impl(values_ptr, n, out_objective_ptr, out_obj_gradient_ptr,
              out_constraints_ptr, out_con_gradients_ptr, n_constraints,
              user_data, error_flag_ptr):
        if state.exception is not None:
            error_flag_ptr[0] = 1
            return
        try:
            params = {names[i]: values_ptr[i] for i in range(n)}
            result = simulation(params)

            for attribute in ("objective", "objective_gradient",
                              "constraints", "constraint_gradients"):
                if not hasattr(result, attribute):
                    raise TypeError(
                        f"Constrained simulation must return a ConstrainedResult; got "
                        f"{type(result).__name__}, which has no '{attribute}' attribute."
                    )

            objective = float(result.objective)
            if not math.isfinite(objective):
                raise ValueError(
                    f"Constrained simulation returned objective {objective}, which is not a "
                    f"finite number. Non-finite values corrupt the optimizer's internal "
                    f"state without raising an error, so they are rejected here."
                )
            out_objective_ptr[0] = objective

            _write_gradient_dict(result.objective_gradient, names,
                                 out_obj_gradient_ptr, 0, "Objective gradient")

            constraints = list(result.constraints)
            if len(constraints) != n_constraints:
                raise ValueError(
                    f"Constrained simulation returned {len(constraints)} constraint value(s) "
                    f"but constraint_count={n_constraints} was declared. The count is fixed "
                    f"for the whole run and must not vary between evaluations."
                )
            gradients = list(result.constraint_gradients)
            if len(gradients) != n_constraints:
                raise ValueError(
                    f"Constrained simulation returned {len(gradients)} constraint gradient(s) "
                    f"but {n_constraints} constraint value(s). Every constraint needs exactly "
                    f"one gradient."
                )

            for i, value in enumerate(constraints):
                value = float(value)
                if not math.isfinite(value):
                    raise ValueError(
                        f"Constraint {i} is {value}, which is not a finite number."
                    )
                out_constraints_ptr[i] = value

            # Row-major, matching the C ABI: constraint i, parameter j at [i * n + j].
            for i, gradient in enumerate(gradients):
                _write_gradient_dict(gradient, names, out_con_gradients_ptr,
                                     i * len(names), f"Gradient of constraint {i}")

        except BaseException:
            state.exception = sys.exc_info()
            error_flag_ptr[0] = 1

    return ConstrainedCallback(_impl)


def _reraise(state: _CallbackState) -> None:
    """Re-raise the exception a callback stashed, preserving its traceback."""
    exc_info = state.exception
    state.exception = None
    if exc_info is None:
        # The native side reported a callback abort but nothing was recorded.
        # Surfacing this rather than returning a bogus result keeps the failure
        # visible instead of silently producing an unoptimized answer.
        raise RuntimeError(
            "ParameterOptimization reported a callback failure but no Python exception "
            "was recorded. This indicates an internal inconsistency in the callback bridge."
        )
    _, exc_value, exc_traceback = exc_info
    raise exc_value.with_traceback(exc_traceback)


def _build_parameter_array(parameters: List[dict]) -> Tuple[ctypes.Array, list]:
    """
    Build the C parameter array.

    Returns the array along with a keepalive list holding every buffer the array
    points into. The array stores borrowed pointers, so those buffers must
    outlive the native call -- see the keepalive note in the run functions.
    """
    count = len(parameters)
    array = (PyHeliosParameterSpec * count)()
    keepalive: list = []

    for i, spec in enumerate(parameters):
        encoded_name = spec["name"].encode("utf-8")
        keepalive.append(encoded_name)

        array[i].name = encoded_name
        array[i].value = spec["value"]
        array[i].min = spec["min"]
        array[i].max = spec["max"]
        array[i].type = spec["type"]

        categories = spec.get("categories") or ()
        if categories:
            category_array = (ctypes.c_float * len(categories))(*categories)
            keepalive.append(category_array)
            array[i].categories = category_array
            array[i].category_count = len(categories)
        else:
            array[i].categories = None
            array[i].category_count = 0

    keepalive.append(array)
    return array, keepalive


#=============================================================================
# Lifecycle
#=============================================================================

def createParameterOptimization():
    """Create a ParameterOptimization instance."""
    _require_available()
    return helios_lib.createParameterOptimization()


def destroyParameterOptimization(opt) -> None:
    """Destroy a ParameterOptimization instance."""
    if opt and _PARAMETEROPTIMIZATION_FUNCTIONS_AVAILABLE:
        helios_lib.destroyParameterOptimization(opt)


def isAlgorithmAvailable(algorithm_name: str) -> bool:
    """
    Check whether an algorithm can run in this build.

    L-BFGS, BOBYQA and SLSQP depend on NLopt, and L-BFGS additionally on the
    LGPL Luksan solvers that implement it.

    Args:
        algorithm_name: One of "GA", "BO", "CMAES", "LBFGS", "ADAM", "BOBYQA", "SLSQP"
    """
    if not _PARAMETEROPTIMIZATION_FUNCTIONS_AVAILABLE:
        return False
    return bool(helios_lib.parameterOptimizationAlgorithmAvailable(algorithm_name.encode("utf-8")))


#=============================================================================
# Algorithm selection
#=============================================================================

def setGeneticAlgorithm(opt, settings: PyHeliosGeneticAlgorithm) -> None:
    """Select the genetic algorithm."""
    _require_available()
    helios_lib.setParameterOptimizationGeneticAlgorithm(opt, ctypes.byref(settings))


def setBayesianOptimization(opt, settings: PyHeliosBayesianOptimization) -> None:
    """Select Bayesian optimization."""
    _require_available()
    helios_lib.setParameterOptimizationBayesian(opt, ctypes.byref(settings))


def setCMAES(opt, settings: PyHeliosCMAES) -> None:
    """Select CMA-ES."""
    _require_available()
    helios_lib.setParameterOptimizationCMAES(opt, ctypes.byref(settings))


def setAdam(opt, settings: PyHeliosAdam) -> None:
    """Select AdamW."""
    _require_available()
    helios_lib.setParameterOptimizationAdam(opt, ctypes.byref(settings))


def setLBFGS(opt, settings: PyHeliosLBFGS) -> None:
    """Select L-BFGS."""
    _require_available()
    helios_lib.setParameterOptimizationLBFGS(opt, ctypes.byref(settings))


def setBOBYQA(opt, settings: PyHeliosBOBYQA) -> None:
    """Select BOBYQA."""
    _require_available()
    helios_lib.setParameterOptimizationBOBYQA(opt, ctypes.byref(settings))


def setSLSQP(opt, settings: PyHeliosSLSQP) -> None:
    """Select SLSQP."""
    _require_available()
    helios_lib.setParameterOptimizationSLSQP(opt, ctypes.byref(settings))


#=============================================================================
# Preset settings
#=============================================================================

def _fetch_preset(function_name: str, struct_type):
    """Read a settings preset from the native library."""
    _require_available()
    settings = struct_type()
    getattr(helios_lib, function_name)(ctypes.byref(settings))
    return settings


def getGeneticAlgorithmDefaults() -> PyHeliosGeneticAlgorithm:
    """Get the plugin's default genetic algorithm settings."""
    return _fetch_preset("getParameterOptimizationGADefaults", PyHeliosGeneticAlgorithm)


def getGeneticAlgorithmExplore() -> PyHeliosGeneticAlgorithm:
    """Get the exploration-biased genetic algorithm preset."""
    return _fetch_preset("getParameterOptimizationGAExplore", PyHeliosGeneticAlgorithm)


def getGeneticAlgorithmExploit() -> PyHeliosGeneticAlgorithm:
    """Get the exploitation-biased genetic algorithm preset."""
    return _fetch_preset("getParameterOptimizationGAExploit", PyHeliosGeneticAlgorithm)


def getBayesianDefaults() -> PyHeliosBayesianOptimization:
    """Get the plugin's default Bayesian optimization settings."""
    return _fetch_preset("getParameterOptimizationBayesianDefaults", PyHeliosBayesianOptimization)


def getBayesianExplore() -> PyHeliosBayesianOptimization:
    """Get the exploration-biased Bayesian optimization preset."""
    return _fetch_preset("getParameterOptimizationBayesianExplore", PyHeliosBayesianOptimization)


def getBayesianExploit() -> PyHeliosBayesianOptimization:
    """Get the exploitation-biased Bayesian optimization preset."""
    return _fetch_preset("getParameterOptimizationBayesianExploit", PyHeliosBayesianOptimization)


def getCMAESDefaults() -> PyHeliosCMAES:
    """Get the plugin's default CMA-ES settings."""
    return _fetch_preset("getParameterOptimizationCMAESDefaults", PyHeliosCMAES)


def getCMAESExplore() -> PyHeliosCMAES:
    """Get the exploration-biased CMA-ES preset."""
    return _fetch_preset("getParameterOptimizationCMAESExplore", PyHeliosCMAES)


def getCMAESExploit() -> PyHeliosCMAES:
    """Get the exploitation-biased CMA-ES preset."""
    return _fetch_preset("getParameterOptimizationCMAESExploit", PyHeliosCMAES)


def getLBFGSDefaults() -> PyHeliosLBFGS:
    """Get the plugin's default L-BFGS settings."""
    return _fetch_preset("getParameterOptimizationLBFGSDefaults", PyHeliosLBFGS)


def getAdamDefaults() -> PyHeliosAdam:
    """Get the plugin's default Adam settings."""
    return _fetch_preset("getParameterOptimizationAdamDefaults", PyHeliosAdam)


def getBOBYQADefaults() -> PyHeliosBOBYQA:
    """Get the plugin's default BOBYQA settings."""
    return _fetch_preset("getParameterOptimizationBOBYQADefaults", PyHeliosBOBYQA)


def getSLSQPDefaults() -> PyHeliosSLSQP:
    """Get the plugin's default SLSQP settings."""
    return _fetch_preset("getParameterOptimizationSLSQPDefaults", PyHeliosSLSQP)


#=============================================================================
# I/O configuration
#=============================================================================

def setPrintProgress(opt, enable: bool) -> None:
    """Enable or disable the plugin's progress printout."""
    _require_available()
    helios_lib.setParameterOptimizationPrintProgress(opt, 1 if enable else 0)


def setResultFile(opt, path: Optional[str]) -> None:
    """Set the file the final result is written to (.csv or .txt)."""
    _require_available()
    helios_lib.setParameterOptimizationResultFile(opt, path.encode("utf-8") if path else None)


def setProgressFile(opt, path: Optional[str]) -> None:
    """Set the file per-generation progress is written to (.csv or .txt)."""
    _require_available()
    helios_lib.setParameterOptimizationProgressFile(opt, path.encode("utf-8") if path else None)


def setInputFile(opt, path: Optional[str]) -> None:
    """Set a file to read the initial parameter set from."""
    _require_available()
    helios_lib.setParameterOptimizationInputFile(opt, path.encode("utf-8") if path else None)


#=============================================================================
# Run
#=============================================================================

def _finish_run(rc: int, state: _CallbackState, names: Sequence[str],
                out_values: ctypes.Array, out_fitness: ctypes.c_float) -> Tuple[Dict[str, float], float]:
    """Translate a native return code into a result or an exception."""
    if rc == PARAMOPT_CALLBACK_FAILED:
        _reraise(state)
    if rc != PARAMOPT_OK:
        # Surfaces the C++ message as the appropriate HeliosError subclass.
        check_helios_error(helios_lib.getLastErrorCode, helios_lib.getLastErrorMessage,
                           helios_lib.clearError)
        raise RuntimeError("ParameterOptimization run failed without reporting an error message.")

    values = {name: out_values[i] for i, name in enumerate(names)}
    return values, out_fitness.value


def runOptimization(opt, parameters: List[dict],
                    objective: Callable[[Dict[str, float]], float]) -> Tuple[Dict[str, float], float]:
    """
    Run a derivative-free optimization.

    Args:
        opt: ParameterOptimization instance pointer
        parameters: Parameter specs as dicts with keys name/value/min/max/type/categories
        objective: Callable receiving {name: value} and returning a scalar cost

    Returns:
        Tuple of ({name: optimized value}, fitness)
    """
    _require_available()
    if not parameters:
        raise ValueError("Parameter list cannot be empty")

    # The native side orders everything by a lexicographic sort of the names.
    names = sorted(spec["name"] for spec in parameters)
    array, keepalive = _build_parameter_array(parameters)

    state = _CallbackState()
    # Bound to a local, never passed inline: the CFUNCTYPE object owns the
    # trampoline's executable thunk, and if the only reference were a temporary
    # it could be collected while C++ still holds the pointer.
    objective_cb = _make_objective_trampoline(objective, names, state)

    out_values = (ctypes.c_float * len(names))()
    out_fitness = ctypes.c_float()

    rc = helios_lib.runParameterOptimization(
        opt, array, len(parameters), objective_cb, None,
        out_values, ctypes.byref(out_fitness))

    # Referenced after the call so nothing above can be collected early.
    del keepalive, objective_cb

    return _finish_run(rc, state, names, out_values, out_fitness)


def runOptimizationWithGradient(opt, parameters: List[dict],
                                objective: Callable[[Dict[str, float]], float],
                                gradient: Callable[[Dict[str, float]], Dict[str, float]]
                                ) -> Tuple[Dict[str, float], float]:
    """
    Run an optimization with a user-supplied gradient.

    Args:
        opt: ParameterOptimization instance pointer
        parameters: Parameter specs as dicts
        objective: Callable receiving {name: value} and returning a scalar cost
        gradient: Callable receiving {name: value} and returning {name: partial derivative}

    Returns:
        Tuple of ({name: optimized value}, fitness)
    """
    _require_available()
    if not parameters:
        raise ValueError("Parameter list cannot be empty")

    names = sorted(spec["name"] for spec in parameters)
    array, keepalive = _build_parameter_array(parameters)

    state = _CallbackState()
    objective_cb = _make_objective_trampoline(objective, names, state)
    gradient_cb = _make_gradient_trampoline(gradient, names, state)

    out_values = (ctypes.c_float * len(names))()
    out_fitness = ctypes.c_float()

    rc = helios_lib.runParameterOptimizationWithGradient(
        opt, array, len(parameters), objective_cb, gradient_cb, None,
        out_values, ctypes.byref(out_fitness))

    del keepalive, objective_cb, gradient_cb

    return _finish_run(rc, state, names, out_values, out_fitness)


def runOptimizationWithFDGradient(opt, parameters: List[dict],
                                  objective: Callable[[Dict[str, float]], float],
                                  fd_step: float = 0.0) -> Tuple[Dict[str, float], float]:
    """
    Run an optimization with gradients estimated by finite differences.

    Args:
        opt: ParameterOptimization instance pointer
        parameters: Parameter specs as dicts
        objective: Callable receiving {name: value} and returning a scalar cost
        fd_step: Relative perturbation factor; values <= 0 select the plugin default

    Returns:
        Tuple of ({name: optimized value}, fitness)
    """
    _require_available()
    if not parameters:
        raise ValueError("Parameter list cannot be empty")

    names = sorted(spec["name"] for spec in parameters)
    array, keepalive = _build_parameter_array(parameters)

    state = _CallbackState()
    objective_cb = _make_objective_trampoline(objective, names, state)

    out_values = (ctypes.c_float * len(names))()
    out_fitness = ctypes.c_float()

    rc = helios_lib.runParameterOptimizationWithFDGradient(
        opt, array, len(parameters), objective_cb, fd_step, None,
        out_values, ctypes.byref(out_fitness))

    del keepalive, objective_cb

    return _finish_run(rc, state, names, out_values, out_fitness)


def runOptimizationConstrained(opt, parameters: List[dict],
                               simulation: Callable[[Dict[str, float]], object],
                               constraint_count: int) -> Tuple[Dict[str, float], float]:
    """
    Run a constrained optimization: minimize f(x) subject to c_i(x) <= 0.

    Requires SLSQP, enforced by the plugin.

    Args:
        opt: ParameterOptimization instance pointer
        parameters: Parameter specs as dicts
        simulation: Callable receiving {name: value} and returning a ConstrainedResult
        constraint_count: Number of constraints; fixed for the whole run

    Returns:
        Tuple of ({name: optimized value}, fitness)
    """
    _require_available()
    if not parameters:
        raise ValueError("Parameter list cannot be empty")
    if constraint_count < 1:
        raise ValueError(
            f"constraint_count must be at least 1, got {constraint_count}. "
            f"Use runOptimization() or runOptimizationWithGradient() when there are "
            f"no constraints.")

    names = sorted(spec["name"] for spec in parameters)
    array, keepalive = _build_parameter_array(parameters)

    state = _CallbackState()
    simulation_cb = _make_constrained_trampoline(simulation, names, constraint_count, state)

    out_values = (ctypes.c_float * len(names))()
    out_fitness = ctypes.c_float()

    rc = helios_lib.runParameterOptimizationConstrained(
        opt, array, len(parameters), simulation_cb, constraint_count, None,
        out_values, ctypes.byref(out_fitness))

    del keepalive, simulation_cb

    return _finish_run(rc, state, names, out_values, out_fitness)


# Mock mode functions for development
if not _PARAMETEROPTIMIZATION_FUNCTIONS_AVAILABLE:
    def mock_createParameterOptimization(*args, **kwargs):
        raise RuntimeError(
            "Mock mode: ParameterOptimization not available. "
            "This would create a parameter optimization instance with native library."
        )

    def mock_runParameterOptimization(*args, **kwargs):
        raise RuntimeError(
            "Mock mode: ParameterOptimization methods not available. "
            "This would run an optimization with native library."
        )

    # Replace functions with mocks for development
    createParameterOptimization = mock_createParameterOptimization
    runOptimization = mock_runParameterOptimization
    runOptimizationWithGradient = mock_runParameterOptimization
    runOptimizationWithFDGradient = mock_runParameterOptimization
    runOptimizationConstrained = mock_runParameterOptimization
