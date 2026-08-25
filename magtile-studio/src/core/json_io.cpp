#include "magtile/core/json_io.hpp"

#include <fstream>
#include <set>
#include <sstream>

#include <nlohmann/json.hpp>

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

Vec3 parseVec3(const json& j, const std::string& field) {
    if (!j.is_array() || j.size() != 3) {
        throw JsonIoError("字段 " + field + " 必须是长度为 3 的数组");
    }
    return {j[0].get<double>(), j[1].get<double>(), j[2].get<double>()};
}

TileType parseTileType(const json& j, const std::string& where) {
    const auto key = j.get<std::string>();
    const auto type = tileTypeFromString(key);
    if (!type) {
        throw JsonIoError(where + ": 未知的磁力片形状 \"" + key + "\"");
    }
    return *type;
}

TileColor parseTileColor(const json& j, const std::string& where) {
    const auto key = j.get<std::string>();
    const auto color = tileColorFromString(key);
    if (!color) {
        throw JsonIoError(where + ": 未知的颜色 \"" + key + "\"");
    }
    return *color;
}

}  // namespace

TileCatalog loadTileCatalog(const std::filesystem::path& file) {
    const json root = loadJsonFile(file);
    if (!root.contains("tiles") || !root["tiles"].is_array()) {
        throw JsonIoError("形状目录缺少 tiles 数组: " + file.string());
    }

    TileCatalog catalog;
    for (const auto& entry : root["tiles"]) {
        TileShape shape;
        shape.type = parseTileType(entry.at("type"), "形状目录");
        shape.name_zh = entry.at("name_zh").get<std::string>();
        shape.name_en = entry.value("name_en", std::string{});
        shape.description_zh = entry.value("description_zh", std::string{});

        for (const auto& v : entry.at("vertices")) {
            if (!v.is_array() || v.size() != 2) {
                throw JsonIoError("形状 " + shape.name_zh + " 的顶点必须是 [x, y] 数组");
            }
            shape.vertices.push_back({v[0].get<double>(), v[1].get<double>()});
        }
        if (shape.vertices.size() < 3) {
            throw JsonIoError("形状 " + shape.name_zh + " 至少需要 3 个顶点");
        }

        for (const auto& idx : entry.at("magnet_edges")) {
            const int edge = idx.get<int>();
            if (edge < 0 || edge >= static_cast<int>(shape.vertices.size())) {
                throw JsonIoError("形状 " + shape.name_zh + " 的磁力边索引越界: " +
                                  std::to_string(edge));
            }
            shape.magnet_edge_indices.push_back(edge);
        }
        catalog.addShape(std::move(shape));
    }
    return catalog;
}

ModelDefinition loadModelDefinition(const std::filesystem::path& file) {
    const json root = loadJsonFile(file);

    ModelDefinition model;
    model.id = root.at("id").get<std::string>();
    model.name = root.at("name").get<std::string>();
    model.name_en = root.value("name_en", std::string{});
    model.description = root.value("description", std::string{});
    model.difficulty = root.at("difficulty").get<int>();
    model.total_pieces = root.at("total_pieces").get<int>();
    if (root.contains("tags")) {
        for (const auto& tag : root["tags"]) {
            model.tags.push_back(tag.get<std::string>());
        }
    }

    if (model.difficulty < ModelDefinition::kMinDifficulty ||
        model.difficulty > ModelDefinition::kMaxDifficulty) {
        throw JsonIoError("模型 " + model.id + " 的难度必须在 1~5 之间, 实际为 " +
                          std::to_string(model.difficulty));
    }

    // ---- final_assembly ------------------------------------------
    std::set<std::string> seen_ids;
    for (const auto& entry : root.at("final_assembly")) {
        TileInstance tile;
        tile.id = entry.at("id").get<std::string>();
        tile.type = parseTileType(entry.at("type"), "模型 " + model.id);
        tile.position = parseVec3(entry.at("position"), "position");
        tile.rotation_deg = parseVec3(entry.at("rotation"), "rotation");
        tile.color = parseTileColor(entry.at("color"), "模型 " + model.id);

        if (!seen_ids.insert(tile.id).second) {
            throw JsonIoError("模型 " + model.id + " 中磁力片 id 重复: " + tile.id);
        }
        model.final_assembly.push_back(std::move(tile));
    }

    if (model.total_pieces != static_cast<int>(model.final_assembly.size())) {
        std::ostringstream oss;
        oss << "模型 " << model.id << " 的 total_pieces (" << model.total_pieces
            << ") 与 final_assembly 数量 (" << model.final_assembly.size() << ") 不一致";
        throw JsonIoError(oss.str());
    }

    // ---- steps -----------------------------------------------------
    for (const auto& entry : root.at("steps")) {
        BuildStep step;
        step.step_number = entry.at("step_number").get<int>();
        step.description = entry.at("description").get<std::string>();
        step.tip = entry.value("tip", std::string{});
        for (const auto& tile_id : entry.at("tiles_to_add")) {
            step.tiles_to_add.push_back(tile_id.get<std::string>());
        }
        if (entry.contains("highlight_tiles")) {
            for (const auto& tile_id : entry["highlight_tiles"]) {
                step.highlight_tiles.push_back(tile_id.get<std::string>());
            }
        }
        model.steps.push_back(std::move(step));
    }

    // 步骤引用的磁力片必须存在
    for (const auto& step : model.steps) {
        for (const auto& tile_id : step.tiles_to_add) {
            if (model.findTile(tile_id) == nullptr) {
                throw JsonIoError("模型 " + model.id + " 第 " + std::to_string(step.step_number) +
                                  " 步引用了不存在的磁力片: " + tile_id);
            }
        }
        for (const auto& tile_id : step.highlight_tiles) {
            if (model.findTile(tile_id) == nullptr) {
                throw JsonIoError("模型 " + model.id + " 第 " + std::to_string(step.step_number) +
                                  " 步高亮了不存在的磁力片: " + tile_id);
            }
        }
    }

    return model;
}

}  // namespace magtile::core
