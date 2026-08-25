#include "magtile/billing/store_billing_client.hpp"

#include "magtile/progress/progress_store.hpp"
#include "magtile/progress/subscription_settings.hpp"

// =============================================================
// 分平台现状 (探测 R11 / R11W, tools/check_v1_readiness.sh):
//
// Google Play (Android) 已接线, 但刻意不经过本类 (V1 清单 §2 B2):
// 壳层 platforms/android/.../PlayBillingManager.kt 持有 Play Billing
// Library (连接 / 商品查询 / 购买流 / 恢复 / 回执确认), 购买或恢复
// 成功后经既有 JNI MagTileNative.setSubscriptionActive 写
// progress/subscription_settings 契约键 (与 FakeBillingClient 同键);
// Android 界面锁读同一契约键 (magtile_jni.cpp subscriptionActive),
// 无需 C++ 侧向上调用 Java。本类在 Android 交叉编译中照常参与构建
// 但不被调用 —— 保留同一接口缝, 供商店档统一收口。
//
// Windows 商店 (本文件, MAGTILE_BILLING_WINDOWS_STORE 宏分支):
// WinRT Windows.Services.Store (C++/WinRT 投影, Windows SDK 自带,
// 无第三方依赖) —— StoreContext 查商品 (本地化价格由 Partner Center
// 后台下发) / RequestPurchaseAsync 收银台购买 /
// StoreAppLicense.AddOnLicenses 遍历有效订阅恢复 (商店账户即回执)。
// 商店上下文只在 MSIX 商店包身份下可用 (QT_UI_PLAN QT-6), 故宏由
// 根 CMakeLists -DMAGTILE_BILLING_WINDOWS_STORE=ON 仅在商店出包时
// 开启; 本地开发档保持 OFF 走 FakeBillingClient。
//
// 宏未开启 (桌面开发档 / CI / Android 交叉编译) 时统一返回"商店
// 不可用"语义 —— 界面退回「即将上线」占位, 绝不误报已订阅
// (test_billing.cpp 第 5 节钉死本语义)。
// =============================================================

namespace magtile::billing {

StoreBillingClient::StoreBillingClient(progress::ProgressStore* store) : store_(store) {
#if defined(MAGTILE_BILLING_WINDOWS_STORE)
    // 契约键即离线宽限期凭证 (COMMERCIAL_PLAN §4.4): 启动先读本地
    // (无网也能玩已解锁内容), 商店回执经 restore() 校准 (权威来源)。
    if (store_ != nullptr) {
        active_ = progress::getSubscriptionActive(*store_);
        product_id_ = progress::getSubscriptionProductId(*store_);
    }
#endif
}

}  // namespace magtile::billing

#if defined(MAGTILE_BILLING_WINDOWS_STORE)
// =============================================================
// Windows 商店档: WinRT StoreContext 真实接线 (V1 清单 §2 B2)
// =============================================================

#if !defined(_WIN32)
#error "MAGTILE_BILLING_WINDOWS_STORE 仅支持 Windows (WinRT StoreContext), 其他平台请保持 OFF"
#endif

#ifndef WIN32_LEAN_AND_MEAN
#define WIN32_LEAN_AND_MEAN
#endif
#ifndef NOMINMAX
#define NOMINMAX
#endif
#include <windows.h>

#include <shobjidl.h>  // IInitializeWithWindow: Win32 桌面窗口挂接收银台 UI

#include <winrt/Windows.Foundation.Collections.h>
#include <winrt/Windows.Foundation.h>
#include <winrt/Windows.Services.Store.h>
#include <winrt/base.h>

#include <exception>
#include <optional>
#include <stdexcept>
#include <thread>
#include <type_traits>
#include <utility>

namespace magtile::billing {

namespace {

using winrt::Windows::Services::Store::StoreAppLicense;
using winrt::Windows::Services::Store::StoreContext;
using winrt::Windows::Services::Store::StoreProduct;
using winrt::Windows::Services::Store::StorePurchaseStatus;

/// 三档订阅的本地展示文案 (商品 id 三端统一, COMMERCIAL_PLAN §3.1)。
/// 档位名与一句话说明沿用儿童友好中文 (Partner Center 的 Title 面向
/// 商店页); 价格文本不在本地写死, 以商店后台本地化下发为准
/// (StorePrice.FormattedPrice)。
struct KnownSubscription {
    const char* product_id;
    const char* name_zh;
    const char* blurb_zh;
    bool recommended;
};

constexpr KnownSubscription kKnownSubscriptions[] = {
    {"sub_monthly", "月度订阅", "先试试水, 随时取消", false},
    {"sub_yearly", "年度订阅", "一次开通一整年, 7 天无理由退款", true},
    {"sub_family_yearly", "家庭年度", "最多 4 个儿童档案 + 6 台设备", false},
};

[[nodiscard]] bool isKnownSubscription(const std::string& product_id) {
    for (const KnownSubscription& known : kKnownSubscriptions) {
        if (product_id == known.product_id) return true;
    }
    return false;
}

/// WinRT 异步操作的 .get() 阻塞等待禁止在 STA (UI) 线程进行
/// (C++/WinRT 断言拦截); Qt 主线程在 Windows 上是 OLE STA, 故所有
/// 商店调用挪到一次性 MTA 工作线程同步等待。计费操作低频 (进订阅
/// 页 / 点购买 / 恢复购买), 一次一线程的开销可忽略。
template <typename Fn>
auto runOnStoreWorker(Fn&& fn) -> std::invoke_result_t<Fn&> {
    using Result = std::invoke_result_t<Fn&>;
    std::optional<Result> result;
    std::exception_ptr error;
    std::thread worker([&] {
        winrt::init_apartment(winrt::apartment_type::multi_threaded);
        try {
            result.emplace(fn());
        } catch (...) {
            error = std::current_exception();
        }
        winrt::uninit_apartment();
    });
    worker.join();
    if (error != nullptr) std::rethrow_exception(error);
    return std::move(*result);
}

/// MSIX 商店包身份下取商店上下文; 无包身份 (本地裸 exe / 单测) 时
/// 抛出, 由调用方兜成"商店不可用"温和语义。
[[nodiscard]] StoreContext storeContext() {
    StoreContext ctx = StoreContext::GetDefault();
    if (ctx == nullptr) throw std::runtime_error("无商店上下文 (非 MSIX 包身份)");
    return ctx;
}

/// Win32 桌面应用必须把 StoreContext 挂到自家窗口, 收银台确认 UI
/// 才有宿主 (桌面桥官方要求: IInitializeWithWindow)。窗口句柄须在
/// UI 线程先取好再传入 (工作线程没有"本线程的活动窗口"概念)。
void attachToWindow(const StoreContext& ctx, HWND hwnd) {
    if (hwnd == nullptr) return;  // 无窗口 (无头场景): 查询类调用不需要宿主
    if (auto with_window = ctx.try_as<::IInitializeWithWindow>()) {
        with_window->Initialize(hwnd);
    }
}

}  // namespace

std::vector<ProductInfo> StoreBillingClient::queryProducts() {
    try {
        return runOnStoreWorker([]() -> std::vector<ProductInfo> {
            StoreContext ctx = storeContext();
            // 订阅在 Partner Center 以附加内容 (Durable / Subscription)
            // 配置, InAppOfferToken 即三端统一商品 id
            auto query =
                ctx.GetAssociatedStoreProductsAsync({L"Durable", L"Subscription"}).get();
            std::vector<ProductInfo> products;
            for (const KnownSubscription& known : kKnownSubscriptions) {
                for (const auto& entry : query.Products()) {
                    StoreProduct product = entry.Value();
                    if (winrt::to_string(product.InAppOfferToken()) != known.product_id) {
                        continue;
                    }
                    products.push_back(ProductInfo{
                        known.product_id, known.name_zh,
                        winrt::to_string(product.Price().FormattedPrice()), known.blurb_zh,
                        known.recommended});
                    break;
                }
            }
            return products;
        });
    } catch (...) {
        // 无包身份 / 无网 / 商店后台未配商品: 空表 -> 订阅页退回
        // 「即将上线」温和占位, 绝不显示空价格卡
        return {};
    }
}

PurchaseOutcome StoreBillingClient::purchase(const std::string& product_id) {
    // 未知商品 id 直接拒绝 (与 FakeBilling / Play 侧同口径)
    if (!isKnownSubscription(product_id)) return PurchaseOutcome::Unavailable;
    // 收银台宿主窗口须在调用方 (UI) 线程取好
    HWND hwnd = ::GetActiveWindow();
    if (hwnd == nullptr) hwnd = ::GetForegroundWindow();
    try {
        const StorePurchaseStatus status = runOnStoreWorker([&]() -> StorePurchaseStatus {
            StoreContext ctx = storeContext();
            attachToWindow(ctx, hwnd);
            // 商品 id (InAppOfferToken) -> StoreId: 购买按商店主键发起
            auto query =
                ctx.GetAssociatedStoreProductsAsync({L"Durable", L"Subscription"}).get();
            for (const auto& entry : query.Products()) {
                StoreProduct product = entry.Value();
                if (winrt::to_string(product.InAppOfferToken()) == product_id) {
                    return ctx.RequestPurchaseAsync(product.StoreId()).get().Status();
                }
            }
            throw std::runtime_error("商品未在 Partner Center 配置");
        });
        switch (status) {
            case StorePurchaseStatus::Succeeded:
            case StorePurchaseStatus::AlreadyPurchased:
                // 商店回执落地 -> 写 subscription_active 契约键 (与
                // FakeBilling / Google Play 同键), 免费层锁零改动即感知
                setActive(true, product_id);
                return PurchaseOutcome::Purchased;
            case StorePurchaseStatus::NotPurchased:
                // 家长在收银台合上了对话框: 中性结果, 不是问题
                return PurchaseOutcome::Cancelled;
            case StorePurchaseStatus::NetworkError:
            case StorePurchaseStatus::ServerError:
            default:
                return PurchaseOutcome::Unavailable;
        }
    } catch (...) {
        return PurchaseOutcome::Unavailable;
    }
}

PurchaseOutcome StoreBillingClient::restore() {
    try {
        // 商店账户即回执 (换机 / 重装 / 他端购买场景, 无需本地回执
        // 文件): 遍历附加内容许可证找有效订阅。许可证由系统缓存,
        // 本地快查, 无网也可读。
        const std::optional<std::string> active_sub =
            runOnStoreWorker([]() -> std::optional<std::string> {
                StoreContext ctx = storeContext();
                StoreAppLicense license = ctx.GetAppLicenseAsync().get();
                if (license == nullptr) throw std::runtime_error("许可证查询无结果");
                for (const auto& entry : license.AddOnLicenses()) {
                    const auto addon = entry.Value();
                    if (!addon.IsActive()) continue;
                    std::string token = winrt::to_string(addon.InAppOfferToken());
                    if (isKnownSubscription(token)) return token;
                }
                return std::nullopt;  // 查询成功, 明确没有有效订阅
            });
        if (active_sub.has_value()) {
            setActive(true, *active_sub);
            return PurchaseOutcome::Restored;
        }
        // 商店明确说没有 -> 清本地过期凭证 (宁可锁不放行, 与 Google
        // Play 侧启动静默恢复同口径)
        setActive(false, "");
        return PurchaseOutcome::NothingToRestore;
    } catch (...) {
        // 查询不可用 (无包身份等) 不动本地凭证 —— 契约键即离线宽限
        // 期凭证 (COMMERCIAL_PLAN §4.4)
        return PurchaseOutcome::Unavailable;
    }
}

bool StoreBillingClient::subscriptionActive() const { return active_; }

void StoreBillingClient::setActive(bool active, const std::string& product_id) {
    active_ = active;
    product_id_ = product_id;
    if (store_ != nullptr) {
        progress::setSubscriptionActive(*store_, active, product_id);
    }
}

}  // namespace magtile::billing

#else  // !MAGTILE_BILLING_WINDOWS_STORE
// =============================================================
// 空实现档 (桌面开发档 / CI / Android 交叉编译): 统一"商店不可用"
// =============================================================

namespace magtile::billing {

std::vector<ProductInfo> StoreBillingClient::queryProducts() {
    // 商品与本地化价格由各商店后台下发: Android 走 Kotlin 层
    // PlayBillingManager.queryProducts (Play Billing
    // queryProductDetailsAsync), Windows 商店档走上方 WinRT 分支;
    // 空实现档返回空表 (界面退回占位)。
    return {};
}

PurchaseOutcome StoreBillingClient::purchase(const std::string& /*product_id*/) {
    return PurchaseOutcome::Unavailable;
}

PurchaseOutcome StoreBillingClient::restore() { return PurchaseOutcome::Unavailable; }

bool StoreBillingClient::subscriptionActive() const { return false; }

}  // namespace magtile::billing

#endif  // MAGTILE_BILLING_WINDOWS_STORE
