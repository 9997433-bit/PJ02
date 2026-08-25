#pragma once

// =============================================================
// MagTile Studio - 教程搭建步骤
// =============================================================

#include <string>
#include <vector>

namespace magtile::core {

/// 教程中的一个搭建步骤。
/// 步骤按 step_number 从 1 开始严格递增; 所有步骤的 tiles_to_add
/// 合并后必须恰好覆盖 ModelDefinition::final_assembly 中的全部磁力片。
struct BuildStep {
    int step_number = 0;
    std::string description;                    ///< 中文步骤说明 (面向最终用户)
    std::string tip;                            ///< 可选的中文提示 / 注意事项
    std::vector<std::string> tiles_to_add;      ///< 本步骤新增磁力片的 id 列表
    std::vector<std::string> highlight_tiles;   ///< 需要高亮提示的已有磁力片 (通常为连接参照物)
};

}  // namespace magtile::core
