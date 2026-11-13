// PyHelios C Interface - PlantArchitecture Functions
// Provides procedural plant modeling using plant architecture library

#include "../include/pyhelios_wrapper_common.h"
#include "../include/pyhelios_wrapper_context.h"
#include "Context.h"
#include <string>
#include <vector>
#include <map>
#include <exception>
#include <cstring>
#include <cmath>
#include <stdexcept>
#include <array>
#include <utility>

#ifdef PLANTARCHITECTURE_PLUGIN_AVAILABLE
#include "../include/pyhelios_wrapper_plantarchitecture.h"
#include "PlantArchitecture.h"
#include "CollisionGeometry.h"
#include "../../helios-core/core/lib/json/json.hpp"

// Helper functions for JSON serialization (outside extern "C" - internal C++ helpers)
namespace {

nlohmann::json randomParameterFloatToJSON(RandomParameter_float param) {
    nlohmann::json j;
    j["distribution"] = param.distribution;

    if (param.distribution == "constant") {
        // For constant, get the value using val()
        j["parameters"] = std::vector<float>{param.val()};
    } else {
        j["parameters"] = param.distribution_parameters;
    }
    return j;
}

nlohmann::json randomParameterIntToJSON(RandomParameter_int param) {
    nlohmann::json j;
    j["distribution"] = param.distribution;

    if (param.distribution == "constant") {
        // For constant, get the value using val()
        j["parameters"] = std::vector<float>{static_cast<float>(param.val())};
    } else {
        // Convert int distribution_parameters to float for JSON
        std::vector<float> float_params;
        for (int p : param.distribution_parameters) {
            float_params.push_back(static_cast<float>(p));
        }
        j["parameters"] = float_params;
    }
    return j;
}

RandomParameter_float jsonToRandomParameterFloat(const nlohmann::json& j, std::minstd_rand0* generator) {
    RandomParameter_float param;
    param.initialize(generator);
    std::string dist = j["distribution"];

    if (dist == "constant") {
        std::vector<float> params = j["parameters"];
        if (!params.empty()) {
            param = params[0];
        }
    } else if (dist == "uniform") {
        std::vector<float> params = j["parameters"];
        if (params.size() >= 2) {
            param.uniformDistribution(params[0], params[1]);
        }
    } else if (dist == "normal") {
        std::vector<float> params = j["parameters"];
        if (params.size() >= 2) {
            param.normalDistribution(params[0], params[1]);
        }
    } else if (dist == "weibull") {
        std::vector<float> params = j["parameters"];
        if (params.size() >= 2) {
            param.weibullDistribution(params[0], params[1]);
        }
    }

    return param;
}

RandomParameter_int jsonToRandomParameterInt(const nlohmann::json& j, std::minstd_rand0* generator) {
    RandomParameter_int param;
    param.initialize(generator);
    std::string dist = j["distribution"];

    if (dist == "constant") {
        std::vector<float> params = j["parameters"];
        if (!params.empty()) {
            param = static_cast<int>(params[0]);
        }
    } else if (dist == "uniform") {
        std::vector<float> params = j["parameters"];
        if (params.size() >= 2) {
            param.uniformDistribution(static_cast<int>(params[0]), static_cast<int>(params[1]));
        }
    } else if (dist == "discretevalues") {
        std::vector<float> params = j["parameters"];
        std::vector<int> int_params;
        for (float p : params) {
            int_params.push_back(static_cast<int>(p));
        }
        param.discreteValues(int_params);
    }

    return param;
}

// ---- helios::RGBcolor / helios::vec3 JSON helpers ----
nlohmann::json rgbToJSON(const helios::RGBcolor& c) {
    return nlohmann::json{{"r", c.r}, {"g", c.g}, {"b", c.b}};
}
helios::RGBcolor jsonToRGB(const nlohmann::json& j, helios::RGBcolor fallback) {
    if (j.contains("r")) fallback.r = j["r"];
    if (j.contains("g")) fallback.g = j["g"];
    if (j.contains("b")) fallback.b = j["b"];
    return fallback;
}
nlohmann::json vec3ToJSON(const helios::vec3& v) {
    return nlohmann::json{{"x", v.x}, {"y", v.y}, {"z", v.z}};
}
helios::vec3 jsonToVec3(const nlohmann::json& j, helios::vec3 fallback) {
    if (j.contains("x")) fallback.x = j["x"];
    if (j.contains("y")) fallback.y = j["y"];
    if (j.contains("z")) fallback.z = j["z"];
    return fallback;
}

// ---- Prototype-function registries (name <-> built-in function pointer) ----
// Function pointers cannot cross the ctypes boundary, so the built-in prototype
// functions declared in Assets.h are referenced by name. The phytomer creation function
// and the per-timestep phytomer_callback_function are bound separately through trampolines
// (see phytomerCreationTrampoline and phytomerCallbackTrampoline below).
typedef uint (*LeafPrototypeFn)(helios::Context*, LeafPrototype*, int);
typedef FlowerPrototypeFunction FlowerPrototypeFn;
typedef FruitPrototypeFunction FruitPrototypeFn;

const std::map<std::string, LeafPrototypeFn>& leafPrototypeRegistry() {
    static const std::map<std::string, LeafPrototypeFn> reg = {
        {"GenericLeafPrototype", &GenericLeafPrototype},
        {"AsparagusLeafPrototype", &AsparagusLeafPrototype},
        {"BeanLeafPrototype_unifoliate_OBJ", &BeanLeafPrototype_unifoliate_OBJ},
        {"BeanLeafPrototype_trifoliate_OBJ", &BeanLeafPrototype_trifoliate_OBJ},
        {"CheeseweedLeafPrototype", &CheeseweedLeafPrototype},
        {"CowpeaLeafPrototype_unifoliate_OBJ", &CowpeaLeafPrototype_unifoliate_OBJ},
        {"CowpeaLeafPrototype_trifoliate_OBJ", &CowpeaLeafPrototype_trifoliate_OBJ},
        {"OliveLeafPrototype", &OliveLeafPrototype},
    };
    return reg;
}

const std::map<std::string, FlowerPrototypeFn>& flowerPrototypeRegistry() {
    static const std::map<std::string, FlowerPrototypeFn> reg = {
        {"AlmondFlowerPrototype", &AlmondFlowerPrototype},
        {"AppleFlowerPrototype", &AppleFlowerPrototype},
        {"BeanFlowerPrototype", &BeanFlowerPrototype},
        {"BindweedFlowerPrototype", &BindweedFlowerPrototype},
        {"BougainvilleaFlowerPrototype", &BougainvilleaFlowerPrototype},
        {"CowpeaFlowerPrototype", &CowpeaFlowerPrototype},
        {"CucumberFlowerPrototype", &CucumberFlowerPrototype},
        {"OliveFlowerPrototype", &OliveFlowerPrototype},
        {"PistachioFlowerPrototype", &PistachioFlowerPrototype},
        {"PuncturevineFlowerPrototype", &PuncturevineFlowerPrototype},
        {"RedbudFlowerPrototype", &RedbudFlowerPrototype},
        {"RiceFloweringPaniclePrototype", &RiceFloweringPaniclePrototype},
        {"SoybeanFlowerPrototype", &SoybeanFlowerPrototype},
        {"StrawberryFlowerPrototype", &StrawberryFlowerPrototype},
        {"TomatoFlowerPrototype", &TomatoFlowerPrototype},
        {"WalnutFlowerPrototype", &WalnutFlowerPrototype},
    };
    return reg;
}

const std::map<std::string, FruitPrototypeFn>& fruitPrototypeRegistry() {
    static const std::map<std::string, FruitPrototypeFn> reg = {
        {"GeneralSphericalFruitPrototype", &GeneralSphericalFruitPrototype},
        {"AlmondFruitPrototype", &AlmondFruitPrototype},
        {"AppleFruitPrototype", &AppleFruitPrototype},
        {"BeanFruitPrototype", &BeanFruitPrototype},
        {"CapsicumFruitPrototype", &CapsicumFruitPrototype},
        {"CowpeaFruitPrototype", &CowpeaFruitPrototype},
        {"CucumberFruitPrototype", &CucumberFruitPrototype},
        {"GrapevineFruitPrototype", &GrapevineFruitPrototype},
        {"MaizeTasselPrototype", &MaizeTasselPrototype},
        {"MaizeEarPrototype", &MaizeEarPrototype},
        {"OliveFruitPrototype", &OliveFruitPrototype},
        {"PistachioFruitPrototype", &PistachioFruitPrototype},
        {"RedbudFruitPrototype", &RedbudFruitPrototype},
        {"RicePaniclePrototype", &RicePaniclePrototype},
        {"SorghumPaniclePrototype", &SorghumPaniclePrototype},
        {"SoybeanFruitPrototype", &SoybeanFruitPrototype},
        {"StrawberryFruitPrototype", &StrawberryFruitPrototype},
        {"TomatoFruitPrototype", &TomatoFruitPrototype},
        {"WalnutFruitPrototype", &WalnutFruitPrototype},
        {"WheatSpikePrototype", &WheatSpikePrototype},
    };
    return reg;
}

template<typename FnMap, typename Fn>
std::string prototypeFunctionName(const FnMap& reg, Fn fn) {
    if (fn == nullptr) return "";
    for (const auto& kv : reg) {
        if (kv.second == fn) return kv.first;
    }
    return "";  // unrecognized (e.g. user-supplied) function pointer
}

template<typename FnMap, typename Fn>
void resolvePrototypeFunction(const FnMap& reg, const nlohmann::json& j, const char* key, Fn& out, const char* kind) {
    if (!j.contains(key)) return;
    std::string name = j[key].get<std::string>();
    if (name.empty()) {
        out = nullptr;
        return;
    }
    auto it = reg.find(name);
    if (it == reg.end()) {
        throw std::runtime_error(std::string("Unknown ") + kind + " prototype function name: '" + name + "'");
    }
    out = it->second;
}

// ---- Python fruit and flower prototype functions ----
// A fruit or flower prototype function is a plain function pointer called with nothing but the Context, so a Python
// function cannot be recovered from the call the way the phytomer trampolines recover theirs from the phytomer. There
// is instead a fixed set of slots, each a static function with an address of its own. Installing a Python function on
// a shoot type binds it to a free slot and gives the type that slot's address. The plugin caches prototypes by that
// address, so each Python function has a cache entry of its own, and a slot is never rebound while its
// PlantArchitecture lives: replacing a shoot type's Python function binds a new slot, so shoots created earlier and
// prototypes already cached keep the function they were made with. Destroying the PlantArchitecture frees its slots.
constexpr size_t kPythonPrototypeSlotCount = 32;
const char* const kPythonFruitPrototypePrefix = "PythonFruitPrototype_";
const char* const kPythonFlowerPrototypePrefix = "PythonFlowerPrototype_";

template<typename Callback>
struct PythonPrototypeSlot {
    const PlantArchitecture* owner = nullptr;
    const helios::Context* context = nullptr;
    std::string shoot_type_label;
    Callback callback = nullptr;
};
using FruitPrototypeSlot = PythonPrototypeSlot<PyheliosFruitPrototypeCallback>;
using FlowerPrototypeSlot = PythonPrototypeSlot<PyheliosFlowerPrototypeCallback>;

std::array<FruitPrototypeSlot, kPythonPrototypeSlotCount>& fruitPrototypeSlots() {
    static std::array<FruitPrototypeSlot, kPythonPrototypeSlotCount> slots;
    return slots;
}

std::array<FlowerPrototypeSlot, kPythonPrototypeSlotCount>& flowerPrototypeSlots() {
    static std::array<FlowerPrototypeSlot, kPythonPrototypeSlotCount> slots;
    return slots;
}

//! The function a shoot type had before a Python prototype function was first installed on it, restored by clearing.
std::map<const PlantArchitecture*, std::map<std::string, FruitPrototypeFn>>& originalFruitPrototypeFunctions() {
    static std::map<const PlantArchitecture*, std::map<std::string, FruitPrototypeFn>> originals;
    return originals;
}

std::map<const PlantArchitecture*, std::map<std::string, FlowerPrototypeFn>>& originalFlowerPrototypeFunctions() {
    static std::map<const PlantArchitecture*, std::map<std::string, FlowerPrototypeFn>> originals;
    return originals;
}

void marshalBuildParameters(const std::map<std::string, float>& build_parameters, std::vector<const char*>& names, std::vector<float>& values) {
    names.clear();
    values.clear();
    names.reserve(build_parameters.size());
    values.reserve(build_parameters.size());
    for (const auto& [name, value] : build_parameters) {
        names.push_back(name.c_str());
        values.push_back(value);
    }
}

template<typename Slot>
void checkPythonPrototypeSlot(const Slot& slot, size_t index, const helios::Context* context_ptr, const std::string& kind, const std::string& setter) {
    if (slot.callback == nullptr) {
        throw std::runtime_error("Python " + kind + " prototype slot " + std::to_string(index) +
                                 " was called but is bound to no function; the PlantArchitecture it was installed on has been destroyed.");
    }
    if (slot.context != context_ptr) {
        throw std::runtime_error("The Python " + kind + " prototype function of shoot type '" + slot.shoot_type_label +
                                 "' was asked to build geometry in a different Context from the one it was installed with. Its shoot parameters were carried to a PlantArchitecture on "
                                 "another Context; install the function there with " + setter + " instead.");
    }
}

uint finishPythonPrototype(helios::Context* context_ptr, int status, uint objID, const std::string& kind, const std::string& shoot_type_label) {
    if (status != 0) {
        throw std::runtime_error("The Python " + kind + " prototype function of shoot type '" + shoot_type_label + "' raised an exception.");
    }
    if (!context_ptr->doesObjectExist(objID)) {
        throw std::runtime_error("The Python " + kind + " prototype function of shoot type '" + shoot_type_label + "' returned object ID " + std::to_string(objID) +
                                 ", which does not exist in the Context.");
    }
    return objID;
}

uint callFruitPrototypeSlot(size_t index, helios::Context* context_ptr, uint subdivisions, const std::map<std::string, float>& build_parameters) {
    const FruitPrototypeSlot slot = fruitPrototypeSlots().at(index);  // a copy: the callback may bind other slots
    checkPythonPrototypeSlot(slot, index, context_ptr, "fruit", "setFruitPrototypeFunction");
    std::vector<const char*> names;
    std::vector<float> values;
    marshalBuildParameters(build_parameters, names, values);
    uint objID = 0;
    const int status = slot.callback(subdivisions, names.data(), values.data(), static_cast<unsigned int>(names.size()), &objID);
    return finishPythonPrototype(context_ptr, status, objID, "fruit", slot.shoot_type_label);
}

uint callFlowerPrototypeSlot(size_t index, helios::Context* context_ptr, uint subdivisions, bool flower_is_open, const std::map<std::string, float>& build_parameters) {
    const FlowerPrototypeSlot slot = flowerPrototypeSlots().at(index);  // a copy: the callback may bind other slots
    checkPythonPrototypeSlot(slot, index, context_ptr, "flower", "setFlowerPrototypeFunction");
    std::vector<const char*> names;
    std::vector<float> values;
    marshalBuildParameters(build_parameters, names, values);
    uint objID = 0;
    const int status = slot.callback(subdivisions, flower_is_open ? 1 : 0, names.data(), values.data(), static_cast<unsigned int>(names.size()), &objID);
    return finishPythonPrototype(context_ptr, status, objID, "flower", slot.shoot_type_label);
}

template<size_t N>
uint fruitPrototypeSlotFunction(helios::Context* context_ptr, uint subdivisions, const std::map<std::string, float>& build_parameters) {
    return callFruitPrototypeSlot(N, context_ptr, subdivisions, build_parameters);
}

template<size_t N>
uint flowerPrototypeSlotFunction(helios::Context* context_ptr, uint subdivisions, bool flower_is_open, const std::map<std::string, float>& build_parameters) {
    return callFlowerPrototypeSlot(N, context_ptr, subdivisions, flower_is_open, build_parameters);
}

template<size_t... I>
std::array<FruitPrototypeFn, sizeof...(I)> makeFruitSlotFunctions(std::index_sequence<I...>) {
    return {{&fruitPrototypeSlotFunction<I>...}};
}

template<size_t... I>
std::array<FlowerPrototypeFn, sizeof...(I)> makeFlowerSlotFunctions(std::index_sequence<I...>) {
    return {{&flowerPrototypeSlotFunction<I>...}};
}

const std::array<FruitPrototypeFn, kPythonPrototypeSlotCount>& fruitSlotFunctions() {
    static const auto functions = makeFruitSlotFunctions(std::make_index_sequence<kPythonPrototypeSlotCount>{});
    return functions;
}

const std::array<FlowerPrototypeFn, kPythonPrototypeSlotCount>& flowerSlotFunctions() {
    static const auto functions = makeFlowerSlotFunctions(std::make_index_sequence<kPythonPrototypeSlotCount>{});
    return functions;
}

template<typename Fn>
int slotIndexOf(const std::array<Fn, kPythonPrototypeSlotCount>& functions, Fn fn) {
    for (size_t i = 0; i < functions.size(); i++) {
        if (functions[i] == fn) return static_cast<int>(i);
    }
    return -1;
}

//! A prototype function's name: a library function's own name, or "<prefix><slot>" for a Python function.
template<typename FnMap, typename Fn>
std::string prototypeFunctionName(const FnMap& reg, const std::array<Fn, kPythonPrototypeSlotCount>& slot_functions, const char* slot_prefix, Fn fn) {
    std::string name = prototypeFunctionName(reg, fn);
    if (!name.empty() || fn == nullptr) return name;
    const int slot = slotIndexOf(slot_functions, fn);
    return slot < 0 ? std::string() : std::string(slot_prefix) + std::to_string(slot);
}

//! Resolve a prototype function name, accepting the name of a Python function's slot while that slot is bound.
template<typename FnMap, typename Fn, typename Slots>
void resolvePrototypeFunction(const FnMap& reg, const std::array<Fn, kPythonPrototypeSlotCount>& slot_functions, const Slots& slots, const char* slot_prefix, const nlohmann::json& j,
                              const char* key, Fn& out, const char* kind) {
    if (!j.contains(key)) return;
    const std::string name = j[key].get<std::string>();
    const std::string prefix(slot_prefix);
    if (name.compare(0, prefix.size(), prefix) != 0) {
        resolvePrototypeFunction(reg, j, key, out, kind);
        return;
    }
    const std::string digits = name.substr(prefix.size());
    if (digits.empty() || digits.size() > 3 || digits.find_first_not_of("0123456789") != std::string::npos || std::stoul(digits) >= kPythonPrototypeSlotCount) {
        throw std::runtime_error(std::string("Unknown ") + kind + " prototype function name: '" + name + "'");
    }
    const size_t slot = std::stoul(digits);
    if (slots[slot].callback == nullptr) {
        throw std::runtime_error(std::string("The ") + kind + " prototype function '" + name +
                                 "' names a Python function that is no longer installed; the PlantArchitecture it was installed on has been destroyed.");
    }
    out = slot_functions[slot];
}

//! Bind callback to a free slot and give the shoot type that slot's function, or with no callback restore the function the type had before.
template<typename Callback, typename Fn, typename Access>
void installPythonPrototypeFunction(PlantArchitecture* plantarch, helios::Context* context, const char* shoot_type_label, Callback callback,
                                    std::array<PythonPrototypeSlot<Callback>, kPythonPrototypeSlotCount>& slots, const std::array<Fn, kPythonPrototypeSlotCount>& slot_functions,
                                    std::map<const PlantArchitecture*, std::map<std::string, Fn>>& originals, const std::string& kind, Access access) {
    if (!shoot_type_label) {
        throw std::invalid_argument("Shoot type label is null");
    }
    if (callback != nullptr && context == nullptr) {
        throw std::invalid_argument("Context pointer is null");
    }
    const std::string label(shoot_type_label);
    ShootParameters params = plantarch->getCurrentShootParameters(label);
    Fn& function = access(params);
    auto& type_originals = originals[plantarch];
    // Anything but a slot is the type's own function (a library one, or none), which clearing restores.
    if (slotIndexOf(slot_functions, function) < 0) {
        type_originals[label] = function;
    }
    if (callback == nullptr) {
        const auto original = type_originals.find(label);
        function = original == type_originals.end() ? nullptr : original->second;
        plantarch->defineShootType(label, params);
        return;
    }
    size_t free_slot = slots.size();
    for (size_t i = 0; i < slots.size(); i++) {
        if (slots[i].owner == nullptr) {
            free_slot = i;
            break;
        }
    }
    if (free_slot == slots.size()) {
        throw std::runtime_error("All " + std::to_string(kPythonPrototypeSlotCount) + " Python " + kind +
                                 " prototype slots are in use. Each call that installs a function binds a new slot, which is freed only when its PlantArchitecture is destroyed.");
    }
    slots[free_slot] = PythonPrototypeSlot<Callback>{plantarch, context, label, callback};
    function = slot_functions[free_slot];
    try {
        plantarch->defineShootType(label, params);
    } catch (...) {
        slots[free_slot] = PythonPrototypeSlot<Callback>();
        throw;
    }
}

// ---- LeafPrototype <-> JSON ----
nlohmann::json leafPrototypeToJSON(const LeafPrototype& p) {
    nlohmann::json j;
    j["leaf_aspect_ratio"] = randomParameterFloatToJSON(p.leaf_aspect_ratio);
    j["midrib_fold_fraction"] = randomParameterFloatToJSON(p.midrib_fold_fraction);
    j["longitudinal_curvature"] = randomParameterFloatToJSON(p.longitudinal_curvature);
    j["lateral_curvature"] = randomParameterFloatToJSON(p.lateral_curvature);
    j["petiole_roll"] = randomParameterFloatToJSON(p.petiole_roll);
    j["roll_fraction"] = randomParameterFloatToJSON(p.roll_fraction);
    j["wave_period"] = randomParameterFloatToJSON(p.wave_period);
    j["wave_amplitude"] = randomParameterFloatToJSON(p.wave_amplitude);
    j["longitudinal_curvature_exponent"] = randomParameterFloatToJSON(p.longitudinal_curvature_exponent);
    j["flexibility"] = randomParameterFloatToJSON(p.flexibility);
    j["flexibility_taper"] = randomParameterFloatToJSON(p.flexibility_taper);
    j["flexibility_aging"] = randomParameterFloatToJSON(p.flexibility_aging);
    j["flexibility_aging_max"] = randomParameterFloatToJSON(p.flexibility_aging_max);
    HELIOS_PUSH_IGNORE_DEPRECATED
    j["leaf_buckle_length"] = randomParameterFloatToJSON(p.leaf_buckle_length);
    j["leaf_buckle_angle"] = randomParameterFloatToJSON(p.leaf_buckle_angle);
    HELIOS_POP_IGNORE_DEPRECATED
    j["leaf_offset"] = vec3ToJSON(p.leaf_offset);
    j["subdivisions"] = p.subdivisions;
    j["unique_prototypes"] = p.unique_prototypes;
    j["build_petiolule"] = p.build_petiolule;
    nlohmann::json petiolule_length = nlohmann::json::object();
    for (const auto& kv : p.petiolule_length) {
        petiolule_length[std::to_string(kv.first)] = kv.second;
    }
    j["petiolule_length"] = petiolule_length;
    j["OBJ_model_file"] = p.OBJ_model_file;
    nlohmann::json tex = nlohmann::json::object();
    for (const auto& kv : p.leaf_texture_file) {
        tex[std::to_string(kv.first)] = kv.second;
    }
    j["leaf_texture_file"] = tex;
    nlohmann::json class_maps = nlohmann::json::object();
    for (const auto& kv : p.leaf_class_map_file) {
        class_maps[std::to_string(kv.first)] = kv.second;
    }
    j["leaf_class_map_file"] = class_maps;
    nlohmann::json tex_series = nlohmann::json::object();
    for (const auto& kv : p.leaf_texture_series) {
        tex_series[std::to_string(kv.first)] = kv.second;
    }
    j["leaf_texture_series"] = tex_series;
    j["leaf_texture_stage_ages"] = p.leaf_texture_stage_ages;
    j["prototype_function"] = prototypeFunctionName(leafPrototypeRegistry(), p.prototype_function);
    return j;
}

void jsonToLeafPrototype(LeafPrototype& p, const nlohmann::json& j, std::minstd_rand0* generator) {
    if (j.contains("leaf_aspect_ratio")) p.leaf_aspect_ratio = jsonToRandomParameterFloat(j["leaf_aspect_ratio"], generator);
    if (j.contains("midrib_fold_fraction")) p.midrib_fold_fraction = jsonToRandomParameterFloat(j["midrib_fold_fraction"], generator);
    if (j.contains("longitudinal_curvature")) p.longitudinal_curvature = jsonToRandomParameterFloat(j["longitudinal_curvature"], generator);
    if (j.contains("lateral_curvature")) p.lateral_curvature = jsonToRandomParameterFloat(j["lateral_curvature"], generator);
    if (j.contains("petiole_roll")) p.petiole_roll = jsonToRandomParameterFloat(j["petiole_roll"], generator);
    if (j.contains("roll_fraction")) p.roll_fraction = jsonToRandomParameterFloat(j["roll_fraction"], generator);
    if (j.contains("wave_period")) p.wave_period = jsonToRandomParameterFloat(j["wave_period"], generator);
    if (j.contains("wave_amplitude")) p.wave_amplitude = jsonToRandomParameterFloat(j["wave_amplitude"], generator);
    if (j.contains("longitudinal_curvature_exponent")) p.longitudinal_curvature_exponent = jsonToRandomParameterFloat(j["longitudinal_curvature_exponent"], generator);
    if (j.contains("flexibility")) p.flexibility = jsonToRandomParameterFloat(j["flexibility"], generator);
    if (j.contains("flexibility_taper")) p.flexibility_taper = jsonToRandomParameterFloat(j["flexibility_taper"], generator);
    if (j.contains("flexibility_aging")) p.flexibility_aging = jsonToRandomParameterFloat(j["flexibility_aging"], generator);
    if (j.contains("flexibility_aging_max")) p.flexibility_aging_max = jsonToRandomParameterFloat(j["flexibility_aging_max"], generator);
    HELIOS_PUSH_IGNORE_DEPRECATED
    if (j.contains("leaf_buckle_length")) p.leaf_buckle_length = jsonToRandomParameterFloat(j["leaf_buckle_length"], generator);
    if (j.contains("leaf_buckle_angle")) p.leaf_buckle_angle = jsonToRandomParameterFloat(j["leaf_buckle_angle"], generator);
    HELIOS_POP_IGNORE_DEPRECATED
    if (j.contains("leaf_offset")) p.leaf_offset = jsonToVec3(j["leaf_offset"], p.leaf_offset);
    if (j.contains("subdivisions")) p.subdivisions = j["subdivisions"];
    if (j.contains("unique_prototypes")) p.unique_prototypes = j["unique_prototypes"];
    if (j.contains("build_petiolule")) p.build_petiolule = j["build_petiolule"];
    if (j.contains("petiolule_length")) {
        p.petiolule_length.clear();
        for (auto it = j["petiolule_length"].begin(); it != j["petiolule_length"].end(); ++it) {
            p.petiolule_length[std::stoi(it.key())] = it.value().get<float>();
        }
    }
    if (j.contains("OBJ_model_file")) p.OBJ_model_file = j["OBJ_model_file"].get<std::string>();
    if (j.contains("leaf_texture_file")) {
        p.leaf_texture_file.clear();
        for (auto it = j["leaf_texture_file"].begin(); it != j["leaf_texture_file"].end(); ++it) {
            p.leaf_texture_file[std::stoi(it.key())] = it.value().get<std::string>();
        }
    }
    if (j.contains("leaf_class_map_file")) {
        p.leaf_class_map_file.clear();
        for (auto it = j["leaf_class_map_file"].begin(); it != j["leaf_class_map_file"].end(); ++it) {
            p.leaf_class_map_file[std::stoi(it.key())] = it.value().get<std::string>();
        }
    }
    if (j.contains("leaf_texture_series")) {
        p.leaf_texture_series.clear();
        for (auto it = j["leaf_texture_series"].begin(); it != j["leaf_texture_series"].end(); ++it) {
            p.leaf_texture_series[std::stoi(it.key())] = it.value().get<std::vector<std::vector<std::string>>>();
        }
    }
    if (j.contains("leaf_texture_stage_ages")) p.leaf_texture_stage_ages = j["leaf_texture_stage_ages"].get<std::vector<float>>();
    resolvePrototypeFunction(leafPrototypeRegistry(), j, "prototype_function", p.prototype_function, "leaf");
}

// ---- PhytomerParameters <-> JSON ----
nlohmann::json phytomerParametersToJSON(const PhytomerParameters& pp) {
    nlohmann::json j;

    nlohmann::json in;
    in["pitch"] = randomParameterFloatToJSON(pp.internode.pitch);
    in["phyllotactic_angle"] = randomParameterFloatToJSON(pp.internode.phyllotactic_angle);
    in["radius_initial"] = randomParameterFloatToJSON(pp.internode.radius_initial);
    in["max_vegetative_buds_per_petiole"] = randomParameterIntToJSON(pp.internode.max_vegetative_buds_per_petiole);
    in["max_floral_buds_per_petiole"] = randomParameterIntToJSON(pp.internode.max_floral_buds_per_petiole);
    in["color"] = rgbToJSON(pp.internode.color);
    in["image_texture"] = pp.internode.image_texture;
    in["image_class_map_file"] = pp.internode.image_class_map_file;
    in["length_segments"] = pp.internode.length_segments;
    in["radial_subdivisions"] = pp.internode.radial_subdivisions;
    j["internode"] = in;

    nlohmann::json pe;
    pe["petioles_per_internode"] = pp.petiole.petioles_per_internode;
    pe["pitch"] = randomParameterFloatToJSON(pp.petiole.pitch);
    pe["radius"] = randomParameterFloatToJSON(pp.petiole.radius);
    pe["length"] = randomParameterFloatToJSON(pp.petiole.length);
    pe["curvature"] = randomParameterFloatToJSON(pp.petiole.curvature);
    pe["taper"] = randomParameterFloatToJSON(pp.petiole.taper);
    pe["color"] = rgbToJSON(pp.petiole.color);
    pe["length_segments"] = pp.petiole.length_segments;
    pe["radial_subdivisions"] = pp.petiole.radial_subdivisions;
    pe["flexibility"] = randomParameterFloatToJSON(pp.petiole.flexibility);
    pe["flexibility_aging"] = randomParameterFloatToJSON(pp.petiole.flexibility_aging);
    j["petiole"] = pe;

    nlohmann::json lf;
    lf["leaves_per_petiole"] = randomParameterIntToJSON(pp.leaf.leaves_per_petiole);
    lf["pitch"] = randomParameterFloatToJSON(pp.leaf.pitch);
    lf["yaw"] = randomParameterFloatToJSON(pp.leaf.yaw);
    lf["roll"] = randomParameterFloatToJSON(pp.leaf.roll);
    lf["leaflet_offset"] = randomParameterFloatToJSON(pp.leaf.leaflet_offset);
    lf["leaflet_scale"] = randomParameterFloatToJSON(pp.leaf.leaflet_scale);
    lf["intercalary_leaflet_scale"] = randomParameterFloatToJSON(pp.leaf.intercalary_leaflet_scale);
    lf["prototype_scale"] = randomParameterFloatToJSON(pp.leaf.prototype_scale);
    lf["prototype"] = leafPrototypeToJSON(pp.leaf.prototype);
    j["leaf"] = lf;

    nlohmann::json pd;
    pd["length"] = randomParameterFloatToJSON(pp.peduncle.length);
    pd["radius"] = randomParameterFloatToJSON(pp.peduncle.radius);
    pd["pitch"] = randomParameterFloatToJSON(pp.peduncle.pitch);
    pd["roll"] = randomParameterFloatToJSON(pp.peduncle.roll);
    pd["yaw"] = randomParameterFloatToJSON(pp.peduncle.yaw);
    pd["curvature"] = randomParameterFloatToJSON(pp.peduncle.curvature);
    pd["color"] = rgbToJSON(pp.peduncle.color);
    pd["length_segments"] = pp.peduncle.length_segments;
    pd["radial_subdivisions"] = pp.peduncle.radial_subdivisions;
    j["peduncle"] = pd;

    nlohmann::json inf;
    inf["flowers_per_peduncle"] = randomParameterIntToJSON(pp.inflorescence.flowers_per_peduncle);
    inf["flower_offset"] = randomParameterFloatToJSON(pp.inflorescence.flower_offset);
    inf["pitch"] = randomParameterFloatToJSON(pp.inflorescence.pitch);
    inf["roll"] = randomParameterFloatToJSON(pp.inflorescence.roll);
    inf["flower_prototype_scale"] = randomParameterFloatToJSON(pp.inflorescence.flower_prototype_scale);
    inf["fruit_prototype_scale"] = randomParameterFloatToJSON(pp.inflorescence.fruit_prototype_scale);
    inf["fruit_gravity_factor_fraction"] = randomParameterFloatToJSON(pp.inflorescence.fruit_gravity_factor_fraction);
    inf["unique_prototypes"] = pp.inflorescence.unique_prototypes;
    inf["fruit_class_map_file"] = pp.inflorescence.fruit_class_map_file;
    inf["inflorescence_maturity_period"] = randomParameterFloatToJSON(pp.inflorescence.inflorescence_maturity_period);
    inf["flower_prototype_function"] = prototypeFunctionName(flowerPrototypeRegistry(), flowerSlotFunctions(), kPythonFlowerPrototypePrefix, pp.inflorescence.flower_prototype_function);
    inf["fruit_prototype_function"] = prototypeFunctionName(fruitPrototypeRegistry(), fruitSlotFunctions(), kPythonFruitPrototypePrefix, pp.inflorescence.fruit_prototype_function);
    j["inflorescence"] = inf;

    return j;
}

void jsonToPhytomerParameters(PhytomerParameters& pp, const nlohmann::json& j, std::minstd_rand0* generator) {
    if (j.contains("internode")) {
        const nlohmann::json& in = j["internode"];
        if (in.contains("pitch")) pp.internode.pitch = jsonToRandomParameterFloat(in["pitch"], generator);
        if (in.contains("phyllotactic_angle")) pp.internode.phyllotactic_angle = jsonToRandomParameterFloat(in["phyllotactic_angle"], generator);
        if (in.contains("radius_initial")) pp.internode.radius_initial = jsonToRandomParameterFloat(in["radius_initial"], generator);
        if (in.contains("max_vegetative_buds_per_petiole")) pp.internode.max_vegetative_buds_per_petiole = jsonToRandomParameterInt(in["max_vegetative_buds_per_petiole"], generator);
        if (in.contains("max_floral_buds_per_petiole")) pp.internode.max_floral_buds_per_petiole = jsonToRandomParameterInt(in["max_floral_buds_per_petiole"], generator);
        if (in.contains("color")) pp.internode.color = jsonToRGB(in["color"], pp.internode.color);
        if (in.contains("image_texture")) pp.internode.image_texture = in["image_texture"].get<std::string>();
        if (in.contains("image_class_map_file")) pp.internode.image_class_map_file = in["image_class_map_file"].get<std::string>();
        if (in.contains("length_segments")) pp.internode.length_segments = in["length_segments"];
        if (in.contains("radial_subdivisions")) pp.internode.radial_subdivisions = in["radial_subdivisions"];
    }
    if (j.contains("petiole")) {
        const nlohmann::json& pe = j["petiole"];
        if (pe.contains("petioles_per_internode")) pp.petiole.petioles_per_internode = pe["petioles_per_internode"];
        if (pe.contains("pitch")) pp.petiole.pitch = jsonToRandomParameterFloat(pe["pitch"], generator);
        if (pe.contains("radius")) pp.petiole.radius = jsonToRandomParameterFloat(pe["radius"], generator);
        if (pe.contains("length")) pp.petiole.length = jsonToRandomParameterFloat(pe["length"], generator);
        if (pe.contains("curvature")) pp.petiole.curvature = jsonToRandomParameterFloat(pe["curvature"], generator);
        if (pe.contains("taper")) pp.petiole.taper = jsonToRandomParameterFloat(pe["taper"], generator);
        if (pe.contains("color")) pp.petiole.color = jsonToRGB(pe["color"], pp.petiole.color);
        if (pe.contains("length_segments")) pp.petiole.length_segments = pe["length_segments"];
        if (pe.contains("radial_subdivisions")) pp.petiole.radial_subdivisions = pe["radial_subdivisions"];
        if (pe.contains("flexibility")) pp.petiole.flexibility = jsonToRandomParameterFloat(pe["flexibility"], generator);
        if (pe.contains("flexibility_aging")) pp.petiole.flexibility_aging = jsonToRandomParameterFloat(pe["flexibility_aging"], generator);
    }
    if (j.contains("leaf")) {
        const nlohmann::json& lf = j["leaf"];
        if (lf.contains("leaves_per_petiole")) pp.leaf.leaves_per_petiole = jsonToRandomParameterInt(lf["leaves_per_petiole"], generator);
        if (lf.contains("pitch")) pp.leaf.pitch = jsonToRandomParameterFloat(lf["pitch"], generator);
        if (lf.contains("yaw")) pp.leaf.yaw = jsonToRandomParameterFloat(lf["yaw"], generator);
        if (lf.contains("roll")) pp.leaf.roll = jsonToRandomParameterFloat(lf["roll"], generator);
        if (lf.contains("leaflet_offset")) pp.leaf.leaflet_offset = jsonToRandomParameterFloat(lf["leaflet_offset"], generator);
        if (lf.contains("leaflet_scale")) pp.leaf.leaflet_scale = jsonToRandomParameterFloat(lf["leaflet_scale"], generator);
        if (lf.contains("intercalary_leaflet_scale")) pp.leaf.intercalary_leaflet_scale = jsonToRandomParameterFloat(lf["intercalary_leaflet_scale"], generator);
        if (lf.contains("prototype_scale")) pp.leaf.prototype_scale = jsonToRandomParameterFloat(lf["prototype_scale"], generator);
        if (lf.contains("prototype")) jsonToLeafPrototype(pp.leaf.prototype, lf["prototype"], generator);
    }
    if (j.contains("peduncle")) {
        const nlohmann::json& pd = j["peduncle"];
        if (pd.contains("length")) pp.peduncle.length = jsonToRandomParameterFloat(pd["length"], generator);
        if (pd.contains("radius")) pp.peduncle.radius = jsonToRandomParameterFloat(pd["radius"], generator);
        if (pd.contains("pitch")) pp.peduncle.pitch = jsonToRandomParameterFloat(pd["pitch"], generator);
        if (pd.contains("roll")) pp.peduncle.roll = jsonToRandomParameterFloat(pd["roll"], generator);
        if (pd.contains("yaw")) pp.peduncle.yaw = jsonToRandomParameterFloat(pd["yaw"], generator);
        if (pd.contains("curvature")) pp.peduncle.curvature = jsonToRandomParameterFloat(pd["curvature"], generator);
        if (pd.contains("color")) pp.peduncle.color = jsonToRGB(pd["color"], pp.peduncle.color);
        if (pd.contains("length_segments")) pp.peduncle.length_segments = pd["length_segments"];
        if (pd.contains("radial_subdivisions")) pp.peduncle.radial_subdivisions = pd["radial_subdivisions"];
    }
    if (j.contains("inflorescence")) {
        const nlohmann::json& inf = j["inflorescence"];
        if (inf.contains("flowers_per_peduncle")) pp.inflorescence.flowers_per_peduncle = jsonToRandomParameterInt(inf["flowers_per_peduncle"], generator);
        if (inf.contains("flower_offset")) pp.inflorescence.flower_offset = jsonToRandomParameterFloat(inf["flower_offset"], generator);
        if (inf.contains("pitch")) pp.inflorescence.pitch = jsonToRandomParameterFloat(inf["pitch"], generator);
        if (inf.contains("roll")) pp.inflorescence.roll = jsonToRandomParameterFloat(inf["roll"], generator);
        if (inf.contains("flower_prototype_scale")) pp.inflorescence.flower_prototype_scale = jsonToRandomParameterFloat(inf["flower_prototype_scale"], generator);
        if (inf.contains("fruit_prototype_scale")) pp.inflorescence.fruit_prototype_scale = jsonToRandomParameterFloat(inf["fruit_prototype_scale"], generator);
        if (inf.contains("fruit_gravity_factor_fraction")) pp.inflorescence.fruit_gravity_factor_fraction = jsonToRandomParameterFloat(inf["fruit_gravity_factor_fraction"], generator);
        if (inf.contains("unique_prototypes")) pp.inflorescence.unique_prototypes = inf["unique_prototypes"];
        if (inf.contains("fruit_class_map_file")) pp.inflorescence.fruit_class_map_file = inf["fruit_class_map_file"].get<std::string>();
        if (inf.contains("inflorescence_maturity_period")) pp.inflorescence.inflorescence_maturity_period = jsonToRandomParameterFloat(inf["inflorescence_maturity_period"], generator);
        resolvePrototypeFunction(flowerPrototypeRegistry(), flowerSlotFunctions(), flowerPrototypeSlots(), kPythonFlowerPrototypePrefix, inf, "flower_prototype_function", pp.inflorescence.flower_prototype_function, "flower");
        resolvePrototypeFunction(fruitPrototypeRegistry(), fruitSlotFunctions(), fruitPrototypeSlots(), kPythonFruitPrototypePrefix, inf, "fruit_prototype_function", pp.inflorescence.fruit_prototype_function, "fruit");
    }
}

// ---- CarbohydrateParameters / NitrogenParameters <-> JSON ----
nlohmann::json carbohydrateParametersToJSON(const CarbohydrateParameters& c) {
    return nlohmann::json{
        {"stem_density", c.stem_density},
        {"stem_carbon_percentage", c.stem_carbon_percentage},
        {"stem_carbohydrate_percentage", c.stem_carbohydrate_percentage},
        {"stem_structural_carbon_percentage", c.stem_structural_carbon_percentage},
        {"maturity_age", c.maturity_age},
        {"initial_density_ratio", c.initial_density_ratio},
        {"shoot_root_ratio", c.shoot_root_ratio},
        {"leaf_total_carbon_percentage", c.leaf_total_carbon_percentage},
        {"SLA", c.SLA},
        {"leaf_carbohydrate_percentage", c.leaf_carbohydrate_percentage},
        {"leaf_carbon_percentage", c.leaf_carbon_percentage},
        {"total_flower_cost", c.total_flower_cost},
        {"fruit_density", c.fruit_density},
        {"fruit_carbon_percentage", c.fruit_carbon_percentage},
        {"r_m_w_20", c.r_m_w_20},
        {"r_m_r_20", c.r_m_r_20},
        {"living_wood_fraction", c.living_wood_fraction},
        {"growth_respiration_fraction", c.growth_respiration_fraction},
        {"carbohydrate_abortion_threshold", c.carbohydrate_abortion_threshold},
        {"carbohydrate_pruning_threshold", c.carbohydrate_pruning_threshold},
        {"bud_death_threshold_days", c.bud_death_threshold_days},
        {"branch_death_threshold_days", c.branch_death_threshold_days},
        {"carbohydrate_phyllochron_threshold", c.carbohydrate_phyllochron_threshold},
        {"carbohydrate_vegetative_break_threshold", c.carbohydrate_vegetative_break_threshold},
        {"carbohydrate_growth_threshold", c.carbohydrate_growth_threshold},
        {"starch_sequestration_ratio", c.starch_sequestration_ratio},
        {"carbohydrate_transfer_threshold_down", c.carbohydrate_transfer_threshold_down},
        {"carbohydrate_transfer_threshold_up", c.carbohydrate_transfer_threshold_up},
        {"carbon_conductance_down", c.carbon_conductance_down},
        {"carbon_conductance_up", c.carbon_conductance_up},
    };
}

CarbohydrateParameters jsonToCarbohydrateParameters(const nlohmann::json& j) {
    CarbohydrateParameters c;
    #define PYH_CARB(field) if (j.contains(#field)) c.field = j[#field];
    PYH_CARB(stem_density) PYH_CARB(stem_carbon_percentage) PYH_CARB(stem_carbohydrate_percentage)
    PYH_CARB(stem_structural_carbon_percentage) PYH_CARB(maturity_age) PYH_CARB(initial_density_ratio)
    PYH_CARB(shoot_root_ratio) PYH_CARB(leaf_total_carbon_percentage) PYH_CARB(SLA)
    PYH_CARB(leaf_carbohydrate_percentage) PYH_CARB(leaf_carbon_percentage) PYH_CARB(total_flower_cost)
    PYH_CARB(fruit_density) PYH_CARB(fruit_carbon_percentage) PYH_CARB(r_m_w_20) PYH_CARB(r_m_r_20)
    PYH_CARB(living_wood_fraction) PYH_CARB(growth_respiration_fraction) PYH_CARB(carbohydrate_abortion_threshold)
    PYH_CARB(carbohydrate_pruning_threshold) PYH_CARB(bud_death_threshold_days) PYH_CARB(branch_death_threshold_days)
    PYH_CARB(carbohydrate_phyllochron_threshold) PYH_CARB(carbohydrate_vegetative_break_threshold)
    PYH_CARB(carbohydrate_growth_threshold) PYH_CARB(starch_sequestration_ratio)
    PYH_CARB(carbohydrate_transfer_threshold_down) PYH_CARB(carbohydrate_transfer_threshold_up)
    PYH_CARB(carbon_conductance_down) PYH_CARB(carbon_conductance_up)
    #undef PYH_CARB
    return c;
}

nlohmann::json nitrogenParametersToJSON(const NitrogenParameters& n) {
    return nlohmann::json{
        {"target_leaf_N_area", n.target_leaf_N_area},
        {"minimum_leaf_N_area", n.minimum_leaf_N_area},
        {"root_allocation_fraction", n.root_allocation_fraction},
        {"max_N_accumulation_rate", n.max_N_accumulation_rate},
        {"leaf_remobilization_rate", n.leaf_remobilization_rate},
        {"leaf_remobilization_efficiency", n.leaf_remobilization_efficiency},
        {"leaf_senescence_duration_fraction", n.leaf_senescence_duration_fraction},
        {"stress_senescence_advance_fraction", n.stress_senescence_advance_fraction},
        {"fruit_N_area", n.fruit_N_area},
    };
}

NitrogenParameters jsonToNitrogenParameters(const nlohmann::json& j) {
    NitrogenParameters n;
    #define PYH_N(field) if (j.contains(#field)) n.field = j[#field];
    PYH_N(target_leaf_N_area) PYH_N(minimum_leaf_N_area) PYH_N(root_allocation_fraction)
    PYH_N(max_N_accumulation_rate) PYH_N(leaf_remobilization_rate) PYH_N(leaf_remobilization_efficiency)
    PYH_N(leaf_senescence_duration_fraction) PYH_N(stress_senescence_advance_fraction) PYH_N(fruit_N_area)
    #undef PYH_N
    return n;
}

nlohmann::json shootParametersToJSON(const ShootParameters& params) {
    nlohmann::json j;

    // Geometric parameters
    j["max_nodes"] = randomParameterIntToJSON(params.max_nodes);
    j["max_nodes_per_season"] = randomParameterIntToJSON(params.max_nodes_per_season);
    j["girth_area_factor"] = randomParameterFloatToJSON(params.girth_area_factor);
    j["insertion_angle_tip"] = randomParameterFloatToJSON(params.insertion_angle_tip);
    j["insertion_angle_decay_rate"] = randomParameterFloatToJSON(params.insertion_angle_decay_rate);
    j["internode_length_max"] = randomParameterFloatToJSON(params.internode_length_max);
    j["internode_length_min"] = randomParameterFloatToJSON(params.internode_length_min);
    j["internode_length_decay_rate"] = randomParameterFloatToJSON(params.internode_length_decay_rate);
    j["base_roll"] = randomParameterFloatToJSON(params.base_roll);
    j["base_yaw"] = randomParameterFloatToJSON(params.base_yaw);
    j["gravitropic_curvature"] = randomParameterFloatToJSON(params.gravitropic_curvature);
    j["tortuosity"] = randomParameterFloatToJSON(params.tortuosity);
    j["tortuosity_persistence_length"] = randomParameterFloatToJSON(params.tortuosity_persistence_length);

    // Growth parameters
    j["phyllochron_min"] = randomParameterFloatToJSON(params.phyllochron_min);
    j["elongation_rate_max"] = randomParameterFloatToJSON(params.elongation_rate_max);
    j["leaf_expansion_rate_max"] = randomParameterFloatToJSON(params.leaf_expansion_rate_max);
    j["vegetative_bud_break_probability_min"] = randomParameterFloatToJSON(params.vegetative_bud_break_probability_min);
    j["vegetative_bud_break_probability_max"] = randomParameterFloatToJSON(params.vegetative_bud_break_probability_max);
    j["vegetative_bud_break_probability_decay_rate"] = randomParameterFloatToJSON(params.vegetative_bud_break_probability_decay_rate);
    j["max_terminal_floral_buds"] = randomParameterIntToJSON(params.max_terminal_floral_buds);
    j["flower_bud_break_probability"] = randomParameterFloatToJSON(params.flower_bud_break_probability);
    j["fruit_set_probability"] = randomParameterFloatToJSON(params.fruit_set_probability);
    j["vegetative_bud_break_time"] = randomParameterFloatToJSON(params.vegetative_bud_break_time);

    // Boolean flags
    j["flowers_require_dormancy"] = params.flowers_require_dormancy;
    j["growth_requires_dormancy"] = params.growth_requires_dormancy;
    j["determinate_shoot_growth"] = params.determinate_shoot_growth;

    // Child shoot types. Readable since helios-core 1.3.84 via ShootParameters::getChildShootTypeLabels()
    // and getChildShootTypeProbabilities(); an empty list is meaningful (the shoot reproduces its own type).
    nlohmann::json child = nlohmann::json::object();
    child["labels"] = params.getChildShootTypeLabels();
    child["probabilities"] = params.getChildShootTypeProbabilities();
    j["child_shoot_types"] = child;

    // Nested phytomer parameters (internode/petiole/leaf/peduncle/inflorescence + leaf prototype)
    j["phytomer_parameters"] = phytomerParametersToJSON(params.phytomer_parameters);

    return j;
}

// Rebuild a ShootParameters from JSON. When \p base is non-null the result starts as a copy of it,
// so fields that cannot be represented in JSON -- notably the protected child shoot type vectors --
// are preserved; JSON values are then overlaid on top and still take precedence.
ShootParameters jsonToShootParameters(const nlohmann::json& j, std::minstd_rand0* generator, const ShootParameters* base = nullptr) {
    ShootParameters params(generator);
    if (base != nullptr) {
        params = *base;
    }

    // Geometric parameters
    if (j.contains("max_nodes")) params.max_nodes = jsonToRandomParameterInt(j["max_nodes"], generator);
    if (j.contains("max_nodes_per_season")) params.max_nodes_per_season = jsonToRandomParameterInt(j["max_nodes_per_season"], generator);
    if (j.contains("girth_area_factor")) params.girth_area_factor = jsonToRandomParameterFloat(j["girth_area_factor"], generator);
    if (j.contains("insertion_angle_tip")) params.insertion_angle_tip = jsonToRandomParameterFloat(j["insertion_angle_tip"], generator);
    if (j.contains("insertion_angle_decay_rate")) params.insertion_angle_decay_rate = jsonToRandomParameterFloat(j["insertion_angle_decay_rate"], generator);
    if (j.contains("internode_length_max")) params.internode_length_max = jsonToRandomParameterFloat(j["internode_length_max"], generator);
    if (j.contains("internode_length_min")) params.internode_length_min = jsonToRandomParameterFloat(j["internode_length_min"], generator);
    if (j.contains("internode_length_decay_rate")) params.internode_length_decay_rate = jsonToRandomParameterFloat(j["internode_length_decay_rate"], generator);
    if (j.contains("base_roll")) params.base_roll = jsonToRandomParameterFloat(j["base_roll"], generator);
    if (j.contains("base_yaw")) params.base_yaw = jsonToRandomParameterFloat(j["base_yaw"], generator);
    if (j.contains("gravitropic_curvature")) params.gravitropic_curvature = jsonToRandomParameterFloat(j["gravitropic_curvature"], generator);
    if (j.contains("tortuosity")) params.tortuosity = jsonToRandomParameterFloat(j["tortuosity"], generator);
    if (j.contains("tortuosity_persistence_length")) params.tortuosity_persistence_length = jsonToRandomParameterFloat(j["tortuosity_persistence_length"], generator);

    // Growth parameters
    if (j.contains("phyllochron_min")) params.phyllochron_min = jsonToRandomParameterFloat(j["phyllochron_min"], generator);
    if (j.contains("elongation_rate_max")) params.elongation_rate_max = jsonToRandomParameterFloat(j["elongation_rate_max"], generator);
    if (j.contains("leaf_expansion_rate_max")) params.leaf_expansion_rate_max = jsonToRandomParameterFloat(j["leaf_expansion_rate_max"], generator);
    if (j.contains("vegetative_bud_break_probability_min")) params.vegetative_bud_break_probability_min = jsonToRandomParameterFloat(j["vegetative_bud_break_probability_min"], generator);
    if (j.contains("vegetative_bud_break_probability_max")) params.vegetative_bud_break_probability_max = jsonToRandomParameterFloat(j["vegetative_bud_break_probability_max"], generator);
    if (j.contains("vegetative_bud_break_probability_decay_rate")) params.vegetative_bud_break_probability_decay_rate = jsonToRandomParameterFloat(j["vegetative_bud_break_probability_decay_rate"], generator);
    if (j.contains("max_terminal_floral_buds")) params.max_terminal_floral_buds = jsonToRandomParameterInt(j["max_terminal_floral_buds"], generator);
    if (j.contains("flower_bud_break_probability")) params.flower_bud_break_probability = jsonToRandomParameterFloat(j["flower_bud_break_probability"], generator);
    if (j.contains("fruit_set_probability")) params.fruit_set_probability = jsonToRandomParameterFloat(j["fruit_set_probability"], generator);
    if (j.contains("vegetative_bud_break_time")) params.vegetative_bud_break_time = jsonToRandomParameterFloat(j["vegetative_bud_break_time"], generator);

    // Boolean flags
    if (j.contains("flowers_require_dormancy")) params.flowers_require_dormancy = j["flowers_require_dormancy"];
    if (j.contains("growth_requires_dormancy")) params.growth_requires_dormancy = j["growth_requires_dormancy"];
    if (j.contains("determinate_shoot_growth")) params.determinate_shoot_growth = j["determinate_shoot_growth"];

    // Child shoot types. An empty list is a meaningful state -- the shoot reproduces its own type --
    // but ShootParameters::defineChildShootTypes() rejects empty input, so only call it when non-empty.
    // An explicitly empty list therefore leaves whatever the base carried; that is the conservative
    // choice, since erasing a shoot type's branching topology silently is the failure this seeding
    // was introduced to prevent.
    if (j.contains("child_shoot_types")) {
        std::vector<std::string> labels = j["child_shoot_types"]["labels"];
        std::vector<float> probs = j["child_shoot_types"]["probabilities"];
        if (!labels.empty()) {
            params.defineChildShootTypes(labels, probs);
        }
    }

    // Nested phytomer parameters. ShootParameters(generator) does NOT propagate the
    // generator into phytomer_parameters (it is default-constructed with a null
    // generator), so rebuild it with the real generator before overlaying JSON values.
    // This guarantees every nested RandomParameter has a valid generator even for
    // fields absent from the JSON. When seeding from an existing entry its phytomer
    // parameters already carry a valid generator, and resetting them here would discard
    // the very values we copied it for.
    if (base == nullptr) {
        params.phytomer_parameters = PhytomerParameters(generator);
    }
    if (j.contains("phytomer_parameters")) {
        jsonToPhytomerParameters(params.phytomer_parameters, j["phytomer_parameters"], generator);
    }

    return params;
}

//! Resolve (plantID, shootID, node_index) to the phytomer it names.
/**
 * Throws std::runtime_error when node_index is past the end of the shoot, so callers get an explicit
 * message instead of the undefined behaviour of indexing the vector out of range.
 */
std::shared_ptr<Phytomer> resolvePhytomer(PlantArchitecture* plantarch, uint plantID, uint shootID, uint node_index, const char* function_name) {
    const std::shared_ptr<Shoot>& shoot = plantarch->getPlantShoot(plantID, shootID);
    if (node_index >= shoot->phytomers.size()) {
        throw std::runtime_error("ERROR (PlantArchitecture::" + std::string(function_name) + "): Node index " + std::to_string(node_index) + " is out of range for shoot " + std::to_string(shootID) +
                                 ", which has " + std::to_string(shoot->phytomers.size()) + " phytomers.");
    }
    return shoot->phytomers.at(node_index);
}

//! An out-of-range node, petiole or leaf index, reported as PYHELIOS_ERROR_INVALID_PARAMETER so Python raises ValueError.
struct PhytomerIndexError : std::runtime_error {
    using std::runtime_error::runtime_error;
};

//! Like resolvePhytomer(), but an out-of-range node index throws PhytomerIndexError.
std::shared_ptr<Phytomer> resolvePhytomerIndexed(PlantArchitecture* plantarch, uint plantID, uint shootID, uint node_index) {
    const std::shared_ptr<Shoot>& shoot = plantarch->getPlantShoot(plantID, shootID);
    if (node_index >= shoot->phytomers.size()) {
        throw PhytomerIndexError("Node index " + std::to_string(node_index) + " is out of range for shoot " + std::to_string(shootID) + " of plant " + std::to_string(plantID) +
                                 ", which has " + std::to_string(shoot->phytomers.size()) + " phytomers (valid indices 0 to " + std::to_string(shoot->phytomers.size()) + " - 1).");
    }
    return shoot->phytomers.at(node_index);
}

void checkPetioleIndex(size_t petiole_count, uint petiole_index, uint node_index) {
    if (petiole_index >= petiole_count) {
        throw PhytomerIndexError("Petiole index " + std::to_string(petiole_index) + " is out of range for node " + std::to_string(node_index) + ", which has " + std::to_string(petiole_count) +
                                 " petiole(s) (valid indices 0 to " + std::to_string(petiole_count) + " - 1).");
    }
}

void checkLeafIndex(size_t leaf_count, uint leaf_index, uint petiole_index) {
    if (leaf_index >= leaf_count) {
        throw PhytomerIndexError("Leaf index " + std::to_string(leaf_index) + " is out of range for petiole " + std::to_string(petiole_index) + ", which has " + std::to_string(leaf_count) +
                                 " leaves (valid indices 0 to " + std::to_string(leaf_count) + " - 1).");
    }
}

//! Run body() under the standard error protocol, mapping PhytomerIndexError and std::invalid_argument to PYHELIOS_ERROR_INVALID_PARAMETER.
template<typename R, typename F>
R guardedPhytomerCall(PlantArchitecture* plantarch, const char* function_name, R error_value, F&& body) {
    try {
        clearError();
        if (!plantarch) {
            setError(PYHELIOS_ERROR_INVALID_PARAMETER, "PlantArchitecture pointer is null");
            return error_value;
        }
        return body();
    } catch (const PhytomerIndexError& e) {
        setError(PYHELIOS_ERROR_INVALID_PARAMETER, std::string("ERROR (PlantArchitecture::") + function_name + "): " + e.what());
    } catch (const std::invalid_argument& e) {
        setError(PYHELIOS_ERROR_INVALID_PARAMETER, std::string("ERROR (PlantArchitecture::") + function_name + "): " + e.what());
    } catch (const std::exception& e) {
        setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (PlantArchitecture::") + function_name + "): " + e.what());
    } catch (...) {
        setError(PYHELIOS_ERROR_UNKNOWN, std::string("ERROR (PlantArchitecture::") + function_name + "): Unknown error.");
    }
    return error_value;
}

//! Unpack the flat LeafShapeValues layout of getLeafShape() (12 floats, 2 uints).
static LeafShapeValues unpackLeafShape(const float* values, const unsigned int* subdivisions) {
    LeafShapeValues shape;
    shape.aspect_ratio = values[0];
    shape.midrib_fold_fraction = values[1];
    shape.longitudinal_curvature = values[2];
    shape.longitudinal_curvature_exponent = values[3];
    shape.lateral_curvature = values[4];
    shape.petiole_roll = values[5];
    shape.wave_period = values[6];
    shape.wave_amplitude = values[7];
    shape.roll_fraction = values[8];
    shape.lattice_offset = helios::make_vec3(values[9], values[10], values[11]);
    shape.subdivisions_x = subdivisions[0];
    shape.subdivisions_y = subdivisions[1];
    return shape;
}

float* flattenVec3(const std::vector<helios::vec3>& points, int* count) {
    // Flattened as x,y,z triples; *count is the number of vec3 values, not floats.
    static thread_local std::vector<float> static_result;
    static_result.clear();
    static_result.reserve(points.size() * 3);
    for (const helios::vec3& point : points) {
        static_result.push_back(point.x);
        static_result.push_back(point.y);
        static_result.push_back(point.z);
    }
    *count = static_cast<int>(points.size());
    return static_result.data();
}

// ---- Phytomer creation function trampoline ----
// PhytomerParameters::phytomer_creation_function is a plain function pointer with no user data, so one static
// trampoline is installed on every shoot type that has a Python callback. It recovers the owning
// PlantArchitecture and shoot type label from the phytomer and looks the Python callback up in this registry.
// Each entry also keeps the function the shoot type had before a Python callback replaced it (usually a library
// function). Clearing the callback restores that function to the shoot type, and shoots built while the callback was
// set, which still carry the trampoline, are delegated to it.
using PhytomerCreationCallback = PyheliosPhytomerCreationCallback;
using PhytomerCreationFn = void (*)(std::shared_ptr<Phytomer>, uint, uint, uint, float);

struct PhytomerCreationEntry {
    PhytomerCreationCallback callback = nullptr;
    PhytomerCreationFn original = nullptr;
};

std::map<const PlantArchitecture*, std::map<std::string, PhytomerCreationEntry>>& phytomerCreationCallbacks() {
    static std::map<const PlantArchitecture*, std::map<std::string, PhytomerCreationEntry>> registry;
    return registry;
}

void phytomerCreationTrampoline(std::shared_ptr<Phytomer> phytomer, uint shoot_node_index, uint parent_shoot_node_index, uint shoot_max_nodes, float plant_age) {
    const Shoot* shoot = phytomer->parent_shoot_ptr;
    if (shoot == nullptr) {
        throw std::runtime_error("Phytomer creation function was called for a phytomer with no parent shoot.");
    }
    const auto& registry = phytomerCreationCallbacks();
    const auto instance = registry.find(shoot->plantarchitecture_ptr);
    if (instance == registry.end() || instance->second.find(shoot->shoot_type_label) == instance->second.end()) {
        throw std::runtime_error("No Python phytomer creation function is registered for shoot type '" + shoot->shoot_type_label + "'.");
    }
    const PhytomerCreationEntry& entry = instance->second.at(shoot->shoot_type_label);
    const PhytomerCreationCallback callback = entry.callback;
    if (callback == nullptr) {
        if (entry.original != nullptr) {
            entry.original(phytomer, shoot_node_index, parent_shoot_node_index, shoot_max_nodes, plant_age);
        }
        return;
    }

    // The plugin has already appended the new phytomer when it calls the creation function.
    size_t node_index = shoot->phytomers.size();
    for (size_t i = shoot->phytomers.size(); i-- > 0;) {
        if (shoot->phytomers.at(i).get() == phytomer.get()) {
            node_index = i;
            break;
        }
    }
    if (node_index == shoot->phytomers.size()) {
        throw std::runtime_error("Phytomer creation function was called for a phytomer not yet attached to shoot " + std::to_string(shoot->ID) + ".");
    }

    if (callback(phytomer->plantID, phytomer->parent_shoot_ID, static_cast<unsigned int>(node_index), shoot_node_index, parent_shoot_node_index, shoot_max_nodes, plant_age) != 0) {
        throw std::runtime_error("The Python phytomer creation function for shoot type '" + shoot->shoot_type_label + "' raised an exception (node " + std::to_string(node_index) + " of shoot " +
                                 std::to_string(phytomer->parent_shoot_ID) + " of plant " + std::to_string(phytomer->plantID) + ").");
    }
}

// ---- Per-timestep phytomer callback trampoline ----
// Same scheme as the creation function: PhytomerParameters::phytomer_callback_function carries no user data, so one
// static trampoline recovers the Python callback from the phytomer's PlantArchitecture and shoot type label, and
// clearing it restores the function it replaced.
using PhytomerCallback = PyheliosPhytomerCallback;
using PhytomerCallbackFn = void (*)(std::shared_ptr<Phytomer>);

struct PhytomerCallbackEntry {
    PhytomerCallback callback = nullptr;
    PhytomerCallbackFn original = nullptr;
};

std::map<const PlantArchitecture*, std::map<std::string, PhytomerCallbackEntry>>& phytomerCallbacks() {
    static std::map<const PlantArchitecture*, std::map<std::string, PhytomerCallbackEntry>> registry;
    return registry;
}

void phytomerCallbackTrampoline(std::shared_ptr<Phytomer> phytomer) {
    const Shoot* shoot = phytomer->parent_shoot_ptr;
    if (shoot == nullptr) {
        throw std::runtime_error("Phytomer callback function was called for a phytomer with no parent shoot.");
    }
    const auto& registry = phytomerCallbacks();
    const auto instance = registry.find(shoot->plantarchitecture_ptr);
    if (instance == registry.end()) {
        throw std::runtime_error("No Python phytomer callback function is registered for shoot type '" + shoot->shoot_type_label + "'.");
    }
    const auto entry = instance->second.find(shoot->shoot_type_label);
    if (entry == instance->second.end()) {
        throw std::runtime_error("No Python phytomer callback function is registered for shoot type '" + shoot->shoot_type_label + "'.");
    }
    const PhytomerCallback callback = entry->second.callback;
    if (callback == nullptr) {
        if (entry->second.original != nullptr) {
            entry->second.original(phytomer);
        }
        return;
    }

    // shoot_index.x is the phytomer's position on its shoot; confirm it, since this runs on every phytomer every step.
    size_t node_index = static_cast<size_t>(phytomer->shoot_index.x);
    if (node_index >= shoot->phytomers.size() || shoot->phytomers.at(node_index).get() != phytomer.get()) {
        node_index = shoot->phytomers.size();
        for (size_t i = 0; i < shoot->phytomers.size(); i++) {
            if (shoot->phytomers.at(i).get() == phytomer.get()) {
                node_index = i;
                break;
            }
        }
        if (node_index == shoot->phytomers.size()) {
            throw std::runtime_error("Phytomer callback function was called for a phytomer not attached to shoot " + std::to_string(shoot->ID) + ".");
        }
    }

    if (callback(phytomer->plantID, phytomer->parent_shoot_ID, static_cast<unsigned int>(node_index), phytomer->age) != 0) {
        throw std::runtime_error("The Python phytomer callback function for shoot type '" + shoot->shoot_type_label + "' raised an exception (node " + std::to_string(node_index) + " of shoot " +
                                 std::to_string(phytomer->parent_shoot_ID) + " of plant " + std::to_string(phytomer->plantID) + ").");
    }
}

// ---- Library phytomer function registries (name <-> function declared in Assets.h) ----
// The library models' creation and per-timestep callback functions are referenced by name for the same reason as the
// prototype functions above.
// StrawberryPhytomerCreationFunction and GrapevineFlowerPrototype are declared in Assets.h but defined nowhere, so they cannot be listed.
const std::map<std::string, PhytomerCreationFn>& libraryPhytomerCreationRegistry() {
    static const std::map<std::string, PhytomerCreationFn> reg = {
        {"AlmondPhytomerCreationFunction", &AlmondPhytomerCreationFunction},
        {"ApplePhytomerCreationFunction", &ApplePhytomerCreationFunction},
        {"AppleFruitingWallPhytomerCreationFunction", &AppleFruitingWallPhytomerCreationFunction},
        {"AsparagusPhytomerCreationFunction", &AsparagusPhytomerCreationFunction},
        {"BeanPhytomerCreationFunction", &BeanPhytomerCreationFunction},
        {"CapsicumPhytomerCreationFunction", &CapsicumPhytomerCreationFunction},
        {"CowpeaPhytomerCreationFunction", &CowpeaPhytomerCreationFunction},
        {"CucumberMainPhytomerCreationFunction", &CucumberMainPhytomerCreationFunction},
        {"GrapevinePhytomerCreationFunction", &GrapevinePhytomerCreationFunction},
        {"MaizePhytomerCreationFunction", &MaizePhytomerCreationFunction},
        {"OlivePhytomerCreationFunction", &OlivePhytomerCreationFunction},
        {"PistachioPhytomerCreationFunction", &PistachioPhytomerCreationFunction},
        {"RedbudPhytomerCreationFunction", &RedbudPhytomerCreationFunction},
        {"RicePhytomerCreationFunction", &RicePhytomerCreationFunction},
        {"ButterLettucePhytomerCreationFunction", &ButterLettucePhytomerCreationFunction},
        {"SorghumPhytomerCreationFunction", &SorghumPhytomerCreationFunction},
        {"SoybeanPhytomerCreationFunction", &SoybeanPhytomerCreationFunction},
        {"TomatoPhytomerCreationFunction", &TomatoPhytomerCreationFunction},
        {"CherryTomatoPhytomerCreationFunction", &CherryTomatoPhytomerCreationFunction},
        {"WalnutPhytomerCreationFunction", &WalnutPhytomerCreationFunction},
        {"WheatPhytomerCreationFunction", &WheatPhytomerCreationFunction},
    };
    return reg;
}

const std::map<std::string, PhytomerCallbackFn>& libraryPhytomerCallbackRegistry() {
    static const std::map<std::string, PhytomerCallbackFn> reg = {
        {"AlmondPhytomerCallbackFunction", &AlmondPhytomerCallbackFunction},
        {"AlmondSpurPhytomerCallbackFunction", &AlmondSpurPhytomerCallbackFunction},
        {"ApplePhytomerCallbackFunction", &ApplePhytomerCallbackFunction},
        {"AppleFruitingWallPhytomerCallbackFunction", &AppleFruitingWallPhytomerCallbackFunction},
        {"CucumberMainPhytomerCallbackFunction", &CucumberMainPhytomerCallbackFunction},
        {"GrapevinePhytomerCallbackFunction", &GrapevinePhytomerCallbackFunction},
        {"OlivePhytomerCallbackFunction", &OlivePhytomerCallbackFunction},
        {"PistachioPhytomerCallbackFunction", &PistachioPhytomerCallbackFunction},
        {"RedbudPhytomerCallbackFunction", &RedbudPhytomerCallbackFunction},
        {"CherryTomatoPhytomerCallbackFunction", &CherryTomatoPhytomerCallbackFunction},
        {"WalnutPhytomerCallbackFunction", &WalnutPhytomerCallbackFunction},
    };
    return reg;
}

template<typename FnMap>
typename FnMap::mapped_type resolveLibraryPhytomerFunction(const FnMap& reg, const char* name, const char* kind) {
    if (!name || std::strlen(name) == 0) {
        throw std::invalid_argument(std::string("Library phytomer ") + kind + " function name is null or empty");
    }
    const auto it = reg.find(name);
    if (it == reg.end()) {
        throw std::invalid_argument(std::string("Unknown library phytomer ") + kind + " function name: '" + name + "'");
    }
    return it->second;
}

template<typename FnMap>
const char* joinedRegistryNames(const FnMap& reg) {
    static thread_local std::string names;
    names.clear();
    for (const auto& kv : reg) {
        if (!names.empty()) names += '\n';
        names += kv.first;
    }
    return names.c_str();
}

} // anonymous namespace

extern "C" {

    // PlantArchitecture management functions
    PYHELIOS_API PlantArchitecture* createPlantArchitecture(helios::Context* context) {
        try {
            clearError();
            if (!context) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Context pointer is null");
                return nullptr;
            }
            return new PlantArchitecture(context);
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (PlantArchitecture::constructor): ") + e.what());
            return nullptr;
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (PlantArchitecture::constructor): Unknown error creating PlantArchitecture.");
            return nullptr;
        }
    }

    PYHELIOS_API void destroyPlantArchitecture(PlantArchitecture* plantarch) {
        phytomerCreationCallbacks().erase(plantarch);
        phytomerCallbacks().erase(plantarch);
        for (FruitPrototypeSlot& slot : fruitPrototypeSlots()) {
            if (slot.owner == plantarch) slot = FruitPrototypeSlot();
        }
        for (FlowerPrototypeSlot& slot : flowerPrototypeSlots()) {
            if (slot.owner == plantarch) slot = FlowerPrototypeSlot();
        }
        originalFruitPrototypeFunctions().erase(plantarch);
        originalFlowerPrototypeFunctions().erase(plantarch);
        delete plantarch;
    }

    // Plant library functions
    PYHELIOS_API int loadPlantModelFromLibrary(PlantArchitecture* plantarch, const char* plant_label) {
        try {
            clearError();
            if (!plantarch) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "PlantArchitecture pointer is null");
                return -1;
            }
            if (!plant_label) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Plant label is null");
                return -1;
            }

            plantarch->loadPlantModelFromLibrary(std::string(plant_label));
            return 0;
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (PlantArchitecture::loadPlantModelFromLibrary): ") + e.what());
            return -1;
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (PlantArchitecture::loadPlantModelFromLibrary): Unknown error loading plant model.");
            return -1;
        }
    }

    PYHELIOS_API unsigned int buildPlantInstanceFromLibrary(PlantArchitecture* plantarch, float* base_position, float age, char** param_keys, float* param_values, int param_count) {
        try {
            clearError();
            if (!plantarch) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "PlantArchitecture pointer is null");
                return 0;
            }
            if (!base_position) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Base position array is null");
                return 0;
            }

            helios::vec3 position(base_position[0], base_position[1], base_position[2]);

            // Convert parallel arrays to std::map if parameters provided
            std::map<std::string, float> build_params;
            if (param_keys && param_values && param_count > 0) {
                for (int i = 0; i < param_count; i++) {
                    if (param_keys[i]) {
                        build_params[std::string(param_keys[i])] = param_values[i];
                    }
                }
            }

            return plantarch->buildPlantInstanceFromLibrary(position, age, build_params);
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (PlantArchitecture::buildPlantInstanceFromLibrary): ") + e.what());
            return 0;
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (PlantArchitecture::buildPlantInstanceFromLibrary): Unknown error building plant instance.");
            return 0;
        }
    }

    PYHELIOS_API int buildPlantCanopyFromLibrary(PlantArchitecture* plantarch, float* canopy_center, float* plant_spacing, int* plant_count, float age, float germination_rate, unsigned int** plant_ids, int* num_plants, char** param_keys, float* param_values, int param_count_params) {
        try {
            clearError();
            if (!plantarch) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "PlantArchitecture pointer is null");
                return -1;
            }
            if (!canopy_center || !plant_spacing || !plant_count) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Parameter arrays are null");
                return -1;
            }

            helios::vec3 center(canopy_center[0], canopy_center[1], canopy_center[2]);
            helios::vec2 spacing(plant_spacing[0], plant_spacing[1]);
            helios::int2 count(plant_count[0], plant_count[1]);

            // Convert parallel arrays to std::map if parameters provided
            std::map<std::string, float> build_params;
            if (param_keys && param_values && param_count_params > 0) {
                for (int i = 0; i < param_count_params; i++) {
                    if (param_keys[i]) {
                        build_params[std::string(param_keys[i])] = param_values[i];
                    }
                }
            }

            std::vector<uint> plantIDs = plantarch->buildPlantCanopyFromLibrary(center, spacing, count, age, germination_rate, build_params);

            // Convert vector to static array for return
            static thread_local std::vector<unsigned int> static_result;
            static_result = plantIDs;
            *plant_ids = static_result.data();
            *num_plants = static_result.size();

            return 0;
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (PlantArchitecture::buildPlantCanopyFromLibrary): ") + e.what());
            if (num_plants) *num_plants = 0;
            return -1;
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (PlantArchitecture::buildPlantCanopyFromLibrary): Unknown error building plant canopy.");
            if (num_plants) *num_plants = 0;
            return -1;
        }
    }

    // Attraction points steer shoot growth toward target locations (trellis wires, training
    // targets). plantID < 0 selects the global form, which applies to every plant; a
    // non-negative plantID selects the per-plant form. The two C++ overloads carry different
    // default view half-angles (45 vs 80 degrees), so the caller always passes one explicitly.
    PYHELIOS_API int enableAttractionPoints(PlantArchitecture* plantarch, int plantID, float* points, int point_count, float view_half_angle_deg, float look_ahead_distance, float attraction_weight) {
        try {
            clearError();
            if (!plantarch) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "PlantArchitecture pointer is null");
                return -1;
            }
            if (!points && point_count > 0) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Attraction point array is null");
                return -1;
            }
            if (point_count < 0) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Attraction point count cannot be negative");
                return -1;
            }

            std::vector<helios::vec3> pts;
            pts.reserve(point_count);
            for (int i = 0; i < point_count; i++) {
                pts.emplace_back(points[3 * i], points[3 * i + 1], points[3 * i + 2]);
            }

            if (plantID < 0) {
                plantarch->enableAttractionPoints(pts, view_half_angle_deg, look_ahead_distance, attraction_weight);
            } else {
                plantarch->enableAttractionPoints(static_cast<uint>(plantID), pts, view_half_angle_deg, look_ahead_distance, attraction_weight);
            }
            return 0;
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (PlantArchitecture::enableAttractionPoints): ") + e.what());
            return -1;
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (PlantArchitecture::enableAttractionPoints): Unknown error.");
            return -1;
        }
    }

    PYHELIOS_API int disableAttractionPoints(PlantArchitecture* plantarch, int plantID) {
        try {
            clearError();
            if (!plantarch) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "PlantArchitecture pointer is null");
                return -1;
            }

            if (plantID < 0) {
                plantarch->disableAttractionPoints();
            } else {
                plantarch->disableAttractionPoints(static_cast<uint>(plantID));
            }
            return 0;
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (PlantArchitecture::disableAttractionPoints): ") + e.what());
            return -1;
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (PlantArchitecture::disableAttractionPoints): Unknown error.");
            return -1;
        }
    }

    PYHELIOS_API int updateAttractionPoints(PlantArchitecture* plantarch, int plantID, float* points, int point_count) {
        try {
            clearError();
            if (!plantarch) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "PlantArchitecture pointer is null");
                return -1;
            }
            if (!points && point_count > 0) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Attraction point array is null");
                return -1;
            }
            if (point_count < 0) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Attraction point count cannot be negative");
                return -1;
            }

            std::vector<helios::vec3> pts;
            pts.reserve(point_count);
            for (int i = 0; i < point_count; i++) {
                pts.emplace_back(points[3 * i], points[3 * i + 1], points[3 * i + 2]);
            }

            if (plantID < 0) {
                plantarch->updateAttractionPoints(pts);
            } else {
                plantarch->updateAttractionPoints(static_cast<uint>(plantID), pts);
            }
            return 0;
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (PlantArchitecture::updateAttractionPoints): ") + e.what());
            return -1;
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (PlantArchitecture::updateAttractionPoints): Unknown error.");
            return -1;
        }
    }

    PYHELIOS_API int appendAttractionPoints(PlantArchitecture* plantarch, int plantID, float* points, int point_count) {
        try {
            clearError();
            if (!plantarch) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "PlantArchitecture pointer is null");
                return -1;
            }
            if (!points && point_count > 0) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Attraction point array is null");
                return -1;
            }
            if (point_count < 0) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Attraction point count cannot be negative");
                return -1;
            }

            std::vector<helios::vec3> pts;
            pts.reserve(point_count);
            for (int i = 0; i < point_count; i++) {
                pts.emplace_back(points[3 * i], points[3 * i + 1], points[3 * i + 2]);
            }

            if (plantID < 0) {
                plantarch->appendAttractionPoints(pts);
            } else {
                plantarch->appendAttractionPoints(static_cast<uint>(plantID), pts);
            }
            return 0;
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (PlantArchitecture::appendAttractionPoints): ") + e.what());
            return -1;
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (PlantArchitecture::appendAttractionPoints): Unknown error.");
            return -1;
        }
    }

    PYHELIOS_API int setAttractionParameters(PlantArchitecture* plantarch, int plantID, float view_half_angle_deg, float look_ahead_distance, float attraction_weight, float obstacle_reduction_factor) {
        try {
            clearError();
            if (!plantarch) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "PlantArchitecture pointer is null");
                return -1;
            }

            if (plantID < 0) {
                plantarch->setAttractionParameters(view_half_angle_deg, look_ahead_distance, attraction_weight, obstacle_reduction_factor);
            } else {
                plantarch->setAttractionParameters(static_cast<uint>(plantID), view_half_angle_deg, look_ahead_distance, attraction_weight, obstacle_reduction_factor);
            }
            return 0;
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (PlantArchitecture::setAttractionParameters): ") + e.what());
            return -1;
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (PlantArchitecture::setAttractionParameters): Unknown error.");
            return -1;
        }
    }

    PYHELIOS_API int advanceTimeForPlant(PlantArchitecture* plantarch, unsigned int plantID, float dt) {
        try {
            clearError();
            if (!plantarch) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "PlantArchitecture pointer is null");
                return -1;
            }
            if (dt < 0) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Time step cannot be negative");
                return -1;
            }

            plantarch->advanceTime(plantID, dt);
            return 0;
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (PlantArchitecture::advanceTime): ") + e.what());
            return -1;
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (PlantArchitecture::advanceTime): Unknown error advancing time.");
            return -1;
        }
    }

    PYHELIOS_API int advanceTimeForPlants(PlantArchitecture* plantarch, unsigned int* plantIDs, int count, float dt) {
        try {
            clearError();
            if (!plantarch) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "PlantArchitecture pointer is null");
                return -1;
            }
            if (!plantIDs && count > 0) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Plant ID array is null");
                return -1;
            }
            if (count < 0) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Plant ID count cannot be negative");
                return -1;
            }
            if (dt < 0) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Time step cannot be negative");
                return -1;
            }

            std::vector<uint> ids(plantIDs, plantIDs + count);
            plantarch->advanceTime(ids, dt);
            return 0;
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (PlantArchitecture::advanceTime): ") + e.what());
            return -1;
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (PlantArchitecture::advanceTime): Unknown error advancing time.");
            return -1;
        }
    }

    PYHELIOS_API int advanceTimeYears(PlantArchitecture* plantarch, int time_step_years, float time_step_days) {
        try {
            clearError();
            if (!plantarch) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "PlantArchitecture pointer is null");
                return -1;
            }
            if (time_step_years < 0) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Time step cannot be negative");
                return -1;
            }
            if (time_step_days < 0) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Time step cannot be negative");
                return -1;
            }

            plantarch->advanceTime(time_step_years, time_step_days);
            return 0;
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (PlantArchitecture::advanceTime): ") + e.what());
            return -1;
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (PlantArchitecture::advanceTime): Unknown error advancing time.");
            return -1;
        }
    }

    PYHELIOS_API int advanceTime(PlantArchitecture* plantarch, float dt) {
        try {
            clearError();
            if (!plantarch) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "PlantArchitecture pointer is null");
                return -1;
            }
            if (dt < 0) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Time step cannot be negative");
                return -1;
            }

            plantarch->advanceTime(dt);
            return 0;
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (PlantArchitecture::advanceTime): ") + e.what());
            return -1;
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (PlantArchitecture::advanceTime): Unknown error advancing time.");
            return -1;
        }
    }

    // Plant query functions
    PYHELIOS_API int listShootTypeLabels(PlantArchitecture* plantarch, const char* plant_model_name, int plantID, char*** labels, int* count) {
        try {
            clearError();
            if (!plantarch) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "PlantArchitecture pointer is null");
                return -1;
            }
            if (!labels || !count) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Output parameters are null");
                return -1;
            }

            // Three overloads share one entry point: a model name queries that model without
            // disturbing the loaded one, a non-negative plantID queries a built instance, and
            // neither queries whatever model is currently loaded.
            std::vector<std::string> shoot_labels;
            if (plant_model_name != nullptr) {
                shoot_labels = plantarch->listShootTypeLabels(std::string(plant_model_name));
            } else if (plantID >= 0) {
                shoot_labels = plantarch->listShootTypeLabels(static_cast<uint>(plantID));
            } else {
                shoot_labels = plantarch->listShootTypeLabels();
            }

            *count = shoot_labels.size();
            *labels = new char*[shoot_labels.size()];
            for (size_t i = 0; i < shoot_labels.size(); i++) {
                (*labels)[i] = new char[shoot_labels[i].length() + 1];
                strcpy((*labels)[i], shoot_labels[i].c_str());
            }

            return 0;
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (PlantArchitecture::listShootTypeLabels): ") + e.what());
            if (count) *count = 0;
            return -1;
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (PlantArchitecture::listShootTypeLabels): Unknown error.");
            if (count) *count = 0;
            return -1;
        }
    }

    PYHELIOS_API int getAvailablePlantModels(PlantArchitecture* plantarch, char*** model_names, int* count) {
        try {
            clearError();
            if (!plantarch) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "PlantArchitecture pointer is null");
                return -1;
            }
            if (!model_names || !count) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Output parameters are null");
                return -1;
            }

            std::vector<std::string> models = plantarch->getAvailablePlantModels();
            *count = models.size();

            // Allocate array of string pointers
            *model_names = new char*[models.size()];

            // Copy each string
            for (size_t i = 0; i < models.size(); i++) {
                (*model_names)[i] = new char[models[i].length() + 1];
                strcpy((*model_names)[i], models[i].c_str());
            }

            return 0;
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (PlantArchitecture::getAvailablePlantModels): ") + e.what());
            if (count) *count = 0;
            return -1;
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (PlantArchitecture::getAvailablePlantModels): Unknown error getting available plant models.");
            if (count) *count = 0;
            return -1;
        }
    }

    PYHELIOS_API unsigned int* getAllPlantObjectIDs(PlantArchitecture* plantarch, unsigned int plantID, int* count) {
        try {
            clearError();
            if (!plantarch) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "PlantArchitecture pointer is null");
                if (count) *count = 0;
                return nullptr;
            }
            if (!count) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Count pointer is null");
                return nullptr;
            }

            std::vector<uint> objectIDs = plantarch->getAllPlantObjectIDs(plantID);

            // Convert vector to static array for return
            static thread_local std::vector<unsigned int> static_result;
            static_result = objectIDs;
            *count = static_result.size();

            return static_result.data();
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (PlantArchitecture::getAllPlantObjectIDs): ") + e.what());
            if (count) *count = 0;
            return nullptr;
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (PlantArchitecture::getAllPlantObjectIDs): Unknown error getting plant object IDs.");
            if (count) *count = 0;
            return nullptr;
        }
    }

    PYHELIOS_API unsigned int* getPlantLeafObjectIDs(PlantArchitecture* plantarch, unsigned int plantID, int* count) {
        try {
            clearError();
            if (!plantarch) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "PlantArchitecture pointer is null");
                if (count) *count = 0;
                return nullptr;
            }
            if (!count) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Count pointer is null");
                return nullptr;
            }

            std::vector<uint> objectIDs = plantarch->getPlantLeafObjectIDs(plantID);

            static thread_local std::vector<unsigned int> static_result;
            static_result = objectIDs;
            *count = static_result.size();

            return static_result.data();
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (PlantArchitecture::getPlantLeafObjectIDs): ") + e.what());
            if (count) *count = 0;
            return nullptr;
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (PlantArchitecture::getPlantLeafObjectIDs): Unknown error getting leaf object IDs.");
            if (count) *count = 0;
            return nullptr;
        }
    }

    PYHELIOS_API unsigned int* getPlantPetioleObjectIDs(PlantArchitecture* plantarch, unsigned int plantID, int* count) {
        try {
            clearError();
            if (!plantarch) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "PlantArchitecture pointer is null");
                if (count) *count = 0;
                return nullptr;
            }
            if (!count) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Count pointer is null");
                return nullptr;
            }

            std::vector<uint> objectIDs = plantarch->getPlantPetioleObjectIDs(plantID);

            static thread_local std::vector<unsigned int> static_result;
            static_result = objectIDs;
            *count = static_result.size();

            return static_result.data();
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (PlantArchitecture::getPlantPetioleObjectIDs): ") + e.what());
            if (count) *count = 0;
            return nullptr;
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (PlantArchitecture::getPlantPetioleObjectIDs): Unknown error getting petiole object IDs.");
            if (count) *count = 0;
            return nullptr;
        }
    }

    PYHELIOS_API unsigned int* getPlantPeduncleObjectIDs(PlantArchitecture* plantarch, unsigned int plantID, int* count) {
        try {
            clearError();
            if (!plantarch) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "PlantArchitecture pointer is null");
                if (count) *count = 0;
                return nullptr;
            }
            if (!count) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Count pointer is null");
                return nullptr;
            }

            std::vector<uint> objectIDs = plantarch->getPlantPeduncleObjectIDs(plantID);

            static thread_local std::vector<unsigned int> static_result;
            static_result = objectIDs;
            *count = static_result.size();

            return static_result.data();
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (PlantArchitecture::getPlantPeduncleObjectIDs): ") + e.what());
            if (count) *count = 0;
            return nullptr;
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (PlantArchitecture::getPlantPeduncleObjectIDs): Unknown error getting peduncle object IDs.");
            if (count) *count = 0;
            return nullptr;
        }
    }

    PYHELIOS_API unsigned int* getPlantFlowerObjectIDs(PlantArchitecture* plantarch, unsigned int plantID, int* count) {
        try {
            clearError();
            if (!plantarch) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "PlantArchitecture pointer is null");
                if (count) *count = 0;
                return nullptr;
            }
            if (!count) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Count pointer is null");
                return nullptr;
            }

            std::vector<uint> objectIDs = plantarch->getPlantFlowerObjectIDs(plantID);

            static thread_local std::vector<unsigned int> static_result;
            static_result = objectIDs;
            *count = static_result.size();

            return static_result.data();
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (PlantArchitecture::getPlantFlowerObjectIDs): ") + e.what());
            if (count) *count = 0;
            return nullptr;
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (PlantArchitecture::getPlantFlowerObjectIDs): Unknown error getting flower object IDs.");
            if (count) *count = 0;
            return nullptr;
        }
    }

    PYHELIOS_API unsigned int* plantArchitectureGetAllUUIDs(PlantArchitecture* plantarch, int* count) {
        try {
            clearError();
            if (!plantarch) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "PlantArchitecture pointer is null");
                if (count) *count = 0;
                return nullptr;
            }
            if (!count) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Count pointer is null");
                return nullptr;
            }

            std::vector<uint> ids = plantarch->getAllUUIDs();

            static thread_local std::vector<unsigned int> static_result;
            static_result = ids;
            *count = static_result.size();

            return static_result.data();
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (PlantArchitecture::getAllUUIDs): ") + e.what());
            if (count) *count = 0;
            return nullptr;
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (PlantArchitecture::getAllUUIDs): Unknown error getting all plant primitive UUIDs.");
            if (count) *count = 0;
            return nullptr;
        }
    }

    PYHELIOS_API unsigned int* getAllLeafUUIDs(PlantArchitecture* plantarch, int* count) {
        try {
            clearError();
            if (!plantarch) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "PlantArchitecture pointer is null");
                if (count) *count = 0;
                return nullptr;
            }
            if (!count) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Count pointer is null");
                return nullptr;
            }

            std::vector<uint> ids = plantarch->getAllLeafUUIDs();

            static thread_local std::vector<unsigned int> static_result;
            static_result = ids;
            *count = static_result.size();

            return static_result.data();
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (PlantArchitecture::getAllLeafUUIDs): ") + e.what());
            if (count) *count = 0;
            return nullptr;
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (PlantArchitecture::getAllLeafUUIDs): Unknown error getting all leaf primitive UUIDs.");
            if (count) *count = 0;
            return nullptr;
        }
    }

    PYHELIOS_API unsigned int* getAllInternodeUUIDs(PlantArchitecture* plantarch, int* count) {
        try {
            clearError();
            if (!plantarch) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "PlantArchitecture pointer is null");
                if (count) *count = 0;
                return nullptr;
            }
            if (!count) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Count pointer is null");
                return nullptr;
            }

            std::vector<uint> ids = plantarch->getAllInternodeUUIDs();

            static thread_local std::vector<unsigned int> static_result;
            static_result = ids;
            *count = static_result.size();

            return static_result.data();
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (PlantArchitecture::getAllInternodeUUIDs): ") + e.what());
            if (count) *count = 0;
            return nullptr;
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (PlantArchitecture::getAllInternodeUUIDs): Unknown error getting all internode primitive UUIDs.");
            if (count) *count = 0;
            return nullptr;
        }
    }

    PYHELIOS_API unsigned int* getAllPetioleUUIDs(PlantArchitecture* plantarch, int* count) {
        try {
            clearError();
            if (!plantarch) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "PlantArchitecture pointer is null");
                if (count) *count = 0;
                return nullptr;
            }
            if (!count) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Count pointer is null");
                return nullptr;
            }

            std::vector<uint> ids = plantarch->getAllPetioleUUIDs();

            static thread_local std::vector<unsigned int> static_result;
            static_result = ids;
            *count = static_result.size();

            return static_result.data();
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (PlantArchitecture::getAllPetioleUUIDs): ") + e.what());
            if (count) *count = 0;
            return nullptr;
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (PlantArchitecture::getAllPetioleUUIDs): Unknown error getting all petiole primitive UUIDs.");
            if (count) *count = 0;
            return nullptr;
        }
    }

    PYHELIOS_API unsigned int* getAllPeduncleUUIDs(PlantArchitecture* plantarch, int* count) {
        try {
            clearError();
            if (!plantarch) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "PlantArchitecture pointer is null");
                if (count) *count = 0;
                return nullptr;
            }
            if (!count) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Count pointer is null");
                return nullptr;
            }

            std::vector<uint> ids = plantarch->getAllPeduncleUUIDs();

            static thread_local std::vector<unsigned int> static_result;
            static_result = ids;
            *count = static_result.size();

            return static_result.data();
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (PlantArchitecture::getAllPeduncleUUIDs): ") + e.what());
            if (count) *count = 0;
            return nullptr;
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (PlantArchitecture::getAllPeduncleUUIDs): Unknown error getting all peduncle primitive UUIDs.");
            if (count) *count = 0;
            return nullptr;
        }
    }

    PYHELIOS_API unsigned int* getAllFlowerUUIDs(PlantArchitecture* plantarch, int* count) {
        try {
            clearError();
            if (!plantarch) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "PlantArchitecture pointer is null");
                if (count) *count = 0;
                return nullptr;
            }
            if (!count) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Count pointer is null");
                return nullptr;
            }

            std::vector<uint> ids = plantarch->getAllFlowerUUIDs();

            static thread_local std::vector<unsigned int> static_result;
            static_result = ids;
            *count = static_result.size();

            return static_result.data();
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (PlantArchitecture::getAllFlowerUUIDs): ") + e.what());
            if (count) *count = 0;
            return nullptr;
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (PlantArchitecture::getAllFlowerUUIDs): Unknown error getting all flower primitive UUIDs.");
            if (count) *count = 0;
            return nullptr;
        }
    }

    PYHELIOS_API unsigned int* getAllFruitUUIDs(PlantArchitecture* plantarch, int* count) {
        try {
            clearError();
            if (!plantarch) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "PlantArchitecture pointer is null");
                if (count) *count = 0;
                return nullptr;
            }
            if (!count) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Count pointer is null");
                return nullptr;
            }

            std::vector<uint> ids = plantarch->getAllFruitUUIDs();

            static thread_local std::vector<unsigned int> static_result;
            static_result = ids;
            *count = static_result.size();

            return static_result.data();
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (PlantArchitecture::getAllFruitUUIDs): ") + e.what());
            if (count) *count = 0;
            return nullptr;
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (PlantArchitecture::getAllFruitUUIDs): Unknown error getting all fruit primitive UUIDs.");
            if (count) *count = 0;
            return nullptr;
        }
    }

    PYHELIOS_API unsigned int* plantArchitectureGetAllObjectIDs(PlantArchitecture* plantarch, int* count) {
        try {
            clearError();
            if (!plantarch) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "PlantArchitecture pointer is null");
                if (count) *count = 0;
                return nullptr;
            }
            if (!count) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Count pointer is null");
                return nullptr;
            }

            std::vector<uint> ids = plantarch->getAllObjectIDs();

            static thread_local std::vector<unsigned int> static_result;
            static_result = ids;
            *count = static_result.size();

            return static_result.data();
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (PlantArchitecture::getAllObjectIDs): ") + e.what());
            if (count) *count = 0;
            return nullptr;
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (PlantArchitecture::getAllObjectIDs): Unknown error getting all plant object IDs.");
            if (count) *count = 0;
            return nullptr;
        }
    }

    PYHELIOS_API unsigned int* getAllPlantIDs(PlantArchitecture* plantarch, int* count) {
        try {
            clearError();
            if (!plantarch) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "PlantArchitecture pointer is null");
                if (count) *count = 0;
                return nullptr;
            }
            if (!count) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Count pointer is null");
                return nullptr;
            }

            std::vector<uint> ids = plantarch->getAllPlantIDs();

            static thread_local std::vector<unsigned int> static_result;
            static_result = ids;
            *count = static_result.size();

            return static_result.data();
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (PlantArchitecture::getAllPlantIDs): ") + e.what());
            if (count) *count = 0;
            return nullptr;
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (PlantArchitecture::getAllPlantIDs): Unknown error getting all plant instance IDs.");
            if (count) *count = 0;
            return nullptr;
        }
    }

    PYHELIOS_API unsigned int* getPlantFruitObjectIDs(PlantArchitecture* plantarch, unsigned int plantID, int* count) {
        try {
            clearError();
            if (!plantarch) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "PlantArchitecture pointer is null");
                if (count) *count = 0;
                return nullptr;
            }
            if (!count) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Count pointer is null");
                return nullptr;
            }

            std::vector<uint> objectIDs = plantarch->getPlantFruitObjectIDs(plantID);

            static thread_local std::vector<unsigned int> static_result;
            static_result = objectIDs;
            *count = static_result.size();

            return static_result.data();
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (PlantArchitecture::getPlantFruitObjectIDs): ") + e.what());
            if (count) *count = 0;
            return nullptr;
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (PlantArchitecture::getPlantFruitObjectIDs): Unknown error getting fruit object IDs.");
            if (count) *count = 0;
            return nullptr;
        }
    }

    PYHELIOS_API float* getPlantLeafBases(PlantArchitecture* plantarch, unsigned int plantID, int* count) {
        try {
            clearError();
            if (!plantarch) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "PlantArchitecture pointer is null");
                if (count) *count = 0;
                return nullptr;
            }
            if (!count) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Count pointer is null");
                return nullptr;
            }

            std::vector<helios::vec3> bases = plantarch->getPlantLeafBases(plantID);

            // Flattened as x,y,z triples; *count is the number of vec3 values, not floats.
            static thread_local std::vector<float> static_result;
            static_result.clear();
            static_result.reserve(bases.size() * 3);
            for (const helios::vec3& base : bases) {
                static_result.push_back(base.x);
                static_result.push_back(base.y);
                static_result.push_back(base.z);
            }
            *count = static_cast<int>(bases.size());

            return static_result.data();
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (PlantArchitecture::getPlantLeafBases): ") + e.what());
            if (count) *count = 0;
            return nullptr;
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (PlantArchitecture::getPlantLeafBases): Unknown error getting leaf bases.");
            if (count) *count = 0;
            return nullptr;
        }
    }

    PYHELIOS_API unsigned int* getAllPlantUUIDs(PlantArchitecture* plantarch, unsigned int plantID, bool include_hidden, int* count) {
        try {
            clearError();
            if (!plantarch) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "PlantArchitecture pointer is null");
                if (count) *count = 0;
                return nullptr;
            }
            if (!count) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Count pointer is null");
                return nullptr;
            }

            std::vector<uint> uuids = plantarch->getAllPlantUUIDs(plantID, include_hidden);

            // Convert vector to static array for return
            static thread_local std::vector<unsigned int> static_result;
            static_result = uuids;
            *count = static_result.size();

            return static_result.data();
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (PlantArchitecture::getAllPlantUUIDs): ") + e.what());
            if (count) *count = 0;
            return nullptr;
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (PlantArchitecture::getAllPlantUUIDs): Unknown error getting plant UUIDs.");
            if (count) *count = 0;
            return nullptr;
        }
    }

    // Memory cleanup functions
    PYHELIOS_API void freeStringArray(char** strings, int count) {
        if (strings) {
            for (int i = 0; i < count; i++) {
                delete[] strings[i];
            }
            delete[] strings;
        }
    }

    PYHELIOS_API void freeIntArray(unsigned int* array) {
        // Note: For our implementation, arrays are static thread_local,
        // so no explicit cleanup is needed. This function is provided
        // for API consistency and future compatibility.
    }

    // Collision detection functions
    PYHELIOS_API int enableSoftCollisionAvoidance(PlantArchitecture* plantarch, const unsigned int* target_UUIDs, int uuid_count, const unsigned int* target_IDs, int id_count, bool enable_petiole, bool enable_fruit) {
        try {
            clearError();
            if (!plantarch) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "PlantArchitecture pointer is null");
                return -1;
            }

            // Convert arrays to vectors
            std::vector<uint> uuid_vector;
            if (target_UUIDs && uuid_count > 0) {
                uuid_vector.assign(target_UUIDs, target_UUIDs + uuid_count);
            }

            std::vector<uint> id_vector;
            if (target_IDs && id_count > 0) {
                id_vector.assign(target_IDs, target_IDs + id_count);
            }

            plantarch->enableSoftCollisionAvoidance(uuid_vector, id_vector, enable_petiole, enable_fruit);
            return 0;
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (PlantArchitecture::enableSoftCollisionAvoidance): ") + e.what());
            return -1;
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (PlantArchitecture::enableSoftCollisionAvoidance): Unknown error enabling collision avoidance.");
            return -1;
        }
    }

    PYHELIOS_API void plantArchitectureEnableMessages(PlantArchitecture* plantarch) {
        try {
            clearError();
            if (!plantarch) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "PlantArchitecture pointer is null");
                return;
            }

            plantarch->enableMessages();
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (PlantArchitecture::enableMessages): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (PlantArchitecture::enableMessages): Unknown error enabling messages.");
        }
    }

    PYHELIOS_API void plantArchitectureDisableMessages(PlantArchitecture* plantarch) {
        try {
            clearError();
            if (!plantarch) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "PlantArchitecture pointer is null");
                return;
            }

            plantarch->disableMessages();
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (PlantArchitecture::disableMessages): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (PlantArchitecture::disableMessages): Unknown error disabling messages.");
        }
    }

    PYHELIOS_API void enableGroundClipping(PlantArchitecture* plantarch, float ground_height) {
        try {
            clearError();
            if (!plantarch) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "PlantArchitecture pointer is null");
                return;
            }

            plantarch->enableGroundClipping(ground_height);
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (PlantArchitecture::enableGroundClipping): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (PlantArchitecture::enableGroundClipping): Unknown error enabling ground clipping.");
        }
    }

    PYHELIOS_API void disableCollisionDetection(PlantArchitecture* plantarch) {
        try {
            clearError();
            if (!plantarch) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "PlantArchitecture pointer is null");
                return;
            }

            plantarch->disableCollisionDetection();
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (PlantArchitecture::disableCollisionDetection): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (PlantArchitecture::disableCollisionDetection): Unknown error disabling collision detection.");
        }
    }

    PYHELIOS_API void setSoftCollisionAvoidanceParameters(PlantArchitecture* plantarch, float view_half_angle_deg, float look_ahead_distance, int sample_count, float inertia_weight) {
        try {
            clearError();
            if (!plantarch) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "PlantArchitecture pointer is null");
                return;
            }

            plantarch->setSoftCollisionAvoidanceParameters(view_half_angle_deg, look_ahead_distance, sample_count, inertia_weight);
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (PlantArchitecture::setSoftCollisionAvoidanceParameters): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (PlantArchitecture::setSoftCollisionAvoidanceParameters): Unknown error setting collision parameters.");
        }
    }

    PYHELIOS_API void setCollisionRelevantOrgans(PlantArchitecture* plantarch, bool include_internodes, bool include_leaves, bool include_petioles, bool include_flowers, bool include_fruit) {
        try {
            clearError();
            if (!plantarch) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "PlantArchitecture pointer is null");
                return;
            }

            plantarch->setCollisionRelevantOrgans(include_internodes, include_leaves, include_petioles, include_flowers, include_fruit);
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (PlantArchitecture::setCollisionRelevantOrgans): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (PlantArchitecture::setCollisionRelevantOrgans): Unknown error setting collision-relevant organs.");
        }
    }

    PYHELIOS_API int enableSolidObstacleAvoidance(PlantArchitecture* plantarch, const unsigned int* obstacle_UUIDs, int uuid_count, float avoidance_distance, bool enable_fruit_adjustment, bool enable_obstacle_pruning) {
        try {
            clearError();
            if (!plantarch) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "PlantArchitecture pointer is null");
                return -1;
            }

            // Convert array to vector
            std::vector<uint> uuid_vector;
            if (obstacle_UUIDs && uuid_count > 0) {
                uuid_vector.assign(obstacle_UUIDs, obstacle_UUIDs + uuid_count);
            }

            plantarch->enableSolidObstacleAvoidance(uuid_vector, avoidance_distance, enable_fruit_adjustment, enable_obstacle_pruning);
            return 0;
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (PlantArchitecture::enableSolidObstacleAvoidance): ") + e.what());
            return -1;
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (PlantArchitecture::enableSolidObstacleAvoidance): Unknown error enabling solid obstacle avoidance.");
            return -1;
        }
    }

    PYHELIOS_API int setStaticObstacles(PlantArchitecture* plantarch, const unsigned int* target_UUIDs, int uuid_count) {
        try {
            clearError();
            if (!plantarch) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "PlantArchitecture pointer is null");
                return -1;
            }

            // Convert array to vector
            std::vector<uint> uuid_vector;
            if (target_UUIDs && uuid_count > 0) {
                uuid_vector.assign(target_UUIDs, target_UUIDs + uuid_count);
            }

            plantarch->setStaticObstacles(uuid_vector);
            return 0;
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (PlantArchitecture::setStaticObstacles): ") + e.what());
            return -1;
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (PlantArchitecture::setStaticObstacles): Unknown error setting static obstacles.");
            return -1;
        }
    }

    PYHELIOS_API unsigned int* getPlantCollisionRelevantObjectIDs(PlantArchitecture* plantarch, unsigned int plant_id, int* count) {
        try {
            clearError();
            if (!plantarch) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "PlantArchitecture pointer is null");
                if (count) *count = 0;
                return nullptr;
            }
            if (!count) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Count pointer is null");
                return nullptr;
            }

            std::vector<uint> objectIDs = plantarch->getPlantCollisionRelevantObjectIDs(plant_id);

            // Convert vector to static array for return
            static thread_local std::vector<unsigned int> static_result;
            static_result = objectIDs;
            *count = static_result.size();

            return static_result.data();
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (PlantArchitecture::getPlantCollisionRelevantObjectIDs): ") + e.what());
            if (count) *count = 0;
            return nullptr;
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (PlantArchitecture::getPlantCollisionRelevantObjectIDs): Unknown error getting collision-relevant object IDs.");
            if (count) *count = 0;
            return nullptr;
        }
    }

    // File I/O functions
    PYHELIOS_API int writePlantMeshVertices(PlantArchitecture* plantarch, unsigned int plantID, const char* filename) {
        try {
            clearError();
            if (!plantarch) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "PlantArchitecture pointer is null");
                return -1;
            }
            if (!filename) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Filename is null");
                return -1;
            }
            if (std::strlen(filename) == 0) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Filename cannot be empty");
                return -1;
            }

            plantarch->writePlantMeshVertices(plantID, std::string(filename));
            return 0;
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (PlantArchitecture::writePlantMeshVertices): ") + e.what());
            return -1;
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (PlantArchitecture::writePlantMeshVertices): Unknown error writing plant mesh vertices.");
            return -1;
        }
    }

    PYHELIOS_API int writePlantStructureXML(PlantArchitecture* plantarch, unsigned int plantID, const char* filename) {
        try {
            clearError();
            if (!plantarch) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "PlantArchitecture pointer is null");
                return -1;
            }
            if (!filename) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Filename is null");
                return -1;
            }
            if (std::strlen(filename) == 0) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Filename cannot be empty");
                return -1;
            }

            plantarch->writePlantStructureXML(plantID, std::string(filename));
            return 0;
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (PlantArchitecture::writePlantStructureXML): ") + e.what());
            return -1;
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (PlantArchitecture::writePlantStructureXML): Unknown error writing plant structure XML.");
            return -1;
        }
    }

    PYHELIOS_API int writeQSMCylinderFile(PlantArchitecture* plantarch, unsigned int plantID, const char* filename) {
        try {
            clearError();
            if (!plantarch) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "PlantArchitecture pointer is null");
                return -1;
            }
            if (!filename) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Filename is null");
                return -1;
            }
            if (std::strlen(filename) == 0) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Filename cannot be empty");
                return -1;
            }

            plantarch->writeQSMCylinderFile(plantID, std::string(filename));
            return 0;
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (PlantArchitecture::writeQSMCylinderFile): ") + e.what());
            return -1;
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (PlantArchitecture::writeQSMCylinderFile): Unknown error writing QSM cylinder file.");
            return -1;
        }
    }

    PYHELIOS_API int writePlantStructureUSD(PlantArchitecture* plantarch, unsigned int plantID, const char* filename,
                                             float elastic_modulus, float wood_density, float damping_time_constant,
                                             float armature_stability_ratio, float physics_steps_per_second,
                                             float static_friction, float dynamic_friction, float restitution,
                                             float organ_spring_stiffness, float organ_spring_damping,
                                             float leaf_mass_per_area, float fruit_mass, float flower_mass,
                                             unsigned int solver_position_iterations, float min_segment_length) {
        try {
            clearError();
            if (!plantarch) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "PlantArchitecture pointer is null");
                return -1;
            }
            if (!filename || std::strlen(filename) == 0) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Filename cannot be null or empty");
                return -1;
            }

            USDExportParameters params;
            params.elastic_modulus = elastic_modulus;
            params.wood_density = wood_density;
            params.damping_time_constant = damping_time_constant;
            params.armature_stability_ratio = armature_stability_ratio;
            params.physics_steps_per_second = physics_steps_per_second;
            params.static_friction = static_friction;
            params.dynamic_friction = dynamic_friction;
            params.restitution = restitution;
            params.organ_spring_stiffness = organ_spring_stiffness;
            params.organ_spring_damping = organ_spring_damping;
            params.leaf_mass_per_area = leaf_mass_per_area;
            params.fruit_mass = fruit_mass;
            params.flower_mass = flower_mass;
            params.solver_position_iterations = solver_position_iterations;
            params.min_segment_length = min_segment_length;

            plantarch->writePlantStructureUSD(plantID, std::string(filename), params);
            return 0;
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (PlantArchitecture::writePlantStructureUSD): ") + e.what());
            return -1;
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (PlantArchitecture::writePlantStructureUSD): Unknown error writing USD file.");
            return -1;
        }
    }

    PYHELIOS_API int registerGrowthFrame(PlantArchitecture* plantarch, unsigned int plantID, float min_segment_length) {
        try {
            clearError();
            if (!plantarch) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "PlantArchitecture pointer is null");
                return -1;
            }
            plantarch->registerGrowthFrame(plantID, min_segment_length);
            return 0;
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (PlantArchitecture::registerGrowthFrame): ") + e.what());
            return -1;
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (PlantArchitecture::registerGrowthFrame): Unknown error.");
            return -1;
        }
    }

    PYHELIOS_API int writePlantGrowthUSD(PlantArchitecture* plantarch, unsigned int plantID, const char* filename, float seconds_per_frame) {
        try {
            clearError();
            if (!plantarch) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "PlantArchitecture pointer is null");
                return -1;
            }
            if (!filename || std::strlen(filename) == 0) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Filename cannot be null or empty");
                return -1;
            }
            plantarch->writePlantGrowthUSD(plantID, std::string(filename), seconds_per_frame);
            return 0;
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (PlantArchitecture::writePlantGrowthUSD): ") + e.what());
            return -1;
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (PlantArchitecture::writePlantGrowthUSD): Unknown error.");
            return -1;
        }
    }

    PYHELIOS_API int clearGrowthFrames(PlantArchitecture* plantarch, unsigned int plantID) {
        try {
            clearError();
            if (!plantarch) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "PlantArchitecture pointer is null");
                return -1;
            }
            plantarch->clearGrowthFrames(plantID);
            return 0;
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (PlantArchitecture::clearGrowthFrames): ") + e.what());
            return -1;
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (PlantArchitecture::clearGrowthFrames): Unknown error.");
            return -1;
        }
    }

    PYHELIOS_API unsigned int getGrowthFrameCount(PlantArchitecture* plantarch, unsigned int plantID) {
        try {
            clearError();
            if (!plantarch) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "PlantArchitecture pointer is null");
                return 0;
            }
            return plantarch->getGrowthFrameCount(plantID);
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (PlantArchitecture::getGrowthFrameCount): ") + e.what());
            return 0;
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (PlantArchitecture::getGrowthFrameCount): Unknown error.");
            return 0;
        }
    }

    PYHELIOS_API int readPlantStructureXML(PlantArchitecture* plantarch, const char* filename, bool quiet, unsigned int** plant_ids, int* num_plants) {
        try {
            clearError();
            if (!plantarch) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "PlantArchitecture pointer is null");
                if (num_plants) *num_plants = 0;
                return -1;
            }
            if (!filename) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Filename is null");
                if (num_plants) *num_plants = 0;
                return -1;
            }
            if (std::strlen(filename) == 0) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Filename cannot be empty");
                if (num_plants) *num_plants = 0;
                return -1;
            }
            if (!plant_ids || !num_plants) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Output parameters are null");
                if (num_plants) *num_plants = 0;
                return -1;
            }

            std::vector<uint> plantIDs = plantarch->readPlantStructureXML(std::string(filename), quiet);

            // Convert vector to static array for return
            static thread_local std::vector<unsigned int> static_result;
            static_result = plantIDs;
            *plant_ids = static_result.data();
            *num_plants = static_result.size();

            return 0;
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (PlantArchitecture::readPlantStructureXML): ") + e.what());
            if (num_plants) *num_plants = 0;
            return -1;
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (PlantArchitecture::readPlantStructureXML): Unknown error reading plant structure XML.");
            if (num_plants) *num_plants = 0;
            return -1;
        }
    }

    // Custom plant building functions
    PYHELIOS_API unsigned int addPlantInstance(PlantArchitecture* plantarch, float* base_position, float current_age) {
        try {
            clearError();
            if (!plantarch) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "PlantArchitecture pointer is null");
                return 0;
            }
            if (!base_position) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Base position array is null");
                return 0;
            }
            if (current_age < 0) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Current age cannot be negative");
                return 0;
            }

            helios::vec3 position(base_position[0], base_position[1], base_position[2]);
            return plantarch->addPlantInstance(position, current_age);
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (PlantArchitecture::addPlantInstance): ") + e.what());
            return 0;
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (PlantArchitecture::addPlantInstance): Unknown error adding plant instance.");
            return 0;
        }
    }

    PYHELIOS_API int deletePlantInstance(PlantArchitecture* plantarch, unsigned int plantID) {
        try {
            clearError();
            if (!plantarch) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "PlantArchitecture pointer is null");
                return -1;
            }

            plantarch->deletePlantInstance(plantID);
            return 0;
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (PlantArchitecture::deletePlantInstance): ") + e.what());
            return -1;
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (PlantArchitecture::deletePlantInstance): Unknown error deleting plant instance.");
            return -1;
        }
    }

    PYHELIOS_API unsigned int addBaseStemShoot(PlantArchitecture* plantarch, unsigned int plantID, unsigned int current_node_number, float* base_rotation, float internode_radius, float internode_length_max, float internode_length_scale_factor_fraction, float leaf_scale_factor_fraction, float radius_taper, const char* shoot_type_label) {
        try {
            clearError();
            if (!plantarch) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "PlantArchitecture pointer is null");
                return 0;
            }
            if (!base_rotation) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Base rotation array is null");
                return 0;
            }
            if (!shoot_type_label) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Shoot type label is null");
                return 0;
            }
            if (std::strlen(shoot_type_label) == 0) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Shoot type label cannot be empty");
                return 0;
            }

            // Convert rotation array to AxisRotation
            AxisRotation rotation(base_rotation[0], base_rotation[1], base_rotation[2]);

            return plantarch->addBaseStemShoot(plantID, current_node_number, rotation, internode_radius, internode_length_max, internode_length_scale_factor_fraction, leaf_scale_factor_fraction, radius_taper, std::string(shoot_type_label));
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (PlantArchitecture::addBaseStemShoot): ") + e.what());
            return 0;
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (PlantArchitecture::addBaseStemShoot): Unknown error adding base stem shoot.");
            return 0;
        }
    }

    PYHELIOS_API unsigned int appendShoot(PlantArchitecture* plantarch, unsigned int plantID, int parent_shoot_ID, unsigned int current_node_number, float* base_rotation, float internode_radius, float internode_length_max, float internode_length_scale_factor_fraction, float leaf_scale_factor_fraction, float radius_taper, const char* shoot_type_label) {
        try {
            clearError();
            if (!plantarch) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "PlantArchitecture pointer is null");
                return 0;
            }
            if (!base_rotation) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Base rotation array is null");
                return 0;
            }
            if (!shoot_type_label) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Shoot type label is null");
                return 0;
            }
            if (std::strlen(shoot_type_label) == 0) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Shoot type label cannot be empty");
                return 0;
            }

            // Convert rotation array to AxisRotation
            AxisRotation rotation(base_rotation[0], base_rotation[1], base_rotation[2]);

            return plantarch->appendShoot(plantID, parent_shoot_ID, current_node_number, rotation, internode_radius, internode_length_max, internode_length_scale_factor_fraction, leaf_scale_factor_fraction, radius_taper, std::string(shoot_type_label));
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (PlantArchitecture::appendShoot): ") + e.what());
            return 0;
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (PlantArchitecture::appendShoot): Unknown error appending shoot.");
            return 0;
        }
    }

    PYHELIOS_API unsigned int addChildShoot(PlantArchitecture* plantarch, unsigned int plantID, int parent_shoot_ID, unsigned int parent_node_index, unsigned int current_node_number, float* shoot_base_rotation, float internode_radius, float internode_length_max, float internode_length_scale_factor_fraction, float leaf_scale_factor_fraction, float radius_taper, const char* shoot_type_label, unsigned int petiole_index) {
        try {
            clearError();
            if (!plantarch) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "PlantArchitecture pointer is null");
                return 0;
            }
            if (!shoot_base_rotation) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Shoot base rotation array is null");
                return 0;
            }
            if (!shoot_type_label) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Shoot type label is null");
                return 0;
            }
            if (std::strlen(shoot_type_label) == 0) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Shoot type label cannot be empty");
                return 0;
            }

            // Convert rotation array to AxisRotation
            AxisRotation rotation(shoot_base_rotation[0], shoot_base_rotation[1], shoot_base_rotation[2]);

            return plantarch->addChildShoot(plantID, parent_shoot_ID, parent_node_index, current_node_number, rotation, internode_radius, internode_length_max, internode_length_scale_factor_fraction, leaf_scale_factor_fraction, radius_taper, std::string(shoot_type_label), petiole_index);
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (PlantArchitecture::addChildShoot): ") + e.what());
            return 0;
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (PlantArchitecture::addChildShoot): Unknown error adding child shoot.");
            return 0;
        }
    }

    // Get current shoot parameters as JSON
    PYHELIOS_API const char* getCurrentShootParametersJSON(PlantArchitecture* plantarch, const char* shoot_type_label) {
        try {
            clearError();
            if (!plantarch) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "PlantArchitecture pointer is null");
                return nullptr;
            }
            if (!shoot_type_label) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Shoot type label is null");
                return nullptr;
            }

            ShootParameters params = plantarch->getCurrentShootParameters(std::string(shoot_type_label));
            nlohmann::json j = shootParametersToJSON(params);

            static thread_local std::string json_string;
            json_string = j.dump();
            return json_string.c_str();
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (PlantArchitecture::getCurrentShootParameters): ") + e.what());
            return nullptr;
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (PlantArchitecture::getCurrentShootParameters): Unknown error.");
            return nullptr;
        }
    }

    // Carbohydrate model parameters. There is no per-plant getter in the C++ API, so the
    // "get" path returns a default-constructed CarbohydrateParameters serialized to JSON,
    // intended as a template to modify and apply via setPlantCarbohydrateParametersFromJSON.
    PYHELIOS_API const char* getDefaultCarbohydrateParametersJSON() {
        try {
            clearError();
            CarbohydrateParameters params;
            static thread_local std::string json_string;
            json_string = carbohydrateParametersToJSON(params).dump();
            return json_string.c_str();
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (PlantArchitecture::getDefaultCarbohydrateParameters): ") + e.what());
            return nullptr;
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (PlantArchitecture::getDefaultCarbohydrateParameters): Unknown error.");
            return nullptr;
        }
    }

    PYHELIOS_API int setPlantCarbohydrateParametersFromJSON(PlantArchitecture* plantarch, unsigned int plantID, const char* json_params) {
        try {
            clearError();
            if (!plantarch) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "PlantArchitecture pointer is null");
                return -1;
            }
            if (!json_params) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "JSON parameters are null");
                return -1;
            }
            nlohmann::json j = nlohmann::json::parse(json_params);
            CarbohydrateParameters params = jsonToCarbohydrateParameters(j);
            plantarch->setPlantCarbohydrateModelParameters(plantID, params);
            return 0;
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (PlantArchitecture::setPlantCarbohydrateParametersFromJSON): ") + e.what());
            return -1;
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (PlantArchitecture::setPlantCarbohydrateParametersFromJSON): Unknown error.");
            return -1;
        }
    }

    PYHELIOS_API const char* getDefaultNitrogenParametersJSON() {
        try {
            clearError();
            NitrogenParameters params;
            static thread_local std::string json_string;
            json_string = nitrogenParametersToJSON(params).dump();
            return json_string.c_str();
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (PlantArchitecture::getDefaultNitrogenParameters): ") + e.what());
            return nullptr;
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (PlantArchitecture::getDefaultNitrogenParameters): Unknown error.");
            return nullptr;
        }
    }

    PYHELIOS_API int setPlantNitrogenParametersFromJSON(PlantArchitecture* plantarch, unsigned int plantID, const char* json_params) {
        try {
            clearError();
            if (!plantarch) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "PlantArchitecture pointer is null");
                return -1;
            }
            if (!json_params) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "JSON parameters are null");
                return -1;
            }
            nlohmann::json j = nlohmann::json::parse(json_params);
            NitrogenParameters params = jsonToNitrogenParameters(j);
            plantarch->setPlantNitrogenParameters(plantID, params);
            return 0;
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (PlantArchitecture::setPlantNitrogenParametersFromJSON): ") + e.what());
            return -1;
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (PlantArchitecture::setPlantNitrogenParametersFromJSON): Unknown error.");
            return -1;
        }
    }

    // Phenological control functions
    PYHELIOS_API int setPlantPhenologicalThresholds(
        PlantArchitecture* plantarch,
        unsigned int plantID,
        float time_to_dormancy_break,
        float time_to_flower_initiation,
        float time_to_flower_opening,
        float time_to_fruit_set,
        float time_to_fruit_maturity,
        float time_to_dormancy,
        float max_leaf_lifespan,
        int is_evergreen
    ) {
        try {
            clearError();
            if (!plantarch) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "PlantArchitecture pointer is null");
                return -1;
            }

            plantarch->setPlantPhenologicalThresholds(
                plantID,
                time_to_dormancy_break,
                time_to_flower_initiation,
                time_to_flower_opening,
                time_to_fruit_set,
                time_to_fruit_maturity,
                time_to_dormancy,
                max_leaf_lifespan,
                is_evergreen != 0
            );
            return 0;
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (PlantArchitecture::setPlantPhenologicalThresholds): ") + e.what());
            return -1;
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (PlantArchitecture::setPlantPhenologicalThresholds): Unknown error.");
            return -1;
        }
    }

    PYHELIOS_API int disablePlantPhenology(PlantArchitecture* plantarch, unsigned int plantID) {
        try {
            clearError();
            if (!plantarch) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "PlantArchitecture pointer is null");
                return -1;
            }
            plantarch->disablePlantPhenology(plantID);
            return 0;
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (PlantArchitecture::disablePlantPhenology): ") + e.what());
            return -1;
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (PlantArchitecture::disablePlantPhenology): Unknown error.");
            return -1;
        }
    }

    // Dormancy control functions
    PYHELIOS_API int makePlantDormant(PlantArchitecture* plantarch, unsigned int plantID) {
        try {
            clearError();
            if (!plantarch) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "PlantArchitecture pointer is null");
                return -1;
            }
            plantarch->makePlantDormant(plantID);
            return 0;
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (PlantArchitecture::makePlantDormant): ") + e.what());
            return -1;
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (PlantArchitecture::makePlantDormant): Unknown error.");
            return -1;
        }
    }

    PYHELIOS_API int breakPlantDormancy(PlantArchitecture* plantarch, unsigned int plantID) {
        try {
            clearError();
            if (!plantarch) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "PlantArchitecture pointer is null");
                return -1;
            }
            plantarch->breakPlantDormancy(plantID);
            return 0;
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (PlantArchitecture::breakPlantDormancy): ") + e.what());
            return -1;
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (PlantArchitecture::breakPlantDormancy): Unknown error.");
            return -1;
        }
    }

    PYHELIOS_API int isPlantDormant(PlantArchitecture* plantarch, unsigned int plantID) {
        try {
            clearError();
            if (!plantarch) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "PlantArchitecture pointer is null");
                return -1;
            }
            return plantarch->isPlantDormant(plantID) ? 1 : 0;
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (PlantArchitecture::isPlantDormant): ") + e.what());
            return -1;
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (PlantArchitecture::isPlantDormant): Unknown error.");
            return -1;
        }
    }

    // Pruning and organ removal functions

    PYHELIOS_API int pruneBranch(PlantArchitecture* plantarch, unsigned int plantID, unsigned int shootID, unsigned int node_index) {
        try {
            clearError();
            if (!plantarch) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "PlantArchitecture pointer is null");
                return -1;
            }
            plantarch->pruneBranch(plantID, shootID, node_index);
            return 0;
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (PlantArchitecture::pruneBranch): ") + e.what());
            return -1;
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (PlantArchitecture::pruneBranch): Unknown error.");
            return -1;
        }
    }

    PYHELIOS_API int harvestPlant(PlantArchitecture* plantarch, unsigned int plantID) {
        try {
            clearError();
            if (!plantarch) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "PlantArchitecture pointer is null");
                return -1;
            }
            plantarch->harvestPlant(plantID);
            return 0;
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (PlantArchitecture::harvestPlant): ") + e.what());
            return -1;
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (PlantArchitecture::harvestPlant): Unknown error.");
            return -1;
        }
    }

    PYHELIOS_API int removeShootLeaves(PlantArchitecture* plantarch, unsigned int plantID, unsigned int shootID) {
        try {
            clearError();
            if (!plantarch) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "PlantArchitecture pointer is null");
                return -1;
            }
            plantarch->removeShootLeaves(plantID, shootID);
            return 0;
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (PlantArchitecture::removeShootLeaves): ") + e.what());
            return -1;
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (PlantArchitecture::removeShootLeaves): Unknown error.");
            return -1;
        }
    }

    PYHELIOS_API int removeShootVegetativeBuds(PlantArchitecture* plantarch, unsigned int plantID, unsigned int shootID) {
        try {
            clearError();
            if (!plantarch) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "PlantArchitecture pointer is null");
                return -1;
            }
            plantarch->removeShootVegetativeBuds(plantID, shootID);
            return 0;
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (PlantArchitecture::removeShootVegetativeBuds): ") + e.what());
            return -1;
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (PlantArchitecture::removeShootVegetativeBuds): Unknown error.");
            return -1;
        }
    }

    PYHELIOS_API int removeShootFloralBuds(PlantArchitecture* plantarch, unsigned int plantID, unsigned int shootID) {
        try {
            clearError();
            if (!plantarch) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "PlantArchitecture pointer is null");
                return -1;
            }
            plantarch->removeShootFloralBuds(plantID, shootID);
            return 0;
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (PlantArchitecture::removeShootFloralBuds): ") + e.what());
            return -1;
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (PlantArchitecture::removeShootFloralBuds): Unknown error.");
            return -1;
        }
    }

    PYHELIOS_API int removePlantLeaves(PlantArchitecture* plantarch, unsigned int plantID) {
        try {
            clearError();
            if (!plantarch) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "PlantArchitecture pointer is null");
                return -1;
            }
            plantarch->removePlantLeaves(plantID);
            return 0;
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (PlantArchitecture::removePlantLeaves): ") + e.what());
            return -1;
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (PlantArchitecture::removePlantLeaves): Unknown error.");
            return -1;
        }
    }

    // Plant state query functions
    PYHELIOS_API float getPlantAge(PlantArchitecture* plantarch, unsigned int plantID) {
        try {
            clearError();
            if (!plantarch) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "PlantArchitecture pointer is null");
                return -1.0f;
            }
            return plantarch->getPlantAge(plantID);
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (PlantArchitecture::getPlantAge): ") + e.what());
            return -1.0f;
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (PlantArchitecture::getPlantAge): Unknown error.");
            return -1.0f;
        }
    }

    // Maximum age in days beyond which advanceTime() stops growing the plant (helios-core 1.3.82).
    // Returns -1 on failure; callers must consult getLastErrorCode() to tell that apart from a
    // legitimately small maximum age.
    PYHELIOS_API float getPlantMaxAge(PlantArchitecture* plantarch, unsigned int plantID) {
        try {
            clearError();
            if (!plantarch) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "PlantArchitecture pointer is null");
                return -1.0f;
            }
            return plantarch->getPlantMaxAge(plantID);
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (PlantArchitecture::getPlantMaxAge): ") + e.what());
            return -1.0f;
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (PlantArchitecture::getPlantMaxAge): Unknown error.");
            return -1.0f;
        }
    }

    PYHELIOS_API int setPlantMaxAge(PlantArchitecture* plantarch, unsigned int plantID, float max_age) {
        try {
            clearError();
            if (!plantarch) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "PlantArchitecture pointer is null");
                return -1;
            }
            plantarch->setPlantMaxAge(plantID, max_age);
            return 0;
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (PlantArchitecture::setPlantMaxAge): ") + e.what());
            return -1;
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (PlantArchitecture::setPlantMaxAge): Unknown error.");
            return -1;
        }
    }

    PYHELIOS_API float getPlantHeight(PlantArchitecture* plantarch, unsigned int plantID) {
        try {
            clearError();
            if (!plantarch) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "PlantArchitecture pointer is null");
                return -1.0f;
            }
            return plantarch->getPlantHeight(plantID);
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (PlantArchitecture::getPlantHeight): ") + e.what());
            return -1.0f;
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (PlantArchitecture::getPlantHeight): Unknown error.");
            return -1.0f;
        }
    }

    PYHELIOS_API float sumPlantLeafArea(PlantArchitecture* plantarch, unsigned int plantID) {
        try {
            clearError();
            if (!plantarch) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "PlantArchitecture pointer is null");
                return -1.0f;
            }
            return plantarch->sumPlantLeafArea(plantID);
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (PlantArchitecture::sumPlantLeafArea): ") + e.what());
            return -1.0f;
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (PlantArchitecture::sumPlantLeafArea): Unknown error.");
            return -1.0f;
        }
    }

    // Enable an optional output object data field to be written to the Context
    PYHELIOS_API void plantArchitectureOptionalOutputObjectData(PlantArchitecture* plantarch, const char* object_data_label) {
        try {
            clearError();
            if (!plantarch) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "PlantArchitecture pointer is null");
                return;
            }
            if (!object_data_label) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Object data label is null");
                return;
            }
            plantarch->optionalOutputObjectData(std::string(object_data_label));
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (PlantArchitecture::optionalOutputObjectData): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (PlantArchitecture::optionalOutputObjectData): Unknown error.");
        }
    }

    // Define shoot type from JSON
    PYHELIOS_API int defineShootTypeFromJSON(PlantArchitecture* plantarch, helios::Context* context, const char* shoot_type_label, const char* json_params) {
        try {
            clearError();
            if (!plantarch) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "PlantArchitecture pointer is null");
                return -1;
            }
            if (!context) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Context pointer is null");
                return -1;
            }
            if (!shoot_type_label) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Shoot type label is null");
                return -1;
            }
            if (!json_params) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "JSON parameters are null");
                return -1;
            }

            nlohmann::json j = nlohmann::json::parse(json_params);
            // Use context's random generator
            std::minstd_rand0* generator = context->getRandomGenerator();

            // Seed from the entry being replaced, when there is one, rather than from a fresh
            // ShootParameters. Since helios-core 1.3.84 the child shoot types are readable and are
            // round-tripped through the JSON, but the seeding is still what carries the fields that
            // have no JSON representation -- notably the custom function pointers -- across a
            // defineShootType() call, which replaces the stored entry in its entirety. The JSON
            // values are overlaid on top, so any field the caller did send still wins.
            bool shoot_type_exists = false;
            ShootParameters existing(generator);
            try {
                existing = plantarch->getCurrentShootParameters(std::string(shoot_type_label));
                shoot_type_exists = true;
            } catch (...) {
                // Label does not exist yet: defining a new shoot type, nothing to carry over.
            }

            ShootParameters params = shoot_type_exists ? jsonToShootParameters(j, generator, &existing) : jsonToShootParameters(j, generator);

            // The five custom hooks (phytomer creation/callback, and the leaf, flower and fruit
            // prototype functions) are raw function pointers that cannot be represented in JSON,
            // so params was rebuilt from values alone and carries them all null. Redefining an
            // existing library shoot type would therefore silently strip the species behavior they
            // implement (for maize, the hook that places ears rather than a tassel on every node).
            // Carry them over from the entry being replaced.
            if (shoot_type_exists) {
                params.inheritCustomFunctionsFrom(existing);
            }

            plantarch->defineShootType(std::string(shoot_type_label), params);
            return 0;
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (PlantArchitecture::defineShootType): ") + e.what());
            return -1;
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (PlantArchitecture::defineShootType): Unknown error.");
            return -1;
        }
    }

    PYHELIOS_API void plantarch_setProgressCallback(PlantArchitecture* pa_ptr, void (*callback)(float, const char*)) {
        try {
            clearError();
            if (!pa_ptr) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "PlantArchitecture pointer is null");
                return;
            }
            if (callback) {
                pa_ptr->setProgressCallback([callback](float progress, const std::string& msg) {
                    callback(progress, msg.c_str());
                });
            } else {
                pa_ptr->setProgressCallback(nullptr);
            }
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME,
                     std::string("ERROR (plantarch_setProgressCallback): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN,
                     "ERROR (plantarch_setProgressCallback): Unknown error.");
        }
    }

    PYHELIOS_API void plantarch_setCancelFlag(PlantArchitecture* pa_ptr, volatile int* flag) {
        try {
            clearError();
            if (!pa_ptr) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "PlantArchitecture pointer is null");
                return;
            }
            pa_ptr->setCancelFlag(flag);
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME,
                     std::string("ERROR (plantarch_setCancelFlag): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN,
                     "ERROR (plantarch_setCancelFlag): Unknown error.");
        }
    }

    //=============================================================================
    // Shoot Topology Inspection (read-only)
    //=============================================================================

    PYHELIOS_API unsigned int* getAllPlantShootIDs(PlantArchitecture* plantarch, unsigned int plantID, int* count) {
        try {
            clearError();
            if (!plantarch) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "PlantArchitecture pointer is null");
                if (count) *count = 0;
                return nullptr;
            }
            if (!count) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Count pointer is null");
                return nullptr;
            }

            std::vector<uint> shootIDs = plantarch->getAllShootIDs(plantID);

            static thread_local std::vector<unsigned int> static_shoot_ids;
            static_shoot_ids.assign(shootIDs.begin(), shootIDs.end());
            *count = static_cast<int>(static_shoot_ids.size());

            return static_shoot_ids.data();
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (PlantArchitecture::getAllShootIDs): ") + e.what());
            if (count) *count = 0;
            return nullptr;
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (PlantArchitecture::getAllShootIDs): Unknown error getting shoot IDs.");
            if (count) *count = 0;
            return nullptr;
        }
    }

    // Fills out[0..3] = {rank, parent_shoot_ID, parent_node_index, node_count}. parent_shoot_ID is
    // signed (-1 for the base stem). All other fields are non-negative.
    PYHELIOS_API void getPlantShootTopology(PlantArchitecture* plantarch, unsigned int plantID,
                                            unsigned int shootID, int* out) {
        try {
            clearError();
            if (!plantarch) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "PlantArchitecture pointer is null");
                return;
            }
            if (!out) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Output array is null");
                return;
            }
            const std::shared_ptr<Shoot>& shoot = plantarch->getPlantShoot(plantID, shootID);
            out[0] = static_cast<int>(shoot->rank);
            out[1] = shoot->parent_shoot_ID;
            out[2] = static_cast<int>(shoot->parent_node_index);
            out[3] = static_cast<int>(shoot->current_node_number);
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (PlantArchitecture::getPlantShootTopology): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (PlantArchitecture::getPlantShootTopology): Unknown error.");
        }
    }

    // Returns the flattened list of child shoot IDs (across all parent node indices). Caller copies; the
    // storage is thread-local static and must not be freed.
    PYHELIOS_API int* getPlantShootChildIDs(PlantArchitecture* plantarch, unsigned int plantID,
                                            unsigned int shootID, int* count) {
        try {
            clearError();
            if (!plantarch) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "PlantArchitecture pointer is null");
                if (count) *count = 0;
                return nullptr;
            }
            if (!count) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Count pointer is null");
                return nullptr;
            }
            const std::shared_ptr<Shoot>& shoot = plantarch->getPlantShoot(plantID, shootID);

            static thread_local std::vector<int> static_child_ids;
            static_child_ids.clear();
            for (const auto& entry : shoot->childIDs) {
                for (int childID : entry.second) {
                    static_child_ids.push_back(childID);
                }
            }
            *count = static_cast<int>(static_child_ids.size());
            return static_child_ids.data();
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (PlantArchitecture::getPlantShootChildIDs): ") + e.what());
            if (count) *count = 0;
            return nullptr;
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (PlantArchitecture::getPlantShootChildIDs): Unknown error.");
            if (count) *count = 0;
            return nullptr;
        }
    }

    // ---- Shoot hierarchy accessors (helios-core 1.3.82) ----------------------------------
    // These mirror PlantArchitecture's own topology queries rather than recomputing the walk on
    // the Python side, so pruned-shoot handling and ordering stay defined by the native model.

    PYHELIOS_API int getParentShootID(PlantArchitecture* plantarch, unsigned int plantID,
                                      unsigned int shootID) {
        try {
            clearError();
            if (!plantarch) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "PlantArchitecture pointer is null");
                return -1;
            }
            return plantarch->getParentShootID(plantID, shootID);
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (PlantArchitecture::getParentShootID): ") + e.what());
            return -1;
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (PlantArchitecture::getParentShootID): Unknown error.");
            return -1;
        }
    }

    PYHELIOS_API unsigned int getShootRank(PlantArchitecture* plantarch, unsigned int plantID,
                                           unsigned int shootID) {
        try {
            clearError();
            if (!plantarch) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "PlantArchitecture pointer is null");
                return 0;
            }
            return plantarch->getShootRank(plantID, shootID);
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (PlantArchitecture::getShootRank): ") + e.what());
            return 0;
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (PlantArchitecture::getShootRank): Unknown error.");
            return 0;
        }
    }

    PYHELIOS_API unsigned int getShootDepth(PlantArchitecture* plantarch, unsigned int plantID,
                                            unsigned int shootID) {
        try {
            clearError();
            if (!plantarch) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "PlantArchitecture pointer is null");
                return 0;
            }
            return plantarch->getShootDepth(plantID, shootID);
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (PlantArchitecture::getShootDepth): ") + e.what());
            return 0;
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (PlantArchitecture::getShootDepth): Unknown error.");
            return 0;
        }
    }

    PYHELIOS_API int isShootPruned(PlantArchitecture* plantarch, unsigned int plantID,
                                   unsigned int shootID) {
        try {
            clearError();
            if (!plantarch) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "PlantArchitecture pointer is null");
                return -1;
            }
            return plantarch->isShootPruned(plantID, shootID) ? 1 : 0;
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (PlantArchitecture::isShootPruned): ") + e.what());
            return -1;
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (PlantArchitecture::isShootPruned): Unknown error.");
            return -1;
        }
    }

    // Shared body for the three accessors that return a plain list of shoot IDs. The member
    // function differs but the marshalling is identical, so it is factored out here.
    static unsigned int* returnShootIDVector(const std::vector<unsigned int>& ids, int* count) {
        static thread_local std::vector<unsigned int> static_ids;
        static_ids = ids;
        *count = static_cast<int>(static_ids.size());
        return static_ids.empty() ? nullptr : static_ids.data();
    }

    PYHELIOS_API unsigned int* getPathToRoot(PlantArchitecture* plantarch, unsigned int plantID,
                                             unsigned int shootID, int* count) {
        try {
            clearError();
            if (!plantarch) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "PlantArchitecture pointer is null");
                if (count) *count = 0;
                return nullptr;
            }
            if (!count) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Count pointer is null");
                return nullptr;
            }
            return returnShootIDVector(plantarch->getPathToRoot(plantID, shootID), count);
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (PlantArchitecture::getPathToRoot): ") + e.what());
            if (count) *count = 0;
            return nullptr;
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (PlantArchitecture::getPathToRoot): Unknown error.");
            if (count) *count = 0;
            return nullptr;
        }
    }

    PYHELIOS_API unsigned int* getChildShootIDs(PlantArchitecture* plantarch, unsigned int plantID,
                                                unsigned int shootID, int* count) {
        try {
            clearError();
            if (!plantarch) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "PlantArchitecture pointer is null");
                if (count) *count = 0;
                return nullptr;
            }
            if (!count) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Count pointer is null");
                return nullptr;
            }
            return returnShootIDVector(plantarch->getChildShootIDs(plantID, shootID), count);
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (PlantArchitecture::getChildShootIDs): ") + e.what());
            if (count) *count = 0;
            return nullptr;
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (PlantArchitecture::getChildShootIDs): Unknown error.");
            if (count) *count = 0;
            return nullptr;
        }
    }

    PYHELIOS_API unsigned int* getAllDescendantShootIDs(PlantArchitecture* plantarch, unsigned int plantID,
                                                        unsigned int shootID, int* count) {
        try {
            clearError();
            if (!plantarch) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "PlantArchitecture pointer is null");
                if (count) *count = 0;
                return nullptr;
            }
            if (!count) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Count pointer is null");
                return nullptr;
            }
            return returnShootIDVector(plantarch->getAllDescendantShootIDs(plantID, shootID), count);
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (PlantArchitecture::getAllDescendantShootIDs): ") + e.what());
            if (count) *count = 0;
            return nullptr;
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (PlantArchitecture::getAllDescendantShootIDs): Unknown error.");
            if (count) *count = 0;
            return nullptr;
        }
    }

    PYHELIOS_API unsigned int* getTerminalShootIDs(PlantArchitecture* plantarch, unsigned int plantID,
                                                   int* count) {
        try {
            clearError();
            if (!plantarch) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "PlantArchitecture pointer is null");
                if (count) *count = 0;
                return nullptr;
            }
            if (!count) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Count pointer is null");
                return nullptr;
            }
            return returnShootIDVector(plantarch->getTerminalShootIDs(plantID), count);
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (PlantArchitecture::getTerminalShootIDs): ") + e.what());
            if (count) *count = 0;
            return nullptr;
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (PlantArchitecture::getTerminalShootIDs): Unknown error.");
            if (count) *count = 0;
            return nullptr;
        }
    }

    // Groups of shoot IDs are returned as one flat buffer plus a parallel buffer of group lengths,
    // which avoids a second round trip to size each group. Both buffers are thread-local static.
    PYHELIOS_API unsigned int* getShootIDsByRank(PlantArchitecture* plantarch, unsigned int plantID,
                                                 int** group_sizes, int* group_count, int* total_count) {
        try {
            clearError();
            if (!plantarch) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "PlantArchitecture pointer is null");
                if (group_count) *group_count = 0;
                if (total_count) *total_count = 0;
                if (group_sizes) *group_sizes = nullptr;
                return nullptr;
            }
            if (!group_sizes || !group_count || !total_count) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Output pointer is null");
                return nullptr;
            }

            const std::vector<std::vector<uint>> by_rank = plantarch->getShootIDsByRank(plantID);

            static thread_local std::vector<unsigned int> static_flat;
            static thread_local std::vector<int> static_sizes;
            static_flat.clear();
            static_sizes.clear();
            static_sizes.reserve(by_rank.size());
            for (const auto& rank_group : by_rank) {
                static_sizes.push_back(static_cast<int>(rank_group.size()));
                static_flat.insert(static_flat.end(), rank_group.begin(), rank_group.end());
            }

            *group_count = static_cast<int>(static_sizes.size());
            *total_count = static_cast<int>(static_flat.size());
            *group_sizes = static_sizes.empty() ? nullptr : static_sizes.data();
            return static_flat.empty() ? nullptr : static_flat.data();
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (PlantArchitecture::getShootIDsByRank): ") + e.what());
            if (group_count) *group_count = 0;
            if (total_count) *total_count = 0;
            if (group_sizes) *group_sizes = nullptr;
            return nullptr;
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (PlantArchitecture::getShootIDsByRank): Unknown error.");
            if (group_count) *group_count = 0;
            if (total_count) *total_count = 0;
            if (group_sizes) *group_sizes = nullptr;
            return nullptr;
        }
    }

    PYHELIOS_API unsigned int* getShootHierarchyMap(PlantArchitecture* plantarch, unsigned int plantID,
                                                    unsigned int** parent_ids, int** group_sizes,
                                                    int* parent_count, int* total_children) {
        try {
            clearError();
            if (!plantarch) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "PlantArchitecture pointer is null");
                if (parent_count) *parent_count = 0;
                if (total_children) *total_children = 0;
                if (parent_ids) *parent_ids = nullptr;
                if (group_sizes) *group_sizes = nullptr;
                return nullptr;
            }
            if (!parent_ids || !group_sizes || !parent_count || !total_children) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Output pointer is null");
                return nullptr;
            }

            const std::map<uint, std::vector<uint>> hierarchy = plantarch->getShootHierarchyMap(plantID);

            static thread_local std::vector<unsigned int> static_parents;
            static thread_local std::vector<int> static_sizes;
            static thread_local std::vector<unsigned int> static_children;
            static_parents.clear();
            static_sizes.clear();
            static_children.clear();
            static_parents.reserve(hierarchy.size());
            static_sizes.reserve(hierarchy.size());
            for (const auto& entry : hierarchy) {
                static_parents.push_back(entry.first);
                static_sizes.push_back(static_cast<int>(entry.second.size()));
                static_children.insert(static_children.end(), entry.second.begin(), entry.second.end());
            }

            *parent_count = static_cast<int>(static_parents.size());
            *total_children = static_cast<int>(static_children.size());
            *parent_ids = static_parents.empty() ? nullptr : static_parents.data();
            *group_sizes = static_sizes.empty() ? nullptr : static_sizes.data();
            return static_children.empty() ? nullptr : static_children.data();
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (PlantArchitecture::getShootHierarchyMap): ") + e.what());
            if (parent_count) *parent_count = 0;
            if (total_children) *total_children = 0;
            if (parent_ids) *parent_ids = nullptr;
            if (group_sizes) *group_sizes = nullptr;
            return nullptr;
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (PlantArchitecture::getShootHierarchyMap): Unknown error.");
            if (parent_count) *parent_count = 0;
            if (total_children) *total_children = 0;
            if (parent_ids) *parent_ids = nullptr;
            if (group_sizes) *group_sizes = nullptr;
            return nullptr;
        }
    }

    // Returns the flattened woody internode polyline as 3*N floats (x,y,z per vertex), in
    // phytomer-then-segment order; *count is set to N (the number of vertices). The parallel per-vertex
    // radii are available via getPlantShootInternodeRadii. Thread-local static storage; do not free.
    PYHELIOS_API float* getPlantShootInternodeVertices(PlantArchitecture* plantarch, unsigned int plantID,
                                                       unsigned int shootID, int* count) {
        try {
            clearError();
            if (!plantarch) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "PlantArchitecture pointer is null");
                if (count) *count = 0;
                return nullptr;
            }
            if (!count) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Count pointer is null");
                return nullptr;
            }
            const std::shared_ptr<Shoot>& shoot = plantarch->getPlantShoot(plantID, shootID);

            static thread_local std::vector<float> static_vertices;
            static_vertices.clear();
            int n = 0;
            for (const auto& phytomer : shoot->shoot_internode_vertices) {
                for (const helios::vec3& v : phytomer) {
                    static_vertices.push_back(v.x);
                    static_vertices.push_back(v.y);
                    static_vertices.push_back(v.z);
                    n++;
                }
            }
            *count = n;
            return static_vertices.data();
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (PlantArchitecture::getPlantShootInternodeVertices): ") + e.what());
            if (count) *count = 0;
            return nullptr;
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (PlantArchitecture::getPlantShootInternodeVertices): Unknown error.");
            if (count) *count = 0;
            return nullptr;
        }
    }

    // Returns the flattened per-vertex woody internode radii (one per vertex returned by
    // getPlantShootInternodeVertices). Thread-local static storage; do not free.
    PYHELIOS_API float* getPlantShootInternodeRadii(PlantArchitecture* plantarch, unsigned int plantID,
                                                    unsigned int shootID, int* count) {
        try {
            clearError();
            if (!plantarch) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "PlantArchitecture pointer is null");
                if (count) *count = 0;
                return nullptr;
            }
            if (!count) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Count pointer is null");
                return nullptr;
            }
            const std::shared_ptr<Shoot>& shoot = plantarch->getPlantShoot(plantID, shootID);

            static thread_local std::vector<float> static_radii;
            static_radii.clear();
            for (const auto& phytomer : shoot->shoot_internode_radii) {
                for (float r : phytomer) {
                    static_radii.push_back(r);
                }
            }
            *count = static_cast<int>(static_radii.size());
            return static_radii.data();
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (PlantArchitecture::getPlantShootInternodeRadii): ") + e.what());
            if (count) *count = 0;
            return nullptr;
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (PlantArchitecture::getPlantShootInternodeRadii): Unknown error.");
            if (count) *count = 0;
            return nullptr;
        }
    }

    // =========================================================================
    // Reconstruction from measured geometry (helios-core 1.3.85)
    // =========================================================================

    // Shared marshalling for a flat (x,y,z)*n position array plus n radii.
    static bool unpackNodesAndRadii(const float* positions, const float* radii, int count, const char* fn,
                                    std::vector<helios::vec3>& out_positions, std::vector<float>& out_radii) {
        if (!positions || !radii) {
            setError(PYHELIOS_ERROR_INVALID_PARAMETER, std::string("ERROR (PlantArchitecture::") + fn + "): Node position or radius array is null");
            return false;
        }
        if (count < 2) {
            setError(PYHELIOS_ERROR_INVALID_PARAMETER, std::string("ERROR (PlantArchitecture::") + fn + "): At least two node positions are required");
            return false;
        }
        out_positions.clear();
        out_positions.reserve(count);
        out_radii.assign(radii, radii + count);
        for (int i = 0; i < count; ++i) {
            out_positions.push_back(helios::make_vec3(positions[3 * i], positions[3 * i + 1], positions[3 * i + 2]));
        }
        return true;
    }

    PYHELIOS_API unsigned int addShootFromNodePositions(PlantArchitecture* plantarch, unsigned int plantID, int parent_shoot_ID, unsigned int parent_node_index, const float* node_positions, const float* node_radii, int node_count, const char* shoot_type_label, const char* growth_shoot_type_label, unsigned int petiole_index) {
        try {
            clearError();
            if (!plantarch) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "PlantArchitecture pointer is null");
                return 0;
            }
            if (!shoot_type_label || std::strlen(shoot_type_label) == 0) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Shoot type label cannot be empty");
                return 0;
            }
            std::vector<helios::vec3> positions;
            std::vector<float> radii;
            if (!unpackNodesAndRadii(node_positions, node_radii, node_count, "addShootFromNodePositions", positions, radii)) {
                return 0;
            }
            if (growth_shoot_type_label && std::strlen(growth_shoot_type_label) > 0) {
                return plantarch->addShootFromNodePositions(plantID, parent_shoot_ID, parent_node_index, positions, radii, std::string(shoot_type_label), std::string(growth_shoot_type_label), petiole_index);
            }
            return plantarch->addShootFromNodePositions(plantID, parent_shoot_ID, parent_node_index, positions, radii, std::string(shoot_type_label), petiole_index);
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (PlantArchitecture::addShootFromNodePositions): ") + e.what());
            return 0;
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (PlantArchitecture::addShootFromNodePositions): Unknown error.");
            return 0;
        }
    }

    PYHELIOS_API int setPetioleNodePositions(PlantArchitecture* plantarch, unsigned int plantID, unsigned int shootID, unsigned int node_index, unsigned int petiole_index, const float* node_positions, const float* node_radii, int node_count) {
        try {
            clearError();
            if (!plantarch) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "PlantArchitecture pointer is null");
                return -1;
            }
            std::vector<helios::vec3> positions;
            std::vector<float> radii;
            if (!unpackNodesAndRadii(node_positions, node_radii, node_count, "setPetioleNodePositions", positions, radii)) {
                return -1;
            }
            plantarch->setPetioleNodePositions(plantID, shootID, node_index, petiole_index, positions, radii);
            return 0;
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (PlantArchitecture::setPetioleNodePositions): ") + e.what());
            return -1;
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (PlantArchitecture::setPetioleNodePositions): Unknown error.");
            return -1;
        }
    }

    PYHELIOS_API int setPetioleLeafGeometry(PlantArchitecture* plantarch, unsigned int plantID, unsigned int shootID, unsigned int node_index, unsigned int petiole_index, const float* leaf_bases, const float* leaf_rotations, const float* leaf_sizes, int leaf_count, const float* leaf_stalk_lengths, const float* leaf_stalk_bases) {
        try {
            clearError();
            if (!plantarch) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "PlantArchitecture pointer is null");
                return -1;
            }
            if (!leaf_bases || !leaf_rotations || !leaf_sizes) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "ERROR (PlantArchitecture::setPetioleLeafGeometry): Leaf base, rotation or size array is null");
                return -1;
            }
            if (leaf_count < 1) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "ERROR (PlantArchitecture::setPetioleLeafGeometry): At least one leaf is required");
                return -1;
            }
            std::vector<helios::vec3> bases;
            std::vector<AxisRotation> rotations;
            bases.reserve(leaf_count);
            rotations.reserve(leaf_count);
            for (int i = 0; i < leaf_count; ++i) {
                bases.push_back(helios::make_vec3(leaf_bases[3 * i], leaf_bases[3 * i + 1], leaf_bases[3 * i + 2]));
                // (pitch, yaw, roll) in radians, matching the AxisRotation constructor order.
                rotations.emplace_back(leaf_rotations[3 * i], leaf_rotations[3 * i + 1], leaf_rotations[3 * i + 2]);
            }
            std::vector<float> sizes(leaf_sizes, leaf_sizes + leaf_count);
            // Optional stalk arrays (helios-core 1.3.97): NULL means not given, passed on as an empty vector.
            std::vector<float> stalk_lengths;
            if (leaf_stalk_lengths) {
                stalk_lengths.assign(leaf_stalk_lengths, leaf_stalk_lengths + leaf_count);
            }
            std::vector<helios::vec3> stalk_bases;
            if (leaf_stalk_bases) {
                stalk_bases.reserve(leaf_count);
                for (int i = 0; i < leaf_count; ++i) {
                    stalk_bases.push_back(helios::make_vec3(leaf_stalk_bases[3 * i], leaf_stalk_bases[3 * i + 1], leaf_stalk_bases[3 * i + 2]));
                }
            }
            plantarch->setPetioleLeafGeometry(plantID, shootID, node_index, petiole_index, bases, rotations, sizes, stalk_lengths, stalk_bases);
            return 0;
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (PlantArchitecture::setPetioleLeafGeometry): ") + e.what());
            return -1;
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (PlantArchitecture::setPetioleLeafGeometry): Unknown error.");
            return -1;
        }
    }

    PYHELIOS_API int isShootGeometryPrescribed(PlantArchitecture* plantarch, unsigned int plantID, unsigned int shootID) {
        try {
            clearError();
            if (!plantarch) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "PlantArchitecture pointer is null");
                return -1;
            }
            return plantarch->isShootGeometryPrescribed(plantID, shootID) ? 1 : 0;
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (PlantArchitecture::isShootGeometryPrescribed): ") + e.what());
            return -1;
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (PlantArchitecture::isShootGeometryPrescribed): Unknown error.");
            return -1;
        }
    }

    PYHELIOS_API int setPetioleLeafCount(PlantArchitecture* plantarch, unsigned int plantID, unsigned int shootID, unsigned int node_index, unsigned int petiole_index, unsigned int leaf_count) {
        try {
            clearError();
            if (!plantarch) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "PlantArchitecture pointer is null");
                return -1;
            }
            if (leaf_count < 1) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "ERROR (PlantArchitecture::setPetioleLeafCount): Leaf count must be at least 1");
                return -1;
            }
            plantarch->setPetioleLeafCount(plantID, shootID, node_index, petiole_index, leaf_count);
            return 0;
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (PlantArchitecture::setPetioleLeafCount): ") + e.what());
            return -1;
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (PlantArchitecture::setPetioleLeafCount): Unknown error.");
            return -1;
        }
    }

    PYHELIOS_API int setPetioleShape(PlantArchitecture* plantarch, unsigned int plantID, unsigned int shootID, unsigned int node_index, unsigned int petiole_index, const float* outward_direction, float pitch_degrees, float curvature, float length) {
        try {
            clearError();
            if (!plantarch || !outward_direction) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "ERROR (PlantArchitecture::setPetioleShape): PlantArchitecture pointer or outward direction is null");
                return -1;
            }
            plantarch->setPetioleShape(plantID, shootID, node_index, petiole_index, helios::make_vec3(outward_direction[0], outward_direction[1], outward_direction[2]), pitch_degrees, curvature, length);
            return 0;
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (PlantArchitecture::setPetioleShape): ") + e.what());
            return -1;
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (PlantArchitecture::setPetioleShape): Unknown error.");
            return -1;
        }
    }

    PYHELIOS_API int setPetioleLeaflets(PlantArchitecture* plantarch, unsigned int plantID, unsigned int shootID, unsigned int node_index, unsigned int petiole_index, unsigned int leaf_count, float leaflet_offset, float leaflet_scale, float prototype_scale, float intercalary_leaflet_scale) {
        try {
            clearError();
            if (!plantarch) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "PlantArchitecture pointer is null");
                return -1;
            }
            plantarch->setPetioleLeaflets(plantID, shootID, node_index, petiole_index, leaf_count, leaflet_offset, leaflet_scale, prototype_scale, intercalary_leaflet_scale);
            return 0;
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (PlantArchitecture::setPetioleLeaflets): ") + e.what());
            return -1;
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (PlantArchitecture::setPetioleLeaflets): Unknown error.");
            return -1;
        }
    }

    PYHELIOS_API int setPetioleLeafletAngles(PlantArchitecture* plantarch, unsigned int plantID, unsigned int shootID, unsigned int node_index, unsigned int petiole_index, float pitch_degrees, float yaw_degrees, float roll_degrees) {
        try {
            clearError();
            if (!plantarch) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "PlantArchitecture pointer is null");
                return -1;
            }
            plantarch->setPetioleLeafletAngles(plantID, shootID, node_index, petiole_index, pitch_degrees, yaw_degrees, roll_degrees);
            return 0;
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (PlantArchitecture::setPetioleLeafletAngles): ") + e.what());
            return -1;
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (PlantArchitecture::setPetioleLeafletAngles): Unknown error.");
            return -1;
        }
    }

    PYHELIOS_API int setPetioleLeafShape(PlantArchitecture* plantarch, unsigned int plantID, unsigned int shootID, unsigned int node_index, unsigned int petiole_index, float aspect_ratio, float longitudinal_curvature, float lateral_curvature, float midrib_fold_fraction) {
        try {
            clearError();
            if (!plantarch) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "PlantArchitecture pointer is null");
                return -1;
            }
            plantarch->setPetioleLeafShape(plantID, shootID, node_index, petiole_index, aspect_ratio, longitudinal_curvature, lateral_curvature, midrib_fold_fraction);
            return 0;
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (PlantArchitecture::setPetioleLeafShape): ") + e.what());
            return -1;
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (PlantArchitecture::setPetioleLeafShape): Unknown error.");
            return -1;
        }
    }

    PYHELIOS_API int setPetioleLeafletAngleOffsets(PlantArchitecture* plantarch, unsigned int plantID, unsigned int shootID, unsigned int node_index, unsigned int petiole_index, const float* pitch_degrees, const float* yaw_degrees, const float* roll_degrees, unsigned int count) {
        try {
            clearError();
            if (!plantarch || (count > 0 && (!pitch_degrees || !yaw_degrees || !roll_degrees))) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "ERROR (PlantArchitecture::setPetioleLeafletAngleOffsets): PlantArchitecture pointer or an offset array is null");
                return -1;
            }
            const std::vector<float> pitch(pitch_degrees, pitch_degrees + count);
            const std::vector<float> yaw(yaw_degrees, yaw_degrees + count);
            const std::vector<float> roll(roll_degrees, roll_degrees + count);
            plantarch->setPetioleLeafletAngleOffsets(plantID, shootID, node_index, petiole_index, pitch, yaw, roll);
            return 0;
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (PlantArchitecture::setPetioleLeafletAngleOffsets): ") + e.what());
            return -1;
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (PlantArchitecture::setPetioleLeafletAngleOffsets): Unknown error.");
            return -1;
        }
    }

    PYHELIOS_API int setPlantMinimumLeafTextureStage(PlantArchitecture* plantarch, unsigned int plantID, unsigned int stage) {
        return guardedPhytomerCall(plantarch, "setPlantMinimumLeafTextureStage", -1, [&]() -> int {
            plantarch->setPlantMinimumLeafTextureStage(plantID, stage);
            return 0;
        });
    }

    PYHELIOS_API int getPlantMinimumLeafTextureStage(PlantArchitecture* plantarch, unsigned int plantID, unsigned int* stage) {
        return guardedPhytomerCall(plantarch, "getPlantMinimumLeafTextureStage", -1, [&]() -> int {
            if (!stage) {
                throw std::invalid_argument("Output pointer is null");
            }
            *stage = plantarch->getPlantMinimumLeafTextureStage(plantID);
            return 0;
        });
    }

    PYHELIOS_API const char* generateLeafTextureStages(const char* leaf_texture, const char* output_directory, unsigned int stage_count, const char* options_json) {
        try {
            clearError();
            if (!leaf_texture || !output_directory) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "ERROR (PlantArchitecture::generateLeafTextureStages): Leaf texture or output directory is null");
                return nullptr;
            }
            LeafTextureStageOptions options;
            if (options_json && options_json[0] != '\0') {
                const nlohmann::json j = nlohmann::json::parse(std::string(options_json));
                if (!j.is_object()) {
                    setError(PYHELIOS_ERROR_INVALID_PARAMETER, "ERROR (PlantArchitecture::generateLeafTextureStages): options must be a JSON object");
                    return nullptr;
                }
                if (j.contains("senescence_colors")) {
                    options.senescence_colors.clear();
                    for (const auto& c : j["senescence_colors"]) {
                        if (!c.is_array() || c.size() != 3) {
                            setError(PYHELIOS_ERROR_INVALID_PARAMETER, "ERROR (PlantArchitecture::generateLeafTextureStages): each senescence color must be [r, g, b]");
                            return nullptr;
                        }
                        options.senescence_colors.push_back(helios::make_RGBcolor(c[0].get<float>(), c[1].get<float>(), c[2].get<float>()));
                    }
                }
                if (j.contains("senesced_textures")) options.senesced_textures = j["senesced_textures"].get<std::vector<std::string>>();
                if (j.contains("onset_map")) options.onset_map = j["onset_map"].get<std::string>();
                if (j.contains("patchiness")) options.patchiness = j["patchiness"].get<float>();
                if (j.contains("transition_width")) options.transition_width = j["transition_width"].get<float>();
                if (j.contains("noise_seed")) options.noise_seed = j["noise_seed"].get<unsigned int>();
            }
            const std::vector<std::string> files = PlantArchitecture::generateLeafTextureStages(std::string(leaf_texture), std::string(output_directory), stage_count, options);
            static thread_local std::string result;
            result = nlohmann::json(files).dump();
            return result.c_str();
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (PlantArchitecture::generateLeafTextureStages): ") + e.what());
            return nullptr;
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (PlantArchitecture::generateLeafTextureStages): Unknown error.");
            return nullptr;
        }
    }

    PYHELIOS_API int setShootInternodeLengthMax(PlantArchitecture* plantarch, unsigned int plantID, unsigned int shootID, float internode_length_max) {
        try {
            clearError();
            if (!plantarch) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "PlantArchitecture pointer is null");
                return -1;
            }
            if (internode_length_max <= 0.f) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "ERROR (PlantArchitecture::setShootInternodeLengthMax): Internode length must be positive");
                return -1;
            }
            plantarch->setShootInternodeLengthMax(plantID, shootID, internode_length_max);
            return 0;
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (PlantArchitecture::setShootInternodeLengthMax): ") + e.what());
            return -1;
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (PlantArchitecture::setShootInternodeLengthMax): Unknown error.");
            return -1;
        }
    }

    // =========================================================================
    // Bud and apex control
    // =========================================================================

    PYHELIOS_API int terminateShootApicalBud(PlantArchitecture* plantarch, unsigned int plantID, unsigned int shootID) {
        try {
            clearError();
            if (!plantarch) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "PlantArchitecture pointer is null");
                return -1;
            }
            plantarch->getPlantShoot(plantID, shootID)->terminateApicalBud();
            return 0;
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (PlantArchitecture::terminateShootApicalBud): ") + e.what());
            return -1;
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (PlantArchitecture::terminateShootApicalBud): Unknown error.");
            return -1;
        }
    }

    PYHELIOS_API int getShootVegetativeBudCount(PlantArchitecture* plantarch, unsigned int plantID, unsigned int shootID, int bud_state) {
        try {
            clearError();
            if (!plantarch) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "PlantArchitecture pointer is null");
                return -1;
            }
            // Range-check before casting: static_cast of an out-of-range int onto the enum is undefined.
            if (bud_state < -1 || bud_state > static_cast<int>(BUD_DEAD)) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER,
                         "ERROR (PlantArchitecture::getShootVegetativeBudCount): Bud state must be 0-5, or -1 for any state");
                return -1;
            }
            const std::shared_ptr<Shoot>& shoot = plantarch->getPlantShoot(plantID, shootID);

            int count = 0;
            for (const auto& phytomer : shoot->phytomers) {
                for (const auto& petiole : phytomer->axillary_vegetative_buds) {
                    if (bud_state < 0) {
                        count += static_cast<int>(petiole.size());
                    } else {
                        for (const VegetativeBud& bud : petiole) {
                            if (bud.state == static_cast<BudState>(bud_state)) {
                                count++;
                            }
                        }
                    }
                }
            }
            return count;
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (PlantArchitecture::getShootVegetativeBudCount): ") + e.what());
            return -1;
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (PlantArchitecture::getShootVegetativeBudCount): Unknown error.");
            return -1;
        }
    }

    PYHELIOS_API int getPlantLeafCount(PlantArchitecture* plantarch, unsigned int plantID) {
        try {
            clearError();
            if (!plantarch) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "PlantArchitecture pointer is null");
                return -1;
            }
            // Narrowed to int deliberately so the -1 error sentinel cannot surface as 4294967295.
            return static_cast<int>(plantarch->getPlantLeafCount(plantID));
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (PlantArchitecture::getPlantLeafCount): ") + e.what());
            return -1;
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (PlantArchitecture::getPlantLeafCount): Unknown error.");
            return -1;
        }
    }

    // =========================================================================
    // Built-geometry organ queries (helios-core 1.3.85)
    // =========================================================================

    // Shared body for the three per-organ float-vector queries; only the member function differs.
    // A member-function pointer rather than a template: templates cannot appear inside extern "C".
    typedef std::vector<float> (PlantArchitecture::*PlantFloatVectorGetter)(unsigned int) const;
    static float* returnPlantFloatVector(PlantArchitecture* plantarch, unsigned int plantID, int* count, const char* fn, PlantFloatVectorGetter getter) {
        try {
            clearError();
            if (!plantarch) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "PlantArchitecture pointer is null");
                if (count) *count = 0;
                return nullptr;
            }
            if (!count) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Count pointer is null");
                return nullptr;
            }
            static thread_local std::vector<float> static_values;
            static_values = (plantarch->*getter)(plantID);
            *count = static_cast<int>(static_values.size());
            return static_values.data();
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (PlantArchitecture::") + fn + "): " + e.what());
            if (count) *count = 0;
            return nullptr;
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, std::string("ERROR (PlantArchitecture::") + fn + "): Unknown error.");
            if (count) *count = 0;
            return nullptr;
        }
    }

    PYHELIOS_API float* getPlantLeafAreas(PlantArchitecture* plantarch, unsigned int plantID, int* count) {
        return returnPlantFloatVector(plantarch, plantID, count, "getPlantLeafAreas", &PlantArchitecture::getPlantLeafAreas);
    }

    PYHELIOS_API float* getPlantInternodeLengths(PlantArchitecture* plantarch, unsigned int plantID, int* count) {
        return returnPlantFloatVector(plantarch, plantID, count, "getPlantInternodeLengths", &PlantArchitecture::getPlantInternodeLengths);
    }

    PYHELIOS_API float* getPlantLeafInclinations(PlantArchitecture* plantarch, unsigned int plantID, int* count) {
        return returnPlantFloatVector(plantarch, plantID, count, "getPlantLeafInclinations", &PlantArchitecture::getPlantLeafInclinations);
    }

    //=============================================================================
    // Leaf angle distribution tracking (helios-core 1.3.87)
    //=============================================================================

    PYHELIOS_API int enablePlantLeafAngleDistributionTracking(PlantArchitecture* plantarch, unsigned int plantID, float Beta_mu_inclination, float Beta_nu_inclination, float eccentricity,
                                                             float ellipse_rotation_degrees, float lambda_degrees) {
        try {
            clearError();
            if (!plantarch) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "PlantArchitecture pointer is null");
                return -1;
            }
            plantarch->enablePlantLeafAngleDistributionTracking(plantID, Beta_mu_inclination, Beta_nu_inclination, eccentricity, ellipse_rotation_degrees, lambda_degrees);
            return 0;
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (PlantArchitecture::enablePlantLeafAngleDistributionTracking): ") + e.what());
            return -1;
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (PlantArchitecture::enablePlantLeafAngleDistributionTracking): Unknown error.");
            return -1;
        }
    }

    PYHELIOS_API int enablePlantLeafAngleDistributionTrackingMulti(PlantArchitecture* plantarch, const unsigned int* plantIDs, int count, float Beta_mu_inclination, float Beta_nu_inclination,
                                                                  float eccentricity, float ellipse_rotation_degrees, float lambda_degrees) {
        try {
            clearError();
            if (!plantarch) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "PlantArchitecture pointer is null");
                return -1;
            }
            if (!plantIDs || count <= 0) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "ERROR (PlantArchitecture::enablePlantLeafAngleDistributionTracking): Plant ID list is empty");
                return -1;
            }
            std::vector<uint> ids(plantIDs, plantIDs + count);
            plantarch->enablePlantLeafAngleDistributionTracking(ids, Beta_mu_inclination, Beta_nu_inclination, eccentricity, ellipse_rotation_degrees, lambda_degrees);
            return 0;
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (PlantArchitecture::enablePlantLeafAngleDistributionTracking): ") + e.what());
            return -1;
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (PlantArchitecture::enablePlantLeafAngleDistributionTracking): Unknown error.");
            return -1;
        }
    }

    PYHELIOS_API int enablePlantLeafElevationAngleDistributionTracking(PlantArchitecture* plantarch, unsigned int plantID, float Beta_mu_inclination, float Beta_nu_inclination, float lambda_degrees) {
        try {
            clearError();
            if (!plantarch) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "PlantArchitecture pointer is null");
                return -1;
            }
            plantarch->enablePlantLeafElevationAngleDistributionTracking(plantID, Beta_mu_inclination, Beta_nu_inclination, lambda_degrees);
            return 0;
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (PlantArchitecture::enablePlantLeafElevationAngleDistributionTracking): ") + e.what());
            return -1;
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (PlantArchitecture::enablePlantLeafElevationAngleDistributionTracking): Unknown error.");
            return -1;
        }
    }

    PYHELIOS_API int enablePlantLeafAzimuthAngleDistributionTracking(PlantArchitecture* plantarch, unsigned int plantID, float eccentricity, float ellipse_rotation_degrees, float lambda_degrees) {
        try {
            clearError();
            if (!plantarch) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "PlantArchitecture pointer is null");
                return -1;
            }
            plantarch->enablePlantLeafAzimuthAngleDistributionTracking(plantID, eccentricity, ellipse_rotation_degrees, lambda_degrees);
            return 0;
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (PlantArchitecture::enablePlantLeafAzimuthAngleDistributionTracking): ") + e.what());
            return -1;
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (PlantArchitecture::enablePlantLeafAzimuthAngleDistributionTracking): Unknown error.");
            return -1;
        }
    }

    PYHELIOS_API int disablePlantLeafAngleDistributionTracking(PlantArchitecture* plantarch, unsigned int plantID) {
        try {
            clearError();
            if (!plantarch) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "PlantArchitecture pointer is null");
                return -1;
            }
            plantarch->disablePlantLeafAngleDistributionTracking(plantID);
            return 0;
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (PlantArchitecture::disablePlantLeafAngleDistributionTracking): ") + e.what());
            return -1;
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (PlantArchitecture::disablePlantLeafAngleDistributionTracking): Unknown error.");
            return -1;
        }
    }

    PYHELIOS_API int isPlantLeafAngleDistributionTrackingEnabled(PlantArchitecture* plantarch, unsigned int plantID) {
        try {
            clearError();
            if (!plantarch) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "PlantArchitecture pointer is null");
                return -1;
            }
            return plantarch->isPlantLeafAngleDistributionTrackingEnabled(plantID) ? 1 : 0;
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (PlantArchitecture::isPlantLeafAngleDistributionTrackingEnabled): ") + e.what());
            return -1;
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (PlantArchitecture::isPlantLeafAngleDistributionTrackingEnabled): Unknown error.");
            return -1;
        }
    }

    //=============================================================================
    // Per-phytomer petiole and leaf growth targets (helios-core 1.3.87)
    //=============================================================================

    PYHELIOS_API float getPetioleLengthAt(PlantArchitecture* plantarch, unsigned int plantID, unsigned int shootID, unsigned int node_index, unsigned int petiole_index) {
        try {
            clearError();
            if (!plantarch) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "PlantArchitecture pointer is null");
                return -1.f;
            }
            return resolvePhytomer(plantarch, plantID, shootID, node_index, "getPetioleLength")->getPetioleLength(petiole_index);
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (PlantArchitecture::getPetioleLength): ") + e.what());
            return -1.f;
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (PlantArchitecture::getPetioleLength): Unknown error.");
            return -1.f;
        }
    }

    PYHELIOS_API float getPhytomerPetioleLength(PlantArchitecture* plantarch, unsigned int plantID, unsigned int shootID, unsigned int node_index) {
        try {
            clearError();
            if (!plantarch) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "PlantArchitecture pointer is null");
                return -1.f;
            }
            return resolvePhytomer(plantarch, plantID, shootID, node_index, "getPetioleLength")->getPetioleLength();
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (PlantArchitecture::getPetioleLength): ") + e.what());
            return -1.f;
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (PlantArchitecture::getPetioleLength): Unknown error.");
            return -1.f;
        }
    }

    PYHELIOS_API int scalePetioleMaxLength(PlantArchitecture* plantarch, unsigned int plantID, unsigned int shootID, unsigned int node_index, float scale_factor) {
        try {
            clearError();
            if (!plantarch) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "PlantArchitecture pointer is null");
                return -1;
            }
            if (scale_factor <= 0.f) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "ERROR (PlantArchitecture::scalePetioleMaxLength): Scale factor must be positive");
                return -1;
            }
            resolvePhytomer(plantarch, plantID, shootID, node_index, "scalePetioleMaxLength")->scalePetioleMaxLength(scale_factor);
            return 0;
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (PlantArchitecture::scalePetioleMaxLength): ") + e.what());
            return -1;
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (PlantArchitecture::scalePetioleMaxLength): Unknown error.");
            return -1;
        }
    }

    PYHELIOS_API int setPetioleScaleFraction(PlantArchitecture* plantarch, unsigned int plantID, unsigned int shootID, unsigned int node_index, unsigned int petiole_index,
                                            float petiole_scale_factor_fraction) {
        try {
            clearError();
            if (!plantarch) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "PlantArchitecture pointer is null");
                return -1;
            }
            resolvePhytomer(plantarch, plantID, shootID, node_index, "setPetioleScaleFraction")->setPetioleScaleFraction(petiole_index, petiole_scale_factor_fraction);
            return 0;
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (PlantArchitecture::setPetioleScaleFraction): ") + e.what());
            return -1;
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (PlantArchitecture::setPetioleScaleFraction): Unknown error.");
            return -1;
        }
    }

    PYHELIOS_API int setPetioleAndLeafScaleFraction(PlantArchitecture* plantarch, unsigned int plantID, unsigned int shootID, unsigned int node_index, unsigned int petiole_index,
                                                   float petiole_scale_factor_fraction, float leaf_scale_factor_fraction) {
        try {
            clearError();
            if (!plantarch) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "PlantArchitecture pointer is null");
                return -1;
            }
            resolvePhytomer(plantarch, plantID, shootID, node_index, "setPetioleAndLeafScaleFraction")
                    ->setPetioleAndLeafScaleFraction(petiole_index, petiole_scale_factor_fraction, leaf_scale_factor_fraction);
            return 0;
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (PlantArchitecture::setPetioleAndLeafScaleFraction): ") + e.what());
            return -1;
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (PlantArchitecture::setPetioleAndLeafScaleFraction): Unknown error.");
            return -1;
        }
    }

    PYHELIOS_API int scaleLeafSizeMax(PlantArchitecture* plantarch, unsigned int plantID, unsigned int shootID, unsigned int node_index, float scale_factor) {
        try {
            clearError();
            if (!plantarch) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "PlantArchitecture pointer is null");
                return -1;
            }
            if (scale_factor <= 0.f) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "ERROR (PlantArchitecture::scaleLeafSizeMax): Scale factor must be positive");
                return -1;
            }
            resolvePhytomer(plantarch, plantID, shootID, node_index, "scaleLeafSizeMax")->scaleLeafSizeMax(scale_factor);
            return 0;
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (PlantArchitecture::scaleLeafSizeMax): ") + e.what());
            return -1;
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (PlantArchitecture::scaleLeafSizeMax): Unknown error.");
            return -1;
        }
    }

    PYHELIOS_API int setLeafNormal(PlantArchitecture* plantarch, unsigned int plantID, unsigned int shootID, unsigned int node_index, unsigned int petiole_index, unsigned int leaf_index,
                                   float nx, float ny, float nz) {
        try {
            clearError();
            if (!plantarch) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "PlantArchitecture pointer is null");
                return -1;
            }
            resolvePhytomer(plantarch, plantID, shootID, node_index, "setLeafNormal")->setLeafNormal(petiole_index, leaf_index, helios::make_vec3(nx, ny, nz));
            return 0;
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (PlantArchitecture::setLeafNormal): ") + e.what());
            return -1;
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (PlantArchitecture::setLeafNormal): Unknown error.");
            return -1;
        }
    }

    PYHELIOS_API int bendPetioleUnderLeafWeight(PlantArchitecture* plantarch, unsigned int plantID, unsigned int shootID, unsigned int node_index, unsigned int petiole_index) {
        try {
            clearError();
            if (!plantarch) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "PlantArchitecture pointer is null");
                return -1;
            }
            resolvePhytomer(plantarch, plantID, shootID, node_index, "bendPetioleUnderLeafWeight")->bendPetioleUnderLeafWeight(petiole_index);
            return 0;
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (PlantArchitecture::bendPetioleUnderLeafWeight): ") + e.what());
            return -1;
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (PlantArchitecture::bendPetioleUnderLeafWeight): Unknown error.");
            return -1;
        }
    }

    PYHELIOS_API int recordPetioleRestShape(PlantArchitecture* plantarch, unsigned int plantID, unsigned int shootID, unsigned int node_index, unsigned int petiole_index) {
        try {
            clearError();
            if (!plantarch) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "PlantArchitecture pointer is null");
                return -1;
            }
            resolvePhytomer(plantarch, plantID, shootID, node_index, "recordPetioleRestShape")->recordPetioleRestShape(petiole_index);
            return 0;
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (PlantArchitecture::recordPetioleRestShape): ") + e.what());
            return -1;
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (PlantArchitecture::recordPetioleRestShape): Unknown error.");
            return -1;
        }
    }

    //=============================================================================
    // Posing a finished plant
    //=============================================================================

    PYHELIOS_API int setPlantLeafAngleDistribution(PlantArchitecture* plantarch, const unsigned int* plantIDs, int count, float Beta_mu_inclination, float Beta_nu_inclination, int set_azimuth,
                                                   float eccentricity, float ellipse_rotation_degrees) {
        try {
            clearError();
            if (!plantarch) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "PlantArchitecture pointer is null");
                return -1;
            }
            if (!plantIDs || count <= 0) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "ERROR (PlantArchitecture::setPlantLeafAngleDistribution): Plant ID list is empty");
                return -1;
            }
            std::vector<uint> ids(plantIDs, plantIDs + count);
            if (set_azimuth) {
                plantarch->setPlantLeafAngleDistribution(ids, Beta_mu_inclination, Beta_nu_inclination, eccentricity, ellipse_rotation_degrees);
            } else {
                plantarch->setPlantLeafElevationAngleDistribution(ids, Beta_mu_inclination, Beta_nu_inclination);
            }
            return 0;
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (PlantArchitecture::setPlantLeafAngleDistribution): ") + e.what());
            return -1;
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (PlantArchitecture::setPlantLeafAngleDistribution): Unknown error.");
            return -1;
        }
    }

    PYHELIOS_API int bendPetioleWithPosedLeavesUnderLeafWeight(PlantArchitecture* plantarch, unsigned int plantID, unsigned int shootID, unsigned int node_index, unsigned int petiole_index) {
        try {
            clearError();
            if (!plantarch) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "PlantArchitecture pointer is null");
                return -1;
            }
            std::shared_ptr<Phytomer> phytomer = resolvePhytomer(plantarch, plantID, shootID, node_index, "bendPetioleUnderLeafWeight");
            if (petiole_index >= phytomer->leaf_pose_prescribed.size()) {
                phytomer->bendPetioleUnderLeafWeight(petiole_index);
                return 0;
            }
            // Phytomer::bendPetioleUnderLeafWeight() returns early for a petiole carrying a posed leaf, so the flags are
            // lowered for the duration of the call. They are restored afterward because they also select how a leaf is
            // rebuilt as it grows and how it is written to XML.
            const std::vector<bool> posed = phytomer->leaf_pose_prescribed.at(petiole_index);
            phytomer->leaf_pose_prescribed.at(petiole_index).assign(posed.size(), false);
            try {
                phytomer->bendPetioleUnderLeafWeight(petiole_index);
            } catch (...) {
                phytomer->leaf_pose_prescribed.at(petiole_index) = posed;
                throw;
            }
            phytomer->leaf_pose_prescribed.at(petiole_index) = posed;
            return 0;
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (PlantArchitecture::bendPetioleUnderLeafWeight): ") + e.what());
            return -1;
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (PlantArchitecture::bendPetioleUnderLeafWeight): Unknown error.");
            return -1;
        }
    }

    PYHELIOS_API float getPetioleFlexibility(PlantArchitecture* plantarch, unsigned int plantID, unsigned int shootID, unsigned int node_index) {
        try {
            clearError();
            if (!plantarch) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "PlantArchitecture pointer is null");
                return -1.f;
            }
            return resolvePhytomer(plantarch, plantID, shootID, node_index, "getPetioleFlexibility")->petiole_flexibility;
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (PlantArchitecture::getPetioleFlexibility): ") + e.what());
            return -1.f;
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (PlantArchitecture::getPetioleFlexibility): Unknown error.");
            return -1.f;
        }
    }

    PYHELIOS_API int setPetioleFlexibility(PlantArchitecture* plantarch, unsigned int plantID, unsigned int shootID, unsigned int node_index, float flexibility) {
        try {
            clearError();
            if (!plantarch) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "PlantArchitecture pointer is null");
                return -1;
            }
            if (!(flexibility >= 0.f) || !std::isfinite(flexibility)) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "ERROR (PlantArchitecture::setPetioleFlexibility): Flexibility must be finite and non-negative, but " + std::to_string(flexibility) + " was given.");
                return -1;
            }
            resolvePhytomer(plantarch, plantID, shootID, node_index, "setPetioleFlexibility")->petiole_flexibility = flexibility;
            return 0;
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (PlantArchitecture::setPetioleFlexibility): ") + e.what());
            return -1;
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (PlantArchitecture::setPetioleFlexibility): Unknown error.");
            return -1;
        }
    }

    //=============================================================================
    // Phytomer creation callback, per-phytomer growth targets and readouts, live
    // phyllotaxy, per-model leaf inclination distributions (helios-core 1.3.88)
    //=============================================================================

    PYHELIOS_API int setPhytomerCreationFunction(PlantArchitecture* plantarch, const char* shoot_type_label, PhytomerCreationCallback callback) {
        return guardedPhytomerCall(plantarch, "setPhytomerCreationFunction", -1, [&]() {
            if (!shoot_type_label) {
                throw std::invalid_argument("Shoot type label is null");
            }
            const std::string label(shoot_type_label);
            ShootParameters params = plantarch->getCurrentShootParameters(label);
            PhytomerCreationFn& function = params.phytomer_parameters.phytomer_creation_function;
            PhytomerCreationEntry entry = phytomerCreationCallbacks()[plantarch][label];
            // Anything other than the trampoline is the shoot type's own function (e.g. after a library model is reloaded).
            if (function != &phytomerCreationTrampoline) {
                entry.original = function;
            }
            entry.callback = callback;
            function = callback ? &phytomerCreationTrampoline : entry.original;
            plantarch->defineShootType(label, params);
            phytomerCreationCallbacks()[plantarch][label] = entry;
            return 0;
        });
    }

    PYHELIOS_API int setPhytomerCallbackFunction(PlantArchitecture* plantarch, const char* shoot_type_label, PhytomerCallback callback) {
        return guardedPhytomerCall(plantarch, "setPhytomerCallbackFunction", -1, [&]() {
            if (!shoot_type_label) {
                throw std::invalid_argument("Shoot type label is null");
            }
            const std::string label(shoot_type_label);
            ShootParameters params = plantarch->getCurrentShootParameters(label);
            PhytomerCallbackFn& function = params.phytomer_parameters.phytomer_callback_function;
            PhytomerCallbackEntry entry = phytomerCallbacks()[plantarch][label];
            if (function != &phytomerCallbackTrampoline) {
                entry.original = function;
            }
            entry.callback = callback;
            function = callback ? &phytomerCallbackTrampoline : entry.original;
            plantarch->defineShootType(label, params);
            phytomerCallbacks()[plantarch][label] = entry;
            return 0;
        });
    }

    PYHELIOS_API int setFruitPrototypeFunction(PlantArchitecture* plantarch, helios::Context* context, const char* shoot_type_label, PyheliosFruitPrototypeCallback callback) {
        return guardedPhytomerCall(plantarch, "setFruitPrototypeFunction", -1, [&]() {
            installPythonPrototypeFunction(plantarch, context, shoot_type_label, callback, fruitPrototypeSlots(), fruitSlotFunctions(), originalFruitPrototypeFunctions(), "fruit",
                                           [](ShootParameters& params) -> FruitPrototypeFn& { return params.phytomer_parameters.inflorescence.fruit_prototype_function; });
            return 0;
        });
    }

    PYHELIOS_API int setFlowerPrototypeFunction(PlantArchitecture* plantarch, helios::Context* context, const char* shoot_type_label, PyheliosFlowerPrototypeCallback callback) {
        return guardedPhytomerCall(plantarch, "setFlowerPrototypeFunction", -1, [&]() {
            installPythonPrototypeFunction(plantarch, context, shoot_type_label, callback, flowerPrototypeSlots(), flowerSlotFunctions(), originalFlowerPrototypeFunctions(), "flower",
                                           [](ShootParameters& params) -> FlowerPrototypeFn& { return params.phytomer_parameters.inflorescence.flower_prototype_function; });
            return 0;
        });
    }

    PYHELIOS_API int setInternodeMaxLength(PlantArchitecture* plantarch, unsigned int plantID, unsigned int shootID, unsigned int node_index, float length) {
        return guardedPhytomerCall(plantarch, "setInternodeMaxLength", -1, [&]() {
            if (!(length > 0.f) || !std::isfinite(length)) {
                throw std::invalid_argument("Internode max length must be positive and finite, got " + std::to_string(length));
            }
            resolvePhytomerIndexed(plantarch, plantID, shootID, node_index)->setInternodeMaxLength(length);
            return 0;
        });
    }

    PYHELIOS_API int scaleInternodeMaxLength(PlantArchitecture* plantarch, unsigned int plantID, unsigned int shootID, unsigned int node_index, float scale_factor) {
        return guardedPhytomerCall(plantarch, "scaleInternodeMaxLength", -1, [&]() {
            if (!(scale_factor > 0.f)) {
                throw std::invalid_argument("Scale factor must be positive, got " + std::to_string(scale_factor));
            }
            resolvePhytomerIndexed(plantarch, plantID, shootID, node_index)->scaleInternodeMaxLength(scale_factor);
            return 0;
        });
    }

    PYHELIOS_API int scaleLeafPrototypeScale(PlantArchitecture* plantarch, unsigned int plantID, unsigned int shootID, unsigned int node_index, float scale_factor) {
        return guardedPhytomerCall(plantarch, "scaleLeafPrototypeScale", -1, [&]() {
            if (!(scale_factor > 0.f)) {
                throw std::invalid_argument("Scale factor must be positive, got " + std::to_string(scale_factor));
            }
            resolvePhytomerIndexed(plantarch, plantID, shootID, node_index)->scaleLeafPrototypeScale(scale_factor);
            return 0;
        });
    }

    PYHELIOS_API int scaleLeafPrototypeScaleAt(PlantArchitecture* plantarch, unsigned int plantID, unsigned int shootID, unsigned int node_index, unsigned int petiole_index, float scale_factor) {
        return guardedPhytomerCall(plantarch, "scaleLeafPrototypeScale", -1, [&]() {
            if (!(scale_factor > 0.f)) {
                throw std::invalid_argument("Scale factor must be positive, got " + std::to_string(scale_factor));
            }
            const auto phytomer = resolvePhytomerIndexed(plantarch, plantID, shootID, node_index);
            checkPetioleIndex(phytomer->leaf_objIDs.size(), petiole_index, node_index);
            phytomer->scaleLeafPrototypeScale(petiole_index, scale_factor);
            return 0;
        });
    }

    // use_normal = 0 sets a constant angle; otherwise normal(mean, std_dev), which draws from the Context generator for
    // every new phytomer even when std_dev is 0 (as a C++ caller of normalDistribution() does).
    PYHELIOS_API int setShootPhyllotacticAngle(PlantArchitecture* plantarch, unsigned int plantID, unsigned int shootID, float mean_degrees, float std_dev_degrees, int use_normal) {
        return guardedPhytomerCall(plantarch, "setShootPhyllotacticAngle", -1, [&]() {
            if (!std::isfinite(mean_degrees)) {
                throw std::invalid_argument("Mean phyllotactic angle must be finite");
            }
            if (use_normal && (!std::isfinite(std_dev_degrees) || std_dev_degrees < 0.f)) {
                throw std::invalid_argument("Phyllotactic angle standard deviation must be finite and non-negative");
            }
            RandomParameter_float& angle = plantarch->getPlantShoot(plantID, shootID)->shoot_parameters.phytomer_parameters.internode.phyllotactic_angle;
            if (use_normal) {
                angle.normalDistribution(mean_degrees, std_dev_degrees);
            } else {
                angle = mean_degrees;
            }
            return 0;
        });
    }

    PYHELIOS_API float getPhytomerAge(PlantArchitecture* plantarch, unsigned int plantID, unsigned int shootID, unsigned int node_index) {
        return guardedPhytomerCall(plantarch, "getPhytomerAge", -1.f, [&]() { return resolvePhytomerIndexed(plantarch, plantID, shootID, node_index)->age; });
    }

    PYHELIOS_API float getInternodeLength(PlantArchitecture* plantarch, unsigned int plantID, unsigned int shootID, unsigned int node_index) {
        return guardedPhytomerCall(plantarch, "getInternodeLength", -1.f, [&]() { return resolvePhytomerIndexed(plantarch, plantID, shootID, node_index)->getInternodeLength(); });
    }

    PYHELIOS_API float getInternodeRadius(PlantArchitecture* plantarch, unsigned int plantID, unsigned int shootID, unsigned int node_index) {
        return guardedPhytomerCall(plantarch, "getInternodeRadius", -1.f, [&]() { return resolvePhytomerIndexed(plantarch, plantID, shootID, node_index)->getInternodeRadius(); });
    }

    PYHELIOS_API float* getInternodeNodePositions(PlantArchitecture* plantarch, unsigned int plantID, unsigned int shootID, unsigned int node_index, int* count) {
        if (count) *count = 0;
        return guardedPhytomerCall(plantarch, "getInternodeNodePositions", static_cast<float*>(nullptr), [&]() {
            if (!count) {
                throw std::invalid_argument("Count pointer is null");
            }
            return flattenVec3(resolvePhytomerIndexed(plantarch, plantID, shootID, node_index)->getInternodeNodePositions(), count);
        });
    }

    PYHELIOS_API int getInternodeAxisVector(PlantArchitecture* plantarch, unsigned int plantID, unsigned int shootID, unsigned int node_index, float stem_fraction, float* axis) {
        return guardedPhytomerCall(plantarch, "getInternodeAxisVector", -1, [&]() {
            if (!axis) {
                throw std::invalid_argument("Output pointer is null");
            }
            const helios::vec3 v = resolvePhytomerIndexed(plantarch, plantID, shootID, node_index)->getInternodeAxisVector(stem_fraction);
            axis[0] = v.x;
            axis[1] = v.y;
            axis[2] = v.z;
            return 0;
        });
    }

    PYHELIOS_API int getPetioleAxisVector(PlantArchitecture* plantarch, unsigned int plantID, unsigned int shootID, unsigned int node_index, float stem_fraction, unsigned int petiole_index,
                                          float* axis) {
        return guardedPhytomerCall(plantarch, "getPetioleAxisVector", -1, [&]() {
            if (!axis) {
                throw std::invalid_argument("Output pointer is null");
            }
            const auto phytomer = resolvePhytomerIndexed(plantarch, plantID, shootID, node_index);
            checkPetioleIndex(phytomer->petiole_vertices.size(), petiole_index, node_index);
            const helios::vec3 v = phytomer->getPetioleAxisVector(stem_fraction, petiole_index);
            axis[0] = v.x;
            axis[1] = v.y;
            axis[2] = v.z;
            return 0;
        });
    }

    PYHELIOS_API float* getPetioleVertices(PlantArchitecture* plantarch, unsigned int plantID, unsigned int shootID, unsigned int node_index, unsigned int petiole_index, int* count) {
        if (count) *count = 0;
        return guardedPhytomerCall(plantarch, "getPetioleVertices", static_cast<float*>(nullptr), [&]() {
            if (!count) {
                throw std::invalid_argument("Count pointer is null");
            }
            const auto phytomer = resolvePhytomerIndexed(plantarch, plantID, shootID, node_index);
            checkPetioleIndex(phytomer->petiole_vertices.size(), petiole_index, node_index);
            return flattenVec3(phytomer->petiole_vertices.at(petiole_index), count);
        });
    }

    PYHELIOS_API float* getPetioleRadii(PlantArchitecture* plantarch, unsigned int plantID, unsigned int shootID, unsigned int node_index, unsigned int petiole_index, int* count) {
        if (count) *count = 0;
        return guardedPhytomerCall(plantarch, "getPetioleRadii", static_cast<float*>(nullptr), [&]() {
            if (!count) {
                throw std::invalid_argument("Count pointer is null");
            }
            const auto phytomer = resolvePhytomerIndexed(plantarch, plantID, shootID, node_index);
            checkPetioleIndex(phytomer->petiole_radii.size(), petiole_index, node_index);
            static thread_local std::vector<float> static_result;
            static_result = phytomer->petiole_radii.at(petiole_index);
            *count = static_cast<int>(static_result.size());
            return static_result.data();
        });
    }

    // Layout: [petiole_count, leaves_on_petiole_0, ..., leaves_on_petiole_{n-1}, objID...]; *count is the total length.
    PYHELIOS_API unsigned int* getPhytomerLeafObjectIDs(PlantArchitecture* plantarch, unsigned int plantID, unsigned int shootID, unsigned int node_index, int* count) {
        if (count) *count = 0;
        return guardedPhytomerCall(plantarch, "getPhytomerLeafObjectIDs", static_cast<unsigned int*>(nullptr), [&]() {
            if (!count) {
                throw std::invalid_argument("Count pointer is null");
            }
            const auto phytomer = resolvePhytomerIndexed(plantarch, plantID, shootID, node_index);
            static thread_local std::vector<unsigned int> static_result;
            static_result.clear();
            static_result.push_back(static_cast<unsigned int>(phytomer->leaf_objIDs.size()));
            for (const auto& petiole : phytomer->leaf_objIDs) {
                static_result.push_back(static_cast<unsigned int>(petiole.size()));
            }
            for (const auto& petiole : phytomer->leaf_objIDs) {
                static_result.insert(static_result.end(), petiole.begin(), petiole.end());
            }
            *count = static_cast<int>(static_result.size());
            return static_result.data();
        });
    }

    PYHELIOS_API int getLeafBasePosition(PlantArchitecture* plantarch, unsigned int plantID, unsigned int shootID, unsigned int node_index, unsigned int petiole_index, unsigned int leaf_index,
                                         float* position) {
        return guardedPhytomerCall(plantarch, "getLeafBasePosition", -1, [&]() {
            if (!position) {
                throw std::invalid_argument("Output pointer is null");
            }
            const auto phytomer = resolvePhytomerIndexed(plantarch, plantID, shootID, node_index);
            checkPetioleIndex(phytomer->leaf_bases.size(), petiole_index, node_index);
            checkLeafIndex(phytomer->leaf_bases.at(petiole_index).size(), leaf_index, petiole_index);
            const helios::vec3 v = phytomer->getLeafBasePosition(petiole_index, leaf_index);
            position[0] = v.x;
            position[1] = v.y;
            position[2] = v.z;
            return 0;
        });
    }

    PYHELIOS_API int getPlantModelLeafInclinationDistribution(PlantArchitecture* plantarch, const char* plant_model_name, float* mu_nu) {
        return guardedPhytomerCall(plantarch, "getPlantModelLeafInclinationDistribution", -1, [&]() {
            if (!plant_model_name || !mu_nu) {
                throw std::invalid_argument("Null argument");
            }
            const helios::vec2 beta = plantarch->getPlantModelLeafInclinationDistribution(plant_model_name);
            mu_nu[0] = beta.x;
            mu_nu[1] = beta.y;
            return 0;
        });
    }

    PYHELIOS_API int setPlantModelLeafInclinationDistribution(PlantArchitecture* plantarch, const char* plant_model_name, float Beta_mu_inclination, float Beta_nu_inclination) {
        return guardedPhytomerCall(plantarch, "setPlantModelLeafInclinationDistribution", -1, [&]() {
            if (!plant_model_name) {
                throw std::invalid_argument("Plant model name is null");
            }
            plantarch->setPlantModelLeafInclinationDistribution(plant_model_name, Beta_mu_inclination, Beta_nu_inclination);
            return 0;
        });
    }

    PYHELIOS_API int doesPlantModelDeclareLeafInclinationDistribution(PlantArchitecture* plantarch, const char* plant_model_name) {
        return guardedPhytomerCall(plantarch, "doesPlantModelDeclareLeafInclinationDistribution", -1, [&]() {
            if (!plant_model_name) {
                throw std::invalid_argument("Plant model name is null");
            }
            return plantarch->doesPlantModelDeclareLeafInclinationDistribution(plant_model_name) ? 1 : 0;
        });
    }

    PYHELIOS_API float getPlantAvailableNitrogen(PlantArchitecture* plantarch, unsigned int plantID) {
        return guardedPhytomerCall(plantarch, "getPlantAvailableNitrogen", -1.f, [&]() { return plantarch->getPlantAvailableNitrogen(plantID); });
    }

    // ---- helios-core 1.3.89 additions ----

    PYHELIOS_API float getLeafBladeArea(PlantArchitecture* plantarch, unsigned int leaf_objID) {
        return guardedPhytomerCall(plantarch, "getLeafBladeArea", -1.f, [&]() { return plantarch->getLeafBladeArea(leaf_objID); });
    }

    PYHELIOS_API float getShadowLightExposureAtPoint(PlantArchitecture* plantarch, unsigned int plantID, const float* position) {
        return guardedPhytomerCall(plantarch, "getShadowLightExposureAtPoint", -1.f, [&]() {
            if (!position) {
                throw std::invalid_argument("Position array is null");
            }
            return plantarch->getShadowLightExposureAtPoint(plantID, helios::make_vec3(position[0], position[1], position[2]));
        });
    }

    // ---- helios-core 1.3.93 additions ----

    PYHELIOS_API float getSeasonPeakLightExposureAtPoint(PlantArchitecture* plantarch, unsigned int plantID, const float* position) {
        return guardedPhytomerCall(plantarch, "getSeasonPeakLightExposureAtPoint", -1.f, [&]() {
            if (!position) {
                throw std::invalid_argument("Position array is null");
            }
            return plantarch->getSeasonPeakLightExposureAtPoint(plantID, helios::make_vec3(position[0], position[1], position[2]));
        });
    }

    PYHELIOS_API const char* getPlantModelBuildParameterNames(PlantArchitecture* plantarch, const char* plant_model_name, int* count) {
        if (count) *count = 0;
        return guardedPhytomerCall(plantarch, "getPlantModelBuildParameterNames", static_cast<const char*>(nullptr), [&]() -> const char* {
            if (!plant_model_name || !count) {
                throw std::invalid_argument("Plant model name or count pointer is null");
            }
            static thread_local std::string names;
            names.clear();
            const std::vector<std::string> list = plantarch->getPlantModelBuildParameterNames(std::string(plant_model_name));
            for (const std::string& name : list) {
                if (!names.empty()) names += '\n';
                names += name;
            }
            *count = static_cast<int>(list.size());
            return names.c_str();
        });
    }

    PYHELIOS_API float* getPlantBuildParameters(PlantArchitecture* plantarch, unsigned int plantID, const char** names_out, int* count) {
        if (count) *count = 0;
        if (names_out) *names_out = nullptr;
        return guardedPhytomerCall(plantarch, "getPlantBuildParameters", static_cast<float*>(nullptr), [&]() -> float* {
            if (!names_out || !count) {
                throw std::invalid_argument("Output pointer is null");
            }
            static thread_local std::string names;
            static thread_local std::vector<float> values;
            names.clear();
            values.clear();
            for (const auto& [name, value] : plantarch->getPlantBuildParameters(plantID)) {
                if (!names.empty()) names += '\n';
                names += name;
                values.push_back(value);
            }
            *names_out = names.c_str();
            *count = static_cast<int>(values.size());
            return values.data();
        });
    }

    // Draws one realization of a PhytomerParameters with PhytomerParameters::resample(), then writes every
    // distributed field back as a constant holding its draw. The field list is that of
    // PhytomerParameters::resample(); a field resample() leaves alone is left as it was.
    PYHELIOS_API const char* resamplePhytomerParametersJSON(helios::Context* context, const char* json_params) {
        try {
            clearError();
            if (!context) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Context pointer is null");
                return nullptr;
            }
            if (!json_params) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "JSON parameters are null");
                return nullptr;
            }
            std::minstd_rand0* generator = context->getRandomGenerator();
            PhytomerParameters pp(generator);
            jsonToPhytomerParameters(pp, nlohmann::json::parse(json_params), generator);
            pp.resample();

            auto freeze = [](auto& parameter) {
                if (parameter.distribution != "constant") {
                    parameter = parameter.val();
                }
            };
            freeze(pp.internode.pitch);
            freeze(pp.internode.phyllotactic_angle);
            freeze(pp.internode.radius_initial);
            freeze(pp.internode.max_vegetative_buds_per_petiole);
            freeze(pp.internode.max_floral_buds_per_petiole);
            freeze(pp.petiole.pitch);
            freeze(pp.petiole.radius);
            freeze(pp.petiole.length);
            freeze(pp.petiole.curvature);
            freeze(pp.petiole.taper);
            freeze(pp.petiole.flexibility);
            freeze(pp.petiole.flexibility_aging);
            freeze(pp.leaf.leaves_per_petiole);
            freeze(pp.leaf.pitch);
            freeze(pp.leaf.yaw);
            freeze(pp.leaf.roll);
            freeze(pp.leaf.leaflet_offset);
            freeze(pp.leaf.leaflet_scale);
            freeze(pp.leaf.intercalary_leaflet_scale);
            freeze(pp.leaf.prototype_scale);
            freeze(pp.leaf.prototype.leaf_aspect_ratio);
            freeze(pp.leaf.prototype.midrib_fold_fraction);
            freeze(pp.leaf.prototype.longitudinal_curvature_exponent);
            freeze(pp.leaf.prototype.longitudinal_curvature);
            freeze(pp.leaf.prototype.lateral_curvature);
            freeze(pp.leaf.prototype.petiole_roll);
            freeze(pp.leaf.prototype.roll_fraction);
            freeze(pp.leaf.prototype.wave_period);
            freeze(pp.leaf.prototype.wave_amplitude);
            freeze(pp.leaf.prototype.flexibility);
            freeze(pp.leaf.prototype.flexibility_taper);
            freeze(pp.leaf.prototype.flexibility_aging);
            freeze(pp.leaf.prototype.flexibility_aging_max);
            HELIOS_PUSH_IGNORE_DEPRECATED
            freeze(pp.leaf.prototype.leaf_buckle_length);
            freeze(pp.leaf.prototype.leaf_buckle_angle);
            HELIOS_POP_IGNORE_DEPRECATED
            freeze(pp.peduncle.length);
            freeze(pp.peduncle.radius);
            freeze(pp.peduncle.pitch);
            freeze(pp.peduncle.roll);
            freeze(pp.peduncle.yaw);
            freeze(pp.peduncle.curvature);
            freeze(pp.inflorescence.flowers_per_peduncle);
            freeze(pp.inflorescence.flower_offset);
            freeze(pp.inflorescence.pitch);
            freeze(pp.inflorescence.roll);
            freeze(pp.inflorescence.flower_prototype_scale);
            freeze(pp.inflorescence.inflorescence_maturity_period);
            freeze(pp.inflorescence.fruit_prototype_scale);
            freeze(pp.inflorescence.fruit_gravity_factor_fraction);

            static thread_local std::string json_string;
            json_string = phytomerParametersToJSON(pp).dump();
            return json_string.c_str();
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (PhytomerParameters::resample): ") + e.what());
            return nullptr;
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (PhytomerParameters::resample): Unknown error.");
            return nullptr;
        }
    }

    //=============================================================================
    // Library phytomer creation and callback functions by name (Assets.h)
    //=============================================================================

    PYHELIOS_API int setPhytomerCreationFunctionByName(PlantArchitecture* plantarch, const char* shoot_type_label, const char* function_name) {
        return guardedPhytomerCall(plantarch, "setPhytomerCreationFunctionByName", -1, [&]() {
            if (!shoot_type_label) {
                throw std::invalid_argument("Shoot type label is null");
            }
            const PhytomerCreationFn library_function = resolveLibraryPhytomerFunction(libraryPhytomerCreationRegistry(), function_name, "creation");
            const std::string label(shoot_type_label);
            ShootParameters params = plantarch->getCurrentShootParameters(label);
            params.phytomer_parameters.phytomer_creation_function = library_function;
            plantarch->defineShootType(label, params);
            // Shoots built while a Python callback was installed still carry the trampoline; point them at the library function too.
            auto& entries = phytomerCreationCallbacks()[plantarch];
            const auto entry = entries.find(label);
            if (entry != entries.end()) {
                entry->second.callback = nullptr;
                entry->second.original = library_function;
            }
            return 0;
        });
    }

    PYHELIOS_API int setPhytomerCallbackFunctionByName(PlantArchitecture* plantarch, const char* shoot_type_label, const char* function_name) {
        return guardedPhytomerCall(plantarch, "setPhytomerCallbackFunctionByName", -1, [&]() {
            if (!shoot_type_label) {
                throw std::invalid_argument("Shoot type label is null");
            }
            const PhytomerCallbackFn library_function = resolveLibraryPhytomerFunction(libraryPhytomerCallbackRegistry(), function_name, "callback");
            const std::string label(shoot_type_label);
            ShootParameters params = plantarch->getCurrentShootParameters(label);
            params.phytomer_parameters.phytomer_callback_function = library_function;
            plantarch->defineShootType(label, params);
            auto& entries = phytomerCallbacks()[plantarch];
            const auto entry = entries.find(label);
            if (entry != entries.end()) {
                entry->second.callback = nullptr;
                entry->second.original = library_function;
            }
            return 0;
        });
    }

    PYHELIOS_API const char* getPhytomerCreationFunctionName(PlantArchitecture* plantarch, const char* shoot_type_label) {
        return guardedPhytomerCall(plantarch, "getPhytomerCreationFunctionName", static_cast<const char*>(nullptr), [&]() -> const char* {
            if (!shoot_type_label) {
                throw std::invalid_argument("Shoot type label is null");
            }
            static thread_local std::string name;
            name = prototypeFunctionName(libraryPhytomerCreationRegistry(), plantarch->getCurrentShootParameters(std::string(shoot_type_label)).phytomer_parameters.phytomer_creation_function);
            return name.c_str();
        });
    }

    PYHELIOS_API const char* getPhytomerCallbackFunctionName(PlantArchitecture* plantarch, const char* shoot_type_label) {
        return guardedPhytomerCall(plantarch, "getPhytomerCallbackFunctionName", static_cast<const char*>(nullptr), [&]() -> const char* {
            if (!shoot_type_label) {
                throw std::invalid_argument("Shoot type label is null");
            }
            static thread_local std::string name;
            name = prototypeFunctionName(libraryPhytomerCallbackRegistry(), plantarch->getCurrentShootParameters(std::string(shoot_type_label)).phytomer_parameters.phytomer_callback_function);
            return name.c_str();
        });
    }

    PYHELIOS_API const char* getLibraryPhytomerCreationFunctionNames() {
        clearError();
        return joinedRegistryNames(libraryPhytomerCreationRegistry());
    }

    PYHELIOS_API const char* getLibraryPhytomerCallbackFunctionNames() {
        clearError();
        return joinedRegistryNames(libraryPhytomerCallbackRegistry());
    }

    // =========================================================================
    // Plant-level queries: name, phenology stage, base position, stem height,
    // shoot node count, internode object IDs and leaf angle distributions
    // =========================================================================

    PYHELIOS_API const char* determinePhenologyStage(PlantArchitecture* plantarch, unsigned int plantID) {
        return guardedPhytomerCall(plantarch, "determinePhenologyStage", static_cast<const char*>(nullptr), [&]() -> const char* {
            static thread_local std::string stage;
            stage = plantarch->determinePhenologyStage(plantID);
            return stage.c_str();
        });
    }

    PYHELIOS_API const char* getPlantName(PlantArchitecture* plantarch, unsigned int plantID) {
        return guardedPhytomerCall(plantarch, "getPlantName", static_cast<const char*>(nullptr), [&]() -> const char* {
            static thread_local std::string name;
            name = plantarch->getPlantName(plantID);
            return name.c_str();
        });
    }

    PYHELIOS_API unsigned int getShootNodeCount(PlantArchitecture* plantarch, unsigned int plantID, unsigned int shootID) {
        return guardedPhytomerCall(plantarch, "getShootNodeCount", 0u, [&]() -> unsigned int {
            return plantarch->getShootNodeCount(plantID, shootID);
        });
    }

    PYHELIOS_API float getPlantStemHeight(PlantArchitecture* plantarch, unsigned int plantID) {
        return guardedPhytomerCall(plantarch, "getPlantStemHeight", -1.0f, [&]() -> float {
            // helios-core dereferences the plant's first shoot without checking that one exists.
            if (plantarch->getAllShootIDs(plantID).empty()) {
                throw std::runtime_error("Plant with ID of " + std::to_string(plantID) + " has no shoots, so it has no stem height.");
            }
            return plantarch->getPlantStemHeight(plantID);
        });
    }

    PYHELIOS_API int getPlantBasePosition(PlantArchitecture* plantarch, unsigned int plantID, float* position) {
        return guardedPhytomerCall(plantarch, "getPlantBasePosition", -1, [&]() {
            if (!position) {
                throw std::invalid_argument("Output pointer is null");
            }
            const helios::vec3 p = plantarch->getPlantBasePosition(plantID);
            position[0] = p.x;
            position[1] = p.y;
            position[2] = p.z;
            return 0;
        });
    }

    PYHELIOS_API float* getPlantBasePositions(PlantArchitecture* plantarch, const unsigned int* plantIDs, int plant_count, int* count) {
        if (count) *count = 0;
        return guardedPhytomerCall(plantarch, "getPlantBasePosition", static_cast<float*>(nullptr), [&]() {
            if (!count) {
                throw std::invalid_argument("Count pointer is null");
            }
            if (plant_count <= 0 || !plantIDs) {
                throw std::invalid_argument("At least one plant ID is required");
            }
            const std::vector<uint> ids(plantIDs, plantIDs + plant_count);
            return flattenVec3(plantarch->getPlantBasePosition(ids), count);
        });
    }

    PYHELIOS_API int setPlantBasePosition(PlantArchitecture* plantarch, unsigned int plantID, const float* position) {
        return guardedPhytomerCall(plantarch, "setPlantBasePosition", -1, [&]() {
            if (!position) {
                throw std::invalid_argument("Position pointer is null");
            }
            plantarch->setPlantBasePosition(plantID, helios::make_vec3(position[0], position[1], position[2]));
            return 0;
        });
    }

    PYHELIOS_API unsigned int* getPlantInternodeObjectIDs(PlantArchitecture* plantarch, unsigned int plantID, const char* shoot_type_label, int* count) {
        if (count) *count = 0;
        return guardedPhytomerCall(plantarch, "getPlantInternodeObjectIDs", static_cast<unsigned int*>(nullptr), [&]() -> unsigned int* {
            if (!count) {
                throw std::invalid_argument("Count pointer is null");
            }
            static thread_local std::vector<unsigned int> static_result;
            static_result = shoot_type_label ? plantarch->getPlantInternodeObjectIDs(plantID, std::string(shoot_type_label)) : plantarch->getPlantInternodeObjectIDs(plantID);
            *count = static_cast<int>(static_result.size());
            return static_result.data();
        });
    }

    // Shared body for the two angle histograms; one plant uses the single-plant overload, several the multi-plant one.
    typedef std::vector<float> (PlantArchitecture::*PlantAngleDistributionGetter)(uint, uint, bool) const;
    typedef std::vector<float> (PlantArchitecture::*PlantsAngleDistributionGetter)(const std::vector<uint> &, uint, bool) const;
    static float* returnPlantAngleDistribution(PlantArchitecture* plantarch, const unsigned int* plantIDs, int plant_count, unsigned int Nbins, int normalize, int* count, const char* fn,
                                               PlantAngleDistributionGetter single, PlantsAngleDistributionGetter multiple) {
        if (count) *count = 0;
        return guardedPhytomerCall(plantarch, fn, static_cast<float*>(nullptr), [&]() -> float* {
            if (!count) {
                throw std::invalid_argument("Count pointer is null");
            }
            if (plant_count <= 0 || !plantIDs) {
                throw std::invalid_argument("At least one plant ID is required");
            }
            if (Nbins == 0) {
                throw std::invalid_argument("Number of bins must be at least 1");
            }
            static thread_local std::vector<float> static_values;
            if (plant_count == 1) {
                static_values = (plantarch->*single)(plantIDs[0], Nbins, normalize != 0);
            } else {
                static_values = (plantarch->*multiple)(std::vector<uint>(plantIDs, plantIDs + plant_count), Nbins, normalize != 0);
            }
            *count = static_cast<int>(static_values.size());
            return static_values.data();
        });
    }

    PYHELIOS_API float* getPlantLeafInclinationAngleDistribution(PlantArchitecture* plantarch, const unsigned int* plantIDs, int plant_count, unsigned int Nbins, int normalize, int* count) {
        return returnPlantAngleDistribution(plantarch, plantIDs, plant_count, Nbins, normalize, count, "getPlantLeafInclinationAngleDistribution",
                                            &PlantArchitecture::getPlantLeafInclinationAngleDistribution, &PlantArchitecture::getPlantLeafInclinationAngleDistribution);
    }

    PYHELIOS_API float* getPlantLeafAzimuthAngleDistribution(PlantArchitecture* plantarch, const unsigned int* plantIDs, int plant_count, unsigned int Nbins, int normalize, int* count) {
        return returnPlantAngleDistribution(plantarch, plantIDs, plant_count, Nbins, normalize, count, "getPlantLeafAzimuthAngleDistribution",
                                            &PlantArchitecture::getPlantLeafAzimuthAngleDistribution, &PlantArchitecture::getPlantLeafAzimuthAngleDistribution);
    }

    // ---- helios-core 1.3.96: leaf roll, leaf shape, fruit-branch collision, nitrogen pools ---- //

    PYHELIOS_API int setPetioleLeafRoll(PlantArchitecture* plantarch, unsigned int plantID, unsigned int shootID, unsigned int node_index, unsigned int petiole_index, float roll_fraction) {
        return guardedPhytomerCall(plantarch, "setPetioleLeafRoll", -1, [&]() {
            plantarch->setPetioleLeafRoll(plantID, shootID, node_index, petiole_index, roll_fraction);
            return 0;
        });
    }

    PYHELIOS_API int setPlantLeafRoll(PlantArchitecture* plantarch, unsigned int plantID, float roll_fraction) {
        return guardedPhytomerCall(plantarch, "setPlantLeafRoll", -1, [&]() {
            plantarch->setPlantLeafRoll(plantID, roll_fraction);
            return 0;
        });
    }

    // LeafShapeValues flat layout: floats[12] = {aspect_ratio, midrib_fold_fraction, longitudinal_curvature,
    // longitudinal_curvature_exponent, lateral_curvature, petiole_roll, wave_period, wave_amplitude, roll_fraction,
    // lattice_offset.x, lattice_offset.y, lattice_offset.z}; subdivisions[2] = {subdivisions_x, subdivisions_y}.
    PYHELIOS_API int getLeafShape(PlantArchitecture* plantarch, unsigned int plantID, unsigned int shootID, unsigned int node_index, unsigned int petiole_index, unsigned int leaf_index, float* values,
                                  unsigned int* subdivisions) {
        return guardedPhytomerCall(plantarch, "getLeafShape", -1, [&]() {
            if (!values || !subdivisions) {
                throw std::invalid_argument("Output pointer is null");
            }
            const auto phytomer = resolvePhytomerIndexed(plantarch, plantID, shootID, node_index);
            checkPetioleIndex(phytomer->leaf_objIDs.size(), petiole_index, node_index);
            checkLeafIndex(phytomer->leaf_objIDs.at(petiole_index).size(), leaf_index, petiole_index);
            const LeafShapeValues shape = phytomer->getLeafShape(petiole_index, leaf_index);
            values[0] = shape.aspect_ratio;
            values[1] = shape.midrib_fold_fraction;
            values[2] = shape.longitudinal_curvature;
            values[3] = shape.longitudinal_curvature_exponent;
            values[4] = shape.lateral_curvature;
            values[5] = shape.petiole_roll;
            values[6] = shape.wave_period;
            values[7] = shape.wave_amplitude;
            values[8] = shape.roll_fraction;
            values[9] = shape.lattice_offset.x;
            values[10] = shape.lattice_offset.y;
            values[11] = shape.lattice_offset.z;
            subdivisions[0] = shape.subdivisions_x;
            subdivisions[1] = shape.subdivisions_y;
            return 0;
        });
    }

    PYHELIOS_API int reshapeLeaf(PlantArchitecture* plantarch, unsigned int plantID, unsigned int shootID, unsigned int node_index, unsigned int petiole_index, unsigned int leaf_index, const float* values,
                                 const unsigned int* subdivisions) {
        return guardedPhytomerCall(plantarch, "reshapeLeaf", -1, [&]() {
            if (!values || !subdivisions) {
                throw std::invalid_argument("Input pointer is null");
            }
            const auto phytomer = resolvePhytomerIndexed(plantarch, plantID, shootID, node_index);
            checkPetioleIndex(phytomer->leaf_objIDs.size(), petiole_index, node_index);
            checkLeafIndex(phytomer->leaf_objIDs.at(petiole_index).size(), leaf_index, petiole_index);
            phytomer->reshapeLeaf(petiole_index, leaf_index, unpackLeafShape(values, subdivisions));
            return 0;
        });
    }

    PYHELIOS_API int enableFruitBranchCollisionAvoidance(PlantArchitecture* plantarch) {
        return guardedPhytomerCall(plantarch, "enableFruitBranchCollisionAvoidance", -1, [&]() {
            plantarch->enableFruitBranchCollisionAvoidance();
            return 0;
        });
    }

    PYHELIOS_API int disableFruitBranchCollisionAvoidance(PlantArchitecture* plantarch) {
        return guardedPhytomerCall(plantarch, "disableFruitBranchCollisionAvoidance", -1, [&]() {
            plantarch->disableFruitBranchCollisionAvoidance();
            return 0;
        });
    }

    PYHELIOS_API int setFruitBranchCollisionParameters(PlantArchitecture* plantarch, float max_swing_deg, float candidate_refresh_days, float clearance, float settle_rate_deg_per_day) {
        return guardedPhytomerCall(plantarch, "setFruitBranchCollisionParameters", -1, [&]() {
            plantarch->setFruitBranchCollisionParameters(max_swing_deg, candidate_refresh_days, clearance, settle_rate_deg_per_day);
            return 0;
        });
    }

    PYHELIOS_API int enablePlantLeafElevationAngleDistributionTrackingMultiple(PlantArchitecture* plantarch, const unsigned int* plantIDs, unsigned int count, float Beta_mu_inclination,
                                                                                float Beta_nu_inclination, float lambda_degrees) {
        return guardedPhytomerCall(plantarch, "enablePlantLeafElevationAngleDistributionTracking", -1, [&]() {
            if (count > 0 && !plantIDs) {
                throw std::invalid_argument("Plant ID array is null");
            }
            std::vector<uint> ids(plantIDs, plantIDs + count);
            plantarch->enablePlantLeafElevationAngleDistributionTracking(ids, Beta_mu_inclination, Beta_nu_inclination, lambda_degrees);
            return 0;
        });
    }

    PYHELIOS_API float getPlantFruitNitrogen(PlantArchitecture* plantarch, unsigned int plantID) {
        return guardedPhytomerCall(plantarch, "getPlantFruitNitrogen", -1.f, [&]() { return plantarch->getPlantFruitNitrogen(plantID); });
    }

    PYHELIOS_API float getPlantRootNitrogen(PlantArchitecture* plantarch, unsigned int plantID) {
        return guardedPhytomerCall(plantarch, "getPlantRootNitrogen", -1.f, [&]() { return plantarch->getPlantRootNitrogen(plantID); });
    }

    // ---- helios-core 1.3.97: appended measured shoots and in-place reshape query ---- //

    PYHELIOS_API unsigned int appendShootFromNodePositions(PlantArchitecture* plantarch, unsigned int plantID, int parent_shoot_ID, const float* node_positions, const float* node_radii, int node_count, const char* shoot_type_label, const char* growth_shoot_type_label) {
        try {
            clearError();
            if (!plantarch) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "PlantArchitecture pointer is null");
                return 0;
            }
            if (!shoot_type_label || std::strlen(shoot_type_label) == 0) {
                setError(PYHELIOS_ERROR_INVALID_PARAMETER, "Shoot type label cannot be empty");
                return 0;
            }
            std::vector<helios::vec3> positions;
            std::vector<float> radii;
            if (!unpackNodesAndRadii(node_positions, node_radii, node_count, "appendShootFromNodePositions", positions, radii)) {
                return 0;
            }
            if (growth_shoot_type_label && std::strlen(growth_shoot_type_label) > 0) {
                return plantarch->appendShootFromNodePositions(plantID, parent_shoot_ID, positions, radii, std::string(shoot_type_label), std::string(growth_shoot_type_label));
            }
            return plantarch->appendShootFromNodePositions(plantID, parent_shoot_ID, positions, radii, std::string(shoot_type_label));
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (PlantArchitecture::appendShootFromNodePositions): ") + e.what());
            return 0;
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (PlantArchitecture::appendShootFromNodePositions): Unknown error.");
            return 0;
        }
    }

    PYHELIOS_API int canReshapeLeafInPlace(PlantArchitecture* plantarch, unsigned int plantID, unsigned int shootID, unsigned int node_index, unsigned int petiole_index, unsigned int leaf_index, const float* values,
                                           const unsigned int* subdivisions, int* result) {
        return guardedPhytomerCall(plantarch, "canReshapeLeafInPlace", -1, [&]() {
            if (!values || !subdivisions || !result) {
                throw std::invalid_argument("Input or output pointer is null");
            }
            const auto phytomer = resolvePhytomerIndexed(plantarch, plantID, shootID, node_index);
            checkPetioleIndex(phytomer->leaf_objIDs.size(), petiole_index, node_index);
            checkLeafIndex(phytomer->leaf_objIDs.at(petiole_index).size(), leaf_index, petiole_index);
            *result = phytomer->canReshapeLeafInPlace(petiole_index, leaf_index, unpackLeafShape(values, subdivisions)) ? 1 : 0;
            return 0;
        });
    }

    // ---- helios::collision closest-point queries (helios-core 1.3.96) ---- //

    PYHELIOS_API float collisionClosestPointsOnSegments(const float* p1, const float* q1, const float* p2, const float* q2, float* closest1, float* closest2) {
        clearError();
        try {
            if (!p1 || !q1 || !p2 || !q2 || !closest1 || !closest2) { setError(PYHELIOS_ERROR_INVALID_PARAMETER, "ERROR (collision::closestPointsOnSegments): Null pointer argument"); return 0.f; }
            helios::vec3 c1, c2;
            float d2 = helios::collision::closestPointsOnSegments(helios::make_vec3(p1[0], p1[1], p1[2]), helios::make_vec3(q1[0], q1[1], q1[2]), helios::make_vec3(p2[0], p2[1], p2[2]), helios::make_vec3(q2[0], q2[1], q2[2]), c1, c2);
            closest1[0] = c1.x; closest1[1] = c1.y; closest1[2] = c1.z;
            closest2[0] = c2.x; closest2[1] = c2.y; closest2[2] = c2.z;
            return d2;
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (collision::closestPointsOnSegments): ") + e.what()); return 0.f;
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (collision::closestPointsOnSegments): Unknown error."); return 0.f;
        }
    }

    PYHELIOS_API void collisionClosestPointOnTriangle(const float* p, const float* a, const float* b, const float* c, float* out) {
        clearError();
        try {
            if (!p || !a || !b || !c || !out) { setError(PYHELIOS_ERROR_INVALID_PARAMETER, "ERROR (collision::closestPointOnTriangle): Null pointer argument"); return; }
            helios::vec3 r = helios::collision::closestPointOnTriangle(helios::make_vec3(p[0], p[1], p[2]), helios::make_vec3(a[0], a[1], a[2]), helios::make_vec3(b[0], b[1], b[2]), helios::make_vec3(c[0], c[1], c[2]));
            out[0] = r.x; out[1] = r.y; out[2] = r.z;
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (collision::closestPointOnTriangle): ") + e.what());
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (collision::closestPointOnTriangle): Unknown error.");
        }
    }

    PYHELIOS_API float collisionClosestPointsSegmentTriangle(const float* p, const float* q, const float* a, const float* b, const float* c, float* on_segment, float* on_triangle) {
        clearError();
        try {
            if (!p || !q || !a || !b || !c || !on_segment || !on_triangle) { setError(PYHELIOS_ERROR_INVALID_PARAMETER, "ERROR (collision::closestPointsSegmentTriangle): Null pointer argument"); return 0.f; }
            helios::vec3 s_pt, t_pt;
            float d2 = helios::collision::closestPointsSegmentTriangle(helios::make_vec3(p[0], p[1], p[2]), helios::make_vec3(q[0], q[1], q[2]), helios::make_vec3(a[0], a[1], a[2]), helios::make_vec3(b[0], b[1], b[2]), helios::make_vec3(c[0], c[1], c[2]), s_pt, t_pt);
            on_segment[0] = s_pt.x; on_segment[1] = s_pt.y; on_segment[2] = s_pt.z;
            on_triangle[0] = t_pt.x; on_triangle[1] = t_pt.y; on_triangle[2] = t_pt.z;
            return d2;
        } catch (const std::exception& e) {
            setError(PYHELIOS_ERROR_RUNTIME, std::string("ERROR (collision::closestPointsSegmentTriangle): ") + e.what()); return 0.f;
        } catch (...) {
            setError(PYHELIOS_ERROR_UNKNOWN, "ERROR (collision::closestPointsSegmentTriangle): Unknown error."); return 0.f;
        }
    }


    // Nitrogen model controls

    PYHELIOS_API int enableNitrogenModel(PlantArchitecture* plantarch) {
        return guardedPhytomerCall(plantarch, "enableNitrogenModel", -1, [&]() {
            plantarch->enableNitrogenModel();
            return 0;
        });
    }

    PYHELIOS_API int disableNitrogenModel(PlantArchitecture* plantarch) {
        return guardedPhytomerCall(plantarch, "disableNitrogenModel", -1, [&]() {
            plantarch->disableNitrogenModel();
            return 0;
        });
    }

    PYHELIOS_API int isNitrogenModelEnabled(PlantArchitecture* plantarch) {
        return guardedPhytomerCall(plantarch, "isNitrogenModelEnabled", -1, [&]() { return plantarch->isNitrogenModelEnabled() ? 1 : 0; });
    }

    PYHELIOS_API int initializeNitrogenPools(PlantArchitecture* plantarch, float initial_leaf_N_area) {
        return guardedPhytomerCall(plantarch, "initializeNitrogenPools", -1, [&]() {
            plantarch->initializeNitrogenPools(initial_leaf_N_area);
            return 0;
        });
    }

    PYHELIOS_API int initializePlantNitrogenPools(PlantArchitecture* plantarch, unsigned int plantID, float initial_leaf_N_area) {
        return guardedPhytomerCall(plantarch, "initializePlantNitrogenPools", -1, [&]() {
            plantarch->initializePlantNitrogenPools(plantID, initial_leaf_N_area);
            return 0;
        });
    }

    PYHELIOS_API int addPlantNitrogen(PlantArchitecture* plantarch, unsigned int plantID, float amount_gN) {
        return guardedPhytomerCall(plantarch, "addPlantNitrogen", -1, [&]() {
            plantarch->addPlantNitrogen(plantID, amount_gN);
            return 0;
        });
    }

    PYHELIOS_API int addPlantsNitrogen(PlantArchitecture* plantarch, const unsigned int* plantIDs, int plant_count, float amount_gN) {
        return guardedPhytomerCall(plantarch, "addPlantNitrogen", -1, [&]() {
            if (plant_count < 0 || (plant_count > 0 && !plantIDs)) {
                throw std::invalid_argument("Plant ID array is null or its count is negative");
            }
            std::vector<uint> ids(plantIDs, plantIDs + plant_count);
            plantarch->addPlantNitrogen(ids, amount_gN);
            return 0;
        });
    }
} // extern "C"

#endif // PLANTARCHITECTURE_PLUGIN_AVAILABLE
