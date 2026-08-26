#pragma once

// =============================================================
// MagTile Studio - 成就系统: 档位定义与完成链路写库统一收口
//
// UI_UX_SPEC.md §4.5 / §7.1: 成就只与搭建行为挂钩, 按已完成模型数
// 1/3/10/30 分档。本模块是三端 (GL / Qt / Android JNI) 唯一的档位
// 权威定义与完成链路唯一的写库触发点:
//   - kAchievementTiers: 档位表 (id / 标题 / 达成条件 / 阈值),
//     展示层 (Qt StudioBackend::achievementsList / Android JNI
//     progressOverviewJson) 与写库共用同一份, 口径不可能分叉。
//     徽章 emoji 不在此处定义 (增补平面字符过不了 JNI NewStringUTF
//     的 Modified UTF-8), 由各端按 id 映射;
//   - unlockAchievementsOnComplete(): 完成链路唯一写库入口 ——
//     ProgressStore::markCompleted 之后调用, 按存档当前已完成
//     模型数把所有达档成就补齐写入 (幂等: 已解锁的不重写、不覆盖
//     首次解锁时刻)。老存档 (历史版本只写过 first_model_completed,
//     3/10/30 档只在展示层判定从不落库) 在下次任意模型完成时自动
//     补录全部达档成就 —— 不丢不重; 展示层保留 "完成数达档即点亮"
//     兜底, 补录前后界面口径不变。
//
// 纯逻辑层, 不依赖任何 UI 框架 —— 与 age_settings / data_privacy
// 同一模式, 三端外壳共用同一份触发契约。
// =============================================================

#include <string>
#include <vector>

#include "magtile/progress/progress_store.hpp"

namespace magtile::progress {

/// 成就档位 (按已完成模型数分档)。
struct AchievementTier {
    const char* id;           ///< 成就标识 (achievements 表主键, 禁止改名)
    const char* title;        ///< 徽章标题 (中文, 三端展示同文案)
    const char* condition;    ///< 一句话达成条件 (未点亮时展示, §7.1)
    int completed_threshold;  ///< 达成所需的已完成模型数
};

/// 分档表: 1/3/10/30, 阈值严格升序 (三端唯一权威定义, 新增档位只改
/// 这里, 写库与展示自动同步)。
inline constexpr AchievementTier kAchievementTiers[] = {
    {"first_model_completed", "首搭达成", "完成第 1 个模型", 1},
    {"three_models_completed", "小小建造家", "完成 3 个模型", 3},
    {"ten_models_completed", "建造能手", "完成 10 个模型", 10},
    {"thirty_models_completed", "磁力片大师", "完成 30 个模型", 30},
};

/// 完成链路成就统一收口 (唯一写库触发点): 读存档已完成模型数, 把
/// 所有达档且尚未解锁的成就写入存档, 返回本次新解锁的成就 id (按
/// 档位表顺序; 无新解锁返回空)。幂等: 重复完成 / 重复调用不产生新
/// 记录, 不覆盖首次解锁时刻。调用时机: markCompleted 之后 (使完成
/// 数包含刚完成的模型)。读写失败抛 ProgressError, 调用方按 P3 零
/// 挫败策略温和降级 (完成庆祝照常, 下次完成自动补录)。
std::vector<std::string> unlockAchievementsOnComplete(ProgressStore& store);

}  // namespace magtile::progress
