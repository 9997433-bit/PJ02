#pragma once

// =============================================================
// MagTile Studio - 正式商店计费客户端 (跨商店接口缝)
//
// 桌面当前状态: **不接任何真实 SDK / 密钥**。全部方法返回"商店
// 不可用"语义 (queryProducts 空表 / purchase & restore Unavailable /
// subscriptionActive false), 界面据此温和退回「即将上线」占位 ——
// 空实现档绝不误报已订阅, 也绝不弹"失败"。
//
// 各商店档接法 / 现状 (探测 R11 分平台, tools/check_v1_readiness.sh):
//
//   Google Play (已接线, V1 清单 §2 B2 🔶):
//     - SDK 由 Kotlin 壳层独占持有 —— platforms/android/app/.../
//       PlayBillingManager.kt 实现连接 / queryProductDetailsAsync
//       (ProductType.SUBS) / launchBillingFlow +
//       PurchasesUpdatedListener / queryPurchasesAsync 恢复 /
//       acknowledgePurchase 回执确认, 外加进程启动静默恢复
//       (MagTileApplication);
//     - 购买 / 恢复成功后经既有 JNI setSubscriptionActive 写
//       progress/subscription_settings 契约键 (与 FakeBillingClient
//       同键), Android 界面锁读同一契约键 —— 本类不参与 Android
//       购买链路, 无需 C++ -> Java 上行调用;
//     - Debug 构建温和短路 (QA 走「模拟已订阅」开关, 与桌面
//       FakeBillingClient::devSetSubscribed 同角色), Release 走真实
//       Play Billing; 沙盒验收 (B3) 走 Play Console 内部测试轨;
//     - 儿童合规: 入口仍须过家长门, 价格只出现在门后 (§11)。
//
//   Windows 商店 (未接线, 编译期宏守卫拒绝误开):
//     - SDK: Windows.Services.Store (WinRT, C++/WinRT 投影),
//       随 Windows SDK 附带, 无第三方依赖;
//     - queryProducts -> StoreContext.GetAssociatedStoreProductsAsync
//       (kind "Durable"/"Subscription", 商品 id 与 Partner Center
//       后台一致: sub_monthly / sub_yearly / sub_family_yearly);
//     - purchase      -> StoreContext.RequestPurchaseAsync(storeId);
//     - restore/状态  -> StoreAppLicense.AddOnLicenses 遍历有效期
//       (商店侧账户即回执, 无需本地回执文件);
//     - 打包: 仅 MSIX 商店包生效 (QT_UI_PLAN QT-6), 本地开发档
//       无商店上下文, 继续用 FakeBillingClient;
//     - 接入时启用 MAGTILE_BILLING_WINDOWS_STORE 宏并替换 .cpp 内
//       static_assert 守卫。
//
//   App Store (后续): StoreKit 2, 同一接口缝接入, 不再单列。
//
// 共同约定: 购买 / 恢复成功后把订阅状态写入
// progress/subscription_settings (与 FakeBillingClient 同一契约键),
// 作为离线宽限期本地凭证 (COMMERCIAL_PLAN §4.4); 商店回执始终是
// 权威来源, 本地凭证仅供无网启动时读取。商品 id 三端统一:
// sub_monthly / sub_yearly / sub_family_yearly (COMMERCIAL_PLAN §3.1)。
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
