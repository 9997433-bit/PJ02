// =============================================================
// MagTile Studio - 成就解锁统一收口回归测试 (ctest: achievements_unlock)
// 覆盖 progress/achievements.hpp —— 三端 (GL / Qt / Android JNI)
// 完成链路唯一写库触发点 unlockAchievementsOnComplete:
//   - 档位表契约: 1/3/10/30 四档, id 与展示层同名, 阈值严格升序;
//   - 首次完成 -> 只解锁 first_model_completed;
//   - 重复完成同一模型 -> 不重复写、不覆盖首次解锁时刻 (幂等);
//   - 分档边界: 完成数 2/3、9/10、29/30 两侧恰好不亮/点亮对应档;
//   - 老档补录: 历史存档只有完成记录 + 首搭成就 (3/10/30 档从未
//     落库), 下次任意完成一次性补齐全部达档成就, 已有成就不丢;
//   - 跨连接持久化: 重开数据库成就仍在。
// 用法: magtile_achievements_test <临时数据库文件>
// =============================================================

#include <algorithm>
#include <cstdint>
#include <cstdio>
#include <filesystem>
#include <string>
#include <system_error>
#include <vector>

#include "magtile/progress/achievements.hpp"
#include "magtile/progress/progress_store.hpp"

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

/// 合成模型 id: model_001, model_002, ...
std::string modelId(int index) {
    char buffer[32];
    std::snprintf(buffer, sizeof(buffer), "model_%03d", index);
    return buffer;
}

/// 完成一个模型并走统一收口 (与三端完成链路同顺序: 先 markCompleted
/// 再 unlockAchievementsOnComplete), 返回本次新解锁的成就 id。
std::vector<std::string> completeOne(magtile::progress::ProgressStore& store, int index) {
    store.markCompleted(modelId(index));
    return magtile::progress::unlockAchievementsOnComplete(store);
}

}  // namespace

// 档位表契约在编译期锁定: 四档 1/3/10/30 严格升序 (展示与写库共用,
// 改动会同时影响三端, 必须显式过这里)。
static_assert(std::size(magtile::progress::kAchievementTiers) == 4,
              "成就档位表应为 4 档");
static_assert(magtile::progress::kAchievementTiers[0].completed_threshold == 1 &&
                  magtile::progress::kAchievementTiers[1].completed_threshold == 3 &&
                  magtile::progress::kAchievementTiers[2].completed_threshold == 10 &&
                  magtile::progress::kAchievementTiers[3].completed_threshold == 30,
              "成就档位阈值应为 1/3/10/30");

int main(int argc, char** argv) {
    if (argc != 2) {
        std::fprintf(stderr, "用法: %s <临时数据库文件>\n", argv[0]);
        return 2;
    }
    const std::filesystem::path db_file = argv[1];
    const std::filesystem::path legacy_db_file = db_file.string() + ".legacy";
    std::error_code ec;
    std::filesystem::remove(db_file, ec);  // 清除上次运行残留, 保证测试可重复
    std::filesystem::remove(legacy_db_file, ec);

    using magtile::progress::ProgressStore;
    using magtile::progress::unlockAchievementsOnComplete;

    // ---- 档位表契约 (运行期核对 id 与展示层同名) --------------------
    {
        const auto& tiers = magtile::progress::kAchievementTiers;
        expect(std::string(tiers[0].id) == "first_model_completed" &&
                   std::string(tiers[1].id) == "three_models_completed" &&
                   std::string(tiers[2].id) == "ten_models_completed" &&
                   std::string(tiers[3].id) == "thirty_models_completed",
               "档位 id 与展示层 (Qt/Android 成就墙) 同名");
    }

    std::int64_t first_unlocked_at = 0;
    {
        ProgressStore store(db_file);

        // ---- 空档: 没有完成记录时不写任何成就 --------------------------
        expect(unlockAchievementsOnComplete(store).empty() && store.listAchievements().empty(),
               "零完成时调用不写库");

        // ---- 首次完成: 只解锁首搭成就 ----------------------------------
        const auto first = completeOne(store, 1);
        expect(first.size() == 1 && first[0] == "first_model_completed",
               "首次完成返回新解锁 first_model_completed");
        expect(store.isAchievementUnlocked("first_model_completed"),
               "首次完成解锁首搭成就");
        expect(!store.isAchievementUnlocked("three_models_completed") &&
                   !store.isAchievementUnlocked("ten_models_completed") &&
                   !store.isAchievementUnlocked("thirty_models_completed"),
               "首次完成不解锁更高档位");
        expect(store.listAchievements().size() == 1, "成就表恰好一条记录");
        first_unlocked_at = store.listAchievements()[0].unlocked_at;
        expect(first_unlocked_at > 0, "解锁时刻已记录");

        // ---- 重复完成同一模型: 不重复写、不覆盖首次解锁时刻 -------------
        const auto repeat = completeOne(store, 1);
        expect(repeat.empty(), "重复完成无新解锁");
        expect(store.listAchievements().size() == 1, "重复完成不产生重复记录");
        expect(store.listAchievements()[0].unlocked_at == first_unlocked_at,
               "重复完成不覆盖首次解锁时刻");

        // ---- 分档边界 3: 完成数 2 不亮, 3 恰好亮 -----------------------
        expect(completeOne(store, 2).empty() &&
                   !store.isAchievementUnlocked("three_models_completed"),
               "完成 2 个时三模型档不解锁 (边界外)");
        const auto third = completeOne(store, 3);
        expect(third.size() == 1 && third[0] == "three_models_completed",
               "完成第 3 个恰好解锁三模型档");

        // ---- 分档边界 10: 完成数 9 不亮, 10 恰好亮 ---------------------
        for (int i = 4; i <= 9; ++i) {
            expect(completeOne(store, i).empty(), "4~9 个完成之间无新解锁");
        }
        expect(!store.isAchievementUnlocked("ten_models_completed"),
               "完成 9 个时十模型档不解锁 (边界外)");
        const auto tenth = completeOne(store, 10);
        expect(tenth.size() == 1 && tenth[0] == "ten_models_completed",
               "完成第 10 个恰好解锁十模型档");

        // ---- 分档边界 30: 完成数 29 不亮, 30 恰好亮 --------------------
        for (int i = 11; i <= 29; ++i) {
            (void)completeOne(store, i);
        }
        expect(!store.isAchievementUnlocked("thirty_models_completed"),
               "完成 29 个时三十模型档不解锁 (边界外)");
        const auto thirtieth = completeOne(store, 30);
        expect(thirtieth.size() == 1 && thirtieth[0] == "thirty_models_completed",
               "完成第 30 个恰好解锁三十模型档");
        expect(store.listAchievements().size() == 4, "四档全解锁后成就表恰好四条");

        // ---- 全解锁后再调用: 纯幂等 ------------------------------------
        expect(unlockAchievementsOnComplete(store).empty() &&
                   store.listAchievements().size() == 4,
               "全解锁后重复调用不写库");
    }

    // ---- 跨连接持久化: 重开数据库成就仍在, 首次解锁时刻不变 -------------
    {
        ProgressStore store(db_file);
        expect(store.listAchievements().size() == 4, "重开数据库后四档成就仍在");
        expect(store.isAchievementUnlocked("first_model_completed") &&
                   store.isAchievementUnlocked("thirty_models_completed"),
               "重开数据库后档位查询一致");
        std::int64_t reopened_at = 0;
        for (const auto& a : store.listAchievements()) {
            if (a.id == "first_model_completed") reopened_at = a.unlocked_at;
        }
        expect(reopened_at == first_unlocked_at, "重开数据库后首次解锁时刻不变");
    }

    // ---- 老档补录: 历史版本只写过首搭成就, 3/10/30 档只在展示层判定
    // 从未落库 —— 下次任意完成一次性补齐全部达档成就, 已有成就不丢 ----
    {
        ProgressStore store(legacy_db_file);
        // 模拟历史完成链路: 5 个完成 + 手写 first_model_completed
        for (int i = 1; i <= 5; ++i) {
            store.markCompleted(modelId(i));
        }
        store.unlockAchievement("first_model_completed");
        expect(store.listAchievements().size() == 1 &&
                   !store.isAchievementUnlocked("three_models_completed"),
               "老档就位: 5 个完成但三模型档未落库");

        const std::int64_t legacy_first_at = store.listAchievements()[0].unlocked_at;
        const auto backfilled = completeOne(store, 6);  // 第 6 个完成触发收口
        expect(backfilled.size() == 1 && backfilled[0] == "three_models_completed",
               "老档下次完成自动补录三模型档");
        expect(store.isAchievementUnlocked("first_model_completed") &&
                   store.isAchievementUnlocked("three_models_completed"),
               "补录后新旧成就都在 (老档不丢成就)");
        std::int64_t first_at_after = 0;
        for (const auto& a : store.listAchievements()) {
            if (a.id == "first_model_completed") first_at_after = a.unlocked_at;
        }
        expect(first_at_after == legacy_first_at, "补录不覆盖老档已有成就的解锁时刻");
    }

    if (g_failures == 0) {
        std::printf("成就解锁统一收口回归测试全部通过\n");
        return 0;
    }
    std::printf("失败断言数: %d\n", g_failures);
    return 1;
}
