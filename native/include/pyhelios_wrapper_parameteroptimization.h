/**
 * @file pyhelios_wrapper_parameteroptimization.h
 * @brief ParameterOptimization functions for PyHelios C wrapper
 *
 * This header exposes the ParameterOptimization plugin -- gradient-free and
 * gradient-based optimization of named model parameters against a user-supplied
 * objective function.
 *
 * Unlike every other PyHelios plugin, this one calls *back* into the host language:
 * the objective is invoked once per candidate parameter set, potentially thousands
 * of times per run. Two conventions make that tractable across a C ABI:
 *
 *  1. Parameters cross the boundary as flat arrays ordered by a lexicographic sort
 *     of their names. The plugin sorts identically on every internal code path
 *     (getOrderedParamNames in ParameterOptimization.cpp), so index i always refers
 *     to sorted(names)[i] in both directions and no per-call string marshalling is
 *     needed.
 *
 *  2. A callback reports failure by setting its error_flag out-parameter rather than
 *     by returning a sentinel value. Any float is a legitimate objective value, so a
 *     sentinel would be silently consumed by the optimizer and yield a plausible but
 *     wrong result. On a raised flag the bridge throws, unwinding out of run(), and
 *     the run entry point returns PYHELIOS_PARAMOPT_CALLBACK_FAILED.
 */

#ifndef PYHELIOS_WRAPPER_PARAMETEROPTIMIZATION_H
#define PYHELIOS_WRAPPER_PARAMETEROPTIMIZATION_H

#include "pyhelios_wrapper_common.h"

// Forward declaration for the ParameterOptimization interface
class ParameterOptimization;

#ifdef __cplusplus
extern "C" {
#endif

//=============================================================================
// Return codes for the run() entry points
//=============================================================================

//! Optimization completed; out_values and out_fitness are populated.
#define PYHELIOS_PARAMOPT_OK 0
//! Native failure. Details are available via getLastErrorMessage().
#define PYHELIOS_PARAMOPT_ERROR (-1)
/**
 * The host-language callback signalled failure and the run was aborted.
 * No error state is set: the host already holds the original exception and is
 * expected to re-raise it, which preserves its type and traceback.
 */
#define PYHELIOS_PARAMOPT_CALLBACK_FAILED (-2)

//=============================================================================
// Parameter description
//=============================================================================

//! Parameter kind, mirroring the plugin's ParameterType enum class.
typedef enum {
    PYHELIOS_PARAM_FLOAT = 0,       //!< Continuous parameter
    PYHELIOS_PARAM_INTEGER = 1,     //!< Rounded to the nearest whole number
    PYHELIOS_PARAM_CATEGORICAL = 2  //!< Chosen from an explicit set of values
} PyHeliosParameterType;

/**
 * @brief One optimizable parameter, flattened for the C ABI.
 *
 * The plugin's ParameterToOptimize holds a std::vector<float>, so it cannot cross
 * the boundary directly. All pointers are caller-owned and must remain valid for
 * the duration of the run() call.
 */
typedef struct {
    const char* name;           //!< UTF-8, NUL-terminated. Must be non-empty and unique.
    float value;                //!< Initial value
    float min;                  //!< Lower bound (ignored for CATEGORICAL)
    float max;                  //!< Upper bound (ignored for CATEGORICAL)
    int type;                   //!< A PyHeliosParameterType value
    const float* categories;    //!< Allowed values for CATEGORICAL; may be NULL otherwise
    unsigned int category_count; //!< Number of entries in categories; 0 when unused
} PyHeliosParameterSpec;

//=============================================================================
// Callbacks
//=============================================================================

/**
 * @brief Objective function invoked once per candidate parameter set.
 * @param values Candidate values, in sorted-name order
 * @param n Number of values
 * @param user_data Opaque pointer forwarded from the run() call
 * @param error_flag Set to non-zero to abort the optimization; the return value is
 *                   then ignored. Must not be NULL.
 * @return Scalar cost to minimize
 */
typedef float (*PyHeliosObjectiveCallback)(const float* values, unsigned int n,
                                           void* user_data, int* error_flag);

/**
 * @brief Gradient of the objective, invoked alongside the objective.
 * @param values Candidate values, in sorted-name order
 * @param n Number of values
 * @param out_gradient Receives n partial derivatives, in the same sorted-name order
 * @param user_data Opaque pointer forwarded from the run() call
 * @param error_flag Set to non-zero to abort the optimization. Must not be NULL.
 */
typedef void (*PyHeliosGradientCallback)(const float* values, unsigned int n,
                                         float* out_gradient, void* user_data,
                                         int* error_flag);

/**
 * @brief Combined constrained simulation: objective, constraints, and every gradient.
 *
 * Called once per parameter point. The plugin caches the result, so NLopt's separate
 * objective and per-constraint callbacks do not re-enter this at the same point --
 * a simulation that runs a full Helios scene is evaluated once rather than once per
 * constraint.
 *
 * @param values Candidate values, in sorted-name order
 * @param n Number of values
 * @param out_objective Receives the scalar cost to minimize
 * @param out_obj_gradient Receives n partial derivatives of the objective, sorted-name order
 * @param out_constraints Receives constraint_count values; constraint i is satisfied when
 *                        its value is <= 0
 * @param out_con_gradients Receives constraint_count * n partial derivatives, row-major:
 *                          the derivative of constraint i with respect to parameter j is at
 *                          [i * n + j], with j in sorted-name order
 * @param constraint_count Number of constraints, fixed for the whole run
 * @param user_data Opaque pointer forwarded from the run() call
 * @param error_flag Set to non-zero to abort the optimization; all outputs are then
 *                   ignored. Must not be NULL.
 */
typedef void (*PyHeliosConstrainedCallback)(const float* values, unsigned int n,
                                            float* out_objective,
                                            float* out_obj_gradient,
                                            float* out_constraints,
                                            float* out_con_gradients,
                                            unsigned int constraint_count,
                                            void* user_data, int* error_flag);

//=============================================================================
// Algorithm settings (POD mirrors of the plugin's settings structs)
//=============================================================================

//! Crossover operator selection for the genetic algorithm.
typedef enum {
    PYHELIOS_CROSSOVER_BLX_ALPHA = 0,
    PYHELIOS_CROSSOVER_BLX_PCA = 1
} PyHeliosCrossoverKind;

//! Mutation operator selection for the genetic algorithm.
typedef enum {
    PYHELIOS_MUTATION_PER_GENE = 0,
    PYHELIOS_MUTATION_ISOTROPIC = 1,
    PYHELIOS_MUTATION_HYBRID = 2
} PyHeliosMutationKind;

/**
 * @brief Genetic algorithm settings.
 *
 * The plugin's crossover and mutation members are std::variant; here they are a
 * discriminant plus the union of each alternative's fields. Fields not belonging to
 * the selected kind are ignored.
 */
typedef struct {
    size_t generations;
    size_t population_size;
    float crossover_rate;
    float elitism_rate;
    unsigned int random_seed;   //!< 0 selects a nondeterministic seed

    int crossover_kind;                         //!< A PyHeliosCrossoverKind value
    float crossover_alpha;                      //!< BLX_ALPHA and BLX_PCA
    size_t crossover_pca_update_interval;       //!< BLX_PCA only

    int mutation_kind;                          //!< A PyHeliosMutationKind value
    float mutation_rate;                        //!< All kinds
    size_t mutation_pca_update_interval;        //!< HYBRID only
    float mutation_sigma_pca;                   //!< HYBRID only
    float mutation_gamma_cauchy;                //!< HYBRID only
    float mutation_sigma_random;                //!< HYBRID only
    float mutation_pca_gaussian_prob;           //!< HYBRID only
    float mutation_pca_cauchy_prob;             //!< HYBRID only
} PyHeliosGeneticAlgorithm;

//! Bayesian optimization settings.
typedef struct {
    size_t max_evaluations;
    size_t initial_samples;     //!< 0 selects 2*num_params
    float ucb_kappa;
    size_t max_gp_samples;
    size_t acquisition_samples;
    unsigned int random_seed;   //!< 0 selects a nondeterministic seed
} PyHeliosBayesianOptimization;

//! CMA-ES settings.
typedef struct {
    size_t max_evaluations;
    size_t lambda;              //!< 0 selects 4+floor(3*ln(n))
    float sigma;
    unsigned int random_seed;   //!< 0 selects a nondeterministic seed
} PyHeliosCMAES;

//! L-BFGS settings. Requires an NLopt build that includes the Luksan solvers.
typedef struct {
    int max_iterations;
    double ftol_rel;
    double xtol_rel;
    int verify_gradients;       //!< Boolean as int; C++ bool has no fixed ABI
    double fd_step;
} PyHeliosLBFGS;

//! AdamW settings. Requires no external dependency.
typedef struct {
    int max_iterations;
    float learning_rate;
    float beta1;
    float beta2;
    float epsilon;
    float weight_decay;         //!< 0 gives standard Adam
    double ftol_rel;
    double xtol_rel;
} PyHeliosAdam;

//! BOBYQA settings. Requires NLopt.
typedef struct {
    int max_iterations;
    double ftol_rel;
    double xtol_rel;
    double initial_step;        //!< 0 selects 10% of the parameter range
} PyHeliosBOBYQA;

//! SLSQP settings. Requires NLopt.
typedef struct {
    int max_iterations;
    double ftol_rel;
    double xtol_rel;
} PyHeliosSLSQP;

//=============================================================================
// Lifecycle
//=============================================================================

/**
 * @brief Create a ParameterOptimization instance.
 * @note Takes no Context. The plugin operates purely on the user's objective
 *       function, which may close over a Context if it needs one.
 * @return Pointer to the new instance, or nullptr on error
 */
PYHELIOS_API ParameterOptimization* createParameterOptimization();

/**
 * @brief Destroy a ParameterOptimization instance.
 * @param opt Instance to destroy; NULL is ignored
 */
PYHELIOS_API void destroyParameterOptimization(ParameterOptimization* opt);

//=============================================================================
// Capability query
//=============================================================================

/**
 * @brief Report whether an algorithm can actually run in this build.
 *
 * L-BFGS, BOBYQA and SLSQP depend on NLopt being present at build time, and
 * L-BFGS additionally on the LGPL Luksan solvers being enabled. Querying this up
 * front lets the caller fail at algorithm-selection time instead of part-way
 * through a long run.
 *
 * @param algorithm_name One of "GA", "BO", "CMAES", "LBFGS", "ADAM", "BOBYQA", "SLSQP"
 * @return 1 if available, 0 if unavailable or the name is unrecognized
 */
PYHELIOS_API int parameterOptimizationAlgorithmAvailable(const char* algorithm_name);

//=============================================================================
// Algorithm selection
//=============================================================================

/** @brief Select the genetic algorithm. */
PYHELIOS_API void setParameterOptimizationGeneticAlgorithm(ParameterOptimization* opt, const PyHeliosGeneticAlgorithm* settings);
/** @brief Select Bayesian optimization. */
PYHELIOS_API void setParameterOptimizationBayesian(ParameterOptimization* opt, const PyHeliosBayesianOptimization* settings);
/** @brief Select CMA-ES. */
PYHELIOS_API void setParameterOptimizationCMAES(ParameterOptimization* opt, const PyHeliosCMAES* settings);
/** @brief Select L-BFGS. Fails if NLopt's Luksan solvers were not built. */
PYHELIOS_API void setParameterOptimizationLBFGS(ParameterOptimization* opt, const PyHeliosLBFGS* settings);
/** @brief Select AdamW. */
PYHELIOS_API void setParameterOptimizationAdam(ParameterOptimization* opt, const PyHeliosAdam* settings);
/** @brief Select BOBYQA. Fails if NLopt was not built. */
PYHELIOS_API void setParameterOptimizationBOBYQA(ParameterOptimization* opt, const PyHeliosBOBYQA* settings);
/** @brief Select SLSQP. Fails if NLopt was not built. */
PYHELIOS_API void setParameterOptimizationSLSQP(ParameterOptimization* opt, const PyHeliosSLSQP* settings);

//=============================================================================
// Preset settings
//=============================================================================

/*
 * These fill a settings struct from the plugin's own defaults and tuned presets.
 * Reading them from C++ rather than transcribing the constants keeps the Python
 * layer from silently drifting when helios-core is updated.
 */

/** @brief Fill with the plugin's default genetic algorithm settings. */
PYHELIOS_API void getParameterOptimizationGADefaults(PyHeliosGeneticAlgorithm* out);
/** @brief Fill with the exploration-biased genetic algorithm preset. */
PYHELIOS_API void getParameterOptimizationGAExplore(PyHeliosGeneticAlgorithm* out);
/** @brief Fill with the exploitation-biased genetic algorithm preset. */
PYHELIOS_API void getParameterOptimizationGAExploit(PyHeliosGeneticAlgorithm* out);
/** @brief Fill with the plugin's default Bayesian optimization settings. */
PYHELIOS_API void getParameterOptimizationBayesianDefaults(PyHeliosBayesianOptimization* out);
/** @brief Fill with the exploration-biased Bayesian optimization preset. */
PYHELIOS_API void getParameterOptimizationBayesianExplore(PyHeliosBayesianOptimization* out);
/** @brief Fill with the exploitation-biased Bayesian optimization preset. */
PYHELIOS_API void getParameterOptimizationBayesianExploit(PyHeliosBayesianOptimization* out);
/** @brief Fill with the plugin's default CMA-ES settings. */
PYHELIOS_API void getParameterOptimizationCMAESDefaults(PyHeliosCMAES* out);
/** @brief Fill with the exploration-biased CMA-ES preset. */
PYHELIOS_API void getParameterOptimizationCMAESExplore(PyHeliosCMAES* out);
/** @brief Fill with the exploitation-biased CMA-ES preset. */
PYHELIOS_API void getParameterOptimizationCMAESExploit(PyHeliosCMAES* out);
/** @brief Fill with the plugin's default L-BFGS settings. */
PYHELIOS_API void getParameterOptimizationLBFGSDefaults(PyHeliosLBFGS* out);
/** @brief Fill with the plugin's default Adam settings. */
PYHELIOS_API void getParameterOptimizationAdamDefaults(PyHeliosAdam* out);
/** @brief Fill with the plugin's default BOBYQA settings. */
PYHELIOS_API void getParameterOptimizationBOBYQADefaults(PyHeliosBOBYQA* out);
/** @brief Fill with the plugin's default SLSQP settings. */
PYHELIOS_API void getParameterOptimizationSLSQPDefaults(PyHeliosSLSQP* out);

//=============================================================================
// I/O configuration
//=============================================================================

/**
 * @brief Enable or disable the plugin's progress printout to stdout.
 * @param opt ParameterOptimization instance
 * @param enable Non-zero to print progress
 */
PYHELIOS_API void setParameterOptimizationPrintProgress(ParameterOptimization* opt, int enable);

/**
 * @brief Set the file the final result is written to.
 * @param opt ParameterOptimization instance
 * @param path Output path; must end in .csv or .txt. NULL or "" disables writing.
 */
PYHELIOS_API void setParameterOptimizationResultFile(ParameterOptimization* opt, const char* path);

/**
 * @brief Set the file per-generation progress is written to.
 * @param opt ParameterOptimization instance
 * @param path Output path; must end in .csv or .txt. NULL or "" disables writing.
 */
PYHELIOS_API void setParameterOptimizationProgressFile(ParameterOptimization* opt, const char* path);

/**
 * @brief Set a file to read the initial parameter set from.
 * @param opt ParameterOptimization instance
 * @param path Headerless CSV of "name,value,min,max" rows. NULL or "" disables reading.
 * @note Only the genetic algorithm consults this file.
 */
PYHELIOS_API void setParameterOptimizationInputFile(ParameterOptimization* opt, const char* path);

//=============================================================================
// Run
//=============================================================================

/**
 * @brief Run a derivative-free optimization.
 *
 * @param opt ParameterOptimization instance
 * @param params Parameters to optimize. Input order is irrelevant; the callback and
 *               the outputs both use sorted-name order.
 * @param param_count Number of parameters; must be non-zero
 * @param objective Objective callback; must be non-NULL
 * @param user_data Opaque pointer forwarded to the callback
 * @param out_values Receives param_count optimized values in sorted-name order
 * @param out_fitness Receives the objective value at the optimum
 * @return PYHELIOS_PARAMOPT_OK, PYHELIOS_PARAMOPT_ERROR, or PYHELIOS_PARAMOPT_CALLBACK_FAILED
 */
PYHELIOS_API int runParameterOptimization(ParameterOptimization* opt,
                                          const PyHeliosParameterSpec* params,
                                          unsigned int param_count,
                                          PyHeliosObjectiveCallback objective,
                                          void* user_data,
                                          float* out_values,
                                          float* out_fitness);

/**
 * @brief Run an optimization with a user-supplied gradient.
 *
 * Gradient-free algorithms accept this and ignore the gradient; Adam and L-BFGS
 * require it.
 *
 * @param opt ParameterOptimization instance
 * @param params Parameters to optimize
 * @param param_count Number of parameters; must be non-zero
 * @param objective Objective callback; must be non-NULL
 * @param gradient Gradient callback; must be non-NULL
 * @param user_data Opaque pointer forwarded to both callbacks
 * @param out_values Receives param_count optimized values in sorted-name order
 * @param out_fitness Receives the objective value at the optimum
 * @return PYHELIOS_PARAMOPT_OK, PYHELIOS_PARAMOPT_ERROR, or PYHELIOS_PARAMOPT_CALLBACK_FAILED
 */
PYHELIOS_API int runParameterOptimizationWithGradient(ParameterOptimization* opt,
                                                      const PyHeliosParameterSpec* params,
                                                      unsigned int param_count,
                                                      PyHeliosObjectiveCallback objective,
                                                      PyHeliosGradientCallback gradient,
                                                      void* user_data,
                                                      float* out_values,
                                                      float* out_fitness);

/**
 * @brief Run an optimization with gradients estimated by centered finite differences.
 *
 * Lets the gradient-based algorithms be used without the caller supplying a gradient.
 * Each gradient costs 2N additional objective evaluations.
 *
 * @param opt ParameterOptimization instance
 * @param params Parameters to optimize
 * @param param_count Number of parameters; must be non-zero
 * @param objective Objective callback; must be non-NULL
 * @param fd_step Relative perturbation factor; values <= 0 select the plugin default
 * @param user_data Opaque pointer forwarded to the callback
 * @param out_values Receives param_count optimized values in sorted-name order
 * @param out_fitness Receives the objective value at the optimum
 * @return PYHELIOS_PARAMOPT_OK, PYHELIOS_PARAMOPT_ERROR, or PYHELIOS_PARAMOPT_CALLBACK_FAILED
 */
PYHELIOS_API int runParameterOptimizationWithFDGradient(ParameterOptimization* opt,
                                                        const PyHeliosParameterSpec* params,
                                                        unsigned int param_count,
                                                        PyHeliosObjectiveCallback objective,
                                                        float fd_step,
                                                        void* user_data,
                                                        float* out_values,
                                                        float* out_fitness);

/**
 * @brief Run a constrained optimization: minimize f(x) subject to c_i(x) <= 0.
 *
 * Requires SLSQP, the only algorithm in the plugin that handles nonlinear inequality
 * constraints, and all-FLOAT parameters. Both conditions are enforced by the plugin.
 *
 * constraint_count is supplied rather than discovered so the caller can size the
 * output buffers the callback writes into before the first invocation.
 *
 * @param opt ParameterOptimization instance
 * @param params Parameters to optimize
 * @param param_count Number of parameters; must be non-zero
 * @param simulation Combined simulation callback; must be non-NULL
 * @param constraint_count Number of constraints; must be non-zero
 * @param user_data Opaque pointer forwarded to the callback
 * @param out_values Receives param_count optimized values in sorted-name order
 * @param out_fitness Receives the objective value at the optimum
 * @return PYHELIOS_PARAMOPT_OK, PYHELIOS_PARAMOPT_ERROR, or PYHELIOS_PARAMOPT_CALLBACK_FAILED
 */
PYHELIOS_API int runParameterOptimizationConstrained(ParameterOptimization* opt,
                                                     const PyHeliosParameterSpec* params,
                                                     unsigned int param_count,
                                                     PyHeliosConstrainedCallback simulation,
                                                     unsigned int constraint_count,
                                                     void* user_data,
                                                     float* out_values,
                                                     float* out_fitness);

#ifdef __cplusplus
}
#endif

#endif // PYHELIOS_WRAPPER_PARAMETEROPTIMIZATION_H
