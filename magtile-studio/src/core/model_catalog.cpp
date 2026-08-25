#include "magtile/core/model_catalog.hpp"

#include <algorithm>
#include <fstream>
#include <set>

#include <nlohmann/json.hpp>

#include "magtile/core/json_io.hpp"

namespace magtile::core {
namespace {

using nlohmann::json;

/// 用模型 JSON 的完整定义生成 (或补全) 目录条目。
ModelCatalogEntry entryFromModelFile(const std::filesystem::path& model_file) {
    const ModelDefinition model = loadModelDefinition(model_file);
    ModelCatalogEntry entry;
    entry.id = model.id;
    entry.file = model_file;
    entry.name = model.name;
    entry.name_en = model.name_en;
    entry.description = model.description;
    entry.difficulty = model.difficulty;
    entry.total_pieces = model.total_pieces;
    entry.step_count = static_cast<int>(model.steps.size());
    entry.tags = model.tags;
    return entry;
}

/// 列出 models/ 目录下的模型 JSON, 按文件名排序保证稳定顺序。
std::vector<std::filesystem::path> listModelFiles(const std::filesystem::path& models_dir) {
    std::vector<std::filesystem::path> files;
    std::error_code ec;
    for (const auto& dir_entry : std::filesystem::directory_iterator(models_dir, ec)) {
        if (dir_entry.is_regular_file() && dir_entry.path().extension() == ".json") {
            files.push_back(dir_entry.path());
        }
    }
    if (ec) {
        throw JsonIoError("无法扫描模型目录 " + models_dir.string() + ": " + ec.message());
    }
    std::sort(files.begin(), files.end());
    return files;
}

/// 把目录未登记的模型文件补录到条目末尾 (id 冲突的文件跳过,
/// 以目录登记为准)。
void appendUnregisteredModels(const std::filesystem::path& models_dir,
                              std::vector<ModelCatalogEntry>& entries,
                              std::set<std::string>& seen_ids) {
    if (!std::filesystem::exists(models_dir)) return;
    std::set<std::string> referenced_files;
    for (const auto& entry : entries) {
        std::error_code ec;
        const auto canonical = std::filesystem::weakly_canonical(entry.file, ec);
        referenced_files.insert((ec ? entry.file : canonical).string());
    }
    for (const auto& file : listModelFiles(models_dir)) {
        std::error_code ec;
        const auto canonical = std::filesystem::weakly_canonical(file, ec);
        if (referenced_files.count((ec ? file : canonical).string()) > 0) continue;
        ModelCatalogEntry entry = entryFromModelFile(file);
        if (!seen_ids.insert(entry.id).second) continue;
        entries.push_back(std::move(entry));
    }
}

}  // namespace

std::vector<ModelCatalogEntry> loadModelCatalog(const std::filesystem::path& data_dir) {
    const std::filesystem::path catalog_file = data_dir / "model_catalog.json";
    if (!std::filesystem::exists(catalog_file)) {
        std::vector<ModelCatalogEntry> entries;
        std::set<std::string> seen_ids;
        appendUnregisteredModels(data_dir / "models", entries, seen_ids);
        return entries;
    }

    std::ifstream stream(catalog_file);
    if (!stream) {
        throw JsonIoError("无法打开模型库目录: " + catalog_file.string());
    }
    json root;
    try {
        root = json::parse(stream);
    } catch (const json::parse_error& e) {
        throw JsonIoError("JSON 解析失败 (" + catalog_file.string() + "): " + e.what());
    }
    if (!root.contains("models") || !root["models"].is_array()) {
        throw JsonIoError("模型库目录缺少 models 数组: " + catalog_file.string());
    }

    std::vector<ModelCatalogEntry> entries;
    std::set<std::string> seen_ids;
    for (const auto& item : root["models"]) {
        if (!item.contains("id")) {
            throw JsonIoError("模型库目录条目缺少 id 字段: " + catalog_file.string());
        }
        const auto id = item["id"].get<std::string>();
        if (!seen_ids.insert(id).second) {
            throw JsonIoError("模型库目录中 id 重复: " + id);
        }

        const auto relative = item.value("file", "models/" + id + ".json");
        const std::filesystem::path model_file = data_dir / relative;
        if (!std::filesystem::exists(model_file)) {
            throw JsonIoError("模型库目录条目 " + id +
                              " 引用的模型文件不存在: " + model_file.string());
        }

        // 元数据齐全时直接使用 (模型库秒开); 缺字段时加载模型 JSON 补全
        const bool has_metadata = item.contains("name") && item.contains("difficulty") &&
                                  item.contains("total_pieces") && item.contains("step_count");
        ModelCatalogEntry entry;
        if (has_metadata) {
            entry.id = id;
            entry.file = model_file;
            entry.name = item["name"].get<std::string>();
            entry.name_en = item.value("name_en", std::string{});
            entry.description = item.value("description", std::string{});
            entry.difficulty = item["difficulty"].get<int>();
            entry.total_pieces = item["total_pieces"].get<int>();
            entry.step_count = item["step_count"].get<int>();
            if (item.contains("tags")) {
                for (const auto& tag : item["tags"]) {
                    entry.tags.push_back(tag.get<std::string>());
                }
            }
        } else {
            entry = entryFromModelFile(model_file);
            if (entry.id != id) {
                throw JsonIoError("模型库目录条目 " + id + " 与模型文件内 id (" + entry.id +
                                  ") 不一致");
            }
        }

        if (entry.difficulty < ModelDefinition::kMinDifficulty ||
            entry.difficulty > ModelDefinition::kMaxDifficulty) {
            throw JsonIoError("模型库目录条目 " + id + " 的难度必须在 1~5 之间, 实际为 " +
                              std::to_string(entry.difficulty));
        }
        entries.push_back(std::move(entry));
    }

    // 内容制作期新模型未登记也能进库 (登记条目优先, 补录排在末尾)
    appendUnregisteredModels(data_dir / "models", entries, seen_ids);
    return entries;
}

}  // namespace magtile::core
