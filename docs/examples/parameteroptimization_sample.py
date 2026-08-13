"""
ParameterOptimization sample for PyHelios.

Demonstrates calibrating model parameters against an objective function:

1. Basic optimization with the genetic algorithm
2. Gradient-based optimization with Adam
3. Two-stage global search followed by local refinement
4. Discrete (integer and categorical) parameters
5. Constrained optimization with SLSQP
6. Optimizing against a real Helios simulation

Run with:
    python docs/examples/parameteroptimization_sample.py
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from pyhelios import (
    Context, ParameterOptimization, ParameterOptimizationError,
    ConstrainedResult, Parameter, GeneticAlgorithm, CMAES, Adam, BOBYQA, SLSQP,
)
from pyhelios.types import vec2, vec3


def rosenbrock(params):
    """
    Rosenbrock function -- a classic optimization benchmark.

    Its minimum of 0 sits at (1, 1) at the bottom of a narrow curved valley,
    which makes it easy to approach and hard to pin down.
    """
    x, y = params["x"], params["y"]
    return (1.0 - x) ** 2 + 100.0 * (y - x * x) ** 2


def basic_optimization():
    """Minimize a quadratic with the genetic algorithm."""
    print("=" * 60)
    print("1. Basic optimization (genetic algorithm)")
    print("=" * 60)

    def objective(params):
        # Minimum of 0 at x=3, y=-1
        return (params["x"] - 3.0) ** 2 + (params["y"] + 1.0) ** 2

    with ParameterOptimization() as opt:
        # A fixed seed makes the run reproducible; 0 would seed randomly.
        opt.setAlgorithm(GeneticAlgorithm(generations=100, population_size=30,
                                          random_seed=1))
        result = opt.run(objective, {
            "x": Parameter.continuous(0.0, -5.0, 5.0),
            "y": Parameter.continuous(0.0, -5.0, 5.0),
        })

    print(f"  x = {result['x']:.4f}  (expected 3.0)")
    print(f"  y = {result['y']:.4f}  (expected -1.0)")
    print(f"  objective = {result.fitness:.6f}")
    print()


def gradient_based_optimization():
    """Minimize the Rosenbrock function using an analytic gradient."""
    print("=" * 60)
    print("2. Gradient-based optimization (Adam)")
    print("=" * 60)

    def gradient(params):
        # Must return an entry for every parameter.
        x, y = params["x"], params["y"]
        return {
            "x": -2.0 * (1.0 - x) - 400.0 * x * (y - x * x),
            "y": 200.0 * (y - x * x),
        }

    parameters = {
        "x": Parameter.continuous(-1.0, -2.0, 2.0),
        "y": Parameter.continuous(1.0, -1.0, 3.0),
    }

    with ParameterOptimization() as opt:
        opt.setAlgorithm(Adam(max_iterations=5000, learning_rate=0.002))
        analytic = opt.run(rosenbrock, parameters, gradient=gradient)

    print(f"  analytic gradient:   x={analytic['x']:.4f} y={analytic['y']:.4f} "
          f"objective={analytic.fitness:.6f}")

    # The same optimization without writing a gradient, at the cost of 2N extra
    # objective evaluations per step.
    with ParameterOptimization() as opt:
        opt.setAlgorithm(Adam(max_iterations=5000, learning_rate=0.002))
        numeric = opt.run(rosenbrock, parameters, finite_difference=True)

    print(f"  finite differences:  x={numeric['x']:.4f} y={numeric['y']:.4f} "
          f"objective={numeric.fitness:.6f}")
    print("  (true minimum is at x=1, y=1)")
    print()


def two_stage_optimization():
    """Locate the right basin globally, then refine within it."""
    print("=" * 60)
    print("3. Two-stage optimization (CMA-ES then BOBYQA)")
    print("=" * 60)

    parameters = {
        "x": Parameter.continuous(-1.0, -2.0, 2.0),
        "y": Parameter.continuous(1.0, -1.0, 3.0),
    }

    with ParameterOptimization() as explorer:
        explorer.setAlgorithm(CMAES(max_evaluations=600, sigma=0.5, random_seed=2))
        coarse = explorer.run(rosenbrock, parameters)

    print(f"  after global search:  x={coarse['x']:.4f} y={coarse['y']:.4f} "
          f"objective={coarse.fitness:.6f}")

    with ParameterOptimization() as refiner:
        if not refiner.availableAlgorithms()["BOBYQA"]:
            print("  BOBYQA unavailable in this build; skipping refinement")
            print()
            return

        refiner.setAlgorithm(BOBYQA(max_iterations=500))
        # The result carries full Parameter objects, so it feeds straight back in
        # as the starting point for the next stage.
        refined = refiner.run(rosenbrock, coarse.parameters)

    print(f"  after refinement:     x={refined['x']:.4f} y={refined['y']:.4f} "
          f"objective={refined.fitness:.6f}")
    print()


def discrete_parameters():
    """Optimize integer and categorical parameters."""
    print("=" * 60)
    print("4. Discrete parameters (genetic algorithm)")
    print("=" * 60)

    allowed_angles = [15.0, 30.0, 45.0, 60.0, 75.0]

    def objective(params):
        # Prefer 12 leaves at a 45 degree angle.
        return (params["leaf_count"] - 12.0) ** 2 + (params["leaf_angle"] - 45.0) ** 2

    with ParameterOptimization() as opt:
        # The genetic algorithm is the only one that searches discrete spaces
        # correctly. The local solvers reject non-FLOAT parameters outright, and
        # CMA-ES / Bayesian optimization silently return a value outside the
        # allowed category list rather than raising.
        opt.setAlgorithm(GeneticAlgorithm(generations=150, population_size=40,
                                          random_seed=3))
        result = opt.run(objective, {
            "leaf_count": Parameter.integer(5.0, 1.0, 30.0),
            "leaf_angle": Parameter.categorical(15.0, allowed_angles),
        })

    print(f"  leaf_count = {result['leaf_count']:.1f}  (integer, expected 12)")
    print(f"  leaf_angle = {result['leaf_angle']:.1f}  (from {allowed_angles})")
    print(f"  objective  = {result.fitness:.6f}")
    print()


def optimization_with_context():
    """Optimize against a Helios simulation."""
    print("=" * 60)
    print("6. Optimization driving a Helios Context")
    print("=" * 60)

    with Context() as context:
        uuid = context.addPatch(center=vec3(0, 0, 0), size=vec2(1, 1))

        # In a real calibration this would build geometry, run radiation and
        # energy balance, and compare the output against measured data.
        target_reflectivity = 0.35

        def objective(params):
            context.setPrimitiveDataFloat(uuid, "reflectivity", params["reflectivity"])
            modelled = context.getPrimitiveDataFloat(uuid, "reflectivity")
            return (modelled - target_reflectivity) ** 2

        with ParameterOptimization() as opt:
            opt.setAlgorithm(CMAES(max_evaluations=200, random_seed=4))
            result = opt.run(objective, {
                "reflectivity": Parameter.continuous(0.5, 0.0, 1.0),
            })

    print(f"  reflectivity = {result['reflectivity']:.4f} "
          f"(target {target_reflectivity})")
    print(f"  objective    = {result.fitness:.8f}")
    print()


def report_available_algorithms():
    """Report which algorithms this build supports."""
    print("=" * 60)
    print("Available algorithms")
    print("=" * 60)

    with ParameterOptimization() as opt:
        for name, available in opt.availableAlgorithms().items():
            print(f"  {name:8s} {'yes' if available else 'no'}")

    print()
    print("  L-BFGS is normally unavailable: it comes from NLopt's LGPL Luksan")
    print("  sources, which PyHelios omits to keep the library MIT-licensed.")
    print("  Adam and BOBYQA cover the same use cases.")
    print()


def constrained_optimization():
    """Minimize x^2 + y^2 subject to x + y >= 1, stated as a constraint."""
    print("=" * 60)
    print("5. Constrained optimization (SLSQP)")
    print("=" * 60)

    with ParameterOptimization() as opt:
        if not opt.availableAlgorithms()["SLSQP"]:
            print("  SLSQP is unavailable in this build (requires NLopt); skipping.")
            print()
            return

        def simulation(p):
            # One pass returns everything the optimizer needs, so a simulation
            # this expensive runs once per parameter point rather than once per
            # constraint.
            return ConstrainedResult(
                objective=p["x"] ** 2 + p["y"] ** 2,
                objective_gradient={"x": 2.0 * p["x"], "y": 2.0 * p["y"]},
                # x + y >= 1 becomes 1 - x - y <= 0
                constraints=[1.0 - p["x"] - p["y"]],
                constraint_gradients=[{"x": -1.0, "y": -1.0}],
            )

        params = {
            "x": Parameter.continuous(0.0, -5.0, 5.0),
            "y": Parameter.continuous(0.0, -5.0, 5.0),
        }

        opt.setAlgorithm(SLSQP(max_iterations=100))
        result = opt.runConstrained(simulation, params, constraint_count=1)

    print(f"  x = {result['x']:.4f}  (expected 0.5)")
    print(f"  y = {result['y']:.4f}  (expected 0.5)")
    print(f"  objective = {result.fitness:.6f}  (expected 0.5)")

    # Without the constraint the optimum would be (0, 0) with objective 0.
    final = simulation(result.values)
    print(f"  constraint value = {final.constraints[0]:.6f}  (feasible when <= 0)")
    print()


def main():
    print()
    print("PyHelios ParameterOptimization Sample")
    print()

    try:
        report_available_algorithms()
        basic_optimization()
        gradient_based_optimization()
        two_stage_optimization()
        discrete_parameters()
        constrained_optimization()
        optimization_with_context()

    except ParameterOptimizationError as e:
        print(f"ParameterOptimization unavailable: {e}")
        return 1

    print("All examples completed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
