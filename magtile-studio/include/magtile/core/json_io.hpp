#pragma once

// =============================================================
// MagTile Studio - JSON 序列化 (加载目录与模型)
// 依赖 third_party/nlohmann/json.hpp, 仅在 .cpp 中包含。
// =============================================================

#include <filesystem>
#include <stdexcept>
#include <string>

#include "magtile/core/model_definition.hpp"
#include "magtile/core/tile_catalog.hpp"

namespace magtile::core {

/// 数据文件解析失败时抛出, what() 为中文错误信息。
class JsonIoError : public std::runtime_error {
public:
    using std::runtime_error::runtime_error;
};

/// 从 data/tile_catalog.json 加载形状目录。
[[nodiscard]] TileCatalog loadTileCatalog(const std::filesystem::path& file);

/// 从 data/models/*.json 加载模型定义 (含结构性校验:
/// id 唯一、total_pieces 一致、步骤引用存在、difficulty 取值合法)。
[[nodiscard]] ModelDefinition loadModelDefinition(const std::filesystem::path& file);

}  // namespace magtile::core
