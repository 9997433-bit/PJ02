// =============================================================
// MagTile Studio - 订阅/IAP 计费适配层单元测试 (ctest: billing)
// 覆盖 COMMERCIAL_PLAN.md §2.2 付费闭环骨架 (无真实 SDK/密钥):
//   1. 免费层锁口径 isContentUnlocked: 未订阅时付费模型上锁、
//      免费模型 (is_free, 目录「免费」标签) 永远解锁;
//   2. FakeBillingClient 纯内存模式: 三档占位商品、未知商品 id
//      拒绝、假购买立即解锁、纯内存 restore 语义;
//   3. settings 表持久化契约 (progress/subscription_settings):
//      假购买跨实例可见、progress 层直读同一键 (界面锁同口径)、
//      缺键/脏值按未订阅兜底 (宁可锁不放行);
//   4. 恢复购买闭环: 本地订阅状态清空后 restore 从假商店回执
//      恢复; 全新账户 (无回执) NothingToRestore;
//   5. StoreBillingClient 空实现档: 空商品表 / Unavailable /
//      恒未订阅 —— 绝不误报已订阅。
// 用法: magtile_billing_test <临时数据库路径>
// =============================================================

#include <cstdio>
#include <filesystem>
#include <string>

#include "magtile/billing/billing_client.hpp"
#include "magtile/billing/fake_billing_client.hpp"
#include "magtile/billing/store_billing_client.hpp"
#include "magtile/progress/progress_store.hpp"
#include "magtile/progress/subscription_settings.hpp"

namespace {

int g_failures = 0;

void expect(bool condition, const char* message) {
    if (condition) {
        std::printf("[通过] %s\n", message);
    } else {
        std::printf("[失败] %s\n", message);
        ++g_failures;
    }
}

}  // namespace

int main(int argc, char** argv) {
    namespace billing = magtile::billing;
    namespace progress = magtile::progress;
    using billing::PurchaseOutcome;

    if (argc < 2) {
        std::fprintf(stderr, "用法: %s <临时数据库路径>\n", argv[0]);
        return 2;
    }
    const std::filesystem::path db_path = argv[1];
    std::filesystem::remove(db_path);  // 每次全新建库, 测试可重复执行

    // ---- 1+2. 纯内存模式: 未订阅锁付费模型 -> 假购买解锁 ----------------
    {
        billing::FakeBillingClient client;  // store = nullptr (纯内存)
        expect(!client.subscriptionActive(), "初始未订阅");
        expect(!billing::isContentUnlocked(/*is_free_model=*/false, client),
               "未订阅时付费模型上锁");
        expect(billing::isContentUnlocked(/*is_free_model=*/true, client),
               "免费层模型永远解锁 (is_free 口径不受订阅影响)");

        const auto products = client.queryProducts();
        expect(products.size() == 3, "三档占位商品 (月/年/家庭年)");
        bool has_recommended = false;
        for (const billing::ProductInfo& product : products) {
            expect(!product.product_id.empty() && !product.name_zh.empty() &&
                       !product.price_text.empty(),
                   "商品 id / 中文名 / 价格文本齐全");
            if (product.recommended) has_recommended = true;
        }
        expect(has_recommended, "存在主推档位 (年度, COMMERCIAL_PLAN §3.2)");

        expect(client.purchase("sub_nonsense") == PurchaseOutcome::Unavailable,
               "未知商品 id 拒绝 (Unavailable)");
        expect(!client.subscriptionActive(), "被拒购买不改变订阅状态");

        expect(client.purchase("sub_yearly") == PurchaseOutcome::Purchased, "假购买年度档成功");
        expect(client.subscriptionActive(), "假购买后订阅立即生效");
        expect(client.activeProductId() == "sub_yearly", "生效档位为所购档位");
        expect(billing::isContentUnlocked(/*is_free_model=*/false, client),
               "假购买后付费模型解锁");

        expect(client.restore() == PurchaseOutcome::Restored, "纯内存已订阅时 restore 回放");
        billing::FakeBillingClient fresh;  // 纯内存无"商店账户", 新实例无可恢复
        expect(fresh.restore() == PurchaseOutcome::NothingToRestore,
               "纯内存新实例 restore 无可恢复");
    }

    // ---- 3. settings 表持久化契约 (与界面锁 / progress 层同键) ----------
    {
        progress::ProgressStore store(db_path);
        expect(!progress::getSubscriptionActive(store), "全新存档默认未订阅");
        expect(progress::getSubscriptionProductId(store).empty(), "全新存档无生效档位");

        billing::FakeBillingClient client(&store);
        expect(!client.subscriptionActive(), "带存档构造时载入未订阅状态");
        expect(client.purchase("sub_family_yearly") == PurchaseOutcome::Purchased,
               "假购买家庭年度档成功");
        expect(progress::getSubscriptionActive(store),
               "progress 层直读到购买写入的订阅状态 (同一 settings 键)");
        expect(progress::getSubscriptionProductId(store) == "sub_family_yearly",
               "progress 层直读到生效档位");
    }
    {
        // 跨实例: 重开存档与客户端, 订阅状态与档位都在 (界面锁重启后同口径)
        progress::ProgressStore store(db_path);
        billing::FakeBillingClient client(&store);
        expect(client.subscriptionActive(), "订阅状态跨实例持久化");
        expect(client.activeProductId() == "sub_family_yearly", "生效档位跨实例持久化");
        expect(billing::isContentUnlocked(/*is_free_model=*/false, client),
               "重启后付费模型仍解锁");

        // 脏值兜底: 手改数据库为非 "1" 一律按未订阅 (宁可锁不放行)
        store.setSetting(progress::kSubscriptionActiveSettingKey, "yes");
        expect(!progress::getSubscriptionActive(store), "脏值按未订阅兜底");
        expect(progress::getSubscriptionProductId(store).empty(), "脏值下不返回档位");
        store.setSetting(progress::kSubscriptionActiveSettingKey, "1");
    }

    // ---- 4. 恢复购买闭环 (本地状态清空 -> 从假商店回执恢复) -------------
    {
        progress::ProgressStore store(db_path);
        billing::FakeBillingClient client(&store);
        client.devSetSubscribed(false);  // 开发开关关掉本地订阅, 回执保留
        expect(!client.subscriptionActive(), "开发开关关闭后本地未订阅");
        expect(!progress::getSubscriptionActive(store), "关闭状态已落盘");
        expect(!billing::isContentUnlocked(/*is_free_model=*/false, client),
               "关闭后付费模型重新上锁");

        expect(client.restore() == PurchaseOutcome::Restored, "restore 从假商店回执恢复");
        expect(client.subscriptionActive(), "恢复后订阅重新生效");
        expect(client.activeProductId() == "sub_family_yearly", "恢复的档位与回执一致");
        expect(progress::getSubscriptionActive(store), "恢复状态已落盘 (界面锁立即可读)");
    }
    {
        // 全新账户 (另一份存档, 无回执): 无可恢复, 且不误开订阅
        const std::filesystem::path fresh_db = db_path.string() + ".fresh";
        std::filesystem::remove(fresh_db);
        progress::ProgressStore store(fresh_db);
        billing::FakeBillingClient client(&store);
        expect(client.restore() == PurchaseOutcome::NothingToRestore,
               "无回执账户 restore 无可恢复");
        expect(!client.subscriptionActive(), "无可恢复时保持未订阅");
    }

    // ---- 5. StoreBillingClient 空实现档 (正式商店骨架, 未接 SDK) --------
    {
        billing::StoreBillingClient store_client;
        expect(store_client.queryProducts().empty(), "空实现档商品表为空 (界面退回占位)");
        expect(store_client.purchase("sub_yearly") == PurchaseOutcome::Unavailable,
               "空实现档购买 Unavailable");
        expect(store_client.restore() == PurchaseOutcome::Unavailable,
               "空实现档恢复 Unavailable");
        expect(!store_client.subscriptionActive(), "空实现档绝不误报已订阅");
        expect(!billing::isContentUnlocked(/*is_free_model=*/false, store_client),
               "空实现档付费模型保持上锁");
    }

    if (g_failures == 0) {
        std::printf("\n计费适配层单元测试全部通过\n");
        return 0;
    }
    std::printf("\n计费适配层单元测试失败: %d 项\n", g_failures);
    return 1;
}
