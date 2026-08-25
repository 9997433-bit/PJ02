#pragma once

// =============================================================
// MagTile Studio - 正式商店计费客户端 (跨商店接口缝)
//
// 桌面开发档 / CI 现状: **不接任何真实 SDK / 密钥**。宏未开启时全部
// 方法返回"商店不可用"语义 (queryProducts 空表 / purchase & restore
// Unavailable / subscriptionActive false), 界面据此温和退回「即将
// 上线」占位 —— 空实现档绝不误报已订阅, 也绝不弹"失败"。
//
// 各商店档接法 / 现状 (探测 R11 分平台, tools/check_v1_readiness.sh):
//
//   Google Play (已接线, V1 清单 §2 B2 🔶; 探测 R11):
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
//   Windows 商店 (已接线, V1 清单 §2 B2 🔶; 探测 R11W;
//   MAGTILE_BILLING_WINDOWS_STORE 宏分支, store_billing_client.cpp):
//     - SDK: Windows.Services.Store (WinRT, C++/WinRT 投影),
//       随 Windows SDK 附带 (链接 windowsapp), 无第三方依赖;
//     - queryProducts -> StoreContext.GetAssociatedStoreProductsAsync
//       (kind "Durable"/"Subscription"), InAppOfferToken 即三端统一
//       商品 id (sub_monthly / sub_yearly / sub_family_yearly, 与
//       Partner Center 后台一致), 本地化价格由商店后台下发
//       (StorePrice.FormattedPrice);
//     - purchase      -> StoreContext.RequestPurchaseAsync(storeId)
//       (Win32 桌面窗口经 IInitializeWithWindow 挂接收银台 UI);
//     - restore/状态  -> StoreAppLicense.AddOnLicenses 遍历有效订阅
//       (商店侧账户即回执, 无需本地回执文件); 明确无订阅清本地过期
//       凭证 (宁可锁), 查询不可用不动本地凭证 (离线宽限期);
//     - 购买 / 恢复成功后写 progress/subscription_settings 契约键
//       (setSubscriptionActive, 与 FakeBilling / Google Play 同键),
//       免费层锁零改动即感知;
//     - 打包: 商店上下文仅 MSIX 商店包身份下可用 (QT_UI_PLAN QT-6),
//       故宏只在商店出包配置时开启 (根 CMakeLists
//       -DMAGTILE_BILLING_WINDOWS_STORE=ON); 本地开发档保持 OFF 继续
//       用 FakeBillingClient; 沙盒验收 (B3) 走 Partner Center 商品
//       配置 + 商店内部测试通道, 属人工项。
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

namespace magtile::progress {
class ProgressStore;
}

namespace magtile::billing {

class StoreBillingClient final : public BillingClient {
public:
    /// store 为订阅契约键的持久化目标 (不持有, 生命期由调用方保证);
    /// Windows 商店档构造时从 settings 表载入本地凭证 (离线宽限期),
    /// 空实现档忽略该指针 (恒未订阅)。nullptr = 降级纯内存。
    explicit StoreBillingClient(progress::ProgressStore* store = nullptr);

    [[nodiscard]] std::vector<ProductInfo> queryProducts() override;
    [[nodiscard]] PurchaseOutcome purchase(const std::string& product_id) override;
    [[nodiscard]] PurchaseOutcome restore() override;
    [[nodiscard]] bool subscriptionActive() const override;

    /// 生效中的档位 id (未订阅或空实现档为空串); 订阅页状态卡展示用。
    [[nodiscard]] const std::string& activeProductId() const noexcept { return product_id_; }

private:
    /// 商店回执落地 -> 写 subscription_active 契约键 (仅商店档使用)。
    void setActive(bool active, const std::string& product_id);

    progress::ProgressStore* store_ = nullptr;  ///< 可空 (降级纯内存)
    bool active_ = false;                       ///< 空实现档恒 false
    std::string product_id_;
};

}  // namespace magtile::billing
