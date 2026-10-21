// PyHelios C Interface - StomatalConductance Functions
// Provides stomatal conductance modeling and gas exchange functions

#include "../include/pyhelios_wrapper_common.h"
#include "../include/pyhelios_wrapper_context.h"
#include "Context.h"
#include <string>
#include <exception>
#include <vector>

#ifdef STOMATALCONDUCTANCE_PLUGIN_AVAILABLE
#include "../include/pyhelios_wrapper_stomatalconductance.h"
#include "StomatalConductanceModel.h"

extern "C" {
    
    PYHELIOS_API StomatalConductanceModel* createStomatalConductanceModel(helios::Context* context) {
        try {
            clearError();
            if (!context) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Context pointer is null");
                return nullptr;
            }
            
            return new StomatalConductanceModel(context);
            
        } catch (const std::runtime_error& e) {
            setError(PYHELIOS_ERROR_RUNTIME, e.what());
            return nullptr;
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (createStomatalConductanceModel): ") + e.what());
            return nullptr;
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (createStomatalConductanceModel): Unknown error creating StomatalConductanceModel.");
            return nullptr;
        }
    }
    
    PYHELIOS_API void destroyStomatalConductanceModel(StomatalConductanceModel* model) {
        if (model) {
            delete model;
        }
    }
    
    PYHELIOS_API void enableStomatalConductanceMessages(StomatalConductanceModel* model) {
        try {
            clearError();
            if (!model) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "StomatalConductanceModel pointer is null");
                return;
            }
            
            model->enableMessages();
            
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (StomatalConductanceModel::enableMessages): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (StomatalConductanceModel::enableMessages): Unknown error enabling messages.");
        }
    }
    
    PYHELIOS_API void disableStomatalConductanceMessages(StomatalConductanceModel* model) {
        try {
            clearError();
            if (!model) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "StomatalConductanceModel pointer is null");
                return;
            }
            
            model->disableMessages();
            
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (StomatalConductanceModel::disableMessages): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (StomatalConductanceModel::disableMessages): Unknown error disabling messages.");
        }
    }
    
    PYHELIOS_API void runStomatalConductanceModel(StomatalConductanceModel* model) {
        try {
            clearError();
            if (!model) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "StomatalConductanceModel pointer is null");
                return;
            }
            
            model->run();
            
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (StomatalConductanceModel::run): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (StomatalConductanceModel::run): Unknown error running stomatal conductance model.");
        }
    }
    
    PYHELIOS_API void runStomatalConductanceModelDynamic(StomatalConductanceModel* model, float dt) {
        try {
            clearError();
            if (!model) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "StomatalConductanceModel pointer is null");
                return;
            }
            if (dt <= 0.0f) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Time step must be positive");
                return;
            }
            
            model->run(dt);
            
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (StomatalConductanceModel::run): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (StomatalConductanceModel::run): Unknown error running dynamic stomatal conductance model.");
        }
    }
    
    PYHELIOS_API void runStomatalConductanceModelForUUIDs(StomatalConductanceModel* model, const unsigned int* uuids, unsigned int uuid_count) {
        try {
            clearError();
            if (!model) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "StomatalConductanceModel pointer is null");
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
            model->run(uuid_vector);
            
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (StomatalConductanceModel::run): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (StomatalConductanceModel::run): Unknown error running stomatal conductance model for UUIDs.");
        }
    }
    
    PYHELIOS_API void runStomatalConductanceModelForUUIDsDynamic(StomatalConductanceModel* model, const unsigned int* uuids, unsigned int uuid_count, float dt) {
        try {
            clearError();
            if (!model) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "StomatalConductanceModel pointer is null");
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
            if (dt <= 0.0f) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Time step must be positive");
                return;
            }
            
            std::vector<uint> uuid_vector(uuids, uuids + uuid_count);
            model->run(uuid_vector, dt);
            
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (StomatalConductanceModel::run): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (StomatalConductanceModel::run): Unknown error running dynamic stomatal conductance model for UUIDs.");
        }
    }

    // BWB Model Coefficient Functions
    PYHELIOS_API void setStomatalConductanceBWBCoefficients(StomatalConductanceModel* model, float gs0, float a1) {
        try {
            clearError();
            if (!model) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "StomatalConductanceModel pointer is null");
                return;
            }
            
            BWBcoefficients coeffs;
            coeffs.gs0 = gs0;
            coeffs.a1 = a1;
            model->setModelCoefficients(coeffs);
            
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (StomatalConductanceModel::setModelCoefficients): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (StomatalConductanceModel::setModelCoefficients): Unknown error setting BWB coefficients.");
        }
    }
    
    PYHELIOS_API void setStomatalConductanceBWBCoefficientsForUUIDs(StomatalConductanceModel* model, float gs0, float a1, const unsigned int* uuids, unsigned int uuid_count) {
        try {
            clearError();
            if (!model) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "StomatalConductanceModel pointer is null");
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
            
            BWBcoefficients coeffs;
            coeffs.gs0 = gs0;
            coeffs.a1 = a1;
            std::vector<uint> uuid_vector(uuids, uuids + uuid_count);
            model->setModelCoefficients(coeffs, uuid_vector);
            
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (StomatalConductanceModel::setModelCoefficients): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (StomatalConductanceModel::setModelCoefficients): Unknown error setting BWB coefficients for UUIDs.");
        }
    }

    // BBL Model Coefficient Functions  
    PYHELIOS_API void setStomatalConductanceBBLCoefficients(StomatalConductanceModel* model, float gs0, float a1, float D0) {
        try {
            clearError();
            if (!model) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "StomatalConductanceModel pointer is null");
                return;
            }
            
            BBLcoefficients coeffs;
            coeffs.gs0 = gs0;
            coeffs.a1 = a1;
            coeffs.D0 = D0;
            model->setModelCoefficients(coeffs);
            
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (StomatalConductanceModel::setModelCoefficients): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (StomatalConductanceModel::setModelCoefficients): Unknown error setting BBL coefficients.");
        }
    }
    
    PYHELIOS_API void setStomatalConductanceBBLCoefficientsForUUIDs(StomatalConductanceModel* model, float gs0, float a1, float D0, const unsigned int* uuids, unsigned int uuid_count) {
        try {
            clearError();
            if (!model) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "StomatalConductanceModel pointer is null");
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
            
            BBLcoefficients coeffs;
            coeffs.gs0 = gs0;
            coeffs.a1 = a1;
            coeffs.D0 = D0;
            std::vector<uint> uuid_vector(uuids, uuids + uuid_count);
            model->setModelCoefficients(coeffs, uuid_vector);
            
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (StomatalConductanceModel::setModelCoefficients): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (StomatalConductanceModel::setModelCoefficients): Unknown error setting BBL coefficients for UUIDs.");
        }
    }

    // MOPT Model Coefficient Functions
    PYHELIOS_API void setStomatalConductanceMOPTCoefficients(StomatalConductanceModel* model, float gs0, float g1) {
        try {
            clearError();
            if (!model) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "StomatalConductanceModel pointer is null");
                return;
            }
            
            MOPTcoefficients coeffs;
            coeffs.gs0 = gs0;
            coeffs.g1 = g1;
            model->setModelCoefficients(coeffs);
            
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (StomatalConductanceModel::setModelCoefficients): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (StomatalConductanceModel::setModelCoefficients): Unknown error setting MOPT coefficients.");
        }
    }
    
    PYHELIOS_API void setStomatalConductanceMOPTCoefficientsForUUIDs(StomatalConductanceModel* model, float gs0, float g1, const unsigned int* uuids, unsigned int uuid_count) {
        try {
            clearError();
            if (!model) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "StomatalConductanceModel pointer is null");
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
            
            MOPTcoefficients coeffs;
            coeffs.gs0 = gs0;
            coeffs.g1 = g1;
            std::vector<uint> uuid_vector(uuids, uuids + uuid_count);
            model->setModelCoefficients(coeffs, uuid_vector);
            
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (StomatalConductanceModel::setModelCoefficients): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (StomatalConductanceModel::setModelCoefficients): Unknown error setting MOPT coefficients for UUIDs.");
        }
    }

    // BMF Model Coefficient Functions
    PYHELIOS_API void setStomatalConductanceBMFCoefficients(StomatalConductanceModel* model, float Em, float i0, float k, float b) {
        try {
            clearError();
            if (!model) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "StomatalConductanceModel pointer is null");
                return;
            }
            
            BMFcoefficients coeffs;
            coeffs.Em = Em;
            coeffs.i0 = i0;
            coeffs.k = k;
            coeffs.b = b;
            model->setModelCoefficients(coeffs);
            
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (StomatalConductanceModel::setModelCoefficients): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (StomatalConductanceModel::setModelCoefficients): Unknown error setting BMF coefficients.");
        }
    }
    
    PYHELIOS_API void setStomatalConductanceBMFCoefficientsForUUIDs(StomatalConductanceModel* model, float Em, float i0, float k, float b, const unsigned int* uuids, unsigned int uuid_count) {
        try {
            clearError();
            if (!model) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "StomatalConductanceModel pointer is null");
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
            
            BMFcoefficients coeffs;
            coeffs.Em = Em;
            coeffs.i0 = i0;
            coeffs.k = k;
            coeffs.b = b;
            std::vector<uint> uuid_vector(uuids, uuids + uuid_count);
            model->setModelCoefficients(coeffs, uuid_vector);
            
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (StomatalConductanceModel::setModelCoefficients): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (StomatalConductanceModel::setModelCoefficients): Unknown error setting BMF coefficients for UUIDs.");
        }
    }

    // BB Model Coefficient Functions
    PYHELIOS_API void setStomatalConductanceBBCoefficients(StomatalConductanceModel* model, float pi_0, float pi_m, float theta, float sigma, float chi) {
        try {
            clearError();
            if (!model) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "StomatalConductanceModel pointer is null");
                return;
            }
            
            BBcoefficients coeffs;
            coeffs.pi_0 = pi_0;
            coeffs.pi_m = pi_m;
            coeffs.theta = theta;
            coeffs.sigma = sigma;
            coeffs.chi = chi;
            model->setModelCoefficients(coeffs);
            
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (StomatalConductanceModel::setModelCoefficients): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (StomatalConductanceModel::setModelCoefficients): Unknown error setting BB coefficients.");
        }
    }
    
    PYHELIOS_API void setStomatalConductanceBBCoefficientsForUUIDs(StomatalConductanceModel* model, float pi_0, float pi_m, float theta, float sigma, float chi, const unsigned int* uuids, unsigned int uuid_count) {
        try {
            clearError();
            if (!model) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "StomatalConductanceModel pointer is null");
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
            
            BBcoefficients coeffs;
            coeffs.pi_0 = pi_0;
            coeffs.pi_m = pi_m;
            coeffs.theta = theta;
            coeffs.sigma = sigma;
            coeffs.chi = chi;
            std::vector<uint> uuid_vector(uuids, uuids + uuid_count);
            model->setModelCoefficients(coeffs, uuid_vector);
            
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (StomatalConductanceModel::setModelCoefficients): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (StomatalConductanceModel::setModelCoefficients): Unknown error setting BB coefficients for UUIDs.");
        }
    }

    // Species Library Functions
    PYHELIOS_API void setStomatalConductanceBMFCoefficientsFromLibrary(StomatalConductanceModel* model, const char* species) {
        try {
            clearError();
            if (!model) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "StomatalConductanceModel pointer is null");
                return;
            }
            if (!species) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Species name is null");
                return;
            }
            
            model->setBMFCoefficientsFromLibrary(std::string(species));
            
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (StomatalConductanceModel::setBMFCoefficientsFromLibrary): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (StomatalConductanceModel::setBMFCoefficientsFromLibrary): Unknown error setting BMF coefficients from library.");
        }
    }
    
    PYHELIOS_API void setStomatalConductanceBMFCoefficientsFromLibraryForUUIDs(StomatalConductanceModel* model, const char* species, const unsigned int* uuids, unsigned int uuid_count) {
        try {
            clearError();
            if (!model) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "StomatalConductanceModel pointer is null");
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
            model->setBMFCoefficientsFromLibrary(std::string(species), uuid_vector);
            
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (StomatalConductanceModel::setBMFCoefficientsFromLibrary): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (StomatalConductanceModel::setBMFCoefficientsFromLibrary): Unknown error setting BMF coefficients from library for UUIDs.");
        }
    }

    // Material-label coefficient assignment
    PYHELIOS_API void setStomatalConductanceBWBCoefficientsForMaterial(StomatalConductanceModel* model, const char* material_label, float gs0, float a1) {
        try {
            clearError();
            if (!model) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "StomatalConductanceModel pointer is null");
                return;
            }
            if (!material_label || material_label[0] == '\0') {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Material label is null or empty");
                return;
            }

            BWBcoefficients coeffs;
            coeffs.gs0 = gs0;
            coeffs.a1 = a1;
            model->setModelCoefficients(std::string(material_label), coeffs);

        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (StomatalConductanceModel::setModelCoefficients): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (StomatalConductanceModel::setModelCoefficients): Unknown error setting BWB coefficients for material.");
        }
    }

    PYHELIOS_API void setStomatalConductanceBBLCoefficientsForMaterial(StomatalConductanceModel* model, const char* material_label, float gs0, float a1, float D0) {
        try {
            clearError();
            if (!model) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "StomatalConductanceModel pointer is null");
                return;
            }
            if (!material_label || material_label[0] == '\0') {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Material label is null or empty");
                return;
            }

            BBLcoefficients coeffs;
            coeffs.gs0 = gs0;
            coeffs.a1 = a1;
            coeffs.D0 = D0;
            model->setModelCoefficients(std::string(material_label), coeffs);

        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (StomatalConductanceModel::setModelCoefficients): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (StomatalConductanceModel::setModelCoefficients): Unknown error setting BBL coefficients for material.");
        }
    }

    PYHELIOS_API void setStomatalConductanceMOPTCoefficientsForMaterial(StomatalConductanceModel* model, const char* material_label, float gs0, float g1) {
        try {
            clearError();
            if (!model) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "StomatalConductanceModel pointer is null");
                return;
            }
            if (!material_label || material_label[0] == '\0') {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Material label is null or empty");
                return;
            }

            MOPTcoefficients coeffs;
            coeffs.gs0 = gs0;
            coeffs.g1 = g1;
            model->setModelCoefficients(std::string(material_label), coeffs);

        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (StomatalConductanceModel::setModelCoefficients): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (StomatalConductanceModel::setModelCoefficients): Unknown error setting MOPT coefficients for material.");
        }
    }

    PYHELIOS_API void setStomatalConductanceBMFCoefficientsForMaterial(StomatalConductanceModel* model, const char* material_label, float Em, float i0, float k, float b) {
        try {
            clearError();
            if (!model) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "StomatalConductanceModel pointer is null");
                return;
            }
            if (!material_label || material_label[0] == '\0') {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Material label is null or empty");
                return;
            }

            BMFcoefficients coeffs;
            coeffs.Em = Em;
            coeffs.i0 = i0;
            coeffs.k = k;
            coeffs.b = b;
            model->setModelCoefficients(std::string(material_label), coeffs);

        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (StomatalConductanceModel::setModelCoefficients): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (StomatalConductanceModel::setModelCoefficients): Unknown error setting BMF coefficients for material.");
        }
    }

    PYHELIOS_API void setStomatalConductanceBBCoefficientsForMaterial(StomatalConductanceModel* model, const char* material_label, float pi_0, float pi_m, float theta, float sigma, float chi) {
        try {
            clearError();
            if (!model) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "StomatalConductanceModel pointer is null");
                return;
            }
            if (!material_label || material_label[0] == '\0') {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Material label is null or empty");
                return;
            }

            BBcoefficients coeffs;
            coeffs.pi_0 = pi_0;
            coeffs.pi_m = pi_m;
            coeffs.theta = theta;
            coeffs.sigma = sigma;
            coeffs.chi = chi;
            model->setModelCoefficients(std::string(material_label), coeffs);

        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (StomatalConductanceModel::setModelCoefficients): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (StomatalConductanceModel::setModelCoefficients): Unknown error setting BB coefficients for material.");
        }
    }

    PYHELIOS_API void setStomatalConductanceBMFCoefficientsFromLibraryForMaterial(StomatalConductanceModel* model, const char* species, const char* material_label) {
        try {
            clearError();
            if (!model) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "StomatalConductanceModel pointer is null");
                return;
            }
            if (!species) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Species name is null");
                return;
            }
            if (!material_label || material_label[0] == '\0') {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Material label is null or empty");
                return;
            }

            model->setBMFCoefficientsFromLibrary(std::string(species), std::string(material_label));

        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (StomatalConductanceModel::setBMFCoefficientsFromLibrary): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (StomatalConductanceModel::setBMFCoefficientsFromLibrary): Unknown error setting BMF coefficients from library for material.");
        }
    }

    PYHELIOS_API void setStomatalConductanceBMFCoefficientsPerUUID(StomatalConductanceModel* model, const float* coeffs, const unsigned int* uuids, unsigned int uuid_count) {
        try {
            clearError();
            if (!model) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "StomatalConductanceModel pointer is null");
                return;
            }
            if (!coeffs) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Coefficient array is null");
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

            std::vector<BMFcoefficients> coeff_vector(uuid_count);
            for (unsigned int i = 0; i < uuid_count; i++) {
                coeff_vector[i].Em = coeffs[4 * i + 0];
                coeff_vector[i].i0 = coeffs[4 * i + 1];
                coeff_vector[i].k = coeffs[4 * i + 2];
                coeff_vector[i].b = coeffs[4 * i + 3];
            }
            std::vector<uint> uuid_vector(uuids, uuids + uuid_count);
            model->setModelCoefficients(coeff_vector, uuid_vector);

        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (StomatalConductanceModel::setModelCoefficients): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (StomatalConductanceModel::setModelCoefficients): Unknown error setting per-UUID BMF coefficients.");
        }
    }

    PYHELIOS_API void getStomatalConductanceBMFCoefficientsFromLibrary(StomatalConductanceModel* model, const char* species, float* coeffs_out) {
        try {
            clearError();
            if (!model) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "StomatalConductanceModel pointer is null");
                return;
            }
            if (!species) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Species name is null");
                return;
            }
            if (!coeffs_out) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Output coefficient array is null");
                return;
            }

            BMFcoefficients coeffs = model->getBMFCoefficientsFromLibrary(std::string(species));
            coeffs_out[0] = coeffs.Em;
            coeffs_out[1] = coeffs.i0;
            coeffs_out[2] = coeffs.k;
            coeffs_out[3] = coeffs.b;

        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (StomatalConductanceModel::getBMFCoefficientsFromLibrary): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (StomatalConductanceModel::getBMFCoefficientsFromLibrary): Unknown error getting BMF coefficients from library.");
        }
    }

    // Dynamic Time Constants
    PYHELIOS_API void setStomatalConductanceDynamicTimeConstants(StomatalConductanceModel* model, float tau_open, float tau_close) {
        try {
            clearError();
            if (!model) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "StomatalConductanceModel pointer is null");
                return;
            }
            if (tau_open <= 0.0f) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Opening time constant must be positive");
                return;
            }
            if (tau_close <= 0.0f) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Closing time constant must be positive");
                return;
            }
            
            model->setDynamicTimeConstants(tau_open, tau_close);
            
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (StomatalConductanceModel::setDynamicTimeConstants): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (StomatalConductanceModel::setDynamicTimeConstants): Unknown error setting dynamic time constants.");
        }
    }
    
    PYHELIOS_API void setStomatalConductanceDynamicTimeConstantsForUUIDs(StomatalConductanceModel* model, float tau_open, float tau_close, const unsigned int* uuids, unsigned int uuid_count) {
        try {
            clearError();
            if (!model) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "StomatalConductanceModel pointer is null");
                return;
            }
            if (tau_open <= 0.0f) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Opening time constant must be positive");
                return;
            }
            if (tau_close <= 0.0f) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Closing time constant must be positive");
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
            model->setDynamicTimeConstants(tau_open, tau_close, uuid_vector);
            
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (StomatalConductanceModel::setDynamicTimeConstants): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (StomatalConductanceModel::setDynamicTimeConstants): Unknown error setting dynamic time constants for UUIDs.");
        }
    }
    
    // Utility Functions
    PYHELIOS_API void addStomatalConductanceOptionalOutput(StomatalConductanceModel* model, const char* label) {
        try {
            clearError();
            if (!model) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "StomatalConductanceModel pointer is null");
                return;
            }
            if (!label) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Label is null");
                return;
            }
            
            model->optionalOutputPrimitiveData(label);
            
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (StomatalConductanceModel::optionalOutputPrimitiveData): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (StomatalConductanceModel::optionalOutputPrimitiveData): Unknown error adding optional output data.");
        }
    }
    
    PYHELIOS_API void printStomatalConductanceDefaultValueReport(StomatalConductanceModel* model) {
        try {
            clearError();
            if (!model) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "StomatalConductanceModel pointer is null");
                return;
            }
            
            model->printDefaultValueReport();
            
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (StomatalConductanceModel::printDefaultValueReport): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (StomatalConductanceModel::printDefaultValueReport): Unknown error printing default value report.");
        }
    }
    
    PYHELIOS_API void printStomatalConductanceDefaultValueReportForUUIDs(StomatalConductanceModel* model, const unsigned int* uuids, unsigned int uuid_count) {
        try {
            clearError();
            if (!model) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "StomatalConductanceModel pointer is null");
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
            model->printDefaultValueReport(uuid_vector);
            
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (StomatalConductanceModel::printDefaultValueReport): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (StomatalConductanceModel::printDefaultValueReport): Unknown error printing default value report for UUIDs.");
        }
    }
    
} //extern "C"

#endif //STOMATALCONDUCTANCE_PLUGIN_AVAILABLE