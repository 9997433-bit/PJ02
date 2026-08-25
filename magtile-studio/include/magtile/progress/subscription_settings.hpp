#pragma once

// =============================================================
// MagTile Studio - 订阅状态持久化 (存于 ProgressStore settings 表)
//
// COMMERCIAL_PLAN.md §2.2 付费闭环的本地凭证层: 订阅是否有效与
// 对应商品档位, 由计费适配层 (billing/billing_client.hpp) 在购买 /
// 恢复购买成功后写入, 由界面 (Qt 订阅页 / 模型详情锁) 读取。
//
// 与年龄段 (age_settings) / 无障碍 (ui_settings) 同一模式: 基于
// ProgressStore 通用键值表的类型化读写, 纯逻辑层零 UI 依赖 ——
// Qt 版 / GL 版 / 移动端外壳共用同一份持久化契约。
//
// 安全口径: 缺键 / 脏值一律按「未订阅」处理 (宁可锁, 不放行) ——
// 与免费层锁的方向相反 (is_free 缺数据时宁可放行), 因为这里守的
// 是付费权益而不是免费内容。本地明文只是宽限期凭证 (离线优先,
// COMMERCIAL_PLAN §4.4); 正式商店档以商店回执为准, 见
// billing/store_billing_client.hpp。
// =============================================================

#include <string>

#include "magtile/progress/progress_store.hpp"

namespace magtile::progress {

/// 订阅是否有效在 settings 表中的键名 (持久化契约, 禁止改名)。
inline constexpr const char* kSubscriptionActiveSettingKey = "subscription_active";
/// 生效中的订阅商品档位 id 在 settings 表中的键名 (持久化契约, 禁止改名)。
inline constexpr const char* kSubscriptionProductSettingKey = "subscription_product_id";

/// 保存订阅状态 (立即落盘); product_id 为生效档位 (如 "sub_yearly"),
/// active = false 时清空档位记录。
void setSubscriptionActive(ProgressStore& store, bool active, const std::string& product_id);

/// 读取订阅状态; 缺键或脏值一律返回 false (未订阅, 宁可锁不放行)。
[[nodiscard]] bool getSubscriptionActive(const ProgressStore& store);

/// 读取生效中的订阅商品档位 id; 未订阅或从未写入时返回空串。
[[nodiscard]] std::string getSubscriptionProductId(const ProgressStore& store);

}  // namespace magtile::progress
