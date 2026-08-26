#pragma once

// =============================================================
// MagTile Studio - 假计费客户端 (桌面开发档 / 单元测试)
//
// 完整实现 BillingClient 语义但不接任何商店 SDK、不产生真实扣费:
//   - queryProducts: 返回 COMMERCIAL_PLAN §3.1 的三档占位
//     (月度 / 年度主推 / 家庭年度);
//   - purchase: 校验商品 id 后立即"成功", 订阅状态写入
//     ProgressStore settings 表 (progress/subscription_settings
//     契约键, 与界面锁读取同一份), 另记一条"假商店回执"
//     (fake_billing_receipt 键) 模拟商店账户侧的权益记录;
//   - restore: 查假商店回执, 有则重新激活本地订阅 (Restored),
//     无则 NothingToRestore —— 覆盖「本地状态丢失但商店账户仍有
//     权益」的恢复购买闭环;
//   - devSetSubscribed: 开发档「模拟已订阅」开关 (Qt 订阅页开发
//     控件用), 只改本地订阅状态不动回执, 关掉后可用 restore 演练
//     恢复流程。
//
// store 传 nullptr 时退化为纯内存模式 (进程内有效, 不落盘) ——
// 存档打不开时桌面壳的温和降级路径与部分单测用。
// =============================================================

#include <string>
#include <vector>

#include "magtile/billing/billing_client.hpp"

namespace magtile::progress {
class ProgressStore;
}

namespace magtile::billing {

/// 假商店回执在 settings 表中的键名 (仅 FakeBillingClient 读写,
/// 模拟商店账户侧的订阅记录; 正式商店档不使用本键)。
inline constexpr const char* kFakeReceiptSettingKey = "fake_billing_receipt";

class FakeBillingClient final : public BillingClient {
public:
    /// store 为订阅状态持久化目标 (不持有, 生命期由调用方保证);
    /// nullptr = 纯内存模式。构造时从 settings 表载入既有订阅状态。
    explicit FakeBillingClient(progress::ProgressStore* store = nullptr);

    [[nodiscard]] std::vector<ProductInfo> queryProducts() override;
    [[nodiscard]] PurchaseOutcome purchase(const std::string& product_id) override;
    [[nodiscard]] PurchaseOutcome restore() override;
    [[nodiscard]] bool subscriptionActive() const override { return active_; }

    /// 生效中的档位 id (未订阅时为空串); 订阅页状态卡展示用。
    [[nodiscard]] const std::string& activeProductId() const noexcept { return product_id_; }

    /// 开发档「模拟已订阅」开关: 直接设置本地订阅状态并持久化。
    /// 打开时以年度档为模拟档位; 关闭只清本地状态、保留假回执
    /// (可再用 restore 演练恢复购买)。
    void devSetSubscribed(bool active);

private:
    void persist();

    progress::ProgressStore* store_ = nullptr;  ///< 可空 (纯内存模式)
    bool active_ = false;
    std::string product_id_;
};

}  // namespace magtile::billing
