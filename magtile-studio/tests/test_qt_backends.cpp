// =============================================================
// MagTile Studio - Qt 后端桥单元测试 (ctest: qt_backend_bridges)
// 仅在 MAGTILE_BUILD_QT=ON 时构建注册, 无需显示环境 (纯 QObject)。
// 覆盖 QT-2 的两座桥 (docs/QT_UI_PLAN.md):
//   1. SettingsBackend: 默认值 / 字号三档与减少动效与年龄段的
//      SQLite 往返 / 跨实例持久化 / 非法值忽略;
//   2. 与 GL 版 / CLI 的共库契约: 桥写入的键能被 progress 层
//      (age_settings / ui_settings) 原样读回, 反向亦然;
//   3. ParentGateBackend: 出题 / 答对开会话 / 答错温和提示 /
//      3 次答错进冷却 (冷却期拒答) / 锁定会话。
// 用法: magtile_qt_backend_test <临时数据库路径>
// =============================================================

#include <QCoreApplication>
#include <QString>
#include <QVariantList>
#include <QVariantMap>
#include <cstdio>
#include <filesystem>

#include "magtile/core/age_mode.hpp"
#include "magtile/progress/age_settings.hpp"
#include "magtile/progress/progress_store.hpp"
#include "magtile/progress/ui_settings.hpp"
#include "parent_gate_backend.hpp"
#include "settings_backend.hpp"

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

    using magtile::core::AgeMode;
    namespace core = magtile::core;
    namespace progress = magtile::progress;
    using magtile::qtui::ParentGateBackend;
    using magtile::qtui::SettingsBackend;

    // ---- 1. SettingsBackend: 默认值与选项数据源 ------------------------
    {
        SettingsBackend settings(db_path);
        expect(settings.storeAvailable(), "存档可用");
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

    if (g_failures == 0) {
        std::printf("\nQt 后端桥单元测试全部通过\n");
        return 0;
    }
    std::printf("\nQt 后端桥单元测试失败: %d 项\n", g_failures);
    return 1;
}
