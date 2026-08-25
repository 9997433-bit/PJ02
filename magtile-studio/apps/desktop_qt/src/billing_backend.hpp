#pragma once

// =============================================================
// MagTile Studio (Qt) - 计费后端桥 (订阅/IAP 适配层, COMMERCIAL_PLAN §2.2)
//
// SubscriptionPage.qml 与 billing::BillingClient 抽象层之间的桥:
// 订阅页主 CTA (购买) / 恢复购买 / 订阅状态展示只面向本桥, 换商店
// 实现零 QML 改动。订阅状态经 progress/subscription_settings 契约
// 键持久化到 ProgressStore settings 表 (独立连接, SQLite 同库多
// 连接安全), 免费层锁 (DetailPage/LibraryPage) 读同一状态。
//
// 客户端选择 (编译期分流, 本地开发档不引入真实 SDK/密钥):
//   - 默认 (桌面开发档): FakeBillingClient —— 完整付费闭环但零
//     真实扣费; devControlsEnabled 时订阅页额外显示「模拟已订阅」
//     开发开关;
//   - MAGTILE_BILLING_WINDOWS_STORE (根 CMake 选项, 仅 MSIX 商店包):
//     StoreBillingClient 真实 WinRT StoreContext 接线 —— 商品表查到
//     才亮价格卡 (storeAvailable), 构造时先做启动静默恢复 (商店许可
//     证为权威来源), 购买/恢复写同一契约键;
//   - 仅 MAGTILE_BILLING_STORE (其余商店档): StoreBillingClient 空
//     实现骨架 —— storeAvailable=false, 订阅页退回「即将上线」占位。
//   接法与商品 id 约定统一见
//   include/magtile/billing/store_billing_client.hpp 文档。
//
// 存档打不开只降级不崩溃 (P3 零挫败): FakeBillingClient 退化为
// 纯内存模式, 订阅状态在当前运行内有效, 不落盘。
// =============================================================

#include <QObject>
#include <QString>
#include <QVariantList>
#include <filesystem>
#include <memory>

#include "magtile/billing/billing_client.hpp"
#include "magtile/progress/progress_store.hpp"

namespace magtile::qtui {

class BillingBackend final : public QObject {
    Q_OBJECT
    /// 订阅当前是否有效 (免费层锁与订阅页状态卡的读取口径)。
    Q_PROPERTY(bool subscriptionActive READ subscriptionActive NOTIFY billingChanged)
    /// 生效中的档位中文名 (如 "年度订阅"), 未订阅时为空串。
    Q_PROPERTY(QString activePlanName READ activePlanName NOTIFY billingChanged)
    /// 商店是否可用: false = 空实现档 (订阅页退回「即将上线」占位)。
    Q_PROPERTY(bool storeAvailable READ storeAvailable CONSTANT)
    /// 开发控件开关: true 时订阅页显示「模拟已订阅」切换 (Debug 构建
    /// 默认开, Release 桌面档经 --dev-billing 开; 商店档恒关)。
    Q_PROPERTY(bool devControlsEnabled READ devControlsEnabled CONSTANT)
    /// 是否为假计费档 (FakeBillingClient): 订阅页 CTA 据此标注
    /// 「开发模拟, 不产生扣费」; 商店档 (真实扣费) 为 false。
    Q_PROPERTY(bool simulatedBilling READ simulatedBilling CONSTANT)

public:
    explicit BillingBackend(std::filesystem::path db_file, bool dev_controls,
                            QObject* parent = nullptr);
    ~BillingBackend() override;

    [[nodiscard]] bool subscriptionActive() const { return client_->subscriptionActive(); }
    [[nodiscard]] QString activePlanName() const;
    [[nodiscard]] bool storeAvailable() const noexcept { return store_available_; }
    [[nodiscard]] bool devControlsEnabled() const noexcept { return dev_controls_; }
    [[nodiscard]] bool simulatedBilling() const noexcept { return simulated_; }

    /// 可购档位列表 (订阅页三卡数据源): 每项 {productId, name,
    /// priceText, blurb, recommended}; 商店不可用时为空列表。
    Q_INVOKABLE QVariantList products() const;

    /// 订阅页主 CTA: 发起购买, 返回给家长看的温和结果文案
    /// (成功 / 取消 / 即将上线, 永不出现"失败"字样)。
    Q_INVOKABLE QString purchase(const QString& product_id);

    /// 「恢复购买」: 从商店账户回执恢复订阅, 返回温和结果文案。
    Q_INVOKABLE QString restore();

    /// 开发档「模拟已订阅」开关 (devControlsEnabled 时订阅页可见;
    /// 非开发档调用被忽略, QML 侧误接线也不会改变订阅状态)。
    Q_INVOKABLE void devSetSubscribed(bool active);

signals:
    void billingChanged();

private:
    std::unique_ptr<progress::ProgressStore> store_;  ///< 打开失败时为空 (只降级不崩溃)
    std::unique_ptr<billing::BillingClient> client_;
    std::vector<billing::ProductInfo> product_cache_;  ///< 构造时查询一次 (档位表静态)
    bool store_available_ = false;
    bool dev_controls_ = false;
    bool simulated_ = false;  ///< true = FakeBillingClient (开发模拟档)
};

}  // namespace magtile::qtui
