#pragma once

// =============================================================
// MagTile Studio - 年龄段模式设置 (存于 ProgressStore settings 表)
//
// UI_UX_SPEC.md §2 / §8: 年龄段由家长在 Onboarding / 家长区选择,
// 全局切换分层体验; 仅存本地 SQLite 设置项, 不构成儿童个人信息
// 采集 (SECURITY_AND_PRIVACY.md §3)。
//
// 以独立小模块提供类型化读写 (基于 ProgressStore 的通用键值
// settings 表), 核心枚举见 core/age_mode.hpp。
// =============================================================

#include "magtile/core/age_mode.hpp"
#include "magtile/progress/progress_store.hpp"

namespace magtile::progress {

/// 年龄段模式在 settings 表中的键名 (持久化契约, 禁止改名)。
inline constexpr const char* kAgeModeSettingKey = "age_mode";

/// 保存年龄段模式 (立即落盘)。
void setAgeMode(ProgressStore& store, core::AgeMode mode);

/// 读取年龄段模式; 从未设置或存量脏值时返回默认档
/// (core::kDefaultAgeMode, 即 7-9 岁标准模式), 调用方无需判空。
[[nodiscard]] core::AgeMode getAgeMode(const ProgressStore& store);

}  // namespace magtile::progress
