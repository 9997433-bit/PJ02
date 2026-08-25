#include "magtile/billing/store_billing_client.hpp"

namespace magtile::billing {

// 空实现档统一返回"商店不可用"语义 —— 界面退回「即将上线」占位,
// 绝不误报已订阅。真实接法与商店分流宏见头文件档说明。

std::vector<ProductInfo> StoreBillingClient::queryProducts() {
#if defined(MAGTILE_BILLING_WINDOWS_STORE)
    // TODO(V1 付费闭环): StoreContext.GetAssociatedStoreProductsAsync
    static_assert(false, "Windows 商店档尚未接入, 勿在未实现前开启此宏");
#elif defined(MAGTILE_BILLING_GOOGLE_PLAY)
    // TODO(V1 付费闭环): JNI 桥 -> BillingClient.queryProductDetailsAsync
    static_assert(false, "Google Play 档尚未接入, 勿在未实现前开启此宏");
#endif
    return {};
}

PurchaseOutcome StoreBillingClient::purchase(const std::string& /*product_id*/) {
    return PurchaseOutcome::Unavailable;
}

PurchaseOutcome StoreBillingClient::restore() { return PurchaseOutcome::Unavailable; }

bool StoreBillingClient::subscriptionActive() const { return false; }

}  // namespace magtile::billing
