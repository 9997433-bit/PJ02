#include "magtile/billing/fake_billing_client.hpp"

#include "magtile/progress/progress_store.hpp"
#include "magtile/progress/subscription_settings.hpp"

namespace magtile::billing {

namespace {

/// 三档占位商品 (COMMERCIAL_PLAN §3.1; 正式价格以商店后台为准)。
const std::vector<ProductInfo>& placeholderProducts() {
    static const std::vector<ProductInfo> kProducts = {
        {"sub_monthly", "月度订阅", "¥28 / 月", "先试试水, 随时取消", false},
        {"sub_yearly", "年度订阅", "¥198 / 年", "相当于每月 ¥16.5, 7 天无理由退款", true},
        {"sub_family_yearly", "家庭年度", "¥268 / 年", "最多 4 个儿童档案 + 6 台设备", false},
    };
    return kProducts;
}

[[nodiscard]] bool isKnownProduct(const std::string& product_id) {
    for (const ProductInfo& product : placeholderProducts()) {
        if (product.product_id == product_id) return true;
    }
    return false;
}

}  // namespace

FakeBillingClient::FakeBillingClient(progress::ProgressStore* store) : store_(store) {
    if (store_ != nullptr) {
        active_ = progress::getSubscriptionActive(*store_);
        product_id_ = progress::getSubscriptionProductId(*store_);
    }
}

std::vector<ProductInfo> FakeBillingClient::queryProducts() { return placeholderProducts(); }

PurchaseOutcome FakeBillingClient::purchase(const std::string& product_id) {
    if (!isKnownProduct(product_id)) return PurchaseOutcome::Unavailable;
    active_ = true;
    product_id_ = product_id;
    persist();
    // 假商店回执: 模拟商店账户侧的权益记录, restore 据此恢复
    if (store_ != nullptr) store_->setSetting(kFakeReceiptSettingKey, product_id);
    return PurchaseOutcome::Purchased;
}

PurchaseOutcome FakeBillingClient::restore() {
    // 纯内存模式没有"商店账户", 只能回放进程内状态
    if (store_ == nullptr) {
        return active_ ? PurchaseOutcome::Restored : PurchaseOutcome::NothingToRestore;
    }
    const auto receipt = store_->getSetting(kFakeReceiptSettingKey);
    if (!receipt.has_value() || receipt->empty() || !isKnownProduct(*receipt)) {
        return PurchaseOutcome::NothingToRestore;
    }
    active_ = true;
    product_id_ = *receipt;
    persist();
    return PurchaseOutcome::Restored;
}

void FakeBillingClient::devSetSubscribed(bool active) {
    active_ = active;
    if (active && product_id_.empty()) product_id_ = "sub_yearly";  // 模拟档位: 年度主推
    if (!active) product_id_.clear();
    persist();
}

void FakeBillingClient::persist() {
    if (store_ == nullptr) return;
    progress::setSubscriptionActive(*store_, active_, product_id_);
}

}  // namespace magtile::billing
