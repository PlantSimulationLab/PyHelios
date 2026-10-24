"""
T8.2 -- real factorial design generation: LAI x fruit_density x clustering x trellis.

Implements a general two-level fractional-factorial screening design generator (not a
hard-coded 8-row table), so it isn't specific to exactly these 4 factors. A full 2^4
factorial is 16 cells; this generates the standard resolution-IV half-fraction (8 cells)
via one defining generator, the textbook construction (Montgomery, "Design and Analysis
of Experiments", ch. 8): pick k-1 "base" factors, run their full 2^(k-1) factorial, then
set the k-th factor's sign to the PRODUCT of the base factors' signs (the generator).
Confounding: with generator D=ABC, main effects are confounded with 3-way interactions
(not with each other or 2-way interactions) -- resolution IV, adequate for a screening
design where the goal is "which factors matter at all", not "estimate every interaction".

The task doc calls for "fractional factorial to screen, full factorial on survivors" --
this module produces the fractional (screening) design and the full design (for
completeness / for a future full run on whichever factors survive screening); which one
`run_t82_factorial.py` actually executes at reduced scale is a separate, documented
choice (see PHASE8_LOG.md).
"""

from itertools import product


def full_factorial(factor_levels):
    """factor_levels: {factor_name: (low_level, high_level)}. Returns a list of dicts,
    one per cell of the full 2^k factorial, {factor_name: level_value}."""
    names = list(factor_levels.keys())
    combos = list(product(*[(-1, 1) for _ in names]))
    cells = []
    for combo in combos:
        cell = {}
        for name, sign in zip(names, combo):
            low, high = factor_levels[name]
            cell[name] = high if sign == 1 else low
        cells.append(cell)
    return cells


def half_fraction(factor_levels, generator):
    """Resolution-IV half-fraction of a 2^k full factorial via one defining generator.

    Args:
        factor_levels: {factor_name: (low_level, high_level)}, k entries.
        generator: (derived_factor_name, [base_factor_names]) -- derived_factor_name's
            sign is set to the PRODUCT of the listed base factors' signs for every row
            of their full factorial. `derived_factor_name` must be one of
            `factor_levels`'s keys and must NOT appear in `base_factor_names`; every
            other key of `factor_levels` not in `base_factor_names` and not the derived
            factor is an error (this generator only supports exactly
            k-1 base factors + 1 derived factor, the standard resolution-IV construction
            for a single half-fraction).

    Returns: list of 2^(k-1) cell dicts, {factor_name: level_value}.
    """
    derived_name, base_names = generator
    all_names = set(factor_levels.keys())
    if derived_name not in all_names:
        raise ValueError(f"generator target {derived_name!r} not in factor_levels")
    if set(base_names) | {derived_name} != all_names:
        raise ValueError(
            "generator base factors + derived factor must cover exactly factor_levels' keys "
            f"(got base={base_names}, derived={derived_name}, factor_levels keys={sorted(all_names)})")

    base_combos = list(product(*[(-1, 1) for _ in base_names]))
    cells = []
    for combo in base_combos:
        signs = dict(zip(base_names, combo))
        derived_sign = 1
        for s in combo:
            derived_sign *= s
        signs[derived_name] = derived_sign

        cell = {}
        for name, sign in signs.items():
            low, high = factor_levels[name]
            cell[name] = high if sign == 1 else low
        cells.append(cell)
    return cells


# The 4 real factors this phase sweeps, and their two named levels. "clustering" only
# has an observable effect when fruit_density's keep-fraction < 1.0 (see canopy_factory.py);
# it is still included as a full factor in the design (its cell value is used whenever
# fruit_density is at its low/thinned level, and is a no-op -- both clustering levels
# produce the identical un-thinned canopy -- whenever fruit_density is at its high/1.0 level).
PHASE8_FACTOR_LEVELS = {
    "lai": (0.3, 1.0),                      # (sparse, dense) keep-fraction
    "fruit_density": (0.3, 1.0),            # (low, high) keep-fraction
    "clustering": ("clustered", "dispersed"),
    "trellis": ("apple", "apple_fruitingwall"),
}

# Resolution-IV generator used for this run's screening design: trellis = lai * fruit_density * clustering.
PHASE8_GENERATOR = ("trellis", ["lai", "fruit_density", "clustering"])


def phase8_full_design():
    return full_factorial(PHASE8_FACTOR_LEVELS)


def phase8_screening_design():
    return half_fraction(PHASE8_FACTOR_LEVELS, PHASE8_GENERATOR)


def cell_label(cell):
    return "lai={lai}_fruit={fruit_density}_clust={clustering}_trellis={trellis}".format(**cell)
