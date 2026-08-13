# ParameterOptimization Plugin Documentation {#ParameterOptimizationDoc}

## Overview

The ParameterOptimization plugin calibrates named model parameters against an
objective function you supply. You describe the parameters and their bounds, write
a function that scores a candidate parameter set, and the plugin searches for the
set that minimizes that score.

The objective is an ordinary Python callable. It can run a full Helios simulation —
build geometry, run radiation and energy balance, compare against measurements —
and return a scalar error. That makes this plugin the natural way to fit model
parameters to observed data.

Six algorithms are available, in two families:

**Global search** — no gradient required, handles rough or multi-modal objectives:

| Algorithm | Best for |
|---|---|
| `GeneticAlgorithm` | Large or awkward search spaces; searches integer and categorical parameters natively |
| `CMAES` | Continuous, non-separable problems; a strong general-purpose default |
| `BayesianOptimization` | Expensive objectives where you can afford few evaluations |

**Local search** — refines a good starting point:

| Algorithm | Best for |
|---|---|
| `Adam` | Gradient-based, noise-tolerant, no external dependency |
| `BOBYQA` | Derivative-free polishing of a global-search result |
| `SLSQP` | Gradient-based; the only algorithm supporting nonlinear constraints |

A common pattern is to run a global search first and polish the result with a local
one — see [Two-stage optimization](#two-stage) below.

## System Requirements

- **Platforms**: Windows, Linux, macOS
- **Dependencies**: none — NLopt is bundled and built from source
- **GPU**: not required
- **Memory**: negligible; the objective dominates

## Installation

The plugin is part of the default build:

```bash
build_scripts/build_helios --clean
```

To check availability:

```python
from pyhelios.plugins import print_plugin_status
print_plugin_status()
```

## Quick Start

```python
from pyhelios import ParameterOptimization, Parameter, GeneticAlgorithm

def objective(params):
    # Return a scalar cost to minimize
    return (params["x"] - 3.0) ** 2 + (params["y"] + 1.0) ** 2

with ParameterOptimization() as opt:
    opt.setAlgorithm(GeneticAlgorithm(generations=100, random_seed=1))
    result = opt.run(objective, {
        "x": Parameter.continuous(0.0, -5.0, 5.0),
        "y": Parameter.continuous(0.0, -5.0, 5.0),
    })

print(result["x"], result["y"], result.fitness)   # ~3.0, ~-1.0, ~0.0
```

The objective receives a `{name: value}` dict and returns a float. The result
exposes `result["name"]` for a single value, `result.values` for all of them as a
plain dict, and `result.parameters` for the full `Parameter` objects with their
bounds intact.

## Examples

### Calibrating against measured data

Replace `run_my_helios_simulation` with your own model. For a runnable example that
drives a real `Context`, see `docs/examples/parameteroptimization_sample.py`.

```python
from pyhelios import ParameterOptimization, Parameter, CMAES

measured = [(400, 12.1), (800, 21.4), (1200, 26.0)]

def objective(params):
    total = 0.0
    for par, observed in measured:
        # Your model goes here: returns assimilation at this PAR level.
        predicted = run_my_helios_simulation(par, params["Vcmax"], params["Jmax"])
        total += (predicted - observed) ** 2
    return total

with ParameterOptimization() as opt:
    opt.setAlgorithm(CMAES(max_evaluations=300, random_seed=1))
    result = opt.run(objective, {
        "Vcmax": Parameter.continuous(60.0, 20.0, 150.0),
        "Jmax": Parameter.continuous(120.0, 40.0, 300.0),
    })

print(f"Vcmax={result['Vcmax']:.1f}, Jmax={result['Jmax']:.1f}, SSE={result.fitness:.3f}")
```

### Gradient-based optimization

Adam, L-BFGS, and SLSQP need a gradient. Supply one directly:

```python
from pyhelios import ParameterOptimization, Parameter, Adam

def objective(p):
    return p["x"] ** 2 + p["y"] ** 2

def gradient(p):
    # Must return an entry for every parameter
    return {"x": 2.0 * p["x"], "y": 2.0 * p["y"]}

params = {
    "x": Parameter.continuous(1.0, -5.0, 5.0),
    "y": Parameter.continuous(1.0, -5.0, 5.0),
}

with ParameterOptimization() as opt:
    opt.setAlgorithm(Adam(max_iterations=500, learning_rate=0.05))
    result = opt.run(objective, params, gradient=gradient)
```

Or let the plugin estimate it numerically, at a cost of 2N extra objective
evaluations per gradient:

```python
    result = opt.run(objective, params, finite_difference=True)
```

### Integer and categorical parameters

**Use `GeneticAlgorithm` for discrete parameters.** It is the only algorithm that
searches integer and categorical spaces correctly.

Every other algorithm (`CMAES`, `BayesianOptimization`, `Adam`, `BOBYQA`, `SLSQP`,
`L-BFGS`) searches a continuous space and requires all parameters to be `FLOAT`.
Passing an `INTEGER` or `CATEGORICAL` parameter to one of them raises `ValueError`
naming the parameter and its type:

```python
opt.setAlgorithm(CMAES(max_evaluations=200))
opt.run(objective, {"n": Parameter.categorical(5.0, [5.0, 12.0, 20.0])})
# ValueError: CMAES requires every parameter to be FLOAT, but 'n' is CATEGORICAL.
```

PyHelios performs this check itself. Older helios-core revisions do not reject
discrete parameters in `CMAES` and `BayesianOptimization`, where a `CATEGORICAL`
parameter would otherwise optimize to `0.0` — outside its own category list — with
no diagnostic.

```python
from pyhelios import ParameterOptimization, Parameter, GeneticAlgorithm

params = {
    "leaf_count": Parameter.integer(10.0, 1.0, 50.0),
    "leaf_angle": Parameter.continuous(45.0, 0.0, 90.0),
    "species": Parameter.categorical(0.0, [0.0, 1.0, 2.0]),
}

def objective(p):
    # Stand-in for a Helios simulation driven by these parameters.
    return (p["leaf_count"] - 20.0) ** 2 + (p["leaf_angle"] - 30.0) ** 2

with ParameterOptimization() as opt:
    opt.setAlgorithm(GeneticAlgorithm(generations=200, population_size=40))
    result = opt.run(objective, params)
```

### Constrained optimization

`SLSQP` solves problems with nonlinear inequality constraints — "maximize A subject
to E below a budget" — stated directly rather than approximated with a penalty. Each
constraint is satisfied when its value is `<= 0`, so a requirement like `x + y >= 1`
is written `1 - x - y <= 0`.

The simulation returns the objective, the constraints, and every gradient together as
a `ConstrainedResult`. The optimizer caches each result per parameter point, so a
simulation that runs a full Helios scene is evaluated **once** per point no matter how
many constraints there are:

```python
from pyhelios import (ParameterOptimization, ConstrainedResult, Parameter, SLSQP)

def simulation(p):
    # One pass computes everything the optimizer needs.
    return ConstrainedResult(
        objective=p["x"] ** 2 + p["y"] ** 2,
        objective_gradient={"x": 2 * p["x"], "y": 2 * p["y"]},
        constraints=[1.0 - p["x"] - p["y"]],          # x + y >= 1
        constraint_gradients=[{"x": -1.0, "y": -1.0}],
    )

params = {
    "x": Parameter.continuous(0.0, -5.0, 5.0),
    "y": Parameter.continuous(0.0, -5.0, 5.0),
}

with ParameterOptimization() as opt:
    opt.setAlgorithm(SLSQP(max_iterations=100))
    result = opt.runConstrained(simulation, params, constraint_count=1)
    print(result["x"], result["y"], result.fitness)   # ~0.5 0.5 0.5
```

`constraint_count` is required and fixed for the run: the buffers the simulation
writes into are sized before it is first called, so the count cannot be discovered by
calling it.

Constraints are satisfied to a tolerance rather than exactly. If feasibility matters,
check the returned parameters:

```python
final = simulation(result.values)
assert all(c <= 1e-6 for c in final.constraints)
```

When the objective and constraints really are independent functions,
`make_constrained_simulation` composes them — at the cost of calling every function at
each parameter point, which forfeits the single-pass advantage above:

```python
from pyhelios import make_constrained_simulation

simulation = make_constrained_simulation(
    lambda p: p["x"] ** 2 + p["y"] ** 2,
    lambda p: {"x": 2 * p["x"], "y": 2 * p["y"]},
    [(lambda p: 1.0 - p["x"] - p["y"], lambda p: {"x": -1.0, "y": -1.0})],
)
```

### Two-stage optimization {#two-stage}

Global search finds the right basin; local search refines within it. Because the
result carries full `Parameter` objects, it can be passed straight back in:

```python
from pyhelios import ParameterOptimization, Parameter, CMAES, BOBYQA

def objective(p):
    return (p["x"] - 3.0) ** 2 + (p["y"] + 1.0) ** 2

params = {
    "x": Parameter.continuous(0.0, -10.0, 10.0),
    "y": Parameter.continuous(0.0, -10.0, 10.0),
}

with ParameterOptimization() as explorer:
    explorer.setAlgorithm(CMAES.explore())
    coarse = explorer.run(objective, params)

with ParameterOptimization() as refiner:
    refiner.setAlgorithm(BOBYQA())
    final = refiner.run(objective, coarse.parameters)
```

### Tuning presets

`GeneticAlgorithm`, `BayesianOptimization`, and `CMAES` offer `explore()` and
`exploit()` presets, read directly from the native library so they always match
the tuned upstream values:

```python
opt.setAlgorithm(CMAES.explore())    # wider search
opt.setAlgorithm(CMAES.exploit())    # tighter refinement
```

Genetic algorithm operators can also be selected explicitly:

```python
from pyhelios import GeneticAlgorithm, BLXPCACrossover, HybridMutation

opt.setAlgorithm(GeneticAlgorithm(
    generations=200,
    population_size=40,
    crossover=BLXPCACrossover(alpha=0.5),
    mutation=HybridMutation(rate=0.2),
))
```

### Recording progress

```python
with ParameterOptimization() as opt:
    opt.setPrintProgress(True)                  # print to stdout
    opt.setResultFile("result.csv")             # final parameters
    opt.setProgressFile("progress.csv")         # per-generation history
    result = opt.run(objective, params)
```

Output paths must end in `.csv` or `.txt`.

## Error Handling

An exception raised inside your objective aborts the run and is re-raised with its
original type and traceback, so it points at your own code:

```python
def objective(params):
    if params["x"] < 0:
        raise ValueError("negative x is unphysical")
    return simulate(params)

try:
    result = opt.run(objective, params)
except ValueError as e:
    print(f"Objective failed: {e}")     # traceback points into objective()
```

`KeyboardInterrupt` works the same way, so Ctrl-C cleanly stops a long run.

Objective values are checked for finiteness. A `NaN` or infinity is rejected with a
clear error rather than silently corrupting the optimizer's internal state:

```python
ValueError: Objective function returned nan, which is not a finite number.
```

Gradient functions must return an entry for every parameter; omissions and unknown
keys are both reported by name.

Selecting an unavailable algorithm raises immediately, rather than failing part-way
through a long run:

```python
from pyhelios import ParameterOptimization

with ParameterOptimization() as opt:
    print(opt.availableAlgorithms())
    # {'GA': True, 'BO': True, 'CMAES': True, 'ADAM': True,
    #  'LBFGS': False, 'BOBYQA': True, 'SLSQP': True}
```

## Troubleshooting

**The optimization does not converge.** Widen the bounds, increase `generations` or
`max_evaluations`, or try `explore()` presets. If the objective is noisy, prefer
`GeneticAlgorithm` or `Adam` over the derivative-free local methods.

**Results differ between runs.** The population-based algorithms seed from
`std::random_device` by default. Set `random_seed` to any non-zero value for
reproducibility.

**`Adam is a gradient-based algorithm and requires a gradient`.** Pass
`gradient=<callable>` or `finite_difference=True`.

**L-BFGS reports as unavailable.** This is expected — see Limitations.

**The run is slow.** The objective dominates: with a genetic algorithm the plugin
calls it up to `generations x population_size` times. Reduce the evaluation budget, or
use `BayesianOptimization`, which is designed for expensive objectives.

## Performance Notes

Each objective evaluation crosses from C++ back into Python. That transition costs
well under a microsecond and is irrelevant next to any real Helios simulation, but
it means the total number of evaluations is what governs runtime. Budget
accordingly:

- `GeneticAlgorithm`: at most `generations x population_size`, and in practice roughly
  a third to a half of it — individuals carried forward unchanged are not re-evaluated.
  Treat the product as an upper bound when budgeting.
- `CMAES` / `BayesianOptimization`: exactly `max_evaluations`
- `Adam` / `BOBYQA` / `SLSQP`: up to `max_iterations`, plus `2N` per gradient when
  using `finite_difference=True`
- `runConstrained`: one simulation call per parameter point regardless of how many
  constraints there are — the result is cached across the optimizer's separate
  objective and constraint queries

## Limitations

**L-BFGS is unavailable in default builds.** NLopt's L-BFGS comes from its
LGPL-2.1 Luksan sources, which PyHelios omits so the distributed library stays
MIT-licensed. `Adam` covers the same gradient-based use case with better noise
tolerance, and `BOBYQA` covers derivative-free local refinement.

Enabling it means accepting the LGPL obligations for anything you redistribute. The
setting is written by the build script, not read from the CMake command line — a
`-DHELIOS_NLOPT_LUKSAN=ON` flag is overridden — so change the `set(HELIOS_NLOPT_LUKSAN
OFF ...)` line emitted in `build_scripts/build_helios.py` and rebuild from clean.

**Constraints require SLSQP and continuous parameters.** No algorithm supports both
discrete parameters and nonlinear constraints. For a discrete problem, fold the
constraint into the objective as a penalty term and use `run()`:

```python
def objective(params):
    cost = base_cost(params)
    violation = max(0.0, 1.0 - params["x"] - params["y"])   # want x + y >= 1
    return cost + 100.0 * violation ** 2
```

Note that a penalty does not guarantee the final solution is feasible — check it.

**No live progress callback.** The plugin reports progress via stdout
(`setPrintProgress`) and CSV files (`setProgressFile`), not a callback hook. To
track progress programmatically, count evaluations inside your own objective.

**Partial results are not recoverable.** If the objective raises, the run is torn
down and no best-so-far value is returned.

**One run at a time per instance.** The optimizer is stateful and not reentrant;
calling `run()` from inside its own objective raises. Use separate instances.
