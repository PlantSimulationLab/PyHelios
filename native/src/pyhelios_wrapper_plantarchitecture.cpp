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

#ifdef PLANTARCHITECTURE_PLUGIN_AVAILABLE
#include "../include/pyhelios_wrapper_plantarchitecture.h"
#include "PlantArchitecture.h"
#include "../../helios-core/plugins/radiation/lib/json/json.hpp"

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
// functions declared in Assets.h are referenced by name. shared_ptr<Phytomer>
// callbacks (phytomer_creation_function/phytomer_callback_function) are not bindable
// and are intentionally not exposed.
typedef uint (*LeafPrototypeFn)(helios::Context*, LeafPrototype*, int);
typedef uint (*FlowerPrototypeFn)(helios::Context*, uint, bool);
typedef uint (*FruitPrototypeFn)(helios::Context*, uint);

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
        {"OliveFlowerPrototype", &OliveFlowerPrototype},
        {"PistachioFlowerPrototype", &PistachioFlowerPrototype},
        {"PuncturevineFlowerPrototype", &PuncturevineFlowerPrototype},
        {"RedbudFlowerPrototype", &RedbudFlowerPrototype},
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
        {"GrapevineFruitPrototype", &GrapevineFruitPrototype},
        {"MaizeTasselPrototype", &MaizeTasselPrototype},
        {"MaizeEarPrototype", &MaizeEarPrototype},
        {"OliveFruitPrototype", &OliveFruitPrototype},
        {"PistachioFruitPrototype", &PistachioFruitPrototype},
        {"RedbudFruitPrototype", &RedbudFruitPrototype},
        {"RiceSpikePrototype", &RiceSpikePrototype},
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

// ---- LeafPrototype <-> JSON ----
nlohmann::json leafPrototypeToJSON(const LeafPrototype& p) {
    nlohmann::json j;
    j["leaf_aspect_ratio"] = randomParameterFloatToJSON(p.leaf_aspect_ratio);
    j["midrib_fold_fraction"] = randomParameterFloatToJSON(p.midrib_fold_fraction);
    j["longitudinal_curvature"] = randomParameterFloatToJSON(p.longitudinal_curvature);
    j["lateral_curvature"] = randomParameterFloatToJSON(p.lateral_curvature);
    j["petiole_roll"] = randomParameterFloatToJSON(p.petiole_roll);
    j["wave_period"] = randomParameterFloatToJSON(p.wave_period);
    j["wave_amplitude"] = randomParameterFloatToJSON(p.wave_amplitude);
    j["leaf_buckle_length"] = randomParameterFloatToJSON(p.leaf_buckle_length);
    j["leaf_buckle_angle"] = randomParameterFloatToJSON(p.leaf_buckle_angle);
    j["leaf_offset"] = vec3ToJSON(p.leaf_offset);
    j["subdivisions"] = p.subdivisions;
    j["unique_prototypes"] = p.unique_prototypes;
    j["build_petiolule"] = p.build_petiolule;
    j["OBJ_model_file"] = p.OBJ_model_file;
    nlohmann::json tex = nlohmann::json::object();
    for (const auto& kv : p.leaf_texture_file) {
        tex[std::to_string(kv.first)] = kv.second;
    }
    j["leaf_texture_file"] = tex;
    j["prototype_function"] = prototypeFunctionName(leafPrototypeRegistry(), p.prototype_function);
    return j;
}

void jsonToLeafPrototype(LeafPrototype& p, const nlohmann::json& j, std::minstd_rand0* generator) {
    if (j.contains("leaf_aspect_ratio")) p.leaf_aspect_ratio = jsonToRandomParameterFloat(j["leaf_aspect_ratio"], generator);
    if (j.contains("midrib_fold_fraction")) p.midrib_fold_fraction = jsonToRandomParameterFloat(j["midrib_fold_fraction"], generator);
    if (j.contains("longitudinal_curvature")) p.longitudinal_curvature = jsonToRandomParameterFloat(j["longitudinal_curvature"], generator);
    if (j.contains("lateral_curvature")) p.lateral_curvature = jsonToRandomParameterFloat(j["lateral_curvature"], generator);
    if (j.contains("petiole_roll")) p.petiole_roll = jsonToRandomParameterFloat(j["petiole_roll"], generator);
    if (j.contains("wave_period")) p.wave_period = jsonToRandomParameterFloat(j["wave_period"], generator);
    if (j.contains("wave_amplitude")) p.wave_amplitude = jsonToRandomParameterFloat(j["wave_amplitude"], generator);
    if (j.contains("leaf_buckle_length")) p.leaf_buckle_length = jsonToRandomParameterFloat(j["leaf_buckle_length"], generator);
    if (j.contains("leaf_buckle_angle")) p.leaf_buckle_angle = jsonToRandomParameterFloat(j["leaf_buckle_angle"], generator);
    if (j.contains("leaf_offset")) p.leaf_offset = jsonToVec3(j["leaf_offset"], p.leaf_offset);
    if (j.contains("subdivisions")) p.subdivisions = j["subdivisions"];
    if (j.contains("unique_prototypes")) p.unique_prototypes = j["unique_prototypes"];
    if (j.contains("build_petiolule")) p.build_petiolule = j["build_petiolule"];
    if (j.contains("OBJ_model_file")) p.OBJ_model_file = j["OBJ_model_file"].get<std::string>();
    if (j.contains("leaf_texture_file")) {
        p.leaf_texture_file.clear();
        for (auto it = j["leaf_texture_file"].begin(); it != j["leaf_texture_file"].end(); ++it) {
            p.leaf_texture_file[std::stoi(it.key())] = it.value().get<std::string>();
        }
    }
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
    j["petiole"] = pe;

    nlohmann::json lf;
    lf["leaves_per_petiole"] = randomParameterIntToJSON(pp.leaf.leaves_per_petiole);
    lf["pitch"] = randomParameterFloatToJSON(pp.leaf.pitch);
    lf["yaw"] = randomParameterFloatToJSON(pp.leaf.yaw);
    lf["roll"] = randomParameterFloatToJSON(pp.leaf.roll);
    lf["leaflet_offset"] = randomParameterFloatToJSON(pp.leaf.leaflet_offset);
    lf["leaflet_scale"] = randomParameterFloatToJSON(pp.leaf.leaflet_scale);
    lf["prototype_scale"] = randomParameterFloatToJSON(pp.leaf.prototype_scale);
    lf["prototype"] = leafPrototypeToJSON(pp.leaf.prototype);
    j["leaf"] = lf;

    nlohmann::json pd;
    pd["length"] = randomParameterFloatToJSON(pp.peduncle.length);
    pd["radius"] = randomParameterFloatToJSON(pp.peduncle.radius);
    pd["pitch"] = randomParameterFloatToJSON(pp.peduncle.pitch);
    pd["roll"] = randomParameterFloatToJSON(pp.peduncle.roll);
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
    inf["flower_prototype_function"] = prototypeFunctionName(flowerPrototypeRegistry(), pp.inflorescence.flower_prototype_function);
    inf["fruit_prototype_function"] = prototypeFunctionName(fruitPrototypeRegistry(), pp.inflorescence.fruit_prototype_function);
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
    }
    if (j.contains("leaf")) {
        const nlohmann::json& lf = j["leaf"];
        if (lf.contains("leaves_per_petiole")) pp.leaf.leaves_per_petiole = jsonToRandomParameterInt(lf["leaves_per_petiole"], generator);
        if (lf.contains("pitch")) pp.leaf.pitch = jsonToRandomParameterFloat(lf["pitch"], generator);
        if (lf.contains("yaw")) pp.leaf.yaw = jsonToRandomParameterFloat(lf["yaw"], generator);
        if (lf.contains("roll")) pp.leaf.roll = jsonToRandomParameterFloat(lf["roll"], generator);
        if (lf.contains("leaflet_offset")) pp.leaf.leaflet_offset = jsonToRandomParameterFloat(lf["leaflet_offset"], generator);
        if (lf.contains("leaflet_scale")) pp.leaf.leaflet_scale = jsonToRandomParameterFloat(lf["leaflet_scale"], generator);
        if (lf.contains("prototype_scale")) pp.leaf.prototype_scale = jsonToRandomParameterFloat(lf["prototype_scale"], generator);
        if (lf.contains("prototype")) jsonToLeafPrototype(pp.leaf.prototype, lf["prototype"], generator);
    }
    if (j.contains("peduncle")) {
        const nlohmann::json& pd = j["peduncle"];
        if (pd.contains("length")) pp.peduncle.length = jsonToRandomParameterFloat(pd["length"], generator);
        if (pd.contains("radius")) pp.peduncle.radius = jsonToRandomParameterFloat(pd["radius"], generator);
        if (pd.contains("pitch")) pp.peduncle.pitch = jsonToRandomParameterFloat(pd["pitch"], generator);
        if (pd.contains("roll")) pp.peduncle.roll = jsonToRandomParameterFloat(pd["roll"], generator);
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
        resolvePrototypeFunction(flowerPrototypeRegistry(), inf, "flower_prototype_function", pp.inflorescence.flower_prototype_function, "flower");
        resolvePrototypeFunction(fruitPrototypeRegistry(), inf, "fruit_prototype_function", pp.inflorescence.fruit_prototype_function, "fruit");
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
        {"leaf_remobilization_efficiency", n.leaf_remobilization_efficiency},
        {"remobilization_age_threshold", n.remobilization_age_threshold},
        {"fruit_N_area", n.fruit_N_area},
    };
}

NitrogenParameters jsonToNitrogenParameters(const nlohmann::json& j) {
    NitrogenParameters n;
    #define PYH_N(field) if (j.contains(#field)) n.field = j[#field];
    PYH_N(target_leaf_N_area) PYH_N(minimum_leaf_N_area) PYH_N(root_allocation_fraction)
    PYH_N(max_N_accumulation_rate) PYH_N(leaf_remobilization_efficiency)
    PYH_N(remobilization_age_threshold) PYH_N(fruit_N_area)
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

    // Growth parameters
    j["phyllochron_min"] = randomParameterFloatToJSON(params.phyllochron_min);
    j["elongation_rate_max"] = randomParameterFloatToJSON(params.elongation_rate_max);
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

    // Nested phytomer parameters (internode/petiole/leaf/peduncle/inflorescence + leaf prototype)
    j["phytomer_parameters"] = phytomerParametersToJSON(params.phytomer_parameters);

    return j;
}

ShootParameters jsonToShootParameters(const nlohmann::json& j, std::minstd_rand0* generator) {
    ShootParameters params(generator);

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

    // Growth parameters
    if (j.contains("phyllochron_min")) params.phyllochron_min = jsonToRandomParameterFloat(j["phyllochron_min"], generator);
    if (j.contains("elongation_rate_max")) params.elongation_rate_max = jsonToRandomParameterFloat(j["elongation_rate_max"], generator);
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

    // Child shoot types
    if (j.contains("child_shoot_types")) {
        std::vector<std::string> labels = j["child_shoot_types"]["labels"];
        std::vector<float> probs = j["child_shoot_types"]["probabilities"];
        params.defineChildShootTypes(labels, probs);
    }

    // Nested phytomer parameters. ShootParameters(generator) does NOT propagate the
    // generator into phytomer_parameters (it is default-constructed with a null
    // generator), so rebuild it with the real generator before overlaying JSON values.
    // This guarantees every nested RandomParameter has a valid generator even for
    // fields absent from the JSON.
    params.phytomer_parameters = PhytomerParameters(generator);
    if (j.contains("phytomer_parameters")) {
        jsonToPhytomerParameters(params.phytomer_parameters, j["phytomer_parameters"], generator);
    }

    return params;
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
                                             float elastic_modulus, float wood_density, float damping_ratio,
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
            params.damping_ratio = damping_ratio;
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
            ShootParameters params = jsonToShootParameters(j, generator);
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

} // extern "C"

#endif // PLANTARCHITECTURE_PLUGIN_AVAILABLE