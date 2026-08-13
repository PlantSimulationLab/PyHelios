"""
Tests for ParameterOptimization functionality in PyHelios.

This module tests the ParameterOptimization class, which calibrates named model
parameters against a user-supplied objective function. Tests are designed to work
in both native and mock modes.

The objective is a Python callable invoked from C++, which is unique among
PyHelios plugins. Several tests below target that bridge specifically: name
ordering across the flat-array ABI, exception propagation back through C++
frames, and callback object lifetime under garbage collection.
"""

import gc
import math
import os
import sys

import pytest

# Add pyhelios to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from pyhelios import (
    ParameterOptimization, ParameterOptimizationError, OptimizationResult,
    ConstrainedResult, make_constrained_simulation,
    Parameter, ParameterType,
    GeneticAlgorithm, BayesianOptimization, CMAES, Adam, BOBYQA, LBFGS, SLSQP,
    BLXAlphaCrossover, BLXPCACrossover,
    PerGeneMutation, IsotropicMutation, HybridMutation,
)
from pyhelios.exceptions import HeliosError
from pyhelios.plugins.registry import get_plugin_registry


# The canonical test problem: a quadratic bowl with its minimum at (3, -1).
QUADRATIC_MINIMUM = {"x": 3.0, "y": -1.0}


def quadratic(params):
    """Objective with a known minimum of 0 at x=3, y=-1."""
    return (params["x"] - 3.0) ** 2 + (params["y"] + 1.0) ** 2


def quadratic_gradient(params):
    """Analytic gradient of ``quadratic``."""
    return {
        "x": 2.0 * (params["x"] - 3.0),
        "y": 2.0 * (params["y"] + 1.0),
    }


def quadratic_parameters():
    """Fresh parameter set for the quadratic problem."""
    return {
        "x": Parameter.continuous(0.0, -5.0, 5.0),
        "y": Parameter.continuous(0.0, -5.0, 5.0),
    }


@pytest.fixture
def optimizer():
    """Provide a ParameterOptimization instance with proper cleanup."""
    if not get_plugin_registry().is_plugin_available('parameteroptimization'):
        pytest.skip("parameteroptimization plugin not available")

    instance = ParameterOptimization()
    yield instance
    instance.__exit__(None, None, None)


class TestParameterOptimizationMetadata:
    """Test plugin metadata and registration."""

    @pytest.mark.cross_platform
    def test_plugin_metadata_exists(self):
        """Plugin metadata is registered and well-formed."""
        from pyhelios.config.plugin_metadata import get_plugin_metadata

        metadata = get_plugin_metadata('parameteroptimization')
        assert metadata is not None
        assert metadata.name == 'parameteroptimization'
        assert metadata.description
        assert metadata.test_symbols
        assert 'createParameterOptimization' in metadata.test_symbols
        assert isinstance(metadata.platforms, list)
        assert len(metadata.platforms) > 0
        assert metadata.gpu_required is False

    @pytest.mark.cross_platform
    def test_plugin_in_registry(self):
        """Plugin appears in the metadata registry."""
        from pyhelios.config.plugin_metadata import PLUGIN_METADATA
        assert 'parameteroptimization' in PLUGIN_METADATA

    @pytest.mark.cross_platform
    def test_plugin_in_integrated_list(self):
        """Plugin is part of the default build."""
        build_script = os.path.join(
            os.path.dirname(__file__), '..', 'build_scripts', 'build_helios.py')
        if not os.path.exists(build_script):
            # Wheel test environments copy only tests/ into an isolated directory,
            # so the build script this asserts on is not present.
            pytest.skip("Build script not available in wheel testing environment "
                        "(build_scripts/build_helios.py not found)")
        with open(build_script) as handle:
            source = handle.read()
        integrated = source.split('INTEGRATED_PLUGINS = [')[1].split(']')[0]
        assert 'parameteroptimization' in integrated


class TestParameterOptimizationInterface:
    """Test the interface without requiring the native library."""

    @pytest.mark.cross_platform
    def test_class_structure(self):
        """The class exposes the expected lifecycle and API."""
        for attribute in ('__init__', '__enter__', '__exit__', '__del__',
                          'run', 'setAlgorithm', 'availableAlgorithms',
                          'setPrintProgress', 'setResultFile', 'setProgressFile',
                          'setInputFile', 'is_available', 'getNativePtr'):
            assert hasattr(ParameterOptimization, attribute), f"missing {attribute}"

    @pytest.mark.cross_platform
    def test_error_type_is_helios_error(self):
        """The plugin error type integrates with the PyHelios hierarchy."""
        assert issubclass(ParameterOptimizationError, HeliosError)

    @pytest.mark.cross_platform
    def test_parameter_constructors(self):
        """Parameter convenience constructors set the right type."""
        continuous = Parameter.continuous(1.0, 0.0, 5.0)
        assert continuous.type == ParameterType.FLOAT
        assert continuous.value == 1.0 and continuous.min == 0.0 and continuous.max == 5.0

        integer = Parameter.integer(2.0, 0.0, 10.0)
        assert integer.type == ParameterType.INTEGER

        categorical = Parameter.categorical(0.5, [0.5, 1.5, 2.5])
        assert categorical.type == ParameterType.CATEGORICAL
        assert categorical.categories == (0.5, 1.5, 2.5)

    @pytest.mark.cross_platform
    def test_optimization_result_accessors(self):
        """OptimizationResult exposes values by property and by subscript."""
        result = OptimizationResult(
            parameters={"a": Parameter.continuous(1.5, 0.0, 2.0)}, fitness=0.25)
        assert result.fitness == 0.25
        assert result.values == {"a": 1.5}
        assert result["a"] == 1.5

    @pytest.mark.cross_platform
    def test_graceful_unavailable_handling(self):
        """An unavailable plugin produces an actionable error."""
        if get_plugin_registry().is_plugin_available('parameteroptimization'):
            pytest.skip("plugin is available - this test covers the unavailable case")

        with pytest.raises(ParameterOptimizationError) as excinfo:
            ParameterOptimization()

        message = str(excinfo.value).lower()
        assert any(keyword in message for keyword in ('rebuild', 'build', 'enable'))


class TestStructureLayout:
    """
    Test the ctypes mirrors against the C structs they shadow.

    A mismatched layout is the worst failure mode available here: fields would
    be read from the wrong offsets and the optimization would run to completion
    on corrupted hyperparameters without raising anything. The int-then-double
    structs are the risky ones, since they rely on the compiler's padding.
    """

    @pytest.mark.cross_platform
    def test_structure_sizes(self):
        """Mirror sizes match the C structs on this platform's ABI."""
        import ctypes
        from pyhelios.wrappers import UParameterOptimizationWrapper as wrapper

        # Verified against sizeof() of the C structs in
        # native/include/pyhelios_wrapper_parameteroptimization.h
        expected = {
            wrapper.PyHeliosParameterSpec: 40,
            wrapper.PyHeliosGeneticAlgorithm: 88,
            wrapper.PyHeliosBayesianOptimization: 48,
            wrapper.PyHeliosCMAES: 24,
            wrapper.PyHeliosLBFGS: 40,
            wrapper.PyHeliosAdam: 40,
            wrapper.PyHeliosBOBYQA: 32,
            wrapper.PyHeliosSLSQP: 24,
        }
        for structure, size in expected.items():
            assert ctypes.sizeof(structure) == size, (
                f"{structure.__name__} is {ctypes.sizeof(structure)} bytes, expected {size}")

    @pytest.mark.cross_platform
    def test_padded_structure_offsets(self):
        """
        Fields following a smaller type sit at their padded offsets.

        These are the layouts a stray _pack_ = 1 would silently break.
        """
        from pyhelios.wrappers import UParameterOptimizationWrapper as wrapper

        assert wrapper.PyHeliosLBFGS.ftol_rel.offset == 8
        assert wrapper.PyHeliosLBFGS.verify_gradients.offset == 24
        assert wrapper.PyHeliosLBFGS.fd_step.offset == 32
        assert wrapper.PyHeliosAdam.ftol_rel.offset == 24
        assert wrapper.PyHeliosBOBYQA.initial_step.offset == 24
        assert wrapper.PyHeliosParameterSpec.categories.offset == 24
        assert wrapper.PyHeliosGeneticAlgorithm.mutation_kind.offset == 48

    @pytest.mark.cross_platform
    def test_no_packing_applied(self):
        """No mirror forces a packed layout."""
        from pyhelios.wrappers import UParameterOptimizationWrapper as wrapper

        for name in ('PyHeliosParameterSpec', 'PyHeliosGeneticAlgorithm',
                     'PyHeliosLBFGS', 'PyHeliosAdam', 'PyHeliosBOBYQA'):
            structure = getattr(wrapper, name)
            assert getattr(structure, '_pack_', 0) == 0, (
                f"{name} sets _pack_, which would misalign it against the C struct")


@pytest.mark.native_only
class TestSettingsRoundTrip:
    """Test that hyperparameters survive the trip into C++ and back."""

    def test_genetic_algorithm_fields_round_trip(self):
        """A GA settings struct reads back with the values written to it."""
        settings = GeneticAlgorithm(
            generations=123, population_size=45, crossover_rate=0.75,
            elitism_rate=0.15, random_seed=99,
            crossover=BLXPCACrossover(alpha=0.33, pca_update_interval=7),
            mutation=HybridMutation(rate=0.22, sigma_pca=0.44))

        struct = settings._to_struct()

        assert struct.generations == 123
        assert struct.population_size == 45
        assert struct.crossover_rate == pytest.approx(0.75)
        assert struct.elitism_rate == pytest.approx(0.15)
        assert struct.random_seed == 99
        assert struct.crossover_alpha == pytest.approx(0.33)
        assert struct.crossover_pca_update_interval == 7
        assert struct.mutation_rate == pytest.approx(0.22)
        assert struct.mutation_sigma_pca == pytest.approx(0.44)

    def test_padded_settings_fields_round_trip(self):
        """
        The int-then-double structs carry every field intact.

        A layout mismatch would show up here as a garbage double.
        """
        adam = Adam(max_iterations=321, learning_rate=0.075, beta1=0.85,
                    beta2=0.995, epsilon=1e-7, weight_decay=0.01,
                    ftol_rel=1e-9, xtol_rel=1e-10)._to_struct()
        assert adam.max_iterations == 321
        assert adam.learning_rate == pytest.approx(0.075)
        assert adam.beta1 == pytest.approx(0.85)
        assert adam.weight_decay == pytest.approx(0.01)
        assert adam.ftol_rel == pytest.approx(1e-9)
        assert adam.xtol_rel == pytest.approx(1e-10)

        bobyqa = BOBYQA(max_iterations=77, ftol_rel=1e-8,
                        xtol_rel=1e-9, initial_step=0.25)._to_struct()
        assert bobyqa.max_iterations == 77
        assert bobyqa.ftol_rel == pytest.approx(1e-8)
        assert bobyqa.initial_step == pytest.approx(0.25)

        lbfgs = LBFGS(max_iterations=55, ftol_rel=1e-7, xtol_rel=1e-8,
                      verify_gradients=True, fd_step=1e-4)._to_struct()
        assert lbfgs.max_iterations == 55
        assert lbfgs.ftol_rel == pytest.approx(1e-7)
        assert lbfgs.verify_gradients == 1
        assert lbfgs.fd_step == pytest.approx(1e-4)

    def test_seed_produces_reproducible_results(self, optimizer):
        """
        A fixed seed gives identical results across runs.

        This is end-to-end evidence that random_seed reaches the C++ struct
        field it is supposed to, rather than landing on a neighbouring one.
        """
        optimizer.setAlgorithm(GeneticAlgorithm(generations=20, population_size=15,
                                                random_seed=12345))
        first = optimizer.run(quadratic, quadratic_parameters())

        optimizer.setAlgorithm(GeneticAlgorithm(generations=20, population_size=15,
                                                random_seed=12345))
        second = optimizer.run(quadratic, quadratic_parameters())

        assert first.fitness == pytest.approx(second.fitness, rel=1e-9)
        assert first["x"] == pytest.approx(second["x"], rel=1e-9)

    def test_different_seeds_differ(self, optimizer):
        """Different seeds explore differently."""
        optimizer.setAlgorithm(GeneticAlgorithm(generations=15, population_size=10,
                                                random_seed=1))
        first = optimizer.run(quadratic, quadratic_parameters())

        optimizer.setAlgorithm(GeneticAlgorithm(generations=15, population_size=10,
                                                random_seed=2))
        second = optimizer.run(quadratic, quadratic_parameters())

        assert first["x"] != second["x"] or first["y"] != second["y"]


@pytest.mark.native_only
class TestParameterOptimizationLifecycle:
    """Test creation and cleanup with the native library."""

    def test_create_and_destroy(self, optimizer):
        """An instance can be created and reports a native pointer."""
        assert optimizer is not None
        assert optimizer.getNativePtr() is not None

    def test_context_manager(self):
        """The context manager releases the native instance on exit."""
        if not get_plugin_registry().is_plugin_available('parameteroptimization'):
            pytest.skip("parameteroptimization plugin not available")

        with ParameterOptimization() as opt:
            assert opt.getNativePtr() is not None
        assert opt.getNativePtr() is None

    def test_use_after_destroy_raises(self):
        """Using a destroyed instance raises rather than crashing."""
        if not get_plugin_registry().is_plugin_available('parameteroptimization'):
            pytest.skip("parameteroptimization plugin not available")

        opt = ParameterOptimization()
        opt.__exit__(None, None, None)

        with pytest.raises(ParameterOptimizationError, match="destroyed"):
            opt.run(quadratic, quadratic_parameters())

    def test_cleanup_without_with_statement(self):
        """__del__ frees the native instance when no context manager is used."""
        if not get_plugin_registry().is_plugin_available('parameteroptimization'):
            pytest.skip("parameteroptimization plugin not available")

        opt = ParameterOptimization()
        assert opt.getNativePtr() is not None

        # Must not warn or crash when the garbage collector runs the destructor.
        del opt
        gc.collect()


@pytest.mark.native_only
class TestParameterOptimizationConvergence:
    """Test that each algorithm actually finds the known optimum."""

    def _assert_converged(self, result, tolerance=0.1):
        assert isinstance(result, OptimizationResult)
        assert result.fitness < tolerance
        assert result["x"] == pytest.approx(QUADRATIC_MINIMUM["x"], abs=tolerance)
        assert result["y"] == pytest.approx(QUADRATIC_MINIMUM["y"], abs=tolerance)

    def test_genetic_algorithm(self, optimizer):
        """The genetic algorithm converges on the quadratic."""
        optimizer.setAlgorithm(GeneticAlgorithm(
            generations=60, population_size=40, random_seed=7))
        self._assert_converged(optimizer.run(quadratic, quadratic_parameters()))

    def test_cmaes(self, optimizer):
        """CMA-ES converges on the quadratic."""
        optimizer.setAlgorithm(CMAES(max_evaluations=400, random_seed=7))
        self._assert_converged(optimizer.run(quadratic, quadratic_parameters()))

    def test_bayesian_optimization(self, optimizer):
        """Bayesian optimization makes substantial progress on the quadratic."""
        optimizer.setAlgorithm(BayesianOptimization(max_evaluations=120, random_seed=7))
        result = optimizer.run(quadratic, quadratic_parameters())
        # A GP surrogate on a small budget lands near, not exactly on, the optimum.
        self._assert_converged(result, tolerance=1.0)

    def test_adam_with_analytic_gradient(self, optimizer):
        """Adam converges when given an analytic gradient."""
        optimizer.setAlgorithm(Adam(max_iterations=2000, learning_rate=0.05))
        result = optimizer.run(quadratic, quadratic_parameters(),
                               gradient=quadratic_gradient)
        self._assert_converged(result, tolerance=0.01)

    def test_adam_with_finite_difference(self, optimizer):
        """Adam converges with a numerically estimated gradient."""
        optimizer.setAlgorithm(Adam(max_iterations=2000, learning_rate=0.05))
        result = optimizer.run(quadratic, quadratic_parameters(),
                               finite_difference=True)
        self._assert_converged(result, tolerance=0.05)

    def test_bobyqa(self, optimizer):
        """BOBYQA converges on the quadratic."""
        if not optimizer.availableAlgorithms()["BOBYQA"]:
            pytest.skip("BOBYQA requires an NLopt-enabled build")
        optimizer.setAlgorithm(BOBYQA(max_iterations=400))
        self._assert_converged(optimizer.run(quadratic, quadratic_parameters()),
                               tolerance=0.01)

    def test_default_algorithm(self, optimizer):
        """Omitting setAlgorithm lets the plugin choose a working default."""
        self._assert_converged(optimizer.run(quadratic, quadratic_parameters()),
                               tolerance=1.0)

    def test_result_feeds_back_into_second_run(self, optimizer):
        """A result can seed a second, refining optimization."""
        optimizer.setAlgorithm(CMAES(max_evaluations=150, random_seed=3))
        coarse = optimizer.run(quadratic, quadratic_parameters())

        with ParameterOptimization() as refiner:
            if not refiner.availableAlgorithms()["BOBYQA"]:
                pytest.skip("BOBYQA requires an NLopt-enabled build")
            refiner.setAlgorithm(BOBYQA(max_iterations=200))
            refined = refiner.run(quadratic, coarse.parameters)

        assert refined.fitness <= coarse.fitness + 1e-6


@pytest.mark.native_only
class TestParameterNameOrdering:
    """
    Test the sorted-name ordering contract of the flat-array ABI.

    Values cross the boundary as bare arrays whose index order is a
    lexicographic sort of the parameter names. If the Python and C++ sides ever
    disagreed, values would be silently attributed to the wrong parameters and
    the optimization would still 'succeed' -- so this needs explicit coverage.
    """

    def test_names_map_to_correct_values(self, optimizer):
        """Each name receives its own optimized value, not a neighbour's."""
        # Insertion order differs from sorted order, and the mixed case pins
        # byte-wise ordering: 'Mango' sorts before 'alpha' and 'zebra'.
        targets = {"zebra": 4.0, "alpha": -2.0, "Mango": 1.0}

        def objective(params):
            return sum((params[name] - target) ** 2 for name, target in targets.items())

        parameters = {
            "zebra": Parameter.continuous(0.0, -5.0, 5.0),
            "alpha": Parameter.continuous(0.0, -5.0, 5.0),
            "Mango": Parameter.continuous(0.0, -5.0, 5.0),
        }

        optimizer.setAlgorithm(CMAES(max_evaluations=900, random_seed=11))
        result = optimizer.run(objective, parameters)

        for name, target in targets.items():
            assert result[name] == pytest.approx(target, abs=0.2), (
                f"parameter '{name}' converged to {result[name]}, expected {target}; "
                f"this indicates a name/value ordering mismatch")

    def test_objective_receives_named_parameters(self, optimizer):
        """The objective is handed every parameter under its own name."""
        seen = {}

        def objective(params):
            seen.update(params)
            return sum(value ** 2 for value in params.values())

        parameters = {
            "delta": Parameter.continuous(1.0, -2.0, 2.0),
            "beta": Parameter.continuous(1.0, -2.0, 2.0),
        }

        optimizer.setAlgorithm(GeneticAlgorithm(generations=5, population_size=5,
                                                random_seed=1))
        optimizer.run(objective, parameters)

        assert set(seen) == {"delta", "beta"}

    def test_result_preserves_bounds_and_type(self, optimizer):
        """Bounds and parameter type carry through to the result unchanged."""
        parameters = {"x": Parameter.continuous(0.0, -3.0, 7.0)}

        optimizer.setAlgorithm(GeneticAlgorithm(generations=5, population_size=5,
                                                random_seed=1))
        result = optimizer.run(lambda p: p["x"] ** 2, parameters)

        assert result.parameters["x"].min == -3.0
        assert result.parameters["x"].max == 7.0
        assert result.parameters["x"].type == ParameterType.FLOAT


@pytest.mark.native_only
class TestCallbackExceptionPropagation:
    """
    Test that a failure inside the objective surfaces correctly in Python.

    A Python exception cannot travel through the intervening C++ frames, and
    ctypes will not even let it leave the callback -- it prints the traceback and
    returns 0.0, which is a plausible objective value. Without the stash-and-
    re-raise bridge the optimizer would silently return a wrong answer.
    """

    def test_exception_type_and_message_preserved(self, optimizer):
        """The user's own exception type and message come back out."""
        class CustomObjectiveError(Exception):
            pass

        def failing(params):
            raise CustomObjectiveError("simulation diverged")

        optimizer.setAlgorithm(GeneticAlgorithm(generations=20, population_size=10,
                                                random_seed=1))

        with pytest.raises(CustomObjectiveError, match="simulation diverged"):
            optimizer.run(failing, quadratic_parameters())

    def test_traceback_points_at_user_code(self, optimizer):
        """The traceback still names the function that actually failed."""
        def failing(params):
            raise ValueError("boom")

        optimizer.setAlgorithm(GeneticAlgorithm(generations=20, population_size=10,
                                                random_seed=1))

        with pytest.raises(ValueError) as excinfo:
            optimizer.run(failing, quadratic_parameters())

        assert "failing" in str(excinfo.traceback[-1])

    def test_exception_from_nlopt_path(self, optimizer):
        """
        Exceptions also survive the NLopt code path.

        NLopt catches exceptions from its own callbacks, so the plugin stashes
        and rethrows them. That is a different mechanism from the direct path
        and needs its own coverage.
        """
        if not optimizer.availableAlgorithms()["BOBYQA"]:
            pytest.skip("BOBYQA requires an NLopt-enabled build")

        def failing(params):
            raise RuntimeError("nlopt path failure")

        optimizer.setAlgorithm(BOBYQA(max_iterations=100))

        with pytest.raises(RuntimeError, match="nlopt path failure"):
            optimizer.run(failing, quadratic_parameters())

    def test_exception_from_gradient(self, optimizer):
        """A failure inside the gradient function propagates too."""
        def failing_gradient(params):
            raise ArithmeticError("gradient blew up")

        optimizer.setAlgorithm(Adam(max_iterations=50))

        with pytest.raises(ArithmeticError, match="gradient blew up"):
            optimizer.run(quadratic, quadratic_parameters(), gradient=failing_gradient)

    def test_keyboard_interrupt_aborts_run(self, optimizer):
        """Ctrl-C during a long run aborts instead of being swallowed."""
        def interrupting(params):
            raise KeyboardInterrupt()

        optimizer.setAlgorithm(GeneticAlgorithm(generations=50, population_size=20,
                                                random_seed=1))

        with pytest.raises(KeyboardInterrupt):
            optimizer.run(interrupting, quadratic_parameters())

    def test_instance_reusable_after_abort(self, optimizer):
        """An aborted run leaves the instance usable."""
        def failing(params):
            raise ValueError("first attempt fails")

        optimizer.setAlgorithm(GeneticAlgorithm(generations=20, population_size=10,
                                                random_seed=1))

        with pytest.raises(ValueError):
            optimizer.run(failing, quadratic_parameters())

        result = optimizer.run(quadratic, quadratic_parameters())
        assert result.fitness < 1.0


@pytest.mark.native_only
class TestObjectiveReturnValidation:
    """Test rejection of objective return values that would corrupt the optimizer."""

    @pytest.mark.parametrize("bad_value", [float('nan'), float('inf'), float('-inf')])
    def test_non_finite_objective_rejected(self, optimizer, bad_value):
        """
        Non-finite objective values are rejected rather than silently accepted.

        C++ does not check this, and a NaN corrupts the genetic algorithm's
        elitism sort and the CMA-ES update without raising anything.
        """
        optimizer.setAlgorithm(GeneticAlgorithm(generations=20, population_size=10,
                                                random_seed=1))

        with pytest.raises(ValueError, match="finite"):
            optimizer.run(lambda p: bad_value, quadratic_parameters())

    def test_non_numeric_objective_rejected(self, optimizer):
        """A non-numeric return surfaces as a clear TypeError."""
        optimizer.setAlgorithm(GeneticAlgorithm(generations=20, population_size=10,
                                                random_seed=1))

        with pytest.raises(TypeError):
            optimizer.run(lambda p: None, quadratic_parameters())

    def test_incomplete_gradient_rejected(self, optimizer):
        """A gradient missing a parameter names the omission."""
        optimizer.setAlgorithm(Adam(max_iterations=50))

        with pytest.raises(ValueError, match="omitted"):
            optimizer.run(quadratic, quadratic_parameters(),
                          gradient=lambda p: {"x": 1.0})

    def test_extraneous_gradient_key_rejected(self, optimizer):
        """A gradient with an unknown key is reported rather than ignored."""
        optimizer.setAlgorithm(Adam(max_iterations=50))

        with pytest.raises(ValueError, match="unknown"):
            optimizer.run(quadratic, quadratic_parameters(),
                          gradient=lambda p: {"x": 1.0, "y": 1.0, "z": 1.0})

    def test_non_finite_gradient_rejected(self, optimizer):
        """A non-finite partial derivative is rejected."""
        optimizer.setAlgorithm(Adam(max_iterations=50))

        with pytest.raises(ValueError, match="finite"):
            optimizer.run(quadratic, quadratic_parameters(),
                          gradient=lambda p: {"x": float('nan'), "y": 0.0})


@pytest.mark.native_only
class TestCallbackLifetime:
    """
    Test that callback objects survive garbage collection during a run.

    ctypes callback objects own the executable thunk C++ calls into. If one were
    collected mid-run, C++ would jump into freed memory -- a segfault or, worse,
    a silently wrong value.
    """

    def test_gc_during_optimization(self, optimizer):
        """Collecting garbage from inside the objective does not break the run."""
        def objective_with_gc(params):
            gc.collect()
            return quadratic(params)

        optimizer.setAlgorithm(GeneticAlgorithm(generations=30, population_size=20,
                                                random_seed=5))
        result = optimizer.run(objective_with_gc, quadratic_parameters())

        assert result.fitness < 1.0

    def test_many_sequential_runs(self, optimizer):
        """Repeated runs on one instance neither leak nor crash."""
        optimizer.setAlgorithm(GeneticAlgorithm(generations=10, population_size=10,
                                                random_seed=2))

        for _ in range(10):
            result = optimizer.run(quadratic, quadratic_parameters())
            assert math.isfinite(result.fitness)
            gc.collect()


@pytest.mark.native_only
class TestParameterValidation:
    """Test parameter validation performed before crossing the ABI."""

    def test_empty_parameters_rejected(self, optimizer):
        """An empty parameter set is rejected."""
        with pytest.raises(ValueError, match="empty"):
            optimizer.run(quadratic, {})

    def test_non_callable_objective_rejected(self, optimizer):
        """A non-callable objective is rejected."""
        with pytest.raises(TypeError, match="callable"):
            optimizer.run("not a function", quadratic_parameters())

    def test_wrong_parameter_value_type_rejected(self, optimizer):
        """A raw float in place of a Parameter is rejected."""
        with pytest.raises(TypeError, match="Parameter"):
            optimizer.run(quadratic, {"x": 1.0})

    def test_non_string_parameter_name_rejected(self, optimizer):
        """A non-string parameter name is rejected."""
        with pytest.raises(TypeError, match="strings"):
            optimizer.run(quadratic, {1: Parameter.continuous(0.0, -1.0, 1.0)})

    def test_empty_parameter_name_rejected(self, optimizer):
        """An empty parameter name is rejected."""
        with pytest.raises(ValueError, match="empty"):
            optimizer.run(quadratic, {"": Parameter.continuous(0.0, -1.0, 1.0)})

    def test_null_character_in_name_rejected(self, optimizer):
        """
        A NUL in a parameter name is rejected.

        It would truncate the C string and misalign every later name lookup.
        """
        with pytest.raises(ValueError, match="null character"):
            optimizer.run(quadratic, {"a\x00b": Parameter.continuous(0.0, -1.0, 1.0)})

    def test_categorical_without_categories_rejected(self, optimizer):
        """A CATEGORICAL parameter with no allowed values is rejected."""
        bad = Parameter(value=0.0, min=0.0, max=0.0, type=ParameterType.CATEGORICAL)
        with pytest.raises(ValueError, match="categories"):
            optimizer.run(quadratic, {"x": bad})

    def test_invalid_bounds_rejected_by_native_layer(self, optimizer):
        """
        Bound validation is left to the plugin and still surfaces cleanly.

        Deliberately not duplicated in Python, so the rules cannot drift apart.
        """
        parameters = {"x": Parameter.continuous(0.0, 5.0, -5.0)}
        with pytest.raises((HeliosError, ParameterOptimizationError, RuntimeError)):
            optimizer.run(lambda p: p["x"] ** 2, parameters)

    def test_gradient_and_finite_difference_conflict(self, optimizer):
        """Supplying both a gradient and finite_difference is rejected."""
        with pytest.raises(ValueError, match="not both"):
            optimizer.run(quadratic, quadratic_parameters(),
                          gradient=quadratic_gradient, finite_difference=True)

    def test_gradient_required_error_is_actionable(self, optimizer):
        """A gradient-based algorithm without a gradient explains the fix."""
        optimizer.setAlgorithm(Adam(max_iterations=10))

        with pytest.raises(ValueError, match="finite_difference"):
            optimizer.run(quadratic, quadratic_parameters())

    def test_reentrant_run_rejected(self, optimizer):
        """Calling run() from inside its own objective is rejected."""
        def reentrant(params):
            optimizer.run(quadratic, quadratic_parameters())
            return 0.0

        optimizer.setAlgorithm(GeneticAlgorithm(generations=5, population_size=5,
                                                random_seed=1))

        with pytest.raises(ParameterOptimizationError, match="not reentrant"):
            optimizer.run(reentrant, quadratic_parameters())


@pytest.mark.native_only
class TestAlgorithmSelection:
    """Test algorithm selection, availability reporting, and presets."""

    def test_available_algorithms_reports_all(self, optimizer):
        """Availability is reported for every algorithm."""
        available = optimizer.availableAlgorithms()

        assert set(available) == {"GA", "BO", "CMAES", "ADAM", "LBFGS", "BOBYQA", "SLSQP"}
        # These need no external solver and are always compiled in.
        for name in ("GA", "BO", "CMAES", "ADAM"):
            assert available[name] is True

    def test_unavailable_algorithm_raises_actionable_error(self, optimizer):
        """Selecting an unavailable algorithm explains the alternatives."""
        available = optimizer.availableAlgorithms()
        if available["LBFGS"]:
            pytest.skip("L-BFGS is available in this build")

        with pytest.raises(ParameterOptimizationError) as excinfo:
            optimizer.setAlgorithm(LBFGS())

        message = str(excinfo.value)
        assert "not available" in message.lower()
        assert "Adam" in message or "BOBYQA" in message

    def test_invalid_algorithm_type_rejected(self, optimizer):
        """A non-settings object is rejected."""
        with pytest.raises(TypeError, match="algorithm must be"):
            optimizer.setAlgorithm("GeneticAlgorithm")

    def test_genetic_algorithm_operators(self, optimizer):
        """Every crossover and mutation operator can be selected and run."""
        for crossover in (BLXAlphaCrossover(), BLXPCACrossover()):
            for mutation in (PerGeneMutation(), IsotropicMutation(), HybridMutation()):
                optimizer.setAlgorithm(GeneticAlgorithm(
                    generations=10, population_size=10, random_seed=1,
                    crossover=crossover, mutation=mutation))
                result = optimizer.run(quadratic, quadratic_parameters())
                assert math.isfinite(result.fitness)

    def test_presets_come_from_native_library(self, optimizer):
        """explore/exploit presets differ from the defaults and from each other."""
        default = GeneticAlgorithm()
        explore = GeneticAlgorithm.explore()
        exploit = GeneticAlgorithm.exploit()

        assert explore.population_size != default.population_size
        assert explore.population_size != exploit.population_size

        cmaes_explore = CMAES.explore()
        cmaes_exploit = CMAES.exploit()
        assert cmaes_explore.sigma > cmaes_exploit.sigma

        bayesian_explore = BayesianOptimization.explore()
        bayesian_exploit = BayesianOptimization.exploit()
        assert bayesian_explore.ucb_kappa > bayesian_exploit.ucb_kappa

    def test_preset_is_usable(self, optimizer):
        """A preset can be handed straight to setAlgorithm."""
        optimizer.setAlgorithm(CMAES.exploit())
        result = optimizer.run(quadratic, quadratic_parameters())
        assert math.isfinite(result.fitness)


@pytest.mark.native_only
class TestDiscreteParameters:
    """Test integer and categorical parameter handling."""

    def test_integer_parameter_yields_whole_numbers(self, optimizer):
        """An INTEGER parameter optimizes to a whole number."""
        parameters = {"n": Parameter.integer(0.0, -10.0, 10.0)}

        optimizer.setAlgorithm(GeneticAlgorithm(generations=40, population_size=20,
                                                random_seed=4))
        result = optimizer.run(lambda p: (p["n"] - 4.0) ** 2, parameters)

        assert result["n"] == pytest.approx(round(result["n"]), abs=1e-4)
        assert result["n"] == pytest.approx(4.0, abs=1.0)

    def test_categorical_parameter_selects_allowed_value(self, optimizer):
        """A CATEGORICAL parameter settles on one of its allowed values."""
        categories = [0.5, 1.7, 3.14, 7.2]
        parameters = {"c": Parameter.categorical(0.5, categories)}

        optimizer.setAlgorithm(GeneticAlgorithm(generations=40, population_size=20,
                                                random_seed=6))
        result = optimizer.run(lambda p: (p["c"] - 3.14) ** 2, parameters)

        assert any(result["c"] == pytest.approx(c, abs=1e-4) for c in categories)

    # The genetic algorithm is the only one that understands INTEGER and
    # CATEGORICAL parameters. The others treat every parameter as continuous, so
    # passing a discrete one to them silently returns a value that is not in the
    # allowed set -- a CATEGORICAL parameter collapses to 0.0, because its min and
    # max are documented as ignored and so are conventionally left at zero, which
    # the continuous algorithms read as the bounds [0, 0].
    #
    # helios-core rejects this for L-BFGS, Adam, BOBYQA and SLSQP but not for
    # CMA-ES or Bayesian optimization; the fix for those two landed upstream after
    # the pinned submodule revision. These checks run on the Python side so the
    # error arrives on every core version, and remain correct once core catches up.
    @pytest.mark.parametrize("algorithm", [
        CMAES(max_evaluations=40, random_seed=7),
        BayesianOptimization(max_evaluations=40, random_seed=7),
        Adam(max_iterations=20),
    ], ids=["CMAES", "BayesianOptimization", "Adam"])
    @pytest.mark.parametrize("parameter", [
        Parameter.integer(0.0, -10.0, 10.0),
        Parameter.categorical(5.0, [5.0, 12.0, 20.0]),
    ], ids=["INTEGER", "CATEGORICAL"])
    def test_discrete_parameter_rejected_by_continuous_algorithm(
            self, optimizer, algorithm, parameter):
        """A discrete parameter is refused by algorithms that only handle FLOAT."""
        optimizer.setAlgorithm(algorithm)

        with pytest.raises(ValueError, match="FLOAT"):
            optimizer.run(lambda p: (p["n"] - 12.0) ** 2, {"n": parameter},
                          finite_difference=True)

    def test_discrete_rejection_names_parameter_and_algorithm(self, optimizer):
        """The rejection message identifies the parameter, its type, and the fix."""
        optimizer.setAlgorithm(CMAES(max_evaluations=40, random_seed=7))

        with pytest.raises(ValueError) as excinfo:
            optimizer.run(lambda p: p["n"], {"n": Parameter.categorical(5.0, [5.0, 12.0])})

        message = str(excinfo.value)
        assert "n" in message
        assert "CATEGORICAL" in message
        assert "CMAES" in message
        assert "GeneticAlgorithm" in message

    def test_float_parameters_still_accepted_by_continuous_algorithms(self, optimizer):
        """The guard does not block ordinary continuous parameters."""
        optimizer.setAlgorithm(CMAES(max_evaluations=60, random_seed=3))
        result = optimizer.run(lambda p: (p["x"] - 2.0) ** 2,
                               {"x": Parameter.continuous(0.0, -5.0, 5.0)})

        assert result["x"] == pytest.approx(2.0, abs=0.5)


def _quadratic_simulation(counter=None):
    """Minimize x^2 + y^2 subject to x + y >= 1, i.e. 1 - x - y <= 0.

    Analytic optimum: x = y = 0.5, objective 0.5. The unconstrained optimum is
    (0, 0) with objective 0, so a run that ignores the constraint is obvious.
    """
    def simulation(p):
        if counter is not None:
            counter.append(1)
        return ConstrainedResult(
            objective=p["x"] ** 2 + p["y"] ** 2,
            objective_gradient={"x": 2.0 * p["x"], "y": 2.0 * p["y"]},
            constraints=[1.0 - p["x"] - p["y"]],
            constraint_gradients=[{"x": -1.0, "y": -1.0}],
        )
    return simulation


def _xy_parameters():
    return {"x": Parameter.continuous(0.0, -5.0, 5.0),
            "y": Parameter.continuous(0.0, -5.0, 5.0)}


class TestConstrainedValidation:
    """Constrained-run argument checks that need no native optimization."""

    def test_requires_slsqp(self, optimizer):
        """A non-SLSQP algorithm is rejected before the run starts."""
        optimizer.setAlgorithm(CMAES(max_evaluations=20, random_seed=1))

        with pytest.raises(ValueError, match="requires SLSQP"):
            optimizer.runConstrained(_quadratic_simulation(), _xy_parameters(),
                                     constraint_count=1)

    def test_requires_algorithm_to_be_set(self, optimizer):
        """With no algorithm selected the requirement is still reported up front."""
        with pytest.raises(ValueError, match="requires SLSQP"):
            optimizer.runConstrained(_quadratic_simulation(), _xy_parameters(),
                                     constraint_count=1)

    def test_constraint_count_must_be_positive(self, optimizer):
        """A zero constraint count points at the unconstrained entry point."""
        optimizer.setAlgorithm(SLSQP(max_iterations=20))

        with pytest.raises(ValueError, match="at least 1"):
            optimizer.runConstrained(_quadratic_simulation(), _xy_parameters(),
                                     constraint_count=0)

    def test_simulation_must_be_callable(self, optimizer):
        optimizer.setAlgorithm(SLSQP(max_iterations=20))

        with pytest.raises(TypeError, match="callable"):
            optimizer.runConstrained("not callable", _xy_parameters(), constraint_count=1)

    def test_discrete_parameters_rejected(self, optimizer):
        """SLSQP requires FLOAT parameters, constrained runs included."""
        optimizer.setAlgorithm(SLSQP(max_iterations=20))

        with pytest.raises(ValueError, match="FLOAT"):
            optimizer.runConstrained(
                _quadratic_simulation(),
                {"x": Parameter.continuous(0.0, -5.0, 5.0),
                 "y": Parameter.integer(0.0, -5.0, 5.0)},
                constraint_count=1)


@pytest.mark.native_only
class TestConstrainedOptimization:
    """Nonlinear inequality-constrained optimization through SLSQP."""

    @pytest.fixture(autouse=True)
    def _require_slsqp(self, optimizer):
        if not optimizer.availableAlgorithms()["SLSQP"]:
            pytest.skip("SLSQP requires NLopt, which is not in this build")

    def test_converges_to_constrained_optimum(self, optimizer):
        """The known optimum of a problem with an analytic solution is found."""
        optimizer.setAlgorithm(SLSQP(max_iterations=100))

        result = optimizer.runConstrained(_quadratic_simulation(), _xy_parameters(),
                                          constraint_count=1)

        assert result["x"] == pytest.approx(0.5, abs=1e-2)
        assert result["y"] == pytest.approx(0.5, abs=1e-2)
        assert result.fitness == pytest.approx(0.5, abs=1e-2)

    def test_constraint_is_actually_enforced(self, optimizer):
        """The unconstrained optimum is not returned.

        Without this, a binding that silently dropped the constraints would still
        satisfy a loose fitness assertion by landing at (0, 0) with fitness 0.
        """
        optimizer.setAlgorithm(SLSQP(max_iterations=100))

        result = optimizer.runConstrained(_quadratic_simulation(), _xy_parameters(),
                                          constraint_count=1)

        assert result.fitness > 0.4, "landed at the unconstrained optimum"
        assert result["x"] + result["y"] >= 1.0 - 1e-3

    def test_reported_optimum_is_feasible(self, optimizer):
        """Every constraint holds at the returned parameters."""
        optimizer.setAlgorithm(SLSQP(max_iterations=100))

        result = optimizer.runConstrained(_quadratic_simulation(), _xy_parameters(),
                                          constraint_count=1)

        final = _quadratic_simulation()(result.values)
        for index, value in enumerate(final.constraints):
            assert value <= 1e-3, f"constraint {index} violated: {value}"

    def test_two_constraints_map_to_the_right_parameters(self, optimizer):
        """Two asymmetric constraints pin the row-major gradient layout.

        With one constraint, or two symmetric ones, a transposed [j * n + i]
        flattening would give the same answer. Here constraint 0 binds only x and
        constraint 1 only y, at different values, so a transposition moves the
        optimum.
        """
        def simulation(p):
            return ConstrainedResult(
                objective=p["x"] ** 2 + p["y"] ** 2,
                objective_gradient={"x": 2.0 * p["x"], "y": 2.0 * p["y"]},
                # x >= 1 and y >= 2
                constraints=[1.0 - p["x"], 2.0 - p["y"]],
                constraint_gradients=[{"x": -1.0, "y": 0.0}, {"x": 0.0, "y": -1.0}],
            )

        optimizer.setAlgorithm(SLSQP(max_iterations=150))
        result = optimizer.runConstrained(simulation, _xy_parameters(), constraint_count=2)

        assert result["x"] == pytest.approx(1.0, abs=1e-2)
        assert result["y"] == pytest.approx(2.0, abs=1e-2)

    def test_parameter_ordering_is_by_sorted_name(self, optimizer):
        """Values reach the simulation under the right names.

        Insertion order differs from sorted order, and the mixed case makes the
        byte-wise sort observable ('B' < 'a'). A Python/C++ ordering disagreement
        would silently attribute each value to the wrong parameter.
        """
        seen = {}

        def simulation(p):
            seen.update(p)
            return ConstrainedResult(
                objective=(p["a_second"] - 3.0) ** 2 + (p["B_first"] - 1.0) ** 2,
                objective_gradient={"a_second": 2.0 * (p["a_second"] - 3.0),
                                    "B_first": 2.0 * (p["B_first"] - 1.0)},
                constraints=[-1.0],  # inactive
                constraint_gradients=[{"a_second": 0.0, "B_first": 0.0}],
            )

        parameters = {"a_second": Parameter.continuous(0.0, -10.0, 10.0),
                      "B_first": Parameter.continuous(0.0, -10.0, 10.0)}

        optimizer.setAlgorithm(SLSQP(max_iterations=100))
        result = optimizer.runConstrained(simulation, parameters, constraint_count=1)

        assert set(seen) == {"a_second", "B_first"}
        assert result["a_second"] == pytest.approx(3.0, abs=1e-2)
        assert result["B_first"] == pytest.approx(1.0, abs=1e-2)

    def test_simulation_is_cached_per_parameter_point(self, optimizer):
        """The simulation runs once per point, not once per callback.

        NLopt queries the objective and each constraint separately; the plugin
        caches the combined result so the simulation is not re-run for each. With
        one constraint an uncached binding would call it about twice as often.
        """
        calls = []
        optimizer.setAlgorithm(SLSQP(max_iterations=25))

        result = optimizer.runConstrained(_quadratic_simulation(calls), _xy_parameters(),
                                          constraint_count=1)

        # This problem converges in 4 evaluations when the cache holds. The bound is
        # deliberately close to that: an uncached binding re-runs the simulation for
        # the objective and for each constraint at the same point, so it cannot fit.
        assert len(calls) <= 10, f"simulation called {len(calls)} times; cache not working"
        assert result.fitness == pytest.approx(0.5, abs=1e-2)

    def test_exception_propagates_with_original_traceback(self, optimizer):
        """An exception inside the simulation is re-raised, not swallowed."""
        class SimulationFailure(RuntimeError):
            pass

        def simulation(p):
            raise SimulationFailure("simulation blew up")

        optimizer.setAlgorithm(SLSQP(max_iterations=50))

        with pytest.raises(SimulationFailure, match="simulation blew up") as excinfo:
            optimizer.runConstrained(simulation, _xy_parameters(), constraint_count=1)

        assert "simulation" in str(excinfo.traceback[-1])

    def test_instance_reusable_after_failure(self, optimizer):
        """A failed run leaves the instance usable."""
        def failing(p):
            raise ValueError("nope")

        optimizer.setAlgorithm(SLSQP(max_iterations=50))
        with pytest.raises(ValueError):
            optimizer.runConstrained(failing, _xy_parameters(), constraint_count=1)

        result = optimizer.runConstrained(_quadratic_simulation(), _xy_parameters(),
                                          constraint_count=1)
        assert result.fitness == pytest.approx(0.5, abs=1e-2)

    @pytest.mark.parametrize("broken,match", [
        (lambda p: ConstrainedResult(1.0, {"x": 1.0, "y": 1.0}, [0.0, 0.0],
                                     [{"x": 0.0, "y": 0.0}]),
         "constraint value"),
        (lambda p: ConstrainedResult(1.0, {"x": 1.0, "y": 1.0}, [0.0],
                                     [{"x": 0.0, "y": 0.0}, {"x": 0.0, "y": 0.0}]),
         "constraint gradient"),
        (lambda p: ConstrainedResult(1.0, {"x": 1.0}, [0.0], [{"x": 0.0, "y": 0.0}]),
         "omitted parameter"),
        (lambda p: ConstrainedResult(1.0, {"x": 1.0, "y": 1.0, "z": 1.0}, [0.0],
                                     [{"x": 0.0, "y": 0.0}]),
         "unknown parameter"),
        (lambda p: ConstrainedResult(1.0, {"x": 1.0, "y": 1.0}, [0.0], [{"x": 0.0}]),
         "omitted parameter"),
        (lambda p: ConstrainedResult(float("nan"), {"x": 1.0, "y": 1.0}, [0.0],
                                     [{"x": 0.0, "y": 0.0}]),
         "finite"),
        (lambda p: ConstrainedResult(1.0, {"x": 1.0, "y": 1.0}, [float("inf")],
                                     [{"x": 0.0, "y": 0.0}]),
         "finite"),
        (lambda p: "not a ConstrainedResult", "ConstrainedResult"),
    ], ids=["too_many_constraints", "gradient_count_mismatch", "missing_obj_param",
            "unknown_obj_param", "missing_constraint_param", "nan_objective",
            "inf_constraint", "wrong_return_type"])
    def test_malformed_simulation_output_rejected(self, optimizer, broken, match):
        """A malformed return is reported precisely rather than corrupting the run."""
        optimizer.setAlgorithm(SLSQP(max_iterations=20))

        with pytest.raises((ValueError, TypeError), match=match):
            optimizer.runConstrained(broken, _xy_parameters(), constraint_count=1)

    def test_reentrancy_rejected(self, optimizer):
        """Calling runConstrained from inside its own simulation is refused."""
        def reentrant(p):
            optimizer.runConstrained(_quadratic_simulation(), _xy_parameters(),
                                     constraint_count=1)
            return _quadratic_simulation()(p)

        optimizer.setAlgorithm(SLSQP(max_iterations=20))

        with pytest.raises(ParameterOptimizationError, match="not reentrant"):
            optimizer.runConstrained(reentrant, _xy_parameters(), constraint_count=1)

    def test_make_constrained_simulation_helper(self, optimizer):
        """The composition helper reaches the same optimum as a hand-written one."""
        simulation = make_constrained_simulation(
            lambda p: p["x"] ** 2 + p["y"] ** 2,
            lambda p: {"x": 2.0 * p["x"], "y": 2.0 * p["y"]},
            [(lambda p: 1.0 - p["x"] - p["y"], lambda p: {"x": -1.0, "y": -1.0})],
        )

        optimizer.setAlgorithm(SLSQP(max_iterations=100))
        result = optimizer.runConstrained(simulation, _xy_parameters(), constraint_count=1)

        assert result["x"] == pytest.approx(0.5, abs=1e-2)
        assert result["y"] == pytest.approx(0.5, abs=1e-2)


class TestMakeConstrainedSimulation:
    """Validation of the composition helper, independent of any native run."""

    def test_rejects_non_callable_objective(self):
        with pytest.raises(TypeError, match="objective must be callable"):
            make_constrained_simulation("nope", lambda p: {}, [])

    def test_rejects_malformed_constraint_pair(self):
        with pytest.raises(TypeError, match="function, gradient"):
            make_constrained_simulation(lambda p: 0.0, lambda p: {}, [lambda p: 0.0])

    def test_composes_into_a_constrained_result(self):
        simulation = make_constrained_simulation(
            lambda p: p["x"] ** 2,
            lambda p: {"x": 2.0 * p["x"]},
            [(lambda p: 1.0 - p["x"], lambda p: {"x": -1.0})],
        )

        result = simulation({"x": 3.0})

        assert isinstance(result, ConstrainedResult)
        assert result.objective == pytest.approx(9.0)
        assert result.objective_gradient == {"x": 6.0}
        assert list(result.constraints) == pytest.approx([-2.0])
        assert list(result.constraint_gradients) == [{"x": -1.0}]


@pytest.mark.native_only
class TestFileOutput:
    """Test the plugin's file output configuration."""

    def test_result_file_written(self, optimizer, tmp_path):
        """The final result is written to the configured CSV file."""
        output = tmp_path / "result.csv"
        optimizer.setResultFile(str(output))
        optimizer.setAlgorithm(GeneticAlgorithm(generations=10, population_size=10,
                                                random_seed=1))
        optimizer.run(quadratic, quadratic_parameters())

        assert output.exists()
        contents = output.read_text()
        assert "parameter" in contents
        assert "x" in contents and "y" in contents

    def test_progress_file_written(self, optimizer, tmp_path):
        """Per-generation progress is written to the configured CSV file."""
        output = tmp_path / "progress.csv"
        optimizer.setProgressFile(str(output))
        optimizer.setAlgorithm(GeneticAlgorithm(generations=10, population_size=10,
                                                random_seed=1))
        optimizer.run(quadratic, quadratic_parameters())

        assert output.exists()
        assert "generation" in output.read_text()

    def test_invalid_output_extension_rejected(self, optimizer, tmp_path):
        """An unsupported output extension is rejected by the native layer."""
        optimizer.setResultFile(str(tmp_path / "result.json"))
        optimizer.setAlgorithm(GeneticAlgorithm(generations=5, population_size=5,
                                                random_seed=1))

        with pytest.raises((HeliosError, ParameterOptimizationError, RuntimeError)):
            optimizer.run(quadratic, quadratic_parameters())


@pytest.mark.native_only
class TestContextIntegration:
    """Test optimizing against a real Helios simulation."""

    def test_objective_using_context(self, optimizer):
        """The objective may drive a Context and read primitive data back."""
        from pyhelios import Context
        from pyhelios.types import vec2, vec3

        with Context() as context:
            uuid = context.addPatch(center=vec3(0, 0, 0), size=vec2(1, 1))

            def objective(params):
                # Round-trip the candidate values through the Context, mirroring
                # how a real calibration would drive a Helios simulation.
                for name, value in params.items():
                    context.setPrimitiveDataFloat(uuid, name, value)
                x = context.getPrimitiveDataFloat(uuid, "x")
                y = context.getPrimitiveDataFloat(uuid, "y")
                return (x - 3.0) ** 2 + (y + 1.0) ** 2

            optimizer.setAlgorithm(GeneticAlgorithm(generations=50, population_size=30,
                                                    random_seed=9))
            result = optimizer.run(objective, quadratic_parameters())

        assert result["x"] == pytest.approx(3.0, abs=0.3)
        assert result["y"] == pytest.approx(-1.0, abs=0.3)
