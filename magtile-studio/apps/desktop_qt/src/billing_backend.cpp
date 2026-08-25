#include "billing_backend.hpp"

#include <QVariantMap>
#include <utility>

#include "magtile/billing/fake_billing_client.hpp"
#include "magtile/billing/store_billing_client.hpp"

namespace magtile::qtui {

namespace {

QString fromUtf8(const std::string& s) {
    return QString::fromUtf8(s.data(), static_cast<int>(s.size()));
}

}  // namespace

BillingBackend::BillingBackend(std::filesystem::path db_file, bool dev_controls, QObject* parent)
    : QObject(parent) {
    try {
        store_ = std::make_unique<progress::ProgressStore>(std::move(db_file));
    } catch (const progress::ProgressError&) {
        store_.reset();  // 存档打不开只降级: 假计费退化为纯内存模式
    }

#if defined(MAGTILE_BILLING_STORE)
    // 正式商店档: 空实现骨架 (storeAvailable=false, 界面退回「即将上线」)。
    // Windows 商店 / Google Play 的真实接法与商品 id 约定见
    // include/magtile/billing/store_billing_client.hpp 文档。
    client_ = std::make_unique<billing::StoreBillingClient>();
    store_available_ = false;
    dev_controls_ = false;  // 商店档绝不暴露模拟开关
    (void)dev_controls;
#else
    // 桌面开发档: 假计费走通完整付费闭环 (零真实扣费), 订阅状态经
    // progress/subscription_settings 契约键持久化
    client_ = std::make_unique<billing::FakeBillingClient>(store_.get());
    store_available_ = true;
    dev_controls_ = dev_controls;
#endif
    product_cache_ = client_->queryProducts();
}

BillingBackend::~BillingBackend() = default;

QString BillingBackend::activePlanName() const {
    const auto* fake = dynamic_cast<const billing::FakeBillingClient*>(client_.get());
    if (fake == nullptr || !fake->subscriptionActive()) return {};
    const std::string& active_id = fake->activeProductId();
    for (const billing::ProductInfo& product : product_cache_) {
        if (product.product_id == active_id) return fromUtf8(product.name_zh);
    }
    return QStringLiteral("订阅");  // 档位记录缺失时的温和兜底
}

QVariantList BillingBackend::products() const {
    QVariantList list;
    for (const billing::ProductInfo& product : product_cache_) {
        QVariantMap entry;
        entry.insert(QStringLiteral("productId"), fromUtf8(product.product_id));
        entry.insert(QStringLiteral("name"), fromUtf8(product.name_zh));
        entry.insert(QStringLiteral("priceText"), fromUtf8(product.price_text));
        entry.insert(QStringLiteral("blurb"), fromUtf8(product.blurb_zh));
        entry.insert(QStringLiteral("recommended"), product.recommended);
        list.push_back(entry);
    }
    return list;
}

QString BillingBackend::purchase(const QString& product_id) {
    const billing::PurchaseOutcome outcome = client_->purchase(product_id.toStdString());
    emit billingChanged();
    switch (outcome) {
        case billing::PurchaseOutcome::Purchased:
            return QStringLiteral("订阅已开通 (开发模拟, 未产生任何扣费) —— 全库已解锁");
        case billing::PurchaseOutcome::Cancelled:
            return QStringLiteral("已取消, 随时可以再来");
        default:
            // Unavailable (空实现档 / 未知商品): 温和占位, 永不说"失败"
            return QStringLiteral("订阅功能正在准备中, 上线后会在这里开放 —— 免费模型现在就能玩");
    }
}

QString BillingBackend::restore() {
    const billing::PurchaseOutcome outcome = client_->restore();
    emit billingChanged();
    switch (outcome) {
        case billing::PurchaseOutcome::Restored:
            return QStringLiteral("已恢复订阅 —— 全库重新解锁");
        case billing::PurchaseOutcome::NothingToRestore:
            return QStringLiteral("这个账户下暂时没有可恢复的订阅");
        default:
            return QStringLiteral("恢复购买将随正式商店版开放");
    }
}

void BillingBackend::devSetSubscribed(bool active) {
    if (!dev_controls_) return;  // 非开发档忽略: 误接线也改不了订阅状态
    if (auto* fake = dynamic_cast<billing::FakeBillingClient*>(client_.get()); fake != nullptr) {
        fake->devSetSubscribed(active);
        emit billingChanged();
    }
}

}  // namespace magtile::qtui
