#pragma once

// =============================================================
// MagTile Studio - 家长数据控制: 本地数据导出 (JSON)
//
// SECURITY_AND_PRIVACY.md §3 / §4 (COPPA C4 · 《儿童个人信息网络
// 保护规定》Z8): 家长可查看、导出、删除全部本地数据。本模块把
// ProgressStore 里的全部用户数据 (进度 / 成就 / 磁力片库存 / 设置
// —— 即 §3.1 数据清单的本地全集, 除此之外应用没有任何用户数据)
// 序列化为自描述 JSON 文本; 写文件 / 展示由各平台外壳完成 (Qt 版
// PrivacyBackend / Android JNI exportLocalDataJson), 三端同一格式。
// 「删除」走 ProgressStore::clearAllData (单事务原子清空)。
//
// 纯逻辑层, 不依赖任何 UI 框架 —— 与 age_settings / ui_settings
// 同一模式, 桌面 / 移动端外壳共用同一份导出契约。
// =============================================================

#include <string>

#include "magtile/progress/progress_store.hpp"

namespace magtile::progress {

/// 导出格式标识 (JSON 顶层 "format" 字段, 导出契约, 禁止改名)。
inline constexpr const char* kExportFormatId = "magtile_local_data_export";
/// 导出格式版本 (JSON 顶层 "format_version" 字段); 结构变更时递增。
inline constexpr int kExportFormatVersion = 1;

/// 导出全部本地数据为 JSON 文本 (UTF-8, 缩进 2 空格, 家长可直接
/// 用任意文本编辑器阅读):
///   {"format": "magtile_local_data_export", "format_version": 1,
///    "exported_at": <unix 秒>,
///    "model_progress": [{"model_id","current_step","completed_at",
///                        "play_seconds","favorited","updated_at"}, ...],
///    "achievements":   [{"id","unlocked_at"}, ...],
///    "tile_inventory": {"square": 24, ...},
///    "settings":       {"age_mode": "age_7_9", ...}}
/// 读库失败抛 ProgressError (界面侧温和降级, 不弹「失败」)。
[[nodiscard]] std::string exportLocalDataJson(const ProgressStore& store);

}  // namespace magtile::progress
