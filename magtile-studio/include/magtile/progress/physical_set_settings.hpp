#pragma once

// =============================================================
// MagTile Studio - 用户拥有的实物套装 (存于 ProgressStore settings 表)
//
// UI_UX_SPEC.md §10.2: 库存录入页展示「我的套装」, 多选后一键预填
// 合并 BOM; 拥有清单落盘供下次进入页面恢复选中态。
// =============================================================

#include <string>
#include <vector>

#include "magtile/progress/progress_store.hpp"

namespace magtile::progress {

/// 用户拥有的实物套装 id 列表在 settings 表中的键名 (持久化契约, 禁止改名)。
inline constexpr const char* kOwnedPhysicalSetsSettingKey = "owned_physical_sets";

/// 保存用户拥有的实物套装 id 列表 (JSON 数组字符串落盘)。
void setOwnedPhysicalSets(ProgressStore& store, const std::vector<std::string>& set_ids);

/// 读取用户拥有的实物套装 id 列表; 从未设置或脏值时返回空表。
[[nodiscard]] std::vector<std::string> getOwnedPhysicalSets(const ProgressStore& store);

}  // namespace magtile::progress
