// =============================================================
// MagTile Studio - Qt 计费桥单元测试 (ctest: qt_billing_bridge)
// 仅在 MAGTILE_BUILD_QT=ON 时构建注册, 无需显示环境 (纯 QObject)。
// 覆盖订阅/IAP 适配层的 Qt 侧 (COMMERCIAL_PLAN §2.2, 无真实 SDK):
//   1. BillingBackend 默认态: 未订阅、商店可用 (桌面开发档 =
//      FakeBillingClient)、三卡商品数据源齐全;
//   2. 订阅页主 CTA 契约: purchase 未知商品退「即将上线」占位
//      文案且不改状态; 购买合法档位后 subscriptionActive 生效
//      (免费层锁 DetailPage/LibraryPage 读同一属性);
//   3. 跨实例持久化: 重开桥仍是已订阅 (settings 契约键), progress
//      层直读同键 (与 core 层 / GL 版 / CLI 共库承诺);
//   4. 开发开关门控: devControlsEnabled=false 时 devSetSubscribed
//      被忽略; =true 时可关闭本地订阅再经 restore 恢复;
//   5. LibraryFilterModel 订阅感知: 未订阅时庆祝页推荐排除订阅
//      内容, 订阅生效后同权进推荐 (解锁即可直接开搭)。
// 用法: magtile_qt_billing_test <临时数据库路径>
// =============================================================

#include <QCoreApplication>
#include <QString>
#include <QVariantList>
#include <QVariantMap>
#include <cstdio>
#include <filesystem>
#include <utility>
#include <vector>

#include "billing_backend.hpp"
#include "library_filter_model.hpp"
#include "library_model.hpp"
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
    QCoreApplication app(argc, argv);

    if (argc < 2) {
        std::fprintf(stderr, "用法: %s <临时数据库路径>\n", argv[0]);
        return 2;
    }
    const std::filesystem::path db_path = argv[1];
    std::filesystem::remove(db_path);  // 每次全新建库, 测试可重复执行

    namespace progress = magtile::progress;
    using magtile::qtui::BillingBackend;

    // ---- 1+2. 默认态 -> 主 CTA 假购买解锁 ------------------------------
    {
        BillingBackend billing(db_path, /*dev_controls=*/false);
        expect(!billing.subscriptionActive(), "初始未订阅 (付费模型上锁口径)");
        expect(billing.storeAvailable(), "桌面开发档商店可用 (FakeBillingClient)");
        expect(!billing.devControlsEnabled(), "未开开发档时无模拟开关");
        expect(billing.activePlanName().isEmpty(), "未订阅时无生效档位名");

        const QVariantList products = billing.products();
        expect(products.size() == 3, "订阅页三卡数据源 (月/年/家庭年)");
        for (const QVariant& entry : products) {
            const QVariantMap product = entry.toMap();
            expect(!product.value(QStringLiteral("productId")).toString().isEmpty() &&
                       !product.value(QStringLiteral("name")).toString().isEmpty() &&
                       !product.value(QStringLiteral("priceText")).toString().isEmpty(),
                   "三卡商品字段齐全 (id/名称/价格文本)");
        }

        const QString rejected = billing.purchase(QStringLiteral("sub_nonsense"));
        expect(rejected.contains(QStringLiteral("准备中")), "未知商品退温和占位文案");
        expect(!billing.subscriptionActive(), "被拒购买不改订阅状态");

        const QString purchased = billing.purchase(QStringLiteral("sub_yearly"));
        expect(purchased.contains(QStringLiteral("已开通")), "假购买返回开通文案");
        expect(billing.subscriptionActive(), "假购买后订阅生效 (付费模型解锁口径)");
        expect(billing.activePlanName() == QStringLiteral("年度订阅"), "生效档位中文名正确");

        // 开发开关未启用: devSetSubscribed 被忽略 (误接线也改不了状态)
        billing.devSetSubscribed(false);
        expect(billing.subscriptionActive(), "非开发档 devSetSubscribed 被忽略");
    }

    // ---- 3. 跨实例持久化 + settings 契约键直读 --------------------------
    {
        BillingBackend billing(db_path, /*dev_controls=*/true);
        expect(billing.subscriptionActive(), "订阅状态跨实例持久化 (重启后仍解锁)");
        expect(billing.devControlsEnabled(), "开发档开关可用");
    }
    {
        progress::ProgressStore store(db_path);
        expect(progress::getSubscriptionActive(store),
               "progress 层直读到桥写入的订阅状态 (共用 settings 契约键)");
        expect(progress::getSubscriptionProductId(store) == "sub_yearly",
               "progress 层直读到生效档位");
    }

    // ---- 4. 开发开关关闭本地订阅 -> restore 恢复 ------------------------
    {
        BillingBackend billing(db_path, /*dev_controls=*/true);
        billing.devSetSubscribed(false);
        expect(!billing.subscriptionActive(), "开发开关关闭后未订阅 (付费模型重新上锁)");

        const QString restored = billing.restore();
        expect(restored.contains(QStringLiteral("已恢复")), "restore 返回恢复文案");
        expect(billing.subscriptionActive(), "恢复购买后订阅重新生效");
    }
    {
        // 全新存档 (无假商店回执): restore 无可恢复且不误开订阅
        const std::filesystem::path fresh_db = db_path.string() + ".fresh";
        std::filesystem::remove(fresh_db);
        BillingBackend billing(fresh_db, /*dev_controls=*/false);
        const QString nothing = billing.restore();
        expect(nothing.contains(QStringLiteral("没有可恢复")), "无回执时返回中性文案");
        expect(!billing.subscriptionActive(), "无可恢复时保持未订阅");
    }

    // ---- 5. LibraryFilterModel 订阅感知 (庆祝页推荐口径) ----------------
    {
        using magtile::qtui::LibraryFilterModel;
        using magtile::qtui::LibraryModel;
        using magtile::qtui::LibraryRow;

        const auto makeRow = [](const char* id, int difficulty, int pieces, bool is_free) {
            LibraryRow row;
            row.entry.id = id;
            row.entry.name = id;
            row.entry.difficulty = difficulty;
            row.entry.total_pieces = pieces;
            row.bom_known = true;
            row.can_build = true;
            row.is_free = is_free;
            return row;
        };

        LibraryModel model;
        std::vector<LibraryRow> rows;
        rows.push_back(makeRow("just_done", 3, 50, true));
        rows.push_back(makeRow("free_neighbor", 3, 30, true));
        rows.push_back(makeRow("locked_neighbor", 3, 20, /*is_free=*/false));
        model.resetRows(std::move(rows));

        LibraryFilterModel filter;
        filter.setSourceModel(&model);
        const auto recIds = [&filter](int max_count) {
            QStringList ids;
            const QVariantList recs =
                filter.recommendSimilar(QStringLiteral("just_done"), max_count);
            for (const QVariant& rec : recs) {
                ids << rec.toMap().value(QStringLiteral("modelId")).toString();
            }
            return ids;
        };

        expect(!filter.subscriptionActive(), "筛选代理默认按未订阅兜底 (宁可锁)");
        expect(!recIds(5).contains(QStringLiteral("locked_neighbor")),
               "未订阅时订阅内容不进庆祝页推荐");

        filter.setSubscriptionActive(true);
        expect(recIds(5).contains(QStringLiteral("locked_neighbor")),
               "订阅生效后订阅内容同权进推荐 (解锁即可直接开搭)");

        filter.setSubscriptionActive(false);
        expect(!recIds(5).contains(QStringLiteral("locked_neighbor")),
               "订阅关闭后推荐口径立即回到上锁");
    }

    if (g_failures == 0) {
        std::printf("\nQt 计费桥单元测试全部通过\n");
        return 0;
    }
    std::printf("\nQt 计费桥单元测试失败: %d 项\n", g_failures);
    return 1;
}
