#include "magtile/core/physical_set_catalog.hpp"

#include <fstream>
#include <set>

#include <nlohmann/json.hpp>

#include "magtile/core/json_io.hpp"

namespace magtile::core {
namespace {

using nlohmann::json;

json loadJsonFile(const std::filesystem::path& file) {
    std::ifstream stream(file);
    if (!stream) {
        throw JsonIoError("无法打开数据文件: " + file.string());
    }
    try {
        return json::parse(stream);
    } catch (const json::parse_error& e) {
        throw JsonIoError("JSON 解析失败 (" + file.string() + "): " + e.what());
    }
}

}  // namespace

void PhysicalSetCatalog::addSet(PhysicalSet set) {
    sets_.push_back(std::move(set));
}

const PhysicalSet* PhysicalSetCatalog::find(const std::string& id) const noexcept {
    for (const auto& set : sets_) {
        if (set.id == id) return &set;
    }
    return nullptr;
}

PhysicalSetCatalog loadPhysicalSetCatalog(const std::filesystem::path& file) {
    const json root = loadJsonFile(file);
    if (!root.contains("sets") || !root["sets"].is_array()) {
        throw JsonIoError("实物套装目录缺少 sets 数组: " + file.string());
    }

    PhysicalSetCatalog catalog;
    std::set<std::string> seen_ids;
    for (const auto& entry : root["sets"]) {
        PhysicalSet set;
        set.id = entry.at("id").get<std::string>();
        if (!seen_ids.insert(set.id).second) {
            throw JsonIoError("实物套装 id 重复: " + set.id);
        }
        set.brand = entry.at("brand").get<std::string>();
        // 文档 schema: name_zh / piece_count_label / pieces; 兼容旧字段名
        if (entry.contains("name_zh")) {
            set.name = entry.at("name_zh").get<std::string>();
        } else {
            set.name = entry.at("name").get<std::string>();
        }
        if (entry.contains("piece_count_label")) {
            set.total_pieces = entry.at("piece_count_label").get<int>();
        } else {
            set.total_pieces = entry.at("total_pieces").get<int>();
        }
        set.tier_scope = entry.value("tier_scope", std::string{});
        set.ui_preset_label = entry.value("ui_preset_label_zh", std::string{});
        if (set.ui_preset_label.empty()) {
            set.ui_preset_label = set.name;
        }

        const json* bom_json = nullptr;
        if (entry.contains("pieces") && entry["pieces"].is_object()) {
            bom_json = &entry["pieces"];
        } else if (entry.contains("bom") && entry["bom"].is_object()) {
            bom_json = &entry["bom"];
        }
        if (bom_json == nullptr) {
            throw JsonIoError("套装 " + set.id + " 缺少 pieces/bom 对象");
        }
        int bom_sum = 0;
        for (const auto& [shape_id, value] : bom_json->items()) {
            if (!tileTypeFromString(shape_id).has_value()) {
                throw JsonIoError("套装 " + set.id + " 含未知片型 \"" + shape_id + "\"");
            }
            if (!value.is_number_integer() || value.get<std::int64_t>() < 0) {
                throw JsonIoError("套装 " + set.id + " 的片型 \"" + shape_id + "\" 数量非法");
            }
            const int count = static_cast<int>(value.get<std::int64_t>());
            set.bom.emplace(shape_id, count);
            bom_sum += count;
        }
        if (bom_sum != set.total_pieces) {
            throw JsonIoError("套装 " + set.id + " 的 piece_count_label (" +
                              std::to_string(set.total_pieces) + ") 与 pieces 合计 (" +
                              std::to_string(bom_sum) + ") 不一致");
        }
        catalog.addSet(std::move(set));
    }
    return catalog;
}

std::map<std::string, int> mergePhysicalSetBom(const PhysicalSetCatalog& catalog,
                                               const std::vector<std::string>& set_ids) {
    std::map<std::string, int> merged;
    for (const auto& id : set_ids) {
        const PhysicalSet* set = catalog.find(id);
        if (set == nullptr) continue;
        for (const auto& [shape_id, count] : set->bom) {
            merged[shape_id] += count;
        }
    }
    return merged;
}

}  // namespace magtile::core
