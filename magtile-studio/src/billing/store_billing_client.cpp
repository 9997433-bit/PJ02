#include "magtile/billing/store_billing_client.hpp"

namespace magtile::billing {

// 桌面档统一返回"商店不可用"语义 —— 界面退回「即将上线」占位,
// 绝不误报已订阅 (test_billing.cpp 第 5 节钉死本语义)。
//
// Google Play (Android) 已接线, 但刻意不经过本类 (V1 清单 §2 B2):
// 壳层 platforms/android/.../PlayBillingManager.kt 持有 Play Billing
// Library (连接 / 商品查询 / 购买流 / 恢复 / 回执确认), 购买或恢复
// 成功后经既有 JNI MagTileNative.setSubscriptionActive 写
// progress/subscription_settings 契约键 (与 FakeBillingClient 同键);
// Android 界面锁读同一契约键 (magtile_jni.cpp subscriptionActive),
// 无需 C++ 侧向上调用 Java。本类在 Android 交叉编译中照常参与构建
// 但不被调用 —— 保留同一接口缝, 供后续商店档 (Windows / App Store)
// 统一收口; R11 探测据此改为分平台口径 (tools/check_v1_readiness.sh)。

std::vector<ProductInfo> StoreBillingClient::queryProducts() {
#if defined(MAGTILE_BILLING_WINDOWS_STORE)
    // TODO(V1 付费闭环): StoreContext.GetAssociatedStoreProductsAsync
    static_assert(false, "Windows 商店档尚未接入, 勿在未实现前开启此宏");
#endif
    // 商品与本地化价格由各商店后台下发: Android 走 Kotlin 层
    // PlayBillingManager.queryProducts (Play Billing
    // queryProductDetailsAsync), 桌面空实现档返回空表 (界面退回占位)。
    return {};
}

PurchaseOutcome StoreBillingClient::purchase(const std::string& /*product_id*/) {
    return PurchaseOutcome::Unavailable;
}

PurchaseOutcome StoreBillingClient::restore() { return PurchaseOutcome::Unavailable; }

bool StoreBillingClient::subscriptionActive() const { return false; }

}  // namespace magtile::billing
