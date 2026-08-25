// =============================================================
// MagTile Studio - 跨端进度存档互通回归测试
// (ctest: cross_platform_progress / cross_platform_progress_cli)
//
// Qt 桌面 / GL 桌面 / CLI / Android JNI 四端共用同一个 SQLite
// 进度存档 (PLATFORM_ARCHITECTURE.md §5.1), 互通的前提是 settings
// 表键名与编码严格遵守 progress 模块的持久化契约:
//   - age_mode              (age_settings.hpp, "age_4_6" 等稳定标识)
//   - onboarding_age_done   (ui_settings.hpp, "1" = 引导已完成)
//   - subscription_active   (subscription_settings.hpp, "1"/"0")
//   - subscription_product_id (同上, 生效档位 id)
// 外加 model_progress 完成记录与 achievements 解锁 (achievements.hpp
// 档位表统一收口)。本测试模拟 "一端写 → 另一端读" 的完整链路:
//
//   1. 写入端 (模拟 Android/GL 完成链路): 经 progress 模块类型化
//      API 构造样例存档 —— 年龄段 / 订阅 / 引导标记 / 3 个完成
//      记录 + 1 个进行中 / 成就统一收口解锁;
//   2. schema 键契约: 编译期 static_assert 锁死契约键名字符串;
//      运行期用 listSettings() 快照断言落盘键名与值编码逐一符合
//      契约 (防止某端手写键名漂移导致互通静默失效);
//   3. 读取端 (模拟 Qt 外壳启动): 以第二条连接重开同一存档文件,
//      经与 Qt SettingsBackend / StudioBackend 完全相同的类型化
//      读取口径 (getAgeMode / getSubscriptionActive / ...) 断言
//      读到写入端的全部状态;
//   4. 脏值兜底: 未来版本新增的未知设置键不得毒化既有读取口径。
//
// CLI 真实二进制读取同一存档的断言由 CMake 注册的
// cross_platform_progress_cli 用例执行 (progress list / settings
// show 输出对账), 见顶层 CMakeLists.txt。
// 用法: magtile_cross_platform_test <临时数据库文件>
// =============================================================

#include <cstdio>
#include <filesystem>
#include <string>
#include <string_view>
#include <system_error>

#include "magtile/core/age_mode.hpp"
#include "magtile/progress/achievements.hpp"
#include "magtile/progress/age_settings.hpp"
#include "magtile/progress/progress_store.hpp"
#include "magtile/progress/subscription_settings.hpp"
#include "magtile/progress/ui_settings.hpp"

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

// ---- schema 键契约: 编译期锁死 (改契约键名 = 编译失败) ------------
// 这些字符串是四端共用的 SQLite settings 表键名 (各模块头文件注明
// "持久化契约, 禁止改名"); 任何一端换键名都会破坏跨端互通, 在此
// 用 static_assert 把口径钉死在编译期。
using std::string_view;
static_assert(string_view(magtile::progress::kAgeModeSettingKey) == "age_mode",
              "age_mode 契约键名不得漂移 (age_settings.hpp)");
static_assert(string_view(magtile::progress::kAgeOnboardingDoneSettingKey) ==
                  "onboarding_age_done",
              "onboarding_age_done 契约键名不得漂移 (ui_settings.hpp)");
static_assert(string_view(magtile::progress::kSubscriptionActiveSettingKey) ==
                  "subscription_active",
              "subscription_active 契约键名不得漂移 (subscription_settings.hpp)");
static_assert(string_view(magtile::progress::kSubscriptionProductSettingKey) ==
                  "subscription_product_id",
              "subscription_product_id 契约键名不得漂移 (subscription_settings.hpp)");

// 样例存档使用的模型 id (存档层不校验模型文件存在, 用真实库内 id
// 以贴近实际; CLI 用例按同一组 id 对账, 改动需两处同步)
constexpr const char* kCompletedModels[] = {
    "castle_foundation_01", "rainbow_bridge_01", "dental_clinic_01"};
constexpr const char* kInProgressModel = "eye_clinic_01";

}  // namespace

int main(int argc, char** argv) {
    if (argc != 2) {
        std::fprintf(stderr, "用法: %s <临时数据库文件>\n", argv[0]);
        return 2;
    }
    const std::filesystem::path db_file = argv[1];
    std::error_code ec;
    std::filesystem::remove(db_file, ec);  // 清除上次运行残留, 保证测试可重复

    namespace progress = magtile::progress;
    using magtile::core::AgeMode;

    // =============================================================
    // 1. 写入端: 构造样例存档 (模拟 Android/GL 完成链路的写入口径)
    // =============================================================
    {
        progress::ProgressStore store(db_file);

        // 首启引导 + 年龄段 (Qt AgeOnboardingPage / Android 同一落盘对)
        progress::setAgeMode(store, AgeMode::Age4_6);
        progress::setAgeOnboardingDone(store);

        // 订阅状态 (计费适配层购买成功后的写入口径)
        progress::setSubscriptionActive(store, true, "sub_yearly");

        // 完成记录 + 成就统一收口 (markCompleted 之后调用, 与
        // GL main.cpp / Qt completeBuild / Android JNI 同一口径)
        for (const char* model_id : kCompletedModels) {
            store.saveProgress(model_id, 8, 300);
            store.markCompleted(model_id);
            progress::unlockAchievementsOnComplete(store);
        }
        // 进行中记录 (断点续搭)
        store.saveProgress(kInProgressModel, 4, 120);

        expect(store.listCompleted().size() == 3, "写入端: 3 个完成记录落盘");
        expect(store.isAchievementUnlocked("first_model_completed") &&
                   store.isAchievementUnlocked("three_models_completed"),
               "写入端: 成就统一收口解锁 1/3 两档");
        expect(!store.isAchievementUnlocked("ten_models_completed"),
               "写入端: 未达档成就不提前解锁");
    }

    // =============================================================
    // 2. schema 键契约: settings 表落盘键名与值编码逐一对账
    // =============================================================
    {
        progress::ProgressStore store(db_file);
        const auto settings = store.listSettings();  // settings 表全量快照

        // 年龄段稳定持久化标识 (core/age_mode.cpp toString) 同为跨端契约
        expect(magtile::core::toString(AgeMode::Age4_6) == "age_4_6",
               "schema: age_4_6 持久化标识不漂移 (core/age_mode)");
        expect(settings.count(progress::kAgeModeSettingKey) == 1 &&
                   settings.at(progress::kAgeModeSettingKey) == "age_4_6",
               "schema: age_mode 键按稳定标识编码落盘");
        expect(settings.count(progress::kAgeOnboardingDoneSettingKey) == 1 &&
                   settings.at(progress::kAgeOnboardingDoneSettingKey) == "1",
               "schema: onboarding_age_done 键以 \"1\" 落盘");
        expect(settings.count(progress::kSubscriptionActiveSettingKey) == 1 &&
                   settings.at(progress::kSubscriptionActiveSettingKey) == "1",
               "schema: subscription_active 键以 \"1\" 落盘");
        expect(settings.count(progress::kSubscriptionProductSettingKey) == 1 &&
                   settings.at(progress::kSubscriptionProductSettingKey) == "sub_yearly",
               "schema: subscription_product_id 键记录生效档位");
        expect(settings.size() == 4,
               "schema: 样例存档 settings 表恰好 4 个契约键 (无隐藏键漂移)");
    }

    // =============================================================
    // 3. 读取端: 第二条连接重开, 走 Qt/CLI 同一套类型化读取口径
    // =============================================================
    {
        progress::ProgressStore store(db_file);

        // Qt SettingsBackend / CLI settings show 的读取口径
        expect(progress::getAgeMode(store) == AgeMode::Age4_6,
               "读取端: getAgeMode 读到写入端的启蒙模式");
        expect(progress::getAgeOnboardingDone(store),
               "读取端: 引导完成标记可读 (Qt 首启不再弹引导)");
        expect(progress::getSubscriptionActive(store),
               "读取端: 订阅状态可读 (免费层锁放行口径)");
        expect(progress::getSubscriptionProductId(store) == "sub_yearly",
               "读取端: 订阅档位 id 一致");

        // Qt StudioBackend 进度页 / CLI progress list 的读取口径
        const auto completed = store.listCompleted();
        expect(completed.size() == 3, "读取端: 完成列表 3 个模型");
        bool all_found = true;
        for (const char* model_id : kCompletedModels) {
            const auto record = store.loadProgress(model_id);
            if (!record.has_value() || !record->isCompleted()) all_found = false;
        }
        expect(all_found, "读取端: 每个完成记录均带完成时刻");
        const auto in_progress = store.listInProgress();
        expect(in_progress.size() == 1 && in_progress[0].model_id == kInProgressModel &&
                   in_progress[0].current_step == 4,
               "读取端: 进行中记录保留断点步骤");

        // 成就墙读取口径 (Qt achievementsList / Android progressOverviewJson)
        expect(store.listAchievements().size() == 2,
               "读取端: 成就墙恰好 2 枚 (1/3 两档, 无重复)");

        // 档位表契约: 写入端解锁的 id 必须出自共享档位表
        bool ids_in_tiers = true;
        for (const auto& achievement : store.listAchievements()) {
            bool found = false;
            for (const auto& tier : progress::kAchievementTiers) {
                if (achievement.id == tier.id) found = true;
            }
            if (!found) ids_in_tiers = false;
        }
        expect(ids_in_tiers, "读取端: 成就 id 全部出自 kAchievementTiers 档位表");
    }

    // =============================================================
    // 4. 前向兼容: 未来版本新增未知键不毒化既有读取口径
    // =============================================================
    {
        progress::ProgressStore store(db_file);
        store.setSetting("future_feature_flag", "42");  // 模拟新版本客户端写入
        expect(progress::getAgeMode(store) == AgeMode::Age4_6 &&
                   progress::getSubscriptionActive(store) &&
                   progress::getAgeOnboardingDone(store),
               "前向兼容: 未知设置键不影响契约键读取");
    }

    if (g_failures == 0) {
        std::printf("\n跨端进度存档互通测试全部通过\n");
        return 0;
    }
    std::printf("\n跨端进度存档互通测试失败 %d 项\n", g_failures);
    return 1;
}
