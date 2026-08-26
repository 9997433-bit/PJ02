#pragma once

// =============================================================
// MagTile Studio - 订阅 / IAP 计费适配层 (COMMERCIAL_PLAN.md §2.2)
//
// 目标: 界面与商店 SDK 之间唯一的抽象缝 —— 订阅页 / 免费层锁只
// 面向本接口编程, 具体商店 (Windows 商店 / Google Play / App
// Store) 以实现类接入, 换商店零界面改动。本层不含任何真实 SDK
// 与密钥, 纯逻辑零 UI 依赖 (与 core::ParentGate 同一档次)。
//
// 实现类:
//   - FakeBillingClient  (本文件):  内存 + settings 表持久化的假
//     商店, 供桌面开发档与单元测试走通完整付费闭环 (购买 / 恢复 /
//     解锁), 不产生任何真实扣费;
//   - StoreBillingClient (store_billing_client.hpp): 正式商店档
//     空实现骨架, 各商店接法以 #ifdef 与文档标注, 后续接真 SDK。
//
// 解锁口径 (与既有免费层锁衔接, COMMERCIAL_PLAN §2.1):
//   可玩 = 模型属免费层 (目录 tags 含「免费」, core::isFreeTierModel)
//        或 订阅有效 (subscriptionActive)
// 见下方 isContentUnlocked —— 三端 (Qt / GL / 移动壳) 共用同一判定。
// =============================================================

#include <string>
#include <vector>

namespace magtile::billing {

/// 商品档位快照 (占位定价与 COMMERCIAL_PLAN §3.1 对齐; 正式价格
/// 文本以各商店后台配置为准, 本地文本仅家长门后的订阅页展示)。
struct ProductInfo {
    std::string product_id;   ///< 商店商品 id, 如 "sub_yearly" (三端统一)
    std::string name_zh;      ///< 中文档位名, 如 "年度订阅"
    std::string price_text;   ///< 展示用价格文本, 如 "¥198 / 年"
    std::string blurb_zh;     ///< 一句话说明 (温和, 无催促话术)
    bool recommended = false; ///< 主推档位 (订阅页高亮, §3.2 年度为主推)
};

/// purchase / restore 的结果 (界面据此给出温和提示, 永不弹"失败")。
enum class PurchaseOutcome {
    Purchased,         ///< 购买成功, 订阅已生效
    Restored,          ///< 恢复购买成功, 订阅已生效
    NothingToRestore,  ///< 商店账户下没有可恢复的订阅 (中性结果)
    Cancelled,         ///< 用户取消 (中性结果, 不是错误)
    Unavailable,       ///< 商店不可用 (未接 SDK / 无网络 / 空实现档)
};

/// 计费客户端抽象接口: 订阅页与免费层锁唯一面向的类型。
class BillingClient {
public:
    virtual ~BillingClient() = default;

    /// 可购的订阅档位 (月度 / 年度 / 家庭年度); 商店不可用时返回空表,
    /// 界面据此退回「即将上线」占位而不是显示空价格卡。
    [[nodiscard]] virtual std::vector<ProductInfo> queryProducts() = 0;

    /// 发起购买; 未知商品 id 或商店不可用返回 Unavailable。
    /// 成功后 subscriptionActive() 立即为 true 并完成持久化。
    [[nodiscard]] virtual PurchaseOutcome purchase(const std::string& product_id) = 0;

    /// 恢复购买 (换机 / 重装场景, COMMERCIAL_PLAN §2.2 承诺项):
    /// 从商店账户回执恢复订阅权益。
    [[nodiscard]] virtual PurchaseOutcome restore() = 0;

    /// 订阅当前是否有效 (免费层锁的读取口径)。
    [[nodiscard]] virtual bool subscriptionActive() const = 0;
};

/// 内容解锁判定 (三端共用单一口径): 免费层永远解锁, 订阅内容看
/// 订阅状态。is_free_model 用既有免费层标签判定
/// (core::isFreeTierModel / LibraryRow::is_free)。
[[nodiscard]] inline bool isContentUnlocked(bool is_free_model, const BillingClient& billing) {
    return is_free_model || billing.subscriptionActive();
}

}  // namespace magtile::billing
