#include "../include/pyhelios_wrapper_common.h"
#include <string>
#include <exception>

#ifdef PARAMETEROPTIMIZATION_PLUGIN_AVAILABLE
#include "../include/pyhelios_wrapper_parameteroptimization.h"
#include "ParameterOptimization.h"

#include <algorithm>
#include <cstring>
#include <vector>

namespace {

    /**
     * Thrown when the host-language callback signals failure.
     *
     * Carries no user-facing message: the host already holds the original exception
     * and re-raises it, which preserves the type and traceback the user actually
     * needs. This type exists only so the run() entry points can distinguish a
     * callback abort from a genuine native error.
     *
     * Throwing rather than returning a sentinel is required for correctness. Every
     * float is a legitimate objective value, so a sentinel would be consumed by the
     * optimizer and silently produce a wrong answer. The plugin propagates this
     * exception verbatim, including through NLopt's callbacks, which capture it in
     * an exception_ptr and rethrow after force_stop().
     */
    struct PyHeliosCallbackAbort : public std::runtime_error {
        PyHeliosCallbackAbort()
            : std::runtime_error("ERROR (ParameterOptimization): objective callback signalled failure.") {}
    };

    /**
     * Adapts the C callbacks to the std::function interface the plugin expects.
     *
     * ordered_names is sorted once up front and must match the plugin's own
     * getOrderedParamNames ordering, since that is what makes the positional array
     * ABI coherent in both directions.
     */
    struct CallbackBridge {
        PyHeliosObjectiveCallback objective_cb = nullptr;
        PyHeliosGradientCallback gradient_cb = nullptr;
        PyHeliosConstrainedCallback constrained_cb = nullptr;
        unsigned int constraint_count = 0;
        void* user_data = nullptr;
        std::vector<std::string> ordered_names;
        /**
         * Set once a callback has failed, and never cleared. NLopt polls its stop
         * flag only at its own checkpoints, so it may invoke the callback again
         * between force_stop() and actually stopping. Those calls must not re-enter
         * host code, which may already be unwinding or holding a stashed exception.
         */
        bool aborted = false;
    };

    //! Gather the candidate values into a dense array in sorted-name order.
    std::vector<float> collectValues(const CallbackBridge& bridge, const ParametersToOptimize& params) {
        std::vector<float> values;
        values.reserve(bridge.ordered_names.size());
        for (const std::string& name : bridge.ordered_names) {
            values.push_back(params.at(name).value);
        }
        return values;
    }

    //! Build the objective adapter passed to ParameterOptimization::run.
    ObjectiveFunction makeObjectiveAdapter(CallbackBridge* bridge) {
        return [bridge](const ParametersToOptimize& params) -> float {
            if (bridge->aborted) {
                throw PyHeliosCallbackAbort();
            }

            std::vector<float> values = collectValues(*bridge, params);

            int error_flag = 0;
            float result = bridge->objective_cb(values.data(),
                                                static_cast<unsigned int>(values.size()),
                                                bridge->user_data, &error_flag);
            if (error_flag != 0) {
                bridge->aborted = true;
                throw PyHeliosCallbackAbort();
            }
            return result;
        };
    }

    //! Build the gradient adapter passed to ParameterOptimization::run.
    GradientFunction makeGradientAdapter(CallbackBridge* bridge) {
        return [bridge](const ParametersToOptimize& params) -> ParameterGradient {
            if (bridge->aborted) {
                throw PyHeliosCallbackAbort();
            }

            std::vector<float> values = collectValues(*bridge, params);
            std::vector<float> gradient_values(values.size(), 0.f);

            int error_flag = 0;
            bridge->gradient_cb(values.data(), static_cast<unsigned int>(values.size()),
                                gradient_values.data(), bridge->user_data, &error_flag);
            if (error_flag != 0) {
                bridge->aborted = true;
                throw PyHeliosCallbackAbort();
            }

            ParameterGradient gradient;
            gradient.reserve(bridge->ordered_names.size());
            for (size_t i = 0; i < bridge->ordered_names.size(); ++i) {
                gradient[bridge->ordered_names[i]] = gradient_values[i];
            }
            return gradient;
        };
    }

    //! Build the combined constrained-simulation adapter passed to ParameterOptimization::run.
    ConstrainedSimulation makeConstrainedAdapter(CallbackBridge* bridge) {
        return [bridge](const ParametersToOptimize& params) -> ConstrainedResult {
            if (bridge->aborted) {
                throw PyHeliosCallbackAbort();
            }

            const size_t n = bridge->ordered_names.size();
            const size_t m = bridge->constraint_count;

            std::vector<float> values = collectValues(*bridge, params);
            std::vector<float> obj_gradient(n, 0.f);
            std::vector<float> constraints(m, 0.f);
            // Row-major: constraint i, parameter j at [i * n + j].
            std::vector<float> con_gradients(m * n, 0.f);
            float objective = 0.f;

            int error_flag = 0;
            bridge->constrained_cb(values.data(), static_cast<unsigned int>(n),
                                   &objective, obj_gradient.data(),
                                   constraints.data(), con_gradients.data(),
                                   static_cast<unsigned int>(m),
                                   bridge->user_data, &error_flag);
            if (error_flag != 0) {
                bridge->aborted = true;
                throw PyHeliosCallbackAbort();
            }

            ConstrainedResult result;
            result.objective = objective;
            result.obj_gradient.reserve(n);
            for (size_t j = 0; j < n; ++j) {
                result.obj_gradient[bridge->ordered_names[j]] = obj_gradient[j];
            }

            result.constraints.assign(constraints.begin(), constraints.end());
            result.con_gradients.resize(m);
            for (size_t i = 0; i < m; ++i) {
                ParameterGradient& gradient = result.con_gradients[i];
                gradient.reserve(n);
                for (size_t j = 0; j < n; ++j) {
                    gradient[bridge->ordered_names[j]] = con_gradients[i * n + j];
                }
            }
            return result;
        };
    }

    //! Translate the flat parameter specs into the plugin's map representation.
    ParametersToOptimize buildParameters(const PyHeliosParameterSpec* params, unsigned int param_count) {
        ParametersToOptimize result;
        result.reserve(param_count);

        for (unsigned int i = 0; i < param_count; ++i) {
            const PyHeliosParameterSpec& spec = params[i];

            if (!spec.name || spec.name[0] == '\0') {
                throw std::runtime_error("Parameter name must be a non-empty string.");
            }

            ParameterToOptimize parameter;
            parameter.value = spec.value;
            parameter.min = spec.min;
            parameter.max = spec.max;

            switch (spec.type) {
                case PYHELIOS_PARAM_FLOAT:
                    parameter.type = ParameterType::FLOAT;
                    break;
                case PYHELIOS_PARAM_INTEGER:
                    parameter.type = ParameterType::INTEGER;
                    break;
                case PYHELIOS_PARAM_CATEGORICAL:
                    parameter.type = ParameterType::CATEGORICAL;
                    break;
                default:
                    throw std::runtime_error("Unknown parameter type for parameter '" + std::string(spec.name) + "'.");
            }

            if (spec.categories && spec.category_count > 0) {
                parameter.categories.assign(spec.categories, spec.categories + spec.category_count);
            }

            if (!result.emplace(std::string(spec.name), std::move(parameter)).second) {
                throw std::runtime_error("Duplicate parameter name '" + std::string(spec.name) + "'.");
            }
        }

        return result;
    }

    //! Populate the bridge's name ordering to match the plugin's internal sort.
    void initializeOrdering(CallbackBridge& bridge, const ParametersToOptimize& params) {
        bridge.ordered_names.reserve(params.size());
        for (const auto& entry : params) {
            bridge.ordered_names.push_back(entry.first);
        }
        std::sort(bridge.ordered_names.begin(), bridge.ordered_names.end());
    }

    //! Copy the optimized values out in sorted-name order.
    void writeResult(const CallbackBridge& bridge, const ParameterOptimization::Result& result,
                     float* out_values, float* out_fitness) {
        for (size_t i = 0; i < bridge.ordered_names.size(); ++i) {
            out_values[i] = result.parameters.at(bridge.ordered_names[i]).value;
        }
        *out_fitness = result.fitness;
    }

    //! Validate the arguments common to all three run() entry points.
    bool validateRunArguments(ParameterOptimization* opt, const PyHeliosParameterSpec* params,
                              unsigned int param_count, PyHeliosObjectiveCallback objective,
                              float* out_values, float* out_fitness) {
        if (!opt) {
            setError(PYHELIOS_ERROR_INVALID_PARAMETER, "ParameterOptimization pointer is null");
            return false;
        }
        if (!params || param_count == 0) {
            setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Parameter array is null or empty");
            return false;
        }
        if (!objective) {
            setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Objective callback is null");
            return false;
        }
        if (!out_values || !out_fitness) {
            setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Output pointer is null");
            return false;
        }
        return true;
    }

    //! Copy a GeneticAlgorithm settings struct into its flat mirror.
    void exportGeneticAlgorithm(const GeneticAlgorithm& ga, PyHeliosGeneticAlgorithm* out) {
        out->generations = ga.generations;
        out->population_size = ga.population_size;
        out->crossover_rate = ga.crossover_rate;
        out->elitism_rate = ga.elitism_rate;
        out->random_seed = ga.random_seed;

        // Defaults for fields the selected alternative does not carry, so the mirror
        // is never left holding indeterminate values.
        out->crossover_alpha = 0.5f;
        out->crossover_pca_update_interval = 5;
        out->mutation_rate = 0.1f;
        out->mutation_pca_update_interval = 5;
        out->mutation_sigma_pca = 0.25f;
        out->mutation_gamma_cauchy = 0.1f;
        out->mutation_sigma_random = 0.3f;
        out->mutation_pca_gaussian_prob = 0.70f;
        out->mutation_pca_cauchy_prob = 0.20f;

        if (const auto* blx = std::get_if<BLXAlphaCrossover>(&ga.crossover)) {
            out->crossover_kind = PYHELIOS_CROSSOVER_BLX_ALPHA;
            out->crossover_alpha = blx->alpha;
        } else if (const auto* pca = std::get_if<BLXPCACrossover>(&ga.crossover)) {
            out->crossover_kind = PYHELIOS_CROSSOVER_BLX_PCA;
            out->crossover_alpha = pca->alpha;
            out->crossover_pca_update_interval = pca->pca_update_interval;
        }

        if (const auto* per_gene = std::get_if<PerGeneMutation>(&ga.mutation)) {
            out->mutation_kind = PYHELIOS_MUTATION_PER_GENE;
            out->mutation_rate = per_gene->rate;
        } else if (const auto* isotropic = std::get_if<IsotropicMutation>(&ga.mutation)) {
            out->mutation_kind = PYHELIOS_MUTATION_ISOTROPIC;
            out->mutation_rate = isotropic->rate;
        } else if (const auto* hybrid = std::get_if<HybridMutation>(&ga.mutation)) {
            out->mutation_kind = PYHELIOS_MUTATION_HYBRID;
            out->mutation_rate = hybrid->rate;
            out->mutation_pca_update_interval = hybrid->pca_update_interval;
            out->mutation_sigma_pca = hybrid->sigma_pca;
            out->mutation_gamma_cauchy = hybrid->gamma_cauchy;
            out->mutation_sigma_random = hybrid->sigma_random;
            out->mutation_pca_gaussian_prob = hybrid->pca_gaussian_prob;
            out->mutation_pca_cauchy_prob = hybrid->pca_cauchy_prob;
        }
    }

    //! Copy a BayesianOptimization settings struct into its flat mirror.
    void exportBayesian(const BayesianOptimization& bo, PyHeliosBayesianOptimization* out) {
        out->max_evaluations = bo.max_evaluations;
        out->initial_samples = bo.initial_samples;
        out->ucb_kappa = bo.ucb_kappa;
        out->max_gp_samples = bo.max_gp_samples;
        out->acquisition_samples = bo.acquisition_samples;
        out->random_seed = bo.random_seed;
    }

    //! Copy a CMAES settings struct into its flat mirror.
    void exportCMAES(const CMAES& cmaes, PyHeliosCMAES* out) {
        out->max_evaluations = cmaes.max_evaluations;
        out->lambda = cmaes.lambda;
        out->sigma = cmaes.sigma;
        out->random_seed = cmaes.random_seed;
    }

} // namespace

extern "C" {

//=============================================================================
// Lifecycle
//=============================================================================

PYHELIOS_API ParameterOptimization* createParameterOptimization() {
    try {
        clearError();
        return new ParameterOptimization();
    } catch (const std::runtime_error& e) {
        setError(PYHELIOS_ERROR_RUNTIME, e.what());
        return nullptr;
    } catch (const std::exception& e) {
        setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (createParameterOptimization): ") + e.what());
        return nullptr;
    } catch (...) {
        setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (createParameterOptimization): Unknown error creating ParameterOptimization.");
        return nullptr;
    }
}

PYHELIOS_API void destroyParameterOptimization(ParameterOptimization* opt) {
    if (opt) {
        delete opt;
    }
}

//=============================================================================
// Capability query
//=============================================================================

PYHELIOS_API int parameterOptimizationAlgorithmAvailable(const char* algorithm_name) {
    if (!algorithm_name) {
        return 0;
    }

    // Always compiled in: these need no external solver library.
    if (std::strcmp(algorithm_name, "GA") == 0 ||
        std::strcmp(algorithm_name, "BO") == 0 ||
        std::strcmp(algorithm_name, "CMAES") == 0 ||
        std::strcmp(algorithm_name, "ADAM") == 0) {
        return 1;
    }

    if (std::strcmp(algorithm_name, "BOBYQA") == 0 || std::strcmp(algorithm_name, "SLSQP") == 0) {
#ifdef HELIOS_HAVE_NLOPT
        return 1;
#else
        return 0;
#endif
    }

    if (std::strcmp(algorithm_name, "LBFGS") == 0) {
        // Needs both NLopt and the LGPL Luksan solvers that implement L-BFGS.
#if defined(HELIOS_HAVE_NLOPT) && defined(HELIOS_HAVE_LBFGS)
        return 1;
#else
        return 0;
#endif
    }

    return 0;
}

//=============================================================================
// Algorithm selection
//=============================================================================

PYHELIOS_API void setParameterOptimizationGeneticAlgorithm(ParameterOptimization* opt, const PyHeliosGeneticAlgorithm* settings) {
    try {
        clearError();
        if (!opt || !settings) {
            setError(PYHELIOS_ERROR_INVALID_PARAMETER, "ParameterOptimization or settings pointer is null");
            return;
        }

        GeneticAlgorithm ga;
        ga.generations = settings->generations;
        ga.population_size = settings->population_size;
        ga.crossover_rate = settings->crossover_rate;
        ga.elitism_rate = settings->elitism_rate;
        ga.random_seed = settings->random_seed;

        switch (settings->crossover_kind) {
            case PYHELIOS_CROSSOVER_BLX_ALPHA: {
                BLXAlphaCrossover crossover;
                crossover.alpha = settings->crossover_alpha;
                ga.crossover = crossover;
                break;
            }
            case PYHELIOS_CROSSOVER_BLX_PCA: {
                BLXPCACrossover crossover;
                crossover.alpha = settings->crossover_alpha;
                crossover.pca_update_interval = settings->crossover_pca_update_interval;
                ga.crossover = crossover;
                break;
            }
            default:
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Unknown crossover operator selection");
                return;
        }

        switch (settings->mutation_kind) {
            case PYHELIOS_MUTATION_PER_GENE: {
                PerGeneMutation mutation;
                mutation.rate = settings->mutation_rate;
                ga.mutation = mutation;
                break;
            }
            case PYHELIOS_MUTATION_ISOTROPIC: {
                IsotropicMutation mutation;
                mutation.rate = settings->mutation_rate;
                ga.mutation = mutation;
                break;
            }
            case PYHELIOS_MUTATION_HYBRID: {
                HybridMutation mutation;
                mutation.rate = settings->mutation_rate;
                mutation.pca_update_interval = settings->mutation_pca_update_interval;
                mutation.sigma_pca = settings->mutation_sigma_pca;
                mutation.gamma_cauchy = settings->mutation_gamma_cauchy;
                mutation.sigma_random = settings->mutation_sigma_random;
                mutation.pca_gaussian_prob = settings->mutation_pca_gaussian_prob;
                mutation.pca_cauchy_prob = settings->mutation_pca_cauchy_prob;
                ga.mutation = mutation;
                break;
            }
            default:
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Unknown mutation operator selection");
                return;
        }

        opt->setAlgorithm(ga);

    } catch (const std::runtime_error& e) {
        setError(PYHELIOS_ERROR_RUNTIME, e.what());
    } catch (const std::exception& e) {
        setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (setParameterOptimizationGeneticAlgorithm): ") + e.what());
    } catch (...) {
        setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (setParameterOptimizationGeneticAlgorithm): Unknown error.");
    }
}

PYHELIOS_API void setParameterOptimizationBayesian(ParameterOptimization* opt, const PyHeliosBayesianOptimization* settings) {
    try {
        clearError();
        if (!opt || !settings) {
            setError(PYHELIOS_ERROR_INVALID_PARAMETER, "ParameterOptimization or settings pointer is null");
            return;
        }

        BayesianOptimization bo;
        bo.max_evaluations = settings->max_evaluations;
        bo.initial_samples = settings->initial_samples;
        bo.ucb_kappa = settings->ucb_kappa;
        bo.max_gp_samples = settings->max_gp_samples;
        bo.acquisition_samples = settings->acquisition_samples;
        bo.random_seed = settings->random_seed;

        opt->setAlgorithm(bo);

    } catch (const std::runtime_error& e) {
        setError(PYHELIOS_ERROR_RUNTIME, e.what());
    } catch (const std::exception& e) {
        setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (setParameterOptimizationBayesian): ") + e.what());
    } catch (...) {
        setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (setParameterOptimizationBayesian): Unknown error.");
    }
}

PYHELIOS_API void setParameterOptimizationCMAES(ParameterOptimization* opt, const PyHeliosCMAES* settings) {
    try {
        clearError();
        if (!opt || !settings) {
            setError(PYHELIOS_ERROR_INVALID_PARAMETER, "ParameterOptimization or settings pointer is null");
            return;
        }

        CMAES cmaes;
        cmaes.max_evaluations = settings->max_evaluations;
        cmaes.lambda = settings->lambda;
        cmaes.sigma = settings->sigma;
        cmaes.random_seed = settings->random_seed;

        opt->setAlgorithm(cmaes);

    } catch (const std::runtime_error& e) {
        setError(PYHELIOS_ERROR_RUNTIME, e.what());
    } catch (const std::exception& e) {
        setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (setParameterOptimizationCMAES): ") + e.what());
    } catch (...) {
        setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (setParameterOptimizationCMAES): Unknown error.");
    }
}

PYHELIOS_API void setParameterOptimizationLBFGS(ParameterOptimization* opt, const PyHeliosLBFGS* settings) {
    try {
        clearError();
        if (!opt || !settings) {
            setError(PYHELIOS_ERROR_INVALID_PARAMETER, "ParameterOptimization or settings pointer is null");
            return;
        }

        LBFGS lbfgs;
        lbfgs.max_iterations = settings->max_iterations;
        lbfgs.ftol_rel = settings->ftol_rel;
        lbfgs.xtol_rel = settings->xtol_rel;
        lbfgs.verify_gradients = (settings->verify_gradients != 0);
        lbfgs.fd_step = settings->fd_step;

        opt->setAlgorithm(lbfgs);

    } catch (const std::runtime_error& e) {
        setError(PYHELIOS_ERROR_RUNTIME, e.what());
    } catch (const std::exception& e) {
        setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (setParameterOptimizationLBFGS): ") + e.what());
    } catch (...) {
        setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (setParameterOptimizationLBFGS): Unknown error.");
    }
}

PYHELIOS_API void setParameterOptimizationAdam(ParameterOptimization* opt, const PyHeliosAdam* settings) {
    try {
        clearError();
        if (!opt || !settings) {
            setError(PYHELIOS_ERROR_INVALID_PARAMETER, "ParameterOptimization or settings pointer is null");
            return;
        }

        Adam adam;
        adam.max_iterations = settings->max_iterations;
        adam.learning_rate = settings->learning_rate;
        adam.beta1 = settings->beta1;
        adam.beta2 = settings->beta2;
        adam.epsilon = settings->epsilon;
        adam.weight_decay = settings->weight_decay;
        adam.ftol_rel = settings->ftol_rel;
        adam.xtol_rel = settings->xtol_rel;

        opt->setAlgorithm(adam);

    } catch (const std::runtime_error& e) {
        setError(PYHELIOS_ERROR_RUNTIME, e.what());
    } catch (const std::exception& e) {
        setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (setParameterOptimizationAdam): ") + e.what());
    } catch (...) {
        setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (setParameterOptimizationAdam): Unknown error.");
    }
}

PYHELIOS_API void setParameterOptimizationBOBYQA(ParameterOptimization* opt, const PyHeliosBOBYQA* settings) {
    try {
        clearError();
        if (!opt || !settings) {
            setError(PYHELIOS_ERROR_INVALID_PARAMETER, "ParameterOptimization or settings pointer is null");
            return;
        }

        BOBYQA bobyqa;
        bobyqa.max_iterations = settings->max_iterations;
        bobyqa.ftol_rel = settings->ftol_rel;
        bobyqa.xtol_rel = settings->xtol_rel;
        bobyqa.initial_step = settings->initial_step;

        opt->setAlgorithm(bobyqa);

    } catch (const std::runtime_error& e) {
        setError(PYHELIOS_ERROR_RUNTIME, e.what());
    } catch (const std::exception& e) {
        setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (setParameterOptimizationBOBYQA): ") + e.what());
    } catch (...) {
        setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (setParameterOptimizationBOBYQA): Unknown error.");
    }
}

PYHELIOS_API void setParameterOptimizationSLSQP(ParameterOptimization* opt, const PyHeliosSLSQP* settings) {
    try {
        clearError();
        if (!opt || !settings) {
            setError(PYHELIOS_ERROR_INVALID_PARAMETER, "ParameterOptimization or settings pointer is null");
            return;
        }

        SLSQP slsqp;
        slsqp.max_iterations = settings->max_iterations;
        slsqp.ftol_rel = settings->ftol_rel;
        slsqp.xtol_rel = settings->xtol_rel;

        opt->setAlgorithm(slsqp);

    } catch (const std::runtime_error& e) {
        setError(PYHELIOS_ERROR_RUNTIME, e.what());
    } catch (const std::exception& e) {
        setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (setParameterOptimizationSLSQP): ") + e.what());
    } catch (...) {
        setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (setParameterOptimizationSLSQP): Unknown error.");
    }
}

//=============================================================================
// Preset settings
//=============================================================================

PYHELIOS_API void getParameterOptimizationGADefaults(PyHeliosGeneticAlgorithm* out) {
    if (out) {
        exportGeneticAlgorithm(GeneticAlgorithm(), out);
    }
}

PYHELIOS_API void getParameterOptimizationGAExplore(PyHeliosGeneticAlgorithm* out) {
    if (out) {
        exportGeneticAlgorithm(GeneticAlgorithm::explore(), out);
    }
}

PYHELIOS_API void getParameterOptimizationGAExploit(PyHeliosGeneticAlgorithm* out) {
    if (out) {
        exportGeneticAlgorithm(GeneticAlgorithm::exploit(), out);
    }
}

PYHELIOS_API void getParameterOptimizationBayesianDefaults(PyHeliosBayesianOptimization* out) {
    if (out) {
        exportBayesian(BayesianOptimization(), out);
    }
}

PYHELIOS_API void getParameterOptimizationBayesianExplore(PyHeliosBayesianOptimization* out) {
    if (out) {
        exportBayesian(BayesianOptimization::explore(), out);
    }
}

PYHELIOS_API void getParameterOptimizationBayesianExploit(PyHeliosBayesianOptimization* out) {
    if (out) {
        exportBayesian(BayesianOptimization::exploit(), out);
    }
}

PYHELIOS_API void getParameterOptimizationCMAESDefaults(PyHeliosCMAES* out) {
    if (out) {
        exportCMAES(CMAES(), out);
    }
}

PYHELIOS_API void getParameterOptimizationCMAESExplore(PyHeliosCMAES* out) {
    if (out) {
        exportCMAES(CMAES::explore(), out);
    }
}

PYHELIOS_API void getParameterOptimizationCMAESExploit(PyHeliosCMAES* out) {
    if (out) {
        exportCMAES(CMAES::exploit(), out);
    }
}

PYHELIOS_API void getParameterOptimizationLBFGSDefaults(PyHeliosLBFGS* out) {
    if (out) {
        LBFGS lbfgs;
        out->max_iterations = lbfgs.max_iterations;
        out->ftol_rel = lbfgs.ftol_rel;
        out->xtol_rel = lbfgs.xtol_rel;
        out->verify_gradients = lbfgs.verify_gradients ? 1 : 0;
        out->fd_step = lbfgs.fd_step;
    }
}

PYHELIOS_API void getParameterOptimizationAdamDefaults(PyHeliosAdam* out) {
    if (out) {
        Adam adam;
        out->max_iterations = adam.max_iterations;
        out->learning_rate = adam.learning_rate;
        out->beta1 = adam.beta1;
        out->beta2 = adam.beta2;
        out->epsilon = adam.epsilon;
        out->weight_decay = adam.weight_decay;
        out->ftol_rel = adam.ftol_rel;
        out->xtol_rel = adam.xtol_rel;
    }
}

PYHELIOS_API void getParameterOptimizationBOBYQADefaults(PyHeliosBOBYQA* out) {
    if (out) {
        BOBYQA bobyqa;
        out->max_iterations = bobyqa.max_iterations;
        out->ftol_rel = bobyqa.ftol_rel;
        out->xtol_rel = bobyqa.xtol_rel;
        out->initial_step = bobyqa.initial_step;
    }
}

PYHELIOS_API void getParameterOptimizationSLSQPDefaults(PyHeliosSLSQP* out) {
    if (out) {
        SLSQP slsqp;
        out->max_iterations = slsqp.max_iterations;
        out->ftol_rel = slsqp.ftol_rel;
        out->xtol_rel = slsqp.xtol_rel;
    }
}

//=============================================================================
// I/O configuration
//=============================================================================

PYHELIOS_API void setParameterOptimizationPrintProgress(ParameterOptimization* opt, int enable) {
    try {
        clearError();
        if (!opt) {
            setError(PYHELIOS_ERROR_INVALID_PARAMETER, "ParameterOptimization pointer is null");
            return;
        }
        opt->print_progress = (enable != 0);
    } catch (const std::exception& e) {
        setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (setParameterOptimizationPrintProgress): ") + e.what());
    } catch (...) {
        setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (setParameterOptimizationPrintProgress): Unknown error.");
    }
}

PYHELIOS_API void setParameterOptimizationResultFile(ParameterOptimization* opt, const char* path) {
    try {
        clearError();
        if (!opt) {
            setError(PYHELIOS_ERROR_INVALID_PARAMETER, "ParameterOptimization pointer is null");
            return;
        }
        opt->write_result_to_file = path ? std::string(path) : std::string();
    } catch (const std::exception& e) {
        setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (setParameterOptimizationResultFile): ") + e.what());
    } catch (...) {
        setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (setParameterOptimizationResultFile): Unknown error.");
    }
}

PYHELIOS_API void setParameterOptimizationProgressFile(ParameterOptimization* opt, const char* path) {
    try {
        clearError();
        if (!opt) {
            setError(PYHELIOS_ERROR_INVALID_PARAMETER, "ParameterOptimization pointer is null");
            return;
        }
        opt->write_progress_to_file = path ? std::string(path) : std::string();
    } catch (const std::exception& e) {
        setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (setParameterOptimizationProgressFile): ") + e.what());
    } catch (...) {
        setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (setParameterOptimizationProgressFile): Unknown error.");
    }
}

PYHELIOS_API void setParameterOptimizationInputFile(ParameterOptimization* opt, const char* path) {
    try {
        clearError();
        if (!opt) {
            setError(PYHELIOS_ERROR_INVALID_PARAMETER, "ParameterOptimization pointer is null");
            return;
        }
        opt->read_input_from_file = path ? std::string(path) : std::string();
    } catch (const std::exception& e) {
        setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (setParameterOptimizationInputFile): ") + e.what());
    } catch (...) {
        setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (setParameterOptimizationInputFile): Unknown error.");
    }
}

//=============================================================================
// Run
//=============================================================================

PYHELIOS_API int runParameterOptimization(ParameterOptimization* opt,
                                          const PyHeliosParameterSpec* params,
                                          unsigned int param_count,
                                          PyHeliosObjectiveCallback objective,
                                          void* user_data,
                                          float* out_values,
                                          float* out_fitness) {
    try {
        clearError();
        if (!validateRunArguments(opt, params, param_count, objective, out_values, out_fitness)) {
            return PYHELIOS_PARAMOPT_ERROR;
        }

        ParametersToOptimize parameters = buildParameters(params, param_count);

        CallbackBridge bridge;
        bridge.objective_cb = objective;
        bridge.user_data = user_data;
        initializeOrdering(bridge, parameters);

        ParameterOptimization::Result result = opt->run(makeObjectiveAdapter(&bridge), parameters);
        writeResult(bridge, result, out_values, out_fitness);
        return PYHELIOS_PARAMOPT_OK;

    } catch (const PyHeliosCallbackAbort&) {
        // Deliberately no setError: the host holds the original exception.
        return PYHELIOS_PARAMOPT_CALLBACK_FAILED;
    } catch (const std::runtime_error& e) {
        setError(PYHELIOS_ERROR_RUNTIME, e.what());
        return PYHELIOS_PARAMOPT_ERROR;
    } catch (const std::exception& e) {
        setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (runParameterOptimization): ") + e.what());
        return PYHELIOS_PARAMOPT_ERROR;
    } catch (...) {
        setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (runParameterOptimization): Unknown error.");
        return PYHELIOS_PARAMOPT_ERROR;
    }
}

PYHELIOS_API int runParameterOptimizationWithGradient(ParameterOptimization* opt,
                                                      const PyHeliosParameterSpec* params,
                                                      unsigned int param_count,
                                                      PyHeliosObjectiveCallback objective,
                                                      PyHeliosGradientCallback gradient,
                                                      void* user_data,
                                                      float* out_values,
                                                      float* out_fitness) {
    try {
        clearError();
        if (!validateRunArguments(opt, params, param_count, objective, out_values, out_fitness)) {
            return PYHELIOS_PARAMOPT_ERROR;
        }
        if (!gradient) {
            setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Gradient callback is null");
            return PYHELIOS_PARAMOPT_ERROR;
        }

        ParametersToOptimize parameters = buildParameters(params, param_count);

        CallbackBridge bridge;
        bridge.objective_cb = objective;
        bridge.gradient_cb = gradient;
        bridge.user_data = user_data;
        initializeOrdering(bridge, parameters);

        ParameterOptimization::Result result =
            opt->run(makeObjectiveAdapter(&bridge), parameters, makeGradientAdapter(&bridge));
        writeResult(bridge, result, out_values, out_fitness);
        return PYHELIOS_PARAMOPT_OK;

    } catch (const PyHeliosCallbackAbort&) {
        return PYHELIOS_PARAMOPT_CALLBACK_FAILED;
    } catch (const std::runtime_error& e) {
        setError(PYHELIOS_ERROR_RUNTIME, e.what());
        return PYHELIOS_PARAMOPT_ERROR;
    } catch (const std::exception& e) {
        setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (runParameterOptimizationWithGradient): ") + e.what());
        return PYHELIOS_PARAMOPT_ERROR;
    } catch (...) {
        setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (runParameterOptimizationWithGradient): Unknown error.");
        return PYHELIOS_PARAMOPT_ERROR;
    }
}

PYHELIOS_API int runParameterOptimizationWithFDGradient(ParameterOptimization* opt,
                                                        const PyHeliosParameterSpec* params,
                                                        unsigned int param_count,
                                                        PyHeliosObjectiveCallback objective,
                                                        float fd_step,
                                                        void* user_data,
                                                        float* out_values,
                                                        float* out_fitness) {
    try {
        clearError();
        if (!validateRunArguments(opt, params, param_count, objective, out_values, out_fitness)) {
            return PYHELIOS_PARAMOPT_ERROR;
        }

        ParametersToOptimize parameters = buildParameters(params, param_count);

        CallbackBridge bridge;
        bridge.objective_cb = objective;
        bridge.user_data = user_data;
        initializeOrdering(bridge, parameters);

        ObjectiveFunction objective_fn = makeObjectiveAdapter(&bridge);
        GradientFunction gradient_fn = (fd_step > 0.f) ? makeFDGradient(objective_fn, fd_step)
                                                       : makeFDGradient(objective_fn);

        ParameterOptimization::Result result = opt->run(objective_fn, parameters, gradient_fn);
        writeResult(bridge, result, out_values, out_fitness);
        return PYHELIOS_PARAMOPT_OK;

    } catch (const PyHeliosCallbackAbort&) {
        return PYHELIOS_PARAMOPT_CALLBACK_FAILED;
    } catch (const std::runtime_error& e) {
        setError(PYHELIOS_ERROR_RUNTIME, e.what());
        return PYHELIOS_PARAMOPT_ERROR;
    } catch (const std::exception& e) {
        setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (runParameterOptimizationWithFDGradient): ") + e.what());
        return PYHELIOS_PARAMOPT_ERROR;
    } catch (...) {
        setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (runParameterOptimizationWithFDGradient): Unknown error.");
        return PYHELIOS_PARAMOPT_ERROR;
    }
}

PYHELIOS_API int runParameterOptimizationConstrained(ParameterOptimization* opt,
                                                     const PyHeliosParameterSpec* params,
                                                     unsigned int param_count,
                                                     PyHeliosConstrainedCallback simulation,
                                                     unsigned int constraint_count,
                                                     void* user_data,
                                                     float* out_values,
                                                     float* out_fitness) {
    try {
        clearError();
        // The objective slot carries the constrained callback purely so the shared
        // null checks apply; the bridge below uses it under its own type.
        if (!validateRunArguments(opt, params, param_count,
                                  reinterpret_cast<PyHeliosObjectiveCallback>(simulation),
                                  out_values, out_fitness)) {
            return PYHELIOS_PARAMOPT_ERROR;
        }
        if (constraint_count == 0) {
            setError(PYHELIOS_ERROR_INVALID_PARAMETER,
                     "Constraint count must be non-zero; use an unconstrained run instead.");
            return PYHELIOS_PARAMOPT_ERROR;
        }

        ParametersToOptimize parameters = buildParameters(params, param_count);

        CallbackBridge bridge;
        bridge.constrained_cb = simulation;
        bridge.constraint_count = constraint_count;
        bridge.user_data = user_data;
        initializeOrdering(bridge, parameters);

        ParameterOptimization::Result result =
            opt->run(makeConstrainedAdapter(&bridge), parameters);
        writeResult(bridge, result, out_values, out_fitness);
        return PYHELIOS_PARAMOPT_OK;

    } catch (const PyHeliosCallbackAbort&) {
        return PYHELIOS_PARAMOPT_CALLBACK_FAILED;
    } catch (const std::runtime_error& e) {
        setError(PYHELIOS_ERROR_RUNTIME, e.what());
        return PYHELIOS_PARAMOPT_ERROR;
    } catch (const std::exception& e) {
        setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (runParameterOptimizationConstrained): ") + e.what());
        return PYHELIOS_PARAMOPT_ERROR;
    } catch (...) {
        setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (runParameterOptimizationConstrained): Unknown error.");
        return PYHELIOS_PARAMOPT_ERROR;
    }
}

} // extern "C"

#endif // PARAMETEROPTIMIZATION_PLUGIN_AVAILABLE
