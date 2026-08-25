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

#if defined(MAGTILE_BILLING_STORE) || defined(MAGTILE_BILLING_WINDOWS_STORE)
    // 正式商店档: StoreBillingClient 持有商店接线 (Windows 商店档为
    // WinRT StoreContext 真实实现, 其余商店档为空实现骨架); 订阅状态
    // 写同一 progress/subscription_settings 契约键。接法与商品 id
    // 约定见 include/magtile/billing/store_billing_client.hpp 文档。
    client_ = std::make_unique<billing::StoreBillingClient>(store_.get());
    simulated_ = false;
    dev_controls_ = false;  // 商店档绝不暴露模拟开关
    (void)dev_controls;
#else
    // 桌面开发档: 假计费走通完整付费闭环 (零真实扣费), 订阅状态经
    // progress/subscription_settings 契约键持久化
    client_ = std::make_unique<billing::FakeBillingClient>(store_.get());
    simulated_ = true;
    dev_controls_ = dev_controls;
#endif
#if defined(MAGTILE_BILLING_WINDOWS_STORE)
    // 启动静默恢复 (与 Android MagTileApplication 同口径): 商店许可
    // 证是权威来源 —— 换机 / 重装 / 他端购买启动即生效; 明确无订阅
    // 清本地过期凭证 (宁可锁), 查询不可用 (Unavailable) 不动本地宽限
    // 凭证。AddOnLicenses 读系统缓存的许可证, 本地快查不等网络。
    (void)client_->restore();
#endif
    product_cache_ = client_->queryProducts();
#if defined(MAGTILE_BILLING_WINDOWS_STORE)
    // Windows 商店档: 商品表真查到了才亮价格卡; 无包身份 / 无网 /
    // 后台未配商品时退回「即将上线」占位 (绝不显示空价格卡)
    store_available_ = !product_cache_.empty();
#elif defined(MAGTILE_BILLING_STORE)
    store_available_ = false;  // 其余商店档: 空实现骨架, 界面退回占位
#else
    store_available_ = true;  // 桌面开发档: 假计费闭环恒可用
#endif
}

BillingBackend::~BillingBackend() = default;

QString BillingBackend::activePlanName() const {
    if (!client_->subscriptionActive()) return {};
    std::string active_id;
    if (const auto* fake = dynamic_cast<const billing::FakeBillingClient*>(client_.get());
        fake != nullptr) {
        active_id = fake->activeProductId();
    } else if (const auto* real =
                   dynamic_cast<const billing::StoreBillingClient*>(client_.get());
               real != nullptr) {
        active_id = real->activeProductId();  // 商店档: 契约键载入的档位记录
    }
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
            // 开发模拟标注只出现在假计费档; 商店档是真实扣费, 不得误标
            return simulated_
                       ? QStringLiteral("订阅已开通 (开发模拟, 未产生任何扣费) —— 全库已解锁")
                       : QStringLiteral("订阅已开通 —— 全库已解锁");
        case billing::PurchaseOutcome::Cancelled:
            return QStringLiteral("已取消, 随时可以再来");
        default:
            // Unavailable: 温和占位, 永不说"失败"。Windows 商店档购买链路
            // 已接线, Unavailable 只可能是商店暂时联系不上 (无网 / 商店
            // 服务没回应), 不能再说「正在准备中」误导家长以为功能没上线
#if defined(MAGTILE_BILLING_WINDOWS_STORE)
            return QStringLiteral("商店暂时没有回应, 稍后再试一次就好 —— 免费模型现在就能玩");
#else
            return QStringLiteral("订阅功能正在准备中, 上线后会在这里开放 —— 免费模型现在就能玩");
#endif
    }
}

QString BillingBackend::restore() {
    const billing::PurchaseOutcome outcome = client_->restore();
    emit billingChanged();
    switch (outcome) {
        case billing::PurchaseOutcome::Restored:
            // 与购买成功同口径: 「开发模拟」只在假计费档标注, 商店档不标
            return simulated_ ? QStringLiteral("已恢复订阅 (开发模拟) —— 全库重新解锁")
                              : QStringLiteral("已恢复订阅 —— 全库重新解锁");
        case billing::PurchaseOutcome::NothingToRestore:
            return QStringLiteral("这个账户下暂时没有可恢复的订阅");
        default:
            // Unavailable: Windows 商店档恢复链路已接线 (AddOnLicenses),
            // 拿不到结果只可能是商店暂时联系不上; 其余档保持「随正式版
            // 开放」占位。本地已有的宽限期凭证不受影响 (查询不可用不动)
#if defined(MAGTILE_BILLING_WINDOWS_STORE)
            return QStringLiteral("商店暂时没有回应, 稍后再试一次就好 —— 已有的订阅不会丢");
#else
            return QStringLiteral("恢复购买将随正式商店版开放");
#endif
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
