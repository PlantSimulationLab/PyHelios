# Soil Transport Plugin Documentation {#SoilTransportDoc}

[TOC]

<table>
<tr><th>Dependencies</th><td>None required. NVIDIA CUDA (optional) enables the GPU backend for the full 3D solver.</td></tr>
<tr><th>Python Import</th><td>`from pyhelios import SoilTransportModel`</td></tr>
<tr><th>Main Class</th><td>\ref pyhelios.SoilTransport.SoilTransportModel "SoilTransportModel"</td></tr>
</table>

## Overview

The soil transport plugin solves variably saturated subsurface water flow (the Richards equation) in one, two-and-a-half (quasi-3D), or three dimensions. It is intended for coupling with plant models: drip or sprinkler irrigation, root water uptake, and bare-soil evaporation can all be applied as boundary conditions and sink terms, and point sensors can log water content or pressure head over time.

Three solve modes are available through \ref pyhelios.SoilTransport.SoilTransportModel.setSolverType "setSolverType()":

- **`SolverType.SOLVER_1D`** (the default): a grid of independent vertical columns (fastest; no lateral flow).
- **`SolverType.SOLVER_QUASI_3D`**: vertical columns with periodic operator-split horizontal coupling.
- **`SolverType.SOLVER_3D`**: the fully coupled 3D Richards equation, with an optional GPU backend.

Soil hydraulic behavior follows the van Genuchten–Mualem model by default, with Gardner exponential and linear models available as alternatives. Twelve standard USDA soil textures are provided in a built-in library (see [Soil hydraulic properties](#SWT_SoilProps)). A new model uses loam.

PyHelios wraps the plugin's high-level `SoilTransportModel` class, the class most users interact with in C++ as well. The lower-level C++ solver classes (`SoilColumn`, `SoilGrid`, `SoilSolver3D` and `RootSoilCoupling`) are not exposed, so the features that only they provide are C++-only: per-cell 3D geometry, specified-head cells and specific storage (`SoilSolver3D`), and radial geometry and the head-limited "atmospheric" top boundary (`SoilColumn`).

## System Requirements

<table>
  <tr>
    <th>Dependencies</th>
    <td>None required</td>
  </tr>
  <tr>
    <th>Platforms</th>
    <td>Windows, Linux, macOS</td>
  </tr>
  <tr>
    <th>GPU</th>
    <td>Not required. When the native library is built with CUDA and a usable NVIDIA device is present, the full 3D solver runs on it automatically; otherwise it runs on the CPU with OpenMP. The column solvers always run on the CPU.</td>
  </tr>
</table>

## Known Issues

- The `NonlinearMethod.NGS_FAS` nonlinear method is semi-implicit in the hydraulic conductivity (lagged within each step), so its mass-conservation error grows with both timestep and grid refinement. Keep the timestep moderate (or use adaptive stepping) when accurate conservation matters; use `NonlinearMethod.PICARD` for machine-exact conservation.
- The `NonlinearMethod.M_SCHEME` (Kirchhoff-transform) method is restricted to **homogeneous** van Genuchten soil: `run()` raises an error if the soil properties differ between cells or use `SoilModel.MODIFIED_VAN_GENUCHTEN`.
- The CPU solver synchronizes its OpenMP threads many times per iteration. By default it uses one thread per physical core, which leaves the hyperthreads free for other work, but if more processes than physical cores keep the machine busy, the spinning threads can slow it down many-fold. On a heavily shared machine set the environment variable `OMP_WAIT_POLICY=passive` (about 10% slower on an idle machine) or lower `SolverParameters.num_threads`.
- The GPU backend is double-precision throughout; commodity cards with a low FP64 ratio provide little speedup over a multicore CPU. An A100/H100-class device is recommended.
- Surface ponding and overland flow are not yet modeled; infiltration in excess of the surface capacity is not routed laterally.
- Explicit root geometry is not supported yet. Describe a plant's root zone with `setRootDistribution()` or `setRootDistributionWeibull()`.
- `setRootRadialConductivity()` stores its value, but the current root uptake model does not use it.

## Quick Start

A uniform, moderately dry loam with steady surface infiltration and free drainage at the base. The wetting front descends over the first hour.

```python
from pyhelios import Context, SoilTransportModel, SolverType
from pyhelios.types import vec3

with Context() as context:
    with SoilTransportModel(context) as soil:
        # A 1 m x 1 m x 1 m block of soil, 20 x 20 x 40 cells.
        soil.defineSoilDomain(vec3(0, 0, 0), vec3(1, 1, 1))
        soil.setGridResolution(20, 20, 40)
        soil.setSolverType(SolverType.SOLVER_3D)

        soil.setSoilPropertiesFromTexture("loam")
        soil.setInitialCondition(-1.0)         # uniform pressure head [m]
        soil.setTopBoundaryFlux(2e-6)          # steady infiltration [m/s]
        soil.setBottomBoundaryFreeDrainage()

        for step in range(60):
            soil.run(60.0)                     # advance 60 s

        theta = soil.getWaterContent(vec3(0.5, 0.5, -0.1))
        print("Near-surface water content:", theta)
        print("Total storage [m^3]:", soil.getTotalWaterStorage())
```

The domain origin is the top surface: the domain extends downward from z = 0 to z = -1 m, so points inside it have negative z. The domain, grid resolution and solver type must be set before the domain is set up, which happens in `initializeDomain()` or in the first call that needs it (such as `setInitialCondition()`). Changing them afterwards raises an error.

## Primitive Data

The plugin operates on its own internal finite-volume grid and does **not** require any input primitive data from the Context. It only writes primitive data when the soil geometry is rendered with \ref pyhelios.SoilTransport.SoilTransportModel.addSoilVisualization "addSoilVisualization()" / \ref pyhelios.SoilTransport.SoilTransportModel.updateSoilVisualization "updateSoilVisualization()".

### Output Primitive Data (visualization geometry)

| Primitive Data Label | Symbol | Units | Data Type | Description |
| -------------------- | ------ | ----- | --------- | ----------- |
| water_content | \f$\theta\f$ | m\f$^3\f$ m\f$^{-3}\f$ | `float` | Volumetric water content sampled onto each face patch (`SoilColorMode.WATER_CONTENT` only) |
| pressure_head | \f$h\f$ | m | `float` | Pressure head sampled onto each face patch (`SoilColorMode.PRESSURE_HEAD` only) |
| soil_sample_pos | N/A | m | `vec3` | Sample location used by `updateSoilVisualization()` to re-sample existing geometry in place (field modes only) |
| soil_cut_face | N/A | N/A | `int` | 1 for cross-section faces exposed by a cut or cutaway (off the domain boundary), 0 otherwise |

## Governing Equations

### The Richards equation

Water movement is governed by the mixed form of the Richards equation, written here with the vertical coordinate \f$z\f$ positive upward and pressure head \f$h\f$ (m):

\f[
  \frac{\partial \theta(h)}{\partial t} = \nabla \cdot \left[ K(h)\left(\nabla h + \hat{\mathbf{z}}\right) \right] - S,
\f]

where \f$\theta\f$ is the volumetric water content (m\f$^3\f$ m\f$^{-3}\f$), \f$K\f$ is the unsaturated hydraulic conductivity (m s\f$^{-1}\f$), and \f$S\f$ is a sink (root uptake / evaporation, s\f$^{-1}\f$). The \f$\hat{\mathbf{z}}\f$ term is the gravitational contribution.

### Constitutive relations

The van Genuchten–Mualem model relates effective saturation \f$S_e\f$, water content, and conductivity to pressure head. For \f$h<0\f$,

\f[
  S_e(h) = \left[1 + |\alpha h|^{n}\right]^{-m}, \qquad m = 1 - \frac{1}{n},
\f]

with \f$S_e = 1\f$ for \f$h \ge 0\f$. Water content and conductivity follow as

\f[
  \theta(h) = \theta_r + (\theta_s - \theta_r)\,S_e(h), \qquad
  K(S_e) = K_s\, S_e^{1/2}\left[1 - \left(1 - S_e^{1/m}\right)^{m}\right]^{2},
\f]

where \f$\theta_r\f$ and \f$\theta_s\f$ are the residual and saturated water contents, \f$\alpha\f$ (m\f$^{-1}\f$) is the inverse air-entry scale, \f$n\f$ is the pore-size distribution index, and \f$K_s\f$ is the saturated conductivity. The specific moisture capacity used by the solvers is \f$C(h) = \mathrm{d}\theta/\mathrm{d}h\f$.

#### Modified van Genuchten–Mualem model (air-entry value)

For \f$n < 2\f$ the slope \f$\mathrm{d}K/\mathrm{d}h\f$ of the standard model is unbounded as \f$h \to 0^-\f$, so K drops very steeply just below saturation. Cells that sit at saturation, such as the cells under a drip emitter delivering more than \f$K_s\f$, can then stall the nonlinear solver. `SoilModel.MODIFIED_VAN_GENUCHTEN` (Ippisch, Vogel & Bastian 2006) adds an air-entry head \f$h_e < 0\f$ (`SoilProperties.h_e`): the soil is saturated for \f$h \ge h_e\f$, and for \f$h < h_e\f$

\f[
  S_e = \frac{\left[1 + |\alpha h|^{n}\right]^{-m}}{S_c}, \qquad
  K = K_s\, S_e^{1/2}\left[\frac{1 - \left(1 - (S_e S_c)^{1/m}\right)^{m}}{1 - \left(1 - S_c^{1/m}\right)^{m}}\right]^{2},
  \qquad S_c = \left[1 + |\alpha h_e|^{n}\right]^{-m},
\f]

so \f$\theta = \theta_s\f$ and \f$K = K_s\f$ at \f$h_e\f$, and \f$\mathrm{d}K/\mathrm{d}h\f$ stays finite. With the same parameters as a standard soil, below \f$h_e\f$ the water content is the standard one rescaled by \f$1/S_c\f$ and the conductivity the standard one times \f$F_K = 1/\left(S_c^{1/2}\left[1 - (1 - S_c^{1/m})^{m}\right]^2\right)\f$ (1.3 for sand, 1.7 for loam, 10 for clay at \f$h_e\f$ = -2 cm). \ref pyhelios.SoilTransport.toModifiedVanGenuchten "toModifiedVanGenuchten()" therefore converts standard parameters by setting \f$\theta_s\f$ and \f$K_s\f$ to the standard \f$\theta\f$ and \f$K\f$ at \f$h_e\f$: the modified model is then the standard one truncated at \f$h_e\f$, identical for \f$h < h_e\f$ and saturated above. Passing `match_standard_curves=False` keeps \f$\theta_s\f$ and \f$K_s\f$ instead (HYDRUS's convention). The model is supported by the column, quasi-3D and 3D solvers on the CPU and GPU, except `NonlinearMethod.M_SCHEME`.

#### Relative-conductivity spline near saturation

Alternatively the standard model can keep \f$K_s\f$ at saturation with a finite slope: with `SoilProperties.kr_spline_start` \f$= S_1 < 1\f$ (e.g. 0.9999), the relative conductivity above \f$S_e = S_1\f$ is a cubic Hermite spline from the standard value and slope at \f$S_1\f$ to 1 with zero slope at saturation. The retention curve is unchanged.

A Gardner exponential soil, \f$K(h) = K_s\,e^{\alpha h}\f$, is also available via the `SoilProperties.gardner()` named constructor; it admits closed-form steady-infiltration solutions used in the plugin's verification tests. A linear soil, \f$S_e = 1 + \alpha h\f$ (between 0 and 1) with \f$K = K_s S_e\f$, is available via `SoilProperties.linear()`, for verification against closed-form solutions.

### Discretization

The domain is discretized with a cell-centered finite-volume scheme. Specified-head (Dirichlet) boundary faces are treated as a virtual cell half a cell beyond the face and use the same interblock weighting as interior faces, with flow direction set by total head. Interblock conductivities on cell faces are formed by harmonic, geometric, arithmetic, upstream, or upstream relative-permeability weighting (`SolverParameters.K_weighting`). The default is the arithmetic mean, which in grid-convergence tests (infiltration into dry soil, ponded infiltration, layered recharge, evaporation and 3D drip irrigation) was the most accurate overall at practical resolutions and never failed to converge; the harmonic mean nearly blocks infiltration from a wet cell into a dry one. Upstream weighting takes the conductivity of the donor cell (by total head). Upstream relative-permeability weighting (`KWeighting.UPSTREAM_KR`) multiplies the harmonic mean of the two cells' saturated conductivities by the donor cell's relative permeability (the scheme used by MODFLOW 6); it is the better choice across sharp layer interfaces, where taking the donor's full \f$K\f$ lets a coarse layer's \f$K_s\f$ control flow into a fine one.

Time integration uses backward Euler, giving a nonlinear algebraic system at each step that is solved by one of the strategies below. Backward Euler conserves water exactly, whatever the step sizes. The 3D solver can use second-order BDF2 instead (`SolverParameters.bdf2`), but BDF2 does not conserve water when sources or boundary fluxes change: an emitter switched on and off under adaptive stepping lost 1.6% of its water, and with daily recharge over a year (MODFLOW 6 Test 2) the heads ended 29 cm low. Use BDF2 only with fixed steps and smooth forcing.

The 1D column solver uses the mass-conservative Modified-Picard form of Celia et al. (1990) with a direct tridiagonal solve, or Newton with the default `NonlinearMethod.NEWTON_ANALYTIC`. With fixed stepping the column solvers advance each `run(dt)` in sub-steps of at most `SolverParameters.dt_max`.

### Nonlinear solvers (3D)

The full 3D solver offers several nonlinear strategies, selected with `SolverParameters.nonlinear_method`:

- **`NEWTON_ANALYTIC`** (default): Newton–Raphson on an explicitly assembled 7-point Jacobian with analytic derivatives, including the \f$\mathrm{d}K/\mathrm{d}h\f$ terms that Modified Picard drops, so convergence is quadratic near the solution. The nonsymmetric linear system is solved with ILU(0)-preconditioned BiCGSTAB (on large grids, block-Jacobi ILU(0) with one lateral slab of whole vertical columns per thread). Robustness comes from limiting each cell's effective-saturation change per iteration (unsaturated cells take the update in water-content space; cells with specific storage near or below the water table take it in head) and a backtracking line search. A step converges when every cell's water imbalance is negligible, so mass is conserved to solver tolerance. With adaptive stepping a step that fails to converge is retried with a smaller \f$\Delta t\f$; with fixed steps the solver falls back to Modified Picard for that step on uniform grids and, if the step still fails, sub-steps the interval adaptively. On the GPU the same algorithm runs device-resident, with BiCGSTAB preconditioned by vertical-line relaxation or a geometric-multigrid V-cycle.
- **`PICARD`**: the Modified-Picard iteration of Celia et al. (1990), which linearizes about \f$C(h)\f$ to yield a symmetric positive-definite system each iteration, solved by preconditioned conjugate gradient with geometric multigrid. Robust and machine-exact in mass; also the fallback of a failed `NEWTON_ANALYTIC` step.
- **`NEWTON`**: a Jacobian-free Newton–Krylov (JFNK) scheme using matrix-free Jacobian–vector products and GMRES preconditioned by a single multigrid V-cycle. Roughly 35% faster than Picard on stiff dry-front steps.
- **`PICARD_NEWTON`**: a Picard warm-up followed by Newton for additional globalization.
- **`NGS_FAS`**: lagged-conductivity nonlinear Gauss–Seidel smoothing within a full approximation scheme (FAS) multigrid (Gu & Wang, 2026); its operator uses harmonic-mean faces, so use it with `KWeighting.HARMONIC`. Iteration counts are grid-independent and the smoother is red-black parallel on the GPU; semi-implicit, so mass error is \f$O(\Delta t)\f$.
- **`M_SCHEME`**: a Kirchhoff-transform linearization with a certified a-posteriori error estimator (Mitra & Pop and co-workers, 2025). Homogeneous soil only; CPU only.

#### Failed steps

The 1D column and the 3D solver (CPU and GPU) apply the same rules:

- A cell's residual is accepted when it is small in water-content units or relative to the sum of the magnitudes of its terms; that sum includes the round-off of each face flux, so cells far thinner than the head change across them can still converge in double precision.
- The line search measures the residual in water-flux units (weighted by cell volume), so thin cells do not dominate it on graded grids.
- Newton gives up after ten damped iterations in a row that each remove less than 2% of the residual, the way it behaves when the step has no solution (e.g. a flux the soil can no longer deliver).
- A Picard step run as the fallback of a failed Newton step is accepted only if the water balance also closes.
- With fixed steps a failed step is rescued by sub-stepping it, down to 1/1000 of the step. With `SolverParameters.substep_on_failure = False` a step with no solution fails at once instead of after the sub-steps.
- A failed step leaves the state as it was before that step with every nonlinear method. `run()` raises `SoilTransportModelError` when it cannot complete a step, and its clock and the cumulative root uptake count only the time that was advanced (with adaptive stepping, or the sub-steps of the column solvers, that can be part of `dt`). An error raised part-way through a step for another reason (e.g. a quasi-3D cell reaching saturation, or a GPU failure) leaves the state and the clock as they were before the call.

#### GPU

The full 3D solver runs on an NVIDIA GPU automatically when the native library was built with CUDA and a usable device is present (`SoilTransportModel.isGPUAvailable()`; setting the environment variable `HELIOS_NO_GPU` hides it), except with `NonlinearMethod.M_SCHEME`, which runs on the CPU only. `disableGPU()` selects the CPU; `enableGPU()` requires the GPU and raises an error if none is usable. The column solvers always run on the CPU. A CUDA failure during a solve raises an error and leaves the state as it was before the step.

### Boundary conditions and sinks

Each boundary may be a specified pressure head (`setTopBoundaryPressure()`, `setBottomBoundaryPressure()`), a specified flux (`setTopBoundaryFlux()`, positive into the soil; `setBottomBoundaryFlux()`, positive out of the domain), or, at the base, unit-gradient free drainage (`setBottomBoundaryFreeDrainage()`). Surface irrigation is applied with `addSurfaceEmitter()`: with the 3D solver a drip emitter's discharge is spread over a circular wetting footprint (`radius`, default 0.1 m) for grid independence, and with the column solvers it enters the surface layer of the column containing the emitter. Bare-soil evaporation (`setSurfaceEvaporation()`, 3D solver only) and root uptake enter the equation through the sink term \f$S\f$; root uptake is partitioned over the soil cells according to a Vrugt-type (`RootDistributionParams`) or Weibull (`WeibullRootParameters`) root-density profile.

Root uptake is limited by soil water availability. Each root cell's share is scaled by a Feddes water-stress factor \f$\alpha(h)\f$, equal to 1 above \f$h_\mathrm{onset}\f$ (default \f$-4\f$ m) and falling linearly to 0 at \f$h_\mathrm{wilt}\f$ (default \f$-150\f$ m, about \f$-1.5\f$ MPa). Uptake is redistributed toward unstressed roots (Jarvis compensation), so the full transpiration demand is met while the root-weighted mean \f$\omega = \sum \alpha f / \sum f\f$ is at least \f$\omega_c\f$ (default 0.5); below that the uptake is \f$T\,\omega/\omega_c\f$. Set the parameters with `setRootWaterStressParameters()` and read the applied uptake with `getRootUptakeFlux()`. The root-zone water potential returned for plant-hydraulics coupling (`getSoilWaterPotential()`) is weighted the same way, by \f$f\,\alpha\f$, so it reflects the soil the roots are drawing from.

## Parameters

### Soil hydraulic properties {#SWT_SoilProps}

The \ref pyhelios.SoilTransport.SoilProperties "SoilProperties" dataclass holds the van Genuchten–Mualem (or Gardner / linear) parameters:

| Field | Symbol | Units | Description | Default (sand) |
| ----- | ------ | ----- | ----------- | -------------- |
| theta_r | \f$\theta_r\f$ | m\f$^3\f$ m\f$^{-3}\f$ | Residual water content | 0.045 |
| theta_s | \f$\theta_s\f$ | m\f$^3\f$ m\f$^{-3}\f$ | Saturated water content | 0.43 |
| alpha | \f$\alpha\f$ | m\f$^{-1}\f$ | Inverse air-entry scale (van Genuchten \f$\alpha\f$ / Gardner rate) | 14.5 |
| n | \f$n\f$ | – | Pore-size distribution index (van Genuchten only) | 2.68 |
| K_s | \f$K_s\f$ | m s\f$^{-1}\f$ | Saturated hydraulic conductivity | \f$8.25\times10^{-5}\f$ |
| model | – | – | Constitutive model (`SoilModel`) | `VAN_GENUCHTEN` |
| h_e | \f$h_e\f$ | m | Air-entry head (`MODIFIED_VAN_GENUCHTEN` only, < 0) | 0 |
| kr_spline_start | \f$S_1\f$ | – | Effective saturation where the relative-conductivity spline starts (`VAN_GENUCHTEN` only; 1 = off) | 1 |

Properties may be built directly, via the named constructors `SoilProperties.vanGenuchten()` / `SoilProperties.modifiedVanGenuchten()` / `SoilProperties.gardner()` / `SoilProperties.linear()`, or looked up by USDA texture with \ref pyhelios.SoilTransport.getSoilPropertiesFromTexture "getSoilPropertiesFromTexture()". The native plugin checks that properties are physical when they are set: it requires \f$0 \le \theta_r < \theta_s \le 1\f$, \f$\alpha > 0\f$, \f$K_s > 0\f$ and \f$0 <\f$ `kr_spline_start` \f$\le 1\f$, plus \f$n > 1\f$ for the van Genuchten models and \f$h_e < 0\f$ for the modified model.

The texture library holds the Carsel & Parrish (1988) class averages. The library has van Genuchten parameters only, so the texture functions accept `SoilModel.VAN_GENUCHTEN` and `SoilModel.MODIFIED_VAN_GENUCHTEN` and raise `ValueError` for the Gardner and linear models. `getSoilPropertiesFromTexture(texture, SoilModel.MODIFIED_VAN_GENUCHTEN)` (or `setSoilPropertiesFromTexture(texture, SoilModel.MODIFIED_VAN_GENUCHTEN)`) converts them with `toModifiedVanGenuchten()` at \f$h_e\f$ = -2 cm (the value of HYDRUS's "van Genuchten–Mualem with an air-entry value of -2 cm" option): the Carsel & Parrish curves truncated at \f$h_e\f$. No class averages refitted for the air-entry model have been published for the 12 USDA classes; Schaap & van Genuchten (2006) give 4 texture groups at -4 cm. Available textures (also returned by `getAvailableSoilTextures()`): `sand`, `loamy_sand`, `sandy_loam`, `loam`, `silt`, `silt_loam`, `sandy_clay_loam`, `clay_loam`, `silty_clay_loam`, `sandy_clay`, `silty_clay`, and `clay`.

```python
from pyhelios import SoilModel, getSoilPropertiesFromTexture, toModifiedVanGenuchten

loam = getSoilPropertiesFromTexture("loam")
print(loam.theta_r, loam.theta_s, loam.alpha, loam.n, loam.K_s)

# The same soil with an air-entry head of -2 cm, by either route
air_entry = getSoilPropertiesFromTexture("loam", SoilModel.MODIFIED_VAN_GENUCHTEN)
same = toModifiedVanGenuchten(loam, -0.02)
print(air_entry.theta_s, same.theta_s)
```

### Solver parameters

The \ref pyhelios.SoilTransport.SolverParameters "SolverParameters" dataclass configures the nonlinear/linear solve and timestepping. Pass it to `setSolverParameters()`, which checks the whole set before storing any of it.

| Field | Units | Description | Default |
| ----- | ----- | ----------- | ------- |
| nonlinear_method | – | Nonlinear strategy (`NonlinearMethod`: NEWTON_ANALYTIC, PICARD, NEWTON, PICARD_NEWTON, NGS_FAS, M_SCHEME). The column solvers use Newton for NEWTON_ANALYTIC and Modified Picard for any other value. | NEWTON_ANALYTIC |
| max_picard_iterations | – | Maximum nonlinear iterations per step | 20 |
| picard_tolerance | m | Nonlinear convergence tolerance | \f$1\times10^{-5}\f$ |
| picard_omega | – | Under-relaxation factor (use 0.5–0.7 for sharp fronts) | 1.0 |
| anderson_depth | – | Anderson-acceleration depth for the Picard tail (0 = off) | 0 |
| K_weighting | – | Interblock conductivity weighting (`KWeighting`: DEFAULT/HARMONIC/GEOMETRIC/ARITHMETIC/UPSTREAM/UPSTREAM_KR) | DEFAULT (arithmetic) |
| K_min | m s\f$^{-1}\f$ | Additive conductivity floor easing dry-front infiltration, 3D solver (0 = off) | 0.0 |
| C_regularization | m\f$^{-1}\f$ | Regularization value for the specific moisture capacity at saturation | \f$1\times10^{-10}\f$ |
| num_threads | – | CPU threads for the 3D solver (0 = `OMP_NUM_THREADS` if set, else one per physical core) | 0 |
| enable_gravity | – | Include gravity in the flux (column solvers only; False for horizontal or capillarity-only problems) | True |
| bdf2 | – | 3D solver: BDF2 time integration instead of backward Euler (see Discretization above) | False |
| substep_on_failure | – | Sub-step a failed fixed step (down to 1/1000 of it) before reporting the failure | True |
| adaptive_dt | – | Enable \f$\Delta\theta\f$-controlled adaptive timestepping | False |
| dt_target_rel_change | – | Target per-step \f$|\Delta\theta|/(\theta_s-\theta_r)\f$ for step sizing | 0.03 |
| dt_safety | – | Safety factor applied to the adaptive step estimate | 0.9 |
| dt_growth_max | – | Maximum factor by which the step may grow in a single step | 2.0 |
| dt_reduction_min | – | Minimum factor for a single-step reduction | 0.25 |
| dt_failure_factor | – | Factor by which the step is decreased after a failed step | 0.5 |
| dt_min / dt_max | s | Timestep bounds | 0.01 / 3600 |
| horizontal_coupling_interval | – | Quasi-3D: couple laterally every N vertical steps (replaces an interval set by `enableHorizontalCoupling()`) | 1 |

The C++ struct also has deprecated adaptive-stepping fields that the solver no longer uses; they are not exposed.

## Coupling with Plant Hydraulics

The soil model supplies the soil water potential a plant's roots see, and the plant supplies the transpiration that the roots extract. Two unit conversions are needed:

- `getSoilWaterPotential(plant_id)` returns a pressure head in metres. \ref PlantHydraulicsDoc "PlantHydraulicsModel" works in MPa: multiply by 9.80665e-3 MPa/m (\f$\rho_w g\f$) before passing it to `setSoilWaterPotentialOfPlant()`.
- `setTranspiration(plant_id, transpiration)` takes a flux per unit ground area of the soil domain (m/s): a plant's volumetric transpiration rate (m\f$^3\f$ s\f$^{-1}\f$) divided by the domain's footprint area.

The models may be run at different timesteps (lagged coupling).

```python
from pyhelios import Context, PlantHydraulicsModel, SoilTransportModel, RootDistributionParams
from pyhelios.types import vec2, vec3

LATENT_HEAT = 2.45e6   # latent heat of vaporization of water [J/kg]
WATER_DENSITY = 1000.0 # [kg/m^3]

with Context() as context:
    leaf = context.addPatch(center=vec3(0, 0, 1), size=vec2(0.5, 0.5))
    context.setPrimitiveDataFloat(leaf, "latent_flux", 200.0)  # transpiration [W/m^2]

    with SoilTransportModel(context) as soil, PlantHydraulicsModel(context) as hydraulics:
        soil.defineSoilDomain(vec3(-0.5, -0.5, 0), vec3(1, 1, 1))  # 1 m^2 footprint, 1 m deep
        soil.setColumnResolution(40)
        soil.setInitialCondition(-2.0)

        hydraulics.run([leaf])            # groups the leaf into a plant
        plant = hydraulics.getPlantID(leaf)
        soil.setRootDistribution(plant, RootDistributionParams(z_max=1.0))

        # Leaf transpiration [m^3/s] per unit ground area of the 1 m^2 domain [m/s]
        volume_rate = 200.0 * context.getPrimitiveArea(leaf) / LATENT_HEAT / WATER_DENSITY
        soil.setTranspiration(plant, volume_rate / 1.0)

        for hour in range(24):
            soil.run(3600.0)
            psi_soil = soil.getSoilWaterPotential(plant) * 9.80665e-3   # m -> MPa
            hydraulics.setSoilWaterPotentialOfPlant(plant, psi_soil)
            hydraulics.run([leaf])

        print("Soil water potential:", psi_soil, "MPa")
        print("Stem water potential:", hydraulics.getStemWaterPotential(leaf), "MPa")
```

## Examples

### Drip irrigation with root uptake and sensors

Two drip emitters wet an initially dry loam while a plant transpires; a buried sensor logs the water content over the simulation and the series is written to CSV. The 3D solver uses adaptive timestepping to sub-step through the stiff wetting front.

```python
from pyhelios import (Context, SoilTransportModel, SolverType, SolverParameters,
                      RootDistributionParams, SoilMeasurement)
from pyhelios.types import vec3

with Context() as context:
    with SoilTransportModel(context) as soil:
        soil.defineSoilDomain(vec3(-0.5, -0.5, 0.0), vec3(1, 1, 1.5))
        soil.setGridResolution(24, 24, 32)
        soil.setSolverType(SolverType.SOLVER_3D)
        soil.setSolverParameters(SolverParameters(adaptive_dt=True))
        # soil.disableGPU()                     # the 3D solver uses a GPU when one is available

        soil.setSoilPropertiesFromTexture("loam")
        soil.setInitialCondition(-1.5)          # moderately dry
        soil.setTopBoundaryFlux(0.0)
        soil.setBottomBoundaryFreeDrainage()

        # Two drip emitters at the surface, ~2 L/h each.
        soil.addSurfaceEmitter(-0.25, 0.0, 5.6e-7)
        soil.addSurfaceEmitter(0.25, 0.0, 5.6e-7)

        # A single transpiring plant with a default root distribution.
        soil.setRootDistribution(1, RootDistributionParams())
        soil.setTranspiration(1, 5e-7)

        # A buried water-content sensor.
        sensor = soil.addSensor(vec3(0.0, 0.0, -0.2), SoilMeasurement.WATER_CONTENT)

        for hour in range(12):
            soil.run(3600.0)
            soil.recordSensors()
        soil.writeSensorData("soil_moisture.csv")

        print(f"Sensor {sensor} logged {len(soil.getSensorData(sensor))} samples; "
              f"root-weighted soil water potential is {soil.getSoilWaterPotential(1):.3f} m.")
```

### Visualizing the soil

`addSoilVisualization()` adds a block spanning the soil domain to the Context, with its outer faces colored by water content or pressure head from the current soil state, or shown with a plain dirt texture (`SoilColorMode.TEXTURE`). Optional fractions of the domain extent, measured from the origin corner, cut the block to show its interior:

- `addSoilVisualization(mode, keep_fraction)` keeps the given fraction of each axis.
- `addSoilVisualization(mode, fraction_min, fraction_max)` keeps a sub-box; a zero-thickness axis gives a cross-section slice.
- `addSoilVisualization(mode, fraction_min, fraction_max, region=SoilRegion.REMOVE)` cuts the sub-box out of the domain (a cutaway); anchor it at a domain corner for a clean notch.

The faces are colored on one range shared by the whole visualization. `updateSoilVisualization()` re-samples the field onto existing faces without rebuilding them, which suits animations, but it only rewrites the primitive data; color the primitives by that data in the \ref VisualizerDoc "Visualizer" to show the new values.

```python
from pyhelios import Context, SoilTransportModel, SoilColorMode, SoilRegion, Visualizer
from pyhelios.types import vec3

with Context() as context:
    with SoilTransportModel(context) as soil:
        soil.defineSoilDomain(vec3(0, 0, 0), vec3(1, 1, 1))
        soil.setColumnResolution(40)
        soil.setInitialCondition(-1.0)
        soil.setTopBoundaryFlux(2e-6)           # below the saturated conductivity of loam
        soil.run(12 * 3600.0)

        # Cut a quarter of the block away to expose the wetting front
        uuids = soil.addSoilVisualization(SoilColorMode.WATER_CONTENT, vec3(0.5, 0, 0), vec3(1, 0.5, 1),
                                          region=SoilRegion.REMOVE)

    with Visualizer(800, 600, headless=True) as vis:
        vis.buildContextGeometry(context)
        vis.colorContextPrimitivesByData("water_content")
        vis.setCameraPosition(vec3(2.0, -1.5, 1.0), vec3(0.5, 0.5, -0.5))
        vis.plotUpdate()
        vis.printWindow("soil_water_content.jpeg")
```

### Error Handling

```python
from pyhelios import Context, SoilTransportModel, SoilTransportModelError
from pyhelios.types import vec3

with Context() as context:
    with SoilTransportModel(context) as soil:
        soil.defineSoilDomain(vec3(0, 0, 0), vec3(1, 1, 1))
        soil.setInitialCondition(-1.0)
        try:
            soil.getWaterContent(vec3(0.5, 0.5, 0.5))   # above the surface: outside the domain
        except SoilTransportModelError as e:
            print(f"Soil transport error: {e}")
        try:
            soil.setTopBoundaryFlux("2e-6")             # wrong type
        except ValueError as e:
            print(f"Parameter error: {e}")
```

Invalid arguments (a wrong type, a non-finite number, a negative index) raise `ValueError` before the model is called. Failures in the model itself raise `SoilTransportModelError`, with the native error message.

## Troubleshooting

### Plugin Not Available

If creating a `SoilTransportModel` reports that the plugin is not available, check whether it is in the native library, and rebuild if it is not:

```bash
python -m pyhelios.plugins info soiltransport   # reports whether the plugin is available
build_scripts/build_helios                      # builds all available plugins
```

### The Soil Domain Has Already Been Set Up

`defineSoilDomain()`, `setGridResolution()`, `setColumnResolution()`, `setColumnGrid()` and switching to or from `SolverType.SOLVER_3D` raise this once the domain has been set up by `initializeDomain()` or by the first call that needed it (an initial condition, a boundary condition, a root distribution or a sensor). Call them first.

### The Soil Domain Has Not Been Set Up Yet

Queries such as `getSoilWaterPotential()` and `addSoilVisualization()` need a domain. Call `initializeDomain()` or set an initial condition first.

### Point Outside the Soil Domain

The domain extends downward from its origin, so a point inside it has a z coordinate between the origin's z and that minus the extent. Points on the boundary, such as the soil surface, read the boundary cell.

### The Soil Solver Could Not Complete the Step

`run()` raises this when the step has no solution, usually because a boundary or root-uptake flux exceeds what the soil can deliver or absorb (e.g. evaporation from soil near its residual water content). Reduce the flux, use a shorter timestep, or enable adaptive stepping (`SolverParameters.adaptive_dt`, with `dt_min`). The simulation clock counts only the time that was advanced.

### Plant Has No Root Distribution

`setTranspiration()`, `getSoilWaterPotential()`, `getRootUptakeFlux()` and `getCumulativeRootUptake()` need a root distribution for the plant, set with `setRootDistribution()` or `setRootDistributionWeibull()`.

## References

- Carsel, R.F., Parrish, R.S. (1988). Developing joint probability distributions of soil water retention characteristics. *Water Resources Research* 24(5), 755–769.
- Celia, M.A., Bouloutas, E.T., Zarba, R.L. (1990). A general mass-conservative numerical solution for the unsaturated flow equation. *Water Resources Research* 26(7), 1483–1496.
- Ippisch, O., Vogel, H.-J., Bastian, P. (2006). Validity limits for the van Genuchten–Mualem model and implications for parameter estimation and numerical simulation. *Advances in Water Resources* 29(12), 1780–1789.
- Schaap, M.G., van Genuchten, M.Th. (2006). A modified Mualem–van Genuchten formulation for improved description of the hydraulic conductivity near saturation. *Vadose Zone Journal* 5(1), 27–34.
- Schnepf, A., et al. (2020). Call for participation: collaborative benchmarking of functional-structural root architecture models. The case of root water uptake. *Frontiers in Plant Science* 11, 316.
- van Genuchten, M.Th. (1980). A closed-form equation for predicting the hydraulic conductivity of unsaturated soils. *Soil Science Society of America Journal* 44(5), 892–898.
- Vogel, T., Cislerova, M. (1988). On the reliability of unsaturated hydraulic conductivity calculated from the moisture retention curve. *Transport in Porous Media* 3, 1–15.
