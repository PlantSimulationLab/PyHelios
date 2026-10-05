// PyHelios C Interface - PlantHydraulics Functions
// Provides plant hydraulics modeling of soil, root, stem and leaf water potentials

#include "../include/pyhelios_wrapper_common.h"
#include "../include/pyhelios_wrapper_context.h"
#include "Context.h"
#include <string>
#include <exception>
#include <stdexcept>
#include <vector>

#ifdef PLANTHYDRAULICS_PLUGIN_AVAILABLE
#include "../include/pyhelios_wrapper_planthydraulics.h"
#include "PlantHydraulicsModel.h"

namespace {

    HydraulicConductance makeConductance(const float* c) {
        return HydraulicConductance(c[0], c[1], c[2], c[3] != 0.f);
    }

    HydraulicCapacitance makeCapacitance(const float* c) {
        if (c[4] > 0.f) {
            return HydraulicCapacitance(c[4]);
        }
        return HydraulicCapacitance(c[0], c[1], c[2], c[3]);
    }

    // PlantHydraulicsModelCoefficients keeps its members private, so it is populated through its setters.
    PlantHydraulicsModelCoefficients makeCoefficients(const float* c, const char* leaf_capacitance_species) {
        PlantHydraulicsModelCoefficients coeffs;

        coeffs.setLeafHydraulicConductance(c[0], c[1], c[2], c[3] != 0.f);
        coeffs.setStemHydraulicConductance(c[4], c[5], c[6], c[7] != 0.f);
        coeffs.setRootHydraulicConductance(c[8], c[9], c[10], c[11] != 0.f);

        if (leaf_capacitance_species && leaf_capacitance_species[0] != '\0') {
            coeffs.setLeafHydraulicCapacitanceFromLibrary(std::string(leaf_capacitance_species));
        } else if (c[16] > 0.f) {
            coeffs.setLeafHydraulicCapacitance(c[16]);
        } else {
            coeffs.setLeafHydraulicCapacitance(c[12], c[13], c[14], c[15]);
        }

        if (c[20] > 0.f) {
            coeffs.setStemHydraulicCapacitance(c[20]);
        } else {
            coeffs.setStemHydraulicCapacitance(c[17], c[18], c[19]);
        }

        if (c[24] > 0.f) {
            coeffs.setRootHydraulicCapacitance(c[24]);
        } else {
            coeffs.setRootHydraulicCapacitance(c[21], c[22], c[23]);
        }

        return coeffs;
    }

    // Inverse of makeCoefficients(): writes the PYHELIOS_PLANTHYDRAULICS_COEFFICIENT_SIZE layout.
    void writeCoefficients(const PlantHydraulicsModelCoefficients& coeffs, float* c) {
        const HydraulicConductance conductances[3] = {coeffs.getLeafHydraulicConductance(), coeffs.getStemHydraulicConductance(), coeffs.getRootHydraulicConductance()};
        for (int i = 0; i < 3; i++) {
            c[4 * i] = conductances[i].saturated_conductance;
            c[4 * i + 1] = conductances[i].potential_at_half_saturated;
            c[4 * i + 2] = conductances[i].sensitivity;
            c[4 * i + 3] = conductances[i].temperature_dependence ? 1.f : 0.f;
        }

        const HydraulicCapacitance leaf = coeffs.getLeafHydraulicCapacitance();
        c[12] = leaf.osmotic_potential_at_full_turgor;
        c[13] = leaf.relative_water_content_at_turgor_loss;
        c[14] = leaf.cell_wall_elasticity_exponent;
        c[15] = leaf.saturated_specific_water_content;
        c[16] = leaf.fixed_constant_capacitance;

        const HydraulicCapacitance stem_root[2] = {coeffs.getStemHydraulicCapacitance(), coeffs.getRootHydraulicCapacitance()};
        for (int i = 0; i < 2; i++) {
            c[17 + 4 * i] = stem_root[i].osmotic_potential_at_full_turgor;
            c[18 + 4 * i] = stem_root[i].relative_water_content_at_turgor_loss;
            c[19 + 4 * i] = stem_root[i].cell_wall_elasticity_exponent;
            c[20 + 4 * i] = stem_root[i].fixed_constant_capacitance;
        }
    }

} // namespace

extern "C" {

    PYHELIOS_API PlantHydraulicsModel* createPlantHydraulicsModel(helios::Context* context) {
        try {
            clearError();
            if (!context) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Context pointer is null");
                return nullptr;
            }

            return new PlantHydraulicsModel(context);

        } catch (const std::runtime_error& e) {
            setError(PYHELIOS_ERROR_RUNTIME, e.what());
            return nullptr;
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (createPlantHydraulicsModel): ") + e.what());
            return nullptr;
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (createPlantHydraulicsModel): Unknown error creating PlantHydraulicsModel.");
            return nullptr;
        }
    }

    PYHELIOS_API void destroyPlantHydraulicsModel(PlantHydraulicsModel* model) {
        if (model) {
            delete model;
        }
    }

    PYHELIOS_API void setPlantHydraulicsModelCoefficients(PlantHydraulicsModel* model, const float* coefficients, unsigned int coeff_count, const char* leaf_capacitance_species) {
        try {
            clearError();
            if (!model) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "PlantHydraulicsModel pointer is null");
                return;
            }
            if (!coefficients) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Coefficients array is null");
                return;
            }
            if (coeff_count != PYHELIOS_PLANTHYDRAULICS_COEFFICIENT_SIZE) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Coefficients array must have " + std::to_string(PYHELIOS_PLANTHYDRAULICS_COEFFICIENT_SIZE) + " elements, got " + std::to_string(coeff_count));
                return;
            }

            model->setModelCoefficients(makeCoefficients(coefficients, leaf_capacitance_species));
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (PlantHydraulicsModel::setModelCoefficients): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (PlantHydraulicsModel::setModelCoefficients): Unknown error.");
        }
    }

    PYHELIOS_API void setPlantHydraulicsModelCoefficientsForUUIDs(PlantHydraulicsModel* model, const float* coefficients, unsigned int coeff_count, const char* leaf_capacitance_species, const unsigned int* uuids, unsigned int uuid_count) {
        try {
            clearError();
            if (!model) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "PlantHydraulicsModel pointer is null");
                return;
            }
            if (!coefficients) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Coefficients array is null");
                return;
            }
            if (coeff_count != PYHELIOS_PLANTHYDRAULICS_COEFFICIENT_SIZE) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Coefficients array must have " + std::to_string(PYHELIOS_PLANTHYDRAULICS_COEFFICIENT_SIZE) + " elements, got " + std::to_string(coeff_count));
                return;
            }
            if (!uuids) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "UUIDs array is null");
                return;
            }
            if (uuid_count == 0) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "UUID count must be greater than 0");
                return;
            }

            std::vector<uint> uuid_vector(uuids, uuids + uuid_count);
            model->setModelCoefficients(makeCoefficients(coefficients, leaf_capacitance_species), uuid_vector);
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (PlantHydraulicsModel::setModelCoefficients): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (PlantHydraulicsModel::setModelCoefficients): Unknown error.");
        }
    }

    PYHELIOS_API void setPlantHydraulicsModelCoefficientsFromLibrary(PlantHydraulicsModel* model, const char* species) {
        try {
            clearError();
            if (!model) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "PlantHydraulicsModel pointer is null");
                return;
            }
            if (!species) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Species name is null");
                return;
            }

            model->setModelCoefficientsFromLibrary(std::string(species));
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (PlantHydraulicsModel::setModelCoefficientsFromLibrary): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (PlantHydraulicsModel::setModelCoefficientsFromLibrary): Unknown error.");
        }
    }

    PYHELIOS_API void setPlantHydraulicsModelCoefficientsFromLibraryForUUIDs(PlantHydraulicsModel* model, const char* species, const unsigned int* uuids, unsigned int uuid_count) {
        try {
            clearError();
            if (!model) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "PlantHydraulicsModel pointer is null");
                return;
            }
            if (!species) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Species name is null");
                return;
            }
            if (!uuids) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "UUIDs array is null");
                return;
            }
            if (uuid_count == 0) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "UUID count must be greater than 0");
                return;
            }

            std::vector<uint> uuid_vector(uuids, uuids + uuid_count);
            model->setModelCoefficientsFromLibrary(std::string(species), uuid_vector);
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (PlantHydraulicsModel::setModelCoefficientsFromLibrary): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (PlantHydraulicsModel::setModelCoefficientsFromLibrary): Unknown error.");
        }
    }

    PYHELIOS_API void getPlantHydraulicsModelCoefficients(PlantHydraulicsModel* model, unsigned int uuid, float* coefficients, unsigned int coeff_count) {
        try {
            clearError();
            if (!model) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "PlantHydraulicsModel pointer is null");
                return;
            }
            if (!coefficients) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Coefficients array is null");
                return;
            }
            if (coeff_count != PYHELIOS_PLANTHYDRAULICS_COEFFICIENT_SIZE) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Coefficients array must have " + std::to_string(PYHELIOS_PLANTHYDRAULICS_COEFFICIENT_SIZE) + " elements");
                return;
            }

            writeCoefficients(model->getModelCoefficients(uuid), coefficients);
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (PlantHydraulicsModel::getModelCoefficients): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (PlantHydraulicsModel::getModelCoefficients): Unknown error.");
        }
    }

    PYHELIOS_API void getPlantHydraulicsModelCoefficientsFromLibrary(PlantHydraulicsModel* model, const char* species, float* coefficients, unsigned int coeff_count) {
        try {
            clearError();
            if (!model) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "PlantHydraulicsModel pointer is null");
                return;
            }
            if (!species) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Species name is null");
                return;
            }
            if (!coefficients) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Coefficients array is null");
                return;
            }
            if (coeff_count != PYHELIOS_PLANTHYDRAULICS_COEFFICIENT_SIZE) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Coefficients array must have " + std::to_string(PYHELIOS_PLANTHYDRAULICS_COEFFICIENT_SIZE) + " elements");
                return;
            }

            writeCoefficients(model->getModelCoefficientsFromLibrary(std::string(species)), coefficients);
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (PlantHydraulicsModel::getModelCoefficientsFromLibrary): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (PlantHydraulicsModel::getModelCoefficientsFromLibrary): Unknown error.");
        }
    }

    PYHELIOS_API void runPlantHydraulicsModel(PlantHydraulicsModel* model, int timespan, int timestep) {
        try {
            clearError();
            if (!model) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "PlantHydraulicsModel pointer is null");
                return;
            }

            model->run(timespan, timestep);
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (PlantHydraulicsModel::run): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (PlantHydraulicsModel::run): Unknown error.");
        }
    }

    PYHELIOS_API void runPlantHydraulicsModelForUUIDs(PlantHydraulicsModel* model, const unsigned int* uuids, unsigned int uuid_count, int timespan, int timestep) {
        try {
            clearError();
            if (!model) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "PlantHydraulicsModel pointer is null");
                return;
            }
            if (!uuids) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "UUIDs array is null");
                return;
            }
            if (uuid_count == 0) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "UUID count must be greater than 0");
                return;
            }

            std::vector<uint> uuid_vector(uuids, uuids + uuid_count);
            model->run(uuid_vector, timespan, timestep);
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (PlantHydraulicsModel::run): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (PlantHydraulicsModel::run): Unknown error.");
        }
    }

    PYHELIOS_API void setPlantHydraulicsOutputConductancePrimitiveData(PlantHydraulicsModel* model, bool toggle) {
        try {
            clearError();
            if (!model) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "PlantHydraulicsModel pointer is null");
                return;
            }

            model->outputConductancePrimitiveData(toggle);
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (PlantHydraulicsModel::outputConductancePrimitiveData): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (PlantHydraulicsModel::outputConductancePrimitiveData): Unknown error.");
        }
    }

    PYHELIOS_API void setPlantHydraulicsOutputCapacitancePrimitiveData(PlantHydraulicsModel* model, bool toggle) {
        try {
            clearError();
            if (!model) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "PlantHydraulicsModel pointer is null");
                return;
            }

            model->outputCapacitancePrimitiveData(toggle);
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (PlantHydraulicsModel::outputCapacitancePrimitiveData): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (PlantHydraulicsModel::outputCapacitancePrimitiveData): Unknown error.");
        }
    }

    PYHELIOS_API void groupPlantHydraulicsPrimitivesIntoPlantObject(PlantHydraulicsModel* model, const unsigned int* uuids, unsigned int uuid_count) {
        try {
            clearError();
            if (!model) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "PlantHydraulicsModel pointer is null");
                return;
            }
            if (!uuids) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "UUIDs array is null");
                return;
            }
            if (uuid_count == 0) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "UUID count must be greater than 0");
                return;
            }

            std::vector<uint> uuid_vector(uuids, uuids + uuid_count);
            model->groupPrimitivesIntoPlantObject(uuid_vector);
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (PlantHydraulicsModel::groupPrimitivesIntoPlantObject): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (PlantHydraulicsModel::groupPrimitivesIntoPlantObject): Unknown error.");
        }
    }

    PYHELIOS_API int getPlantHydraulicsPlantID(PlantHydraulicsModel* model, unsigned int uuid) {
        try {
            clearError();
            if (!model) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "PlantHydraulicsModel pointer is null");
                return 0;
            }

            return model->getPlantID(uuid);
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (PlantHydraulicsModel::getPlantID): ") + e.what());
            return 0;
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (PlantHydraulicsModel::getPlantID): Unknown error.");
            return 0;
        }
    }

    PYHELIOS_API int getPlantHydraulicsPlantIDForUUIDs(PlantHydraulicsModel* model, const unsigned int* uuids, unsigned int uuid_count) {
        try {
            clearError();
            if (!model) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "PlantHydraulicsModel pointer is null");
                return 0;
            }
            if (!uuids) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "UUIDs array is null");
                return 0;
            }
            if (uuid_count == 0) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "UUID count must be greater than 0");
                return 0;
            }

            std::vector<uint> uuid_vector(uuids, uuids + uuid_count);
            return model->getPlantID(uuid_vector);
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (PlantHydraulicsModel::getPlantID): ") + e.what());
            return 0;
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (PlantHydraulicsModel::getPlantID): Unknown error.");
            return 0;
        }
    }

    PYHELIOS_API int* getPlantHydraulicsUniquePlantIDs(PlantHydraulicsModel* model, const unsigned int* uuids, unsigned int uuid_count, unsigned int* count) {
        try {
            clearError();
            if (!model) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "PlantHydraulicsModel pointer is null");
                return nullptr;
            }
            if (!count) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Count pointer is null");
                return nullptr;
            }
            *count = 0;
            if (!uuids) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "UUIDs array is null");
                return nullptr;
            }
            if (uuid_count == 0) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "UUID count must be greater than 0");
                return nullptr;
            }

            std::vector<uint> uuid_vector(uuids, uuids + uuid_count);
            static thread_local std::vector<int> static_result;
            static_result = model->getUniquePlantIDs(uuid_vector);
            *count = static_cast<unsigned int>(static_result.size());
            return static_result.data();
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (PlantHydraulicsModel::getUniquePlantIDs): ") + e.what());
            return nullptr;
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (PlantHydraulicsModel::getUniquePlantIDs): Unknown error.");
            return nullptr;
        }
    }

    PYHELIOS_API unsigned int* getPlantHydraulicsPrimitivesByPlantID(PlantHydraulicsModel* model, int plantID, unsigned int* count) {
        try {
            clearError();
            if (!model) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "PlantHydraulicsModel pointer is null");
                return nullptr;
            }
            if (!count) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Count pointer is null");
                return nullptr;
            }
            *count = 0;

            static thread_local std::vector<unsigned int> static_result;
            static_result = model->getPrimitivesByPlantID(plantID);
            *count = static_cast<unsigned int>(static_result.size());
            return static_result.data();
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (PlantHydraulicsModel::getPrimitivesByPlantID): ") + e.what());
            return nullptr;
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (PlantHydraulicsModel::getPrimitivesByPlantID): Unknown error.");
            return nullptr;
        }
    }

    PYHELIOS_API unsigned int* getPlantHydraulicsPrimitivesWithoutPlantID(PlantHydraulicsModel* model, const unsigned int* uuids, unsigned int uuid_count, unsigned int* count) {
        try {
            clearError();
            if (!model) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "PlantHydraulicsModel pointer is null");
                return nullptr;
            }
            if (!count) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Count pointer is null");
                return nullptr;
            }
            *count = 0;
            if (!uuids) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "UUIDs array is null");
                return nullptr;
            }
            if (uuid_count == 0) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "UUID count must be greater than 0");
                return nullptr;
            }

            std::vector<uint> uuid_vector(uuids, uuids + uuid_count);
            static thread_local std::vector<unsigned int> static_result;
            static_result = model->getPrimitivesWithoutPlantID(uuid_vector);
            *count = static_cast<unsigned int>(static_result.size());
            return static_result.data();
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (PlantHydraulicsModel::getPrimitivesWithoutPlantID): ") + e.what());
            return nullptr;
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (PlantHydraulicsModel::getPrimitivesWithoutPlantID): Unknown error.");
            return nullptr;
        }
    }

    PYHELIOS_API float getPlantHydraulicsStemWaterPotential(PlantHydraulicsModel* model, unsigned int uuid) {
        try {
            clearError();
            if (!model) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "PlantHydraulicsModel pointer is null");
                return 0.f;
            }

            return model->getStemWaterPotential(uuid);
        } catch (const std::out_of_range&) {
            setError(PYHELIOS_ERROR_RUNTIME, "ERROR (PlantHydraulicsModel::getStemWaterPotential): No stem water potential is stored for this plant. Call run() for the plant first.");
            return 0.f;
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (PlantHydraulicsModel::getStemWaterPotential): ") + e.what());
            return 0.f;
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (PlantHydraulicsModel::getStemWaterPotential): Unknown error.");
            return 0.f;
        }
    }

    PYHELIOS_API float getPlantHydraulicsStemWaterPotentialForUUIDs(PlantHydraulicsModel* model, const unsigned int* uuids, unsigned int uuid_count) {
        try {
            clearError();
            if (!model) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "PlantHydraulicsModel pointer is null");
                return 0.f;
            }
            if (!uuids) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "UUIDs array is null");
                return 0.f;
            }
            if (uuid_count == 0) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "UUID count must be greater than 0");
                return 0.f;
            }

            std::vector<uint> uuid_vector(uuids, uuids + uuid_count);
            return model->getStemWaterPotential(uuid_vector);
        } catch (const std::out_of_range&) {
            setError(PYHELIOS_ERROR_RUNTIME, "ERROR (PlantHydraulicsModel::getStemWaterPotential): No stem water potential is stored for this plant. Call run() for the plant first.");
            return 0.f;
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (PlantHydraulicsModel::getStemWaterPotential): ") + e.what());
            return 0.f;
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (PlantHydraulicsModel::getStemWaterPotential): Unknown error.");
            return 0.f;
        }
    }

    PYHELIOS_API float getPlantHydraulicsStemWaterPotentialOfPlant(PlantHydraulicsModel* model, unsigned int plantID) {
        try {
            clearError();
            if (!model) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "PlantHydraulicsModel pointer is null");
                return 0.f;
            }

            return model->getStemWaterPotentialOfPlant(plantID);
        } catch (const std::out_of_range&) {
            setError(PYHELIOS_ERROR_RUNTIME, "ERROR (PlantHydraulicsModel::getStemWaterPotentialOfPlant): No stem water potential is stored for this plant. Call run() for the plant first.");
            return 0.f;
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (PlantHydraulicsModel::getStemWaterPotentialOfPlant): ") + e.what());
            return 0.f;
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (PlantHydraulicsModel::getStemWaterPotentialOfPlant): Unknown error.");
            return 0.f;
        }
    }

    PYHELIOS_API float getPlantHydraulicsRootWaterPotential(PlantHydraulicsModel* model, unsigned int uuid) {
        try {
            clearError();
            if (!model) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "PlantHydraulicsModel pointer is null");
                return 0.f;
            }

            return model->getRootWaterPotential(uuid);
        } catch (const std::out_of_range&) {
            setError(PYHELIOS_ERROR_RUNTIME, "ERROR (PlantHydraulicsModel::getRootWaterPotential): No root water potential is stored for this plant. Call run() for the plant first.");
            return 0.f;
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (PlantHydraulicsModel::getRootWaterPotential): ") + e.what());
            return 0.f;
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (PlantHydraulicsModel::getRootWaterPotential): Unknown error.");
            return 0.f;
        }
    }

    PYHELIOS_API float getPlantHydraulicsRootWaterPotentialForUUIDs(PlantHydraulicsModel* model, const unsigned int* uuids, unsigned int uuid_count) {
        try {
            clearError();
            if (!model) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "PlantHydraulicsModel pointer is null");
                return 0.f;
            }
            if (!uuids) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "UUIDs array is null");
                return 0.f;
            }
            if (uuid_count == 0) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "UUID count must be greater than 0");
                return 0.f;
            }

            std::vector<uint> uuid_vector(uuids, uuids + uuid_count);
            return model->getRootWaterPotential(uuid_vector);
        } catch (const std::out_of_range&) {
            setError(PYHELIOS_ERROR_RUNTIME, "ERROR (PlantHydraulicsModel::getRootWaterPotential): No root water potential is stored for this plant. Call run() for the plant first.");
            return 0.f;
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (PlantHydraulicsModel::getRootWaterPotential): ") + e.what());
            return 0.f;
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (PlantHydraulicsModel::getRootWaterPotential): Unknown error.");
            return 0.f;
        }
    }

    PYHELIOS_API float getPlantHydraulicsRootWaterPotentialOfPlant(PlantHydraulicsModel* model, unsigned int plantID) {
        try {
            clearError();
            if (!model) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "PlantHydraulicsModel pointer is null");
                return 0.f;
            }

            return model->getRootWaterPotentialOfPlant(plantID);
        } catch (const std::out_of_range&) {
            setError(PYHELIOS_ERROR_RUNTIME, "ERROR (PlantHydraulicsModel::getRootWaterPotentialOfPlant): No root water potential is stored for this plant. Call run() for the plant first.");
            return 0.f;
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (PlantHydraulicsModel::getRootWaterPotentialOfPlant): ") + e.what());
            return 0.f;
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (PlantHydraulicsModel::getRootWaterPotentialOfPlant): Unknown error.");
            return 0.f;
        }
    }

    PYHELIOS_API float getPlantHydraulicsSoilWaterPotential(PlantHydraulicsModel* model, unsigned int uuid) {
        try {
            clearError();
            if (!model) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "PlantHydraulicsModel pointer is null");
                return 0.f;
            }

            return model->getSoilWaterPotential(uuid);
        } catch (const std::out_of_range&) {
            setError(PYHELIOS_ERROR_RUNTIME, "ERROR (PlantHydraulicsModel::getSoilWaterPotential): No soil water potential is stored for this plant. Call setSoilWaterPotentialOfPlant() or run() for the plant first.");
            return 0.f;
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (PlantHydraulicsModel::getSoilWaterPotential): ") + e.what());
            return 0.f;
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (PlantHydraulicsModel::getSoilWaterPotential): Unknown error.");
            return 0.f;
        }
    }

    PYHELIOS_API float getPlantHydraulicsSoilWaterPotentialForUUIDs(PlantHydraulicsModel* model, const unsigned int* uuids, unsigned int uuid_count) {
        try {
            clearError();
            if (!model) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "PlantHydraulicsModel pointer is null");
                return 0.f;
            }
            if (!uuids) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "UUIDs array is null");
                return 0.f;
            }
            if (uuid_count == 0) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "UUID count must be greater than 0");
                return 0.f;
            }

            std::vector<uint> uuid_vector(uuids, uuids + uuid_count);
            return model->getSoilWaterPotential(uuid_vector);
        } catch (const std::out_of_range&) {
            setError(PYHELIOS_ERROR_RUNTIME, "ERROR (PlantHydraulicsModel::getSoilWaterPotential): No soil water potential is stored for this plant. Call setSoilWaterPotentialOfPlant() or run() for the plant first.");
            return 0.f;
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (PlantHydraulicsModel::getSoilWaterPotential): ") + e.what());
            return 0.f;
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (PlantHydraulicsModel::getSoilWaterPotential): Unknown error.");
            return 0.f;
        }
    }

    PYHELIOS_API float getPlantHydraulicsSoilWaterPotentialOfPlant(PlantHydraulicsModel* model, unsigned int plantID) {
        try {
            clearError();
            if (!model) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "PlantHydraulicsModel pointer is null");
                return 0.f;
            }

            return model->getSoilWaterPotentialOfPlant(plantID);
        } catch (const std::out_of_range&) {
            setError(PYHELIOS_ERROR_RUNTIME, "ERROR (PlantHydraulicsModel::getSoilWaterPotentialOfPlant): No soil water potential is stored for this plant. Call setSoilWaterPotentialOfPlant() or run() for the plant first.");
            return 0.f;
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (PlantHydraulicsModel::getSoilWaterPotentialOfPlant): ") + e.what());
            return 0.f;
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (PlantHydraulicsModel::getSoilWaterPotentialOfPlant): Unknown error.");
            return 0.f;
        }
    }

    PYHELIOS_API void setPlantHydraulicsSoilWaterPotentialOfPlant(PlantHydraulicsModel* model, unsigned int plantID, float soil_water_potential) {
        try {
            clearError();
            if (!model) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "PlantHydraulicsModel pointer is null");
                return;
            }

            model->setSoilWaterPotentialOfPlant(plantID, soil_water_potential);
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (PlantHydraulicsModel::setSoilWaterPotentialOfPlant): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (PlantHydraulicsModel::setSoilWaterPotentialOfPlant): Unknown error.");
        }
    }

    PYHELIOS_API float computePlantHydraulicsOsmoticPotential(const float* capacitance, float relative_water_content) {
        try {
            clearError();
            if (!capacitance) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Capacitance array is null");
                return 0.f;
            }

            return computeOsmoticPotential(makeCapacitance(capacitance), relative_water_content);
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (computeOsmoticPotential): ") + e.what());
            return 0.f;
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (computeOsmoticPotential): Unknown error.");
            return 0.f;
        }
    }

    PYHELIOS_API float computePlantHydraulicsTurgorPressure(const float* capacitance, float relative_water_content) {
        try {
            clearError();
            if (!capacitance) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Capacitance array is null");
                return 0.f;
            }

            return computeTurgorPressure(makeCapacitance(capacitance), relative_water_content);
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (computeTurgorPressure): ") + e.what());
            return 0.f;
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (computeTurgorPressure): Unknown error.");
            return 0.f;
        }
    }

    PYHELIOS_API float computePlantHydraulicsWaterPotential(const float* capacitance, float relative_water_content) {
        try {
            clearError();
            if (!capacitance) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Capacitance array is null");
                return 0.f;
            }

            return computeWaterPotential(makeCapacitance(capacitance), relative_water_content);
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (computeWaterPotential): ") + e.what());
            return 0.f;
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (computeWaterPotential): Unknown error.");
            return 0.f;
        }
    }

    PYHELIOS_API float computePlantHydraulicsCapacitance(const float* capacitance, float relative_water_content) {
        try {
            clearError();
            if (!capacitance) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Capacitance array is null");
                return 0.f;
            }

            return computeCapacitance(makeCapacitance(capacitance), relative_water_content);
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (computeCapacitance): ") + e.what());
            return 0.f;
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (computeCapacitance): Unknown error.");
            return 0.f;
        }
    }

    PYHELIOS_API float computePlantHydraulicsConductance(const float* conductance, float water_potential, float temperature) {
        try {
            clearError();
            if (!conductance) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Conductance array is null");
                return 0.f;
            }

            return computeConductance(makeConductance(conductance), water_potential, temperature);
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (computeConductance): ") + e.what());
            return 0.f;
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (computeConductance): Unknown error.");
            return 0.f;
        }
    }

} //extern "C"

#endif // PLANTHYDRAULICS_PLUGIN_AVAILABLE
