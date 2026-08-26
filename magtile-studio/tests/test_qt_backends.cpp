// =============================================================
// MagTile Studio - Qt 后端桥单元测试 (ctest: qt_backend_bridges)
// 仅在 MAGTILE_BUILD_QT=ON 时构建注册, 无需显示环境 (纯 QObject)。
// 覆盖 QT-2 的两座桥 (docs/QT_UI_PLAN.md):
//   1. SettingsBackend: 默认值 / 字号三档与减少动效与年龄段的
//      SQLite 往返 / 跨实例持久化 / 非法值忽略;
//   2. 与 GL 版 / CLI 的共库契约: 桥写入的键能被 progress 层
//      (age_settings / ui_settings) 原样读回, 反向亦然;
//   3. ParentGateBackend: 出题 / 答对开会话 / 答错温和提示 /
//      3 次答错进冷却 (冷却期拒答) / 锁定会话;
//   4. LibraryFilterModel (QT-1): 「我能搭的」筛选空态推荐
//      recommendBuildable —— 只挑 canBuild、难度升序 (同难度片数
//      少者优先)、无视其他筛选条件、上限截断;
//   4b. LibraryFilterModel (QT-4, §6.2): 庆祝页「再搭一个」推荐
//      recommendSimilar —— 同难度优先、±1 次之、不足时放宽难度,
//      排除刚完成的自身、订阅内容与缺片模型, 无库存时为空;
//   5. TtsBackend (QT-4): 朗读开关默认开 / 跨实例持久化 / 与
//      ui_settings "tts_enabled" 键的双向契约 (设置页开关同键);
//      本目标不定义 MAGTILE_QT_TTS, 顺带覆盖无引擎静默降级路径;
//   6. 首启年龄段引导判定 (QT-5, §10.1): 全新存档待引导 / 选档落盘
//      (age_mode + onboarding_age_done) 且只出现一次 / 选默认 7-9 档
//      同样落盘 / CLI/GL 已设年龄段或只有完成标记都不再弹 (双保险);
//   7. PrivacyBackend (SECURITY_AND_PRIVACY.md §4 C4/Z8): 全量导出
//      JSON 文件 (格式标识/进度/成就/库存/设置齐全, 两次导出互不
//      覆盖) / 一键清除四张表 / 清除后各桥回默认 (等价首次启动) /
//      resetToDefaults 当场复位 (QML onDataCleared 同一条路径)。
//   8. InventoryBackend (§10.2): 实物套装列表 / 拥有清单持久化 /
//      合并 BOM 预览与应用。
// 用法: magtile_qt_backend_test <临时数据库路径> [data 目录]
// =============================================================

#include <QCoreApplication>
#include <QFile>
#include <QJsonArray>
#include <QJsonDocument>
#include <QJsonObject>
#include <QString>
#include <QVariantList>
#include <QVariantMap>
#include <cstdio>
#include <filesystem>
#include <utility>
#include <vector>

#include "library_filter_model.hpp"
#include "library_model.hpp"
#include "inventory_backend.hpp"
#include "magtile/core/age_mode.hpp"
#include "magtile/progress/age_settings.hpp"
#include "magtile/progress/progress_store.hpp"
#include "magtile/progress/ui_settings.hpp"
#include "parent_gate_backend.hpp"
#include "privacy_backend.hpp"
#include "settings_backend.hpp"
#include "tts_backend.hpp"

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
        std::fprintf(stderr, "用法: %s <临时数据库路径> [data 目录]\n", argv[0]);
        return 2;
    }
    const std::filesystem::path db_path = argv[1];
    const std::filesystem::path data_dir =
        argc >= 3 ? std::filesystem::path(argv[2])
                  : std::filesystem::path(__FILE__).parent_path().parent_path() / "data";
    std::filesystem::remove(db_path);  // 每次全新建库, 测试可重复执行

    using magtile::core::AgeMode;
    namespace core = magtile::core;
    namespace progress = magtile::progress;
    using magtile::qtui::ParentGateBackend;
    using magtile::qtui::SettingsBackend;

    // ---- 1. SettingsBackend: 默认值与选项数据源 ------------------------
    {
        SettingsBackend settings(db_path);
        expect(settings.storeAvailable(), "存档可用");
        expect(settings.ageOnboardingPending(), "全新存档首启年龄段引导待完成 (QT-5)");
        expect(settings.fontScalePercent() == 100, "默认字号 100%");
        expect(!settings.reduceMotion(), "默认动效开启");
        expect(settings.ageModeId() == QStringLiteral("age_7_9"), "默认年龄段 7-9 标准模式");
        expect(!settings.ageModeLabel().isEmpty(), "年龄段中文展示名非空");
        expect(settings.fontScaleOptions().size() == 3, "字号选项恰好三档");
        expect(settings.ageModeOptions().size() == 3, "年龄段选项恰好三档");
        const QVariantMap first_age = settings.ageModeOptions().first().toMap();
        expect(first_age.value(QStringLiteral("id")).toString() == QStringLiteral("age_4_6"),
               "年龄段选项按启蒙/标准/进阶排序");

        // 写入三项设置
        settings.setFontScalePercent(125);
        settings.setReduceMotion(true);
        settings.setAgeModeId(QStringLiteral("age_4_6"));
        expect(settings.fontScalePercent() == 125, "字号 125% 立即生效");
        expect(settings.reduceMotion(), "减少动效立即生效");
        expect(settings.ageModeId() == QStringLiteral("age_4_6"), "年龄段启蒙模式立即生效");

        // 非法值忽略 (不改内存值也不落盘)
        settings.setFontScalePercent(137);
        settings.setAgeModeId(QStringLiteral("age_99"));
        expect(settings.fontScalePercent() == 125, "非法字号档位被忽略");
        expect(settings.ageModeId() == QStringLiteral("age_4_6"), "非法年龄段标识被忽略");
    }

    // ---- 2. 跨实例持久化 + 与 GL 版/CLI 的共库契约 ---------------------
    {
        SettingsBackend settings(db_path);  // 重开桥: 验证真正落盘
        expect(settings.fontScalePercent() == 125, "字号跨实例持久化");
        expect(settings.reduceMotion(), "减少动效跨实例持久化");
        expect(settings.ageModeId() == QStringLiteral("age_4_6"), "年龄段跨实例持久化");
    }
    {
        // progress 层直读: Qt 桥写入的就是 GL 版/CLI 读的那几个键
        progress::ProgressStore store(db_path);
        expect(progress::getAgeMode(store) == AgeMode::Age4_6,
               "CLI/GL 层读到 Qt 桥写入的年龄段 (共用 age_mode 键)");
        expect(progress::getFontScalePercent(store) == 125,
               "progress 层读到 Qt 桥写入的字号档位");
        expect(progress::getReduceMotion(store), "progress 层读到 Qt 桥写入的减少动效");

        // 反向: CLI/GL 侧改设置, Qt 桥重开后看得到
        progress::setAgeMode(store, AgeMode::Age10_12);
    }
    {
        SettingsBackend settings(db_path);
        expect(settings.ageModeId() == QStringLiteral("age_10_12"),
               "Qt 桥读到 CLI/GL 层写入的年龄段 (双向共库)");
    }

    // ---- 3. ParentGateBackend: 过门 / 答错 / 冷却 / 锁定 ---------------
    {
        ParentGateBackend gate;
        expect(!gate.sessionActive(), "初始无家长会话");
        expect(!gate.deepLinkRequested(), "默认无深链请求");

        gate.openGate();
        expect(gate.question().contains(QStringLiteral("×")) &&
                   gate.question().contains(QStringLiteral("?")),
               "题面含 × 与 ? (乘法题)");
        expect(gate.attemptsRemaining() == 3, "初始 3 次尝试机会");
        expect(!gate.expectedAnswer().isEmpty(), "标准答案非空 (冒烟钩子)");

        // 答错: 温和提示 + 次数递减 ("零" 永远不是积, 积在 [4,81])
        expect(!gate.submitAnswer(QStringLiteral("零")), "答错返回 false");
        expect(gate.wrongAnswer(), "答错后 wrongAnswer 置位");
        expect(gate.attemptsRemaining() == 2, "答错后剩 2 次");
        expect(!gate.sessionActive(), "答错不开会话");

        // 答对: 开启会话 (约 15 分钟)
        expect(gate.submitAnswer(gate.expectedAnswer()), "答对返回 true");
        expect(!gate.wrongAnswer(), "答对后 wrongAnswer 复位");
        expect(gate.sessionActive(), "答对后会话立即有效");
        expect(gate.sessionRemainingSeconds() > 14 * 60, "会话剩余约 15 分钟");

        // 锁定: 立即结束会话
        gate.lockSession();
        expect(!gate.sessionActive(), "锁定后会话立即失效");
        expect(gate.sessionRemainingSeconds() == 0, "锁定后剩余 0 秒");

        // 冷却: 连续 3 次答错 -> 60 秒冷却, 冷却期内即使答对也拒绝
        gate.openGate();
        (void)gate.submitAnswer(QStringLiteral("零"));
        (void)gate.submitAnswer(QStringLiteral("零"));
        expect(!gate.submitAnswer(QStringLiteral("零")), "第 3 次答错被拒");
        expect(gate.cooldownSeconds() > 0 && gate.cooldownSeconds() <= 60,
               "触发约 60 秒冷却");
        expect(!gate.wrongAnswer(), "冷却态不再叠加答错提示 (界面自带温和文案)");
        expect(!gate.submitAnswer(gate.expectedAnswer()), "冷却期内答对也拒绝");
        expect(!gate.sessionActive(), "冷却期提交不开会话");

        // 重新进门出新题: 冷却仍在 (状态机为准), 答错提示已复位
        gate.openGate();
        expect(!gate.wrongAnswer(), "openGate 复位答错提示");
        expect(gate.cooldownSeconds() > 0, "openGate 不绕过冷却");
    }

    // ---- 4. LibraryFilterModel: 「我能搭的」空态推荐 (QT-1, §5.2) ------
    {
        using magtile::qtui::LibraryFilterModel;
        using magtile::qtui::LibraryModel;
        using magtile::qtui::LibraryRow;

        const auto makeRow = [](const char* id, int difficulty, int pieces, bool can_build) {
            LibraryRow row;
            row.entry.id = id;
            row.entry.name = id;
            row.entry.difficulty = difficulty;
            row.entry.total_pieces = pieces;
            row.bom_known = true;
            row.can_build = can_build;
            return row;
        };

        LibraryModel model;
        std::vector<LibraryRow> rows;
        rows.push_back(makeRow("hard_ok", 3, 50, true));
        rows.push_back(makeRow("easy_big", 1, 80, true));
        rows.push_back(makeRow("easy_small", 1, 40, true));
        rows.push_back(makeRow("missing_tiles", 2, 60, false));
        rows.push_back(makeRow("expert_ok", 5, 200, true));
        model.resetRows(std::move(rows));

        LibraryFilterModel filter;
        filter.setSourceModel(&model);

        // 模拟空态: 难度 4 + 我能搭的 -> 没有任何匹配
        filter.setDifficulty(4);
        filter.setBuildableOnly(true);
        expect(filter.count() == 0, "难度 4 + 我能搭的 组合为空态");

        // 推荐无视其他筛选: canBuild 里按 难度升序 -> 片数升序 挑 3 个
        const QVariantList recs = filter.recommendBuildable(3);
        expect(recs.size() == 3, "空态推荐恰好 3 个可搭模型");
        expect(recs.value(0).toMap().value(QStringLiteral("modelId")).toString() ==
                   QStringLiteral("easy_small"),
               "第 1 个推荐是难度最低且片数最少的模型");
        expect(recs.value(1).toMap().value(QStringLiteral("modelId")).toString() ==
                   QStringLiteral("easy_big"),
               "同难度按片数升序排列");
        expect(recs.value(2).toMap().value(QStringLiteral("modelId")).toString() ==
                   QStringLiteral("hard_ok"),
               "第 3 个推荐是下一档难度的可搭模型");
        for (const QVariant& rec : recs) {
            expect(rec.toMap().value(QStringLiteral("modelId")).toString() !=
                       QStringLiteral("missing_tiles"),
                   "缺片模型不进推荐");
        }
        expect(filter.recommendBuildable(10).size() == 4, "上限大于可搭数时全量返回");

        // 全部缺片时返回空列表 (界面退回普通空态文案)
        std::vector<LibraryRow> none_buildable;
        none_buildable.push_back(makeRow("a", 1, 10, false));
        model.resetRows(std::move(none_buildable));
        expect(filter.recommendBuildable(3).isEmpty(), "没有可搭模型时推荐为空");
    }

    // ---- 4b. LibraryFilterModel: 庆祝页「再搭一个」推荐 (QT-4, §6.2) ---
    {
        using magtile::qtui::LibraryFilterModel;
        using magtile::qtui::LibraryModel;
        using magtile::qtui::LibraryRow;

        const auto makeRow = [](const char* id, int difficulty, int pieces, bool can_build,
                                bool is_free = true) {
            LibraryRow row;
            row.entry.id = id;
            row.entry.name = id;
            row.entry.difficulty = difficulty;
            row.entry.total_pieces = pieces;
            row.bom_known = true;
            row.can_build = can_build;
            row.is_free = is_free;
            return row;
        };
        const auto recId = [](const QVariantList& recs, int i) {
            return recs.value(i).toMap().value(QStringLiteral("modelId")).toString();
        };

        // 刚完成 just_done (难度 3); 候选覆盖 同难度/±1/更远/缺片/订阅
        LibraryModel model;
        std::vector<LibraryRow> rows;
        rows.push_back(makeRow("just_done", 3, 50, true));
        rows.push_back(makeRow("far_easy", 1, 10, true));
        rows.push_back(makeRow("one_down", 2, 40, true));
        rows.push_back(makeRow("one_up", 4, 20, true));
        rows.push_back(makeRow("same_diff_big", 3, 60, true));
        rows.push_back(makeRow("same_diff_small", 3, 30, true));
        rows.push_back(makeRow("same_missing", 3, 20, false));
        rows.push_back(makeRow("same_locked", 3, 15, true, /*is_free=*/false));
        model.resetRows(std::move(rows));

        LibraryFilterModel filter;
        filter.setSourceModel(&model);

        const QVariantList top2 = filter.recommendSimilar(QStringLiteral("just_done"), 2);
        expect(top2.size() == 2, "庆祝页推荐最多 2 张");
        expect(recId(top2, 0) == QStringLiteral("same_diff_small"),
               "同难度优先, 片数少者排第 1");
        expect(recId(top2, 1) == QStringLiteral("same_diff_big"), "同难度片数多者排第 2");

        const QVariantList all = filter.recommendSimilar(QStringLiteral("just_done"), 10);
        expect(all.size() == 5, "同难度不足时放宽到 ±1 再到更远难度");
        expect(recId(all, 2) == QStringLiteral("one_down") &&
                   recId(all, 3) == QStringLiteral("one_up"),
               "±1 难度垫后, 同距离取更轻松的一档");
        expect(recId(all, 4) == QStringLiteral("far_easy"), "候选不足时放宽难度兜底");
        for (const QVariant& rec : all) {
            const QString id = rec.toMap().value(QStringLiteral("modelId")).toString();
            expect(id != QStringLiteral("just_done"), "刚完成的模型自身不进推荐");
            expect(id != QStringLiteral("same_missing"), "缺片模型不进庆祝页推荐");
            expect(id != QStringLiteral("same_locked"),
                   "订阅内容不进庆祝页推荐 (点卡直接开搭, 不绕过订阅门)");
        }

        // 刚完成的模型不在目录 (极端: 目录热更后被下架): 退回难度升序口径
        const QVariantList fallback = filter.recommendSimilar(QStringLiteral("ghost"), 2);
        expect(fallback.size() == 2 && recId(fallback, 0) == QStringLiteral("far_easy"),
               "基准模型不在目录时退回难度升序推荐");

        // 无库存 (canBuild 恒 false) 时返回空列表 (界面整块隐藏)
        std::vector<LibraryRow> none_buildable;
        none_buildable.push_back(makeRow("just_done", 3, 50, false));
        none_buildable.push_back(makeRow("neighbor", 3, 30, false));
        model.resetRows(std::move(none_buildable));
        expect(filter.recommendSimilar(QStringLiteral("just_done"), 2).isEmpty(),
               "无库存可搭时推荐为空 (庆祝页推荐区整块隐藏)");
    }

    // ---- 5. TtsBackend: 朗读开关持久化与 ui_settings 契约 (QT-4) -------
    {
        magtile::qtui::TtsBackend tts(db_path);
        expect(tts.enabled(), "朗读开关默认开");
        // 本测试目标不链 QtTextToSpeech (未定义 MAGTILE_QT_TTS):
        // available 恒 false, speak/stop 必须静默安全 (P3 零挫败)
        expect(!tts.available(), "无引擎构建时 available=false (静默降级)");
        tts.speak(QStringLiteral("把三角片靠在墙边"));
        tts.stop();
        expect(!tts.speaking(), "无引擎时 speak/stop 平稳返回");
        expect(!tts.autoRead(), "无引擎时不自动朗读 (即使启蒙模式)");

        tts.setEnabled(false);
        expect(!tts.enabled(), "关闭朗读立即生效");
    }
    {
        magtile::qtui::TtsBackend tts(db_path);  // 重开桥: 验证真正落盘
        expect(!tts.enabled(), "朗读开关跨实例持久化");

        // 与设置页 / GL 版的共键契约: 桥写入的关闭状态能被 ui_settings
        // 层原样读回, 反向写入同样能被桥读回 (同一个 "tts_enabled" 键)
        progress::ProgressStore store(db_path);
        expect(!progress::getTtsEnabled(store), "桥写入能被 ui_settings 层读回");
        progress::setTtsEnabled(store, true);
    }
    {
        magtile::qtui::TtsBackend tts(db_path);
        expect(tts.enabled(), "ui_settings 层写入能被桥读回 (反向契约)");
    }

    // ---- 6. 首启年龄段引导判定 (QT-5, §10.1) ---------------------------
    {
        // 主库此刻已写过 age_mode (前面几节写入): 引导不待完成
        SettingsBackend settings(db_path);
        expect(!settings.ageOnboardingPending(), "已有 age_mode 的存档不再弹首启引导");
    }
    {
        // 全新存档: 引导待完成 -> 选档落盘 -> 只出现一次
        const std::filesystem::path onboarding_db(db_path.string() + ".onboarding");
        std::filesystem::remove(onboarding_db);
        {
            SettingsBackend settings(onboarding_db);
            expect(settings.ageOnboardingPending(), "全新存档引导待完成");
            settings.completeAgeOnboarding(QStringLiteral("age_99"));
            expect(settings.ageOnboardingPending(), "未知档位标识不结束引导");
            settings.completeAgeOnboarding(QStringLiteral("age_4_6"));
            expect(!settings.ageOnboardingPending(), "选定档位后引导立即结束");
            expect(settings.ageModeId() == QStringLiteral("age_4_6"), "引导选档即落年龄段");
        }
        {
            SettingsBackend settings(onboarding_db);  // 重开桥: 引导只出现一次
            expect(!settings.ageOnboardingPending(), "引导完成跨实例持久化 (只出现一次)");
            expect(settings.ageModeId() == QStringLiteral("age_4_6"),
                   "引导落盘的年龄段跨实例可读");
        }
        {
            // 共库契约: 引导写的就是 CLI/GL 读的 age_mode 键 + 完成标记
            progress::ProgressStore store(onboarding_db);
            expect(progress::getAgeMode(store) == AgeMode::Age4_6,
                   "CLI/GL 层读到引导写入的年龄段 (共用 age_mode 键)");
            expect(progress::getAgeOnboardingDone(store),
                   "ui_settings 层读到引导完成标记 (onboarding_age_done 契约)");
        }
    }
    {
        // 选的正是默认 7-9 档也要显式落盘 (引导只看 "选没选", 不看 "改没改")
        const std::filesystem::path default_db(db_path.string() + ".onboarding_default");
        std::filesystem::remove(default_db);
        {
            SettingsBackend settings(default_db);
            expect(settings.ageOnboardingPending(), "全新存档 (将选默认档) 引导待完成");
            settings.completeAgeOnboarding(QStringLiteral("age_7_9"));
            expect(!settings.ageOnboardingPending(), "选默认 7-9 档同样结束引导");
        }
        {
            SettingsBackend settings(default_db);
            expect(!settings.ageOnboardingPending(),
                   "默认档选择跨实例持久化 (age_mode 已非空)");
        }
    }
    {
        // 存量存档双保险: CLI/GL 先设过年龄段, 或只有完成标记, 都不再弹
        const std::filesystem::path legacy_db(db_path.string() + ".onboarding_legacy");
        std::filesystem::remove(legacy_db);
        {
            progress::ProgressStore store(legacy_db);
            progress::setAgeMode(store, AgeMode::Age10_12);
        }
        {
            SettingsBackend settings(legacy_db);
            expect(!settings.ageOnboardingPending(),
                   "CLI/GL 已设年龄段的存量存档不弹引导 (age_mode 非空判定)");
        }
        const std::filesystem::path marker_db(db_path.string() + ".onboarding_marker");
        std::filesystem::remove(marker_db);
        {
            progress::ProgressStore store(marker_db);
            progress::setAgeOnboardingDone(store);
        }
        {
            SettingsBackend settings(marker_db);
            expect(!settings.ageOnboardingPending(),
                   "只有完成标记也不再弹引导 (双保险任一即生效)");
        }
    }

    // ---- 7. PrivacyBackend: 全量导出 / 一键清除 / 回首启状态 -----------
    // (SECURITY_AND_PRIVACY.md §4 C4/Z8: 家长可查看/导出/删除全部数据)
    {
        using magtile::qtui::PrivacyBackend;
        PrivacyBackend privacy(db_path);
        expect(privacy.storeAvailable(), "隐私桥存档可用");
        expect(!privacy.dbFileText().isEmpty(), "「数据存在哪」存档路径非空");

        // 前置数据: 进度 / 成就 / 库存各放一条, 导出应全部带上
        {
            progress::ProgressStore store(db_path);
            store.saveProgress("privacy_probe_01", 2, 30);
            store.unlockAchievement("privacy_probe_badge");
            store.setInventory("square", 9);
        }

        const QString export_dir = QString::fromStdString(
            (db_path.parent_path() / "privacy_export_test").string());
        const QString exported = privacy.exportData(export_dir);
        expect(!exported.isEmpty(), "导出返回文件完整路径");
        QFile file(exported);
        expect(file.exists() && file.open(QIODevice::ReadOnly), "导出文件已写盘可读");
        const QJsonDocument doc = QJsonDocument::fromJson(file.readAll());
        file.close();
        expect(doc.isObject(), "导出内容是合法 JSON");
        const QJsonObject root = doc.object();
        expect(root.value(QStringLiteral("format")).toString() ==
                       QStringLiteral("magtile_local_data_export") &&
                   root.value(QStringLiteral("format_version")).toInt() == 1,
               "导出格式标识与版本正确 (三端导出契约)");
        expect(root.value(QStringLiteral("exported_at")).toDouble() > 0, "导出带导出时刻");
        bool progress_in_export = false;
        const QJsonArray progress_rows =
            root.value(QStringLiteral("model_progress")).toArray();
        for (const QJsonValue& row : progress_rows) {
            if (row.toObject().value(QStringLiteral("model_id")).toString() ==
                QStringLiteral("privacy_probe_01")) {
                progress_in_export =
                    row.toObject().value(QStringLiteral("current_step")).toInt() == 2;
            }
        }
        expect(progress_in_export, "导出含进度记录 (model_id + 当前步)");
        expect(root.value(QStringLiteral("tile_inventory"))
                       .toObject()
                       .value(QStringLiteral("square"))
                       .toInt() == 9,
               "导出含磁力片库存");
        expect(!root.value(QStringLiteral("settings")).toObject().isEmpty(),
               "导出含设置键值");
        bool badge_in_export = false;
        const QJsonArray achievement_rows =
            root.value(QStringLiteral("achievements")).toArray();
        for (const QJsonValue& row : achievement_rows) {
            badge_in_export = badge_in_export ||
                              row.toObject().value(QStringLiteral("id")).toString() ==
                                  QStringLiteral("privacy_probe_badge");
        }
        expect(badge_in_export, "导出含成就");

        // 时间戳文件名: 两次导出互不覆盖, 家长可留多份存档
        const QString exported_again = privacy.exportData(export_dir);
        expect(!exported_again.isEmpty() && exported_again != exported,
               "再次导出生成新文件不覆盖旧档");

        // 一键清除: 四张表单事务原子清空, 同库其他连接立即可见
        expect(privacy.clearAllData(), "clearAllData 返回 true");
        {
            progress::ProgressStore store(db_path);
            expect(!store.loadProgress("privacy_probe_01").has_value(), "清除后进度消失");
            expect(store.listAchievements().empty(), "清除后成就清空");
            expect(!store.hasInventory(), "清除后库存回未登记引导态");
            expect(store.listSettings().empty(), "清除后 settings 表为空");
        }
    }
    {
        // 清除后重开各桥 = 首次启动: 设置/朗读回默认, 首启引导重新待命
        SettingsBackend settings(db_path);
        expect(settings.fontScalePercent() == 100 && !settings.reduceMotion() &&
                   settings.ageModeId() == QStringLiteral("age_7_9"),
               "清除后重开设置桥回默认 (等价首启)");
        expect(settings.ageOnboardingPending(),
               "清除后首启年龄段引导重新待完成 (温和回到首次状态)");
        magtile::qtui::TtsBackend tts(db_path);
        expect(tts.enabled(), "清除后重开朗读桥回默认开");

        // 清除流程的当场复位 (Main.qml onDataCleared 同一条调用路径)
        settings.setFontScalePercent(150);
        settings.setReduceMotion(true);
        settings.setAgeModeId(QStringLiteral("age_4_6"));
        tts.setEnabled(false);
        magtile::qtui::PrivacyBackend privacy(db_path);
        expect(privacy.clearAllData(), "再次清除返回 true");
        settings.resetToDefaults();
        tts.resetToDefaults();
        expect(settings.fontScalePercent() == 100 && !settings.reduceMotion() &&
                   settings.ageModeId() == QStringLiteral("age_7_9"),
               "resetToDefaults 把设置内存快照拉回默认");
        expect(tts.enabled(), "resetToDefaults 把朗读开关拉回默认开");
    }

    // ---- 8. InventoryBackend: 实物套装快捷预填 (§10.2) ---------------
    {
        using magtile::qtui::InventoryBackend;
        InventoryBackend inventory(data_dir, db_path);
        const QVariantList sets = inventory.physicalSets();
        expect(sets.size() >= 2, "实物套装目录非空");

        QStringList selected{QStringLiteral("standard_102"), QStringLiteral("connetix_42_square")};
        const QVariantMap preview = inventory.mergedPreview(selected);
        expect(preview.value(QStringLiteral("square")).toInt() == 72,
               "mergedPreview 合并两套装正方形数量 (36+36)");

        const QVariantMap applied = inventory.applyPhysicalSets(selected);
        expect(applied.value(QStringLiteral("square")).toInt() == 72,
               "applyPhysicalSets 返回与 preview 一致的合并 BOM");
        const QStringList owned = inventory.ownedPhysicalSets();
        expect(owned.size() == 2, "applyPhysicalSets 持久化拥有套装清单");
    }

    if (g_failures == 0) {
        std::printf("\nQt 后端桥单元测试全部通过\n");
        return 0;
    }
    std::printf("\nQt 后端桥单元测试失败: %d 项\n", g_failures);
    return 1;
}
