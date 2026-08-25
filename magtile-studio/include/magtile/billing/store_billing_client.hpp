#pragma once

// =============================================================
// MagTile Studio - 正式商店计费客户端 (空实现骨架, V1 付费闭环接真)
//
// 当前状态: **不接任何真实 SDK / 密钥**。全部方法返回"商店不可用"
// 语义 (queryProducts 空表 / purchase & restore Unavailable /
// subscriptionActive false), 界面据此温和退回「即将上线」占位 ——
// 空实现档绝不误报已订阅, 也绝不弹"失败"。
//
// 各商店后续接法 (编译期以宏分流, 一次只启用一个商店档):
//
//   Windows 商店 (MAGTILE_BILLING_WINDOWS_STORE):
//     - SDK: Windows.Services.Store (WinRT, C++/WinRT 投影),
//       随 Windows SDK 附带, 无第三方依赖;
//     - queryProducts -> StoreContext.GetAssociatedStoreProductsAsync
//       (kind "Durable"/"Subscription", 商品 id 与 Partner Center
//       后台一致: sub_monthly / sub_yearly / sub_family_yearly);
//     - purchase      -> StoreContext.RequestPurchaseAsync(storeId);
//     - restore/状态  -> StoreAppLicense.AddOnLicenses 遍历有效期
//       (商店侧账户即回执, 无需本地回执文件);
//     - 打包: 仅 MSIX 商店包生效 (QT_UI_PLAN QT-6), 本地开发档
//       无商店上下文, 继续用 FakeBillingClient。
//
//   Google Play (MAGTILE_BILLING_GOOGLE_PLAY):
//     - SDK: Play Billing Library (Kotlin/Java, platforms/android
//       壳层持有), C++ 侧经既有 JNI 最小桥模式对接 (与
//       core::ParentGate 的 parentGate*Json 桥同一策略):
//       壳层实现 queryProducts/purchase/restore, 结果以 JSON 回传;
//     - queryProducts -> BillingClient.queryProductDetailsAsync
//       (ProductType.SUBS, 商品 id 同上, Play Console 后台配置);
//     - purchase      -> launchBillingFlow + PurchasesUpdatedListener,
//       成功后 acknowledgePurchase;
//     - restore/状态  -> queryPurchasesAsync(SUBS) (Play 账户即回执);
//     - 儿童合规: 入口仍须过家长门, 价格只出现在门后 (§11)。
//
//   App Store (后续): StoreKit 2, 同一接口缝接入, 不再单列。
//
// 共同约定: 购买 / 恢复成功后把订阅状态写入
// progress/subscription_settings (与 FakeBillingClient 同一契约键),
// 作为离线宽限期本地凭证 (COMMERCIAL_PLAN §4.4); 商店回执始终是
// 权威来源, 本地凭证仅供无网启动时读取。
// =============================================================

#include <string>
#include <vector>

#include "magtile/billing/billing_client.hpp"

namespace magtile::billing {

class StoreBillingClient final : public BillingClient {
public:
    StoreBillingClient() = default;

    [[nodiscard]] std::vector<ProductInfo> queryProducts() override;
    [[nodiscard]] PurchaseOutcome purchase(const std::string& product_id) override;
    [[nodiscard]] PurchaseOutcome restore() override;
    [[nodiscard]] bool subscriptionActive() const override;
};

}  // namespace magtile::billing
