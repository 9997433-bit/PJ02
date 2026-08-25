#pragma once

// =============================================================
// MagTile Studio - 年龄分层模式 (Age Bands)
//
// UI_UX_SPEC.md §2: Onboarding 时由家长选择孩子年龄段, 全局切换
// UX 模式 (模型库布局密度 / 文字量 / TTS 自动朗读 / 相机控制等)。
// 年龄段仅存本地设置项 (ProgressStore settings 表), 不构成儿童
// 个人信息采集 (SECURITY_AND_PRIVACY.md §3)。
//
// 本枚举是纯逻辑层定义, 不依赖 UI / 平台, 供核心库 / 渲染层 /
// 平台外壳共享同一套分层语义。
// =============================================================

#include <optional>
#include <string_view>

namespace magtile::core {

/// 年龄段模式: 三档分层体验 (UI_UX_SPEC.md §2 对照表)。
enum class AgeMode {
    Age4_6,    ///< 4-6 岁「启蒙模式」: 超大卡片、无筛选器、自动朗读
    Age7_9,    ///< 7-9 岁「标准模式」: 默认档, 标准卡片密度与筛选
    Age10_12,  ///< 10-12 岁「进阶模式」: 全量筛选、完整说明与技巧提示
};

/// 未设置时的默认档: 标准模式 (7-9 岁)。
inline constexpr AgeMode kDefaultAgeMode = AgeMode::Age7_9;

/// 稳定的持久化标识 (存入 settings 表, 禁止随意改名), 如 "age_4_6"。
[[nodiscard]] std::string_view toString(AgeMode mode) noexcept;

/// 面向家长的中文展示名, 如 "4-6 岁 · 启蒙模式"。
[[nodiscard]] std::string_view displayNameZh(AgeMode mode) noexcept;

/// 持久化标识 -> 枚举; 无法识别 (含旧版脏数据) 返回 nullopt。
[[nodiscard]] std::optional<AgeMode> ageModeFromString(std::string_view name) noexcept;

/// 周岁 -> 年龄段 (4~6 / 7~9 / 10~12); 超出产品适龄范围返回 nullopt。
[[nodiscard]] std::optional<AgeMode> ageModeFromAgeYears(int age_years) noexcept;

}  // namespace magtile::core
