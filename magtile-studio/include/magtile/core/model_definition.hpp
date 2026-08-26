#pragma once

// =============================================================
// MagTile Studio - 模型定义
// =============================================================

#include <map>
#include <string>
#include <vector>

#include "magtile/core/build_step.hpp"
#include "magtile/core/tile_instance.hpp"

namespace magtile::core {

/// 一个完整的搭建模型: 最终成品 + 分步教程。
class ModelDefinition {
public:
    static constexpr int kMinDifficulty = 1;
    static constexpr int kMaxDifficulty = 5;

    std::string id;             ///< 模型唯一标识, 与文件名一致, 如 "castle_foundation_01"
    std::string name;           ///< 中文名称
    std::string name_en;        ///< 英文名称 (可选)
    std::string description;    ///< 中文简介
    int difficulty = kMinDifficulty;  ///< 难度 1(入门) ~ 5(大师)
    int total_pieces = 0;       ///< 磁力片总数 (加载时会与 final_assembly 校验)
    std::vector<std::string> tags;          ///< 分类标签, 如 "城堡"、"进阶"
    std::vector<TileInstance> final_assembly;  ///< 最终成品的全部磁力片
    std::vector<BuildStep> steps;              ///< 分步教程

    /// 按 id 查找磁力片, 不存在返回 nullptr。
    [[nodiscard]] const TileInstance* findTile(const std::string& tile_id) const;

    /// 返回前 step_count 个步骤累计放置的磁力片 (用于分步渲染与分步物理校验)。
    [[nodiscard]] std::vector<const TileInstance*> tilesUpToStep(int step_count) const;

    /// 按形状统计用量, 用于生成 "所需磁力片清单"。
    [[nodiscard]] std::map<TileType, int> pieceCountByType() const;

private:
    mutable std::map<std::string, const TileInstance*> tile_index_;  ///< 惰性构建的 id 索引
    void ensureIndex() const;
};

}  // namespace magtile::core
