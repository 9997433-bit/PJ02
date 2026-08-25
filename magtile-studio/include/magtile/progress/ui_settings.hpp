#pragma once

// =============================================================
// MagTile Studio - 界面无障碍设置 (存于 ProgressStore settings 表)
//
// UI_UX_SPEC.md §4.7 / §8: 正文字号三档缩放 (100% / 125% / 150%)
// 与「减少动效」开关由家长在家长区设置页调整; 仅存本地 SQLite
// 设置项, 不构成儿童个人信息采集 (SECURITY_AND_PRIVACY.md §3)。
//
// 与年龄段设置 (age_settings.hpp) 同一模式: 基于 ProgressStore
// 通用键值表的类型化读写, 纯逻辑层不依赖任何 UI 框架 —— Qt 版 /
// GL 版 / 未来移动端外壳共用同一份持久化契约。
// =============================================================

#include "magtile/progress/progress_store.hpp"

namespace magtile::progress {

/// 字号缩放档位在 settings 表中的键名 (持久化契约, 禁止改名)。
inline constexpr const char* kFontScaleSettingKey = "font_scale_percent";
/// 减少动效开关在 settings 表中的键名 (持久化契约, 禁止改名)。
inline constexpr const char* kReduceMotionSettingKey = "reduce_motion";
/// 步骤朗读总开关在 settings 表中的键名 (持久化契约, 禁止改名;
/// UI_UX_SPEC.md §4.2, Qt 版 TtsBackend 与设置页读写同一个键)。
inline constexpr const char* kTtsEnabledSettingKey = "tts_enabled";

/// 字号缩放合法档位 (UI_UX_SPEC.md §4.7 阅读友好三档)。
inline constexpr int kFontScaleTiers[] = {100, 125, 150};

/// percent 是否为合法档位 (100 / 125 / 150)。
[[nodiscard]] bool isValidFontScalePercent(int percent) noexcept;

/// 保存字号缩放档位 (立即落盘); 非法档位直接忽略, 不毒化存档。
void setFontScalePercent(ProgressStore& store, int percent);

/// 读取字号缩放档位; 从未设置或存量脏值时返回 100 (标准档)。
[[nodiscard]] int getFontScalePercent(const ProgressStore& store);

/// 保存「减少动效」开关 (立即落盘)。
void setReduceMotion(ProgressStore& store, bool reduce);

/// 读取「减少动效」开关; 从未设置或脏值时返回 false (动效开启)。
[[nodiscard]] bool getReduceMotion(const ProgressStore& store);

/// 保存步骤朗读总开关 (立即落盘)。
void setTtsEnabled(ProgressStore& store, bool enabled);

/// 读取步骤朗读总开关; 从未设置时返回 true (§4.2 默认开,
/// 非 "0" 的存量脏值同样按开处理, 与 TtsBackend 读取口径一致)。
[[nodiscard]] bool getTtsEnabled(const ProgressStore& store);

}  // namespace magtile::progress
