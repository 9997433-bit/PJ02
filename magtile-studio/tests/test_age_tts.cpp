// =============================================================
// MagTile Studio - 年龄分层与 TTS 单元测试 (ctest: age_tts)
// 覆盖 UI_UX_SPEC.md §2 (年龄分层) 与 §4.2 (TTS 朗读) 的 stub:
//   1. AgeMode: 持久化标识/中文名/周岁映射的往返与非法输入;
//   2. 年龄段设置: SQLite settings 表往返、跨连接持久化、
//      未设置与脏值的默认档兜底;
//   2b. 界面设置 (§4.7/§8 字号三档 + 减少动效): 往返、非法档位
//      忽略、脏值兜底、跨连接持久化;
//   2c. 步骤朗读总开关 (§4.2 "tts_enabled", Qt 版设置页/TtsBackend
//      共用契约): 默认开、往返、脏值按开兜底、跨连接持久化;
//   3. NullTts: speak 替换旧朗读 (无叠音语义)、stop 幂等、
//      空文本等价于 stop;
//   4. 系统 TTS 探测: createSystemTts 永不返回空指针, 无后端时
//      静音降级; PATH 探测辅助函数。
// 用法: magtile_age_tts_test <临时数据库路径>
// =============================================================

#include <cstdio>
#include <filesystem>
#include <string>

#include "magtile/core/age_mode.hpp"
#include "magtile/progress/age_settings.hpp"
#include "magtile/progress/ui_settings.hpp"
#include "magtile/tts/tts_engine.hpp"

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
    using magtile::core::AgeMode;
    namespace core = magtile::core;
    namespace progress = magtile::progress;
    namespace tts = magtile::tts;

    if (argc < 2) {
        std::fprintf(stderr, "用法: %s <临时数据库路径>\n", argv[0]);
        return 2;
    }
    const std::filesystem::path db_path = argv[1];
    std::filesystem::remove(db_path);  // 每次全新建库, 测试可重复执行

    // ---- 1. AgeMode 枚举与映射 ----------------------------------------
    expect(core::toString(AgeMode::Age4_6) == "age_4_6", "Age4_6 -> \"age_4_6\"");
    expect(core::toString(AgeMode::Age7_9) == "age_7_9", "Age7_9 -> \"age_7_9\"");
    expect(core::toString(AgeMode::Age10_12) == "age_10_12", "Age10_12 -> \"age_10_12\"");
    for (const AgeMode mode : {AgeMode::Age4_6, AgeMode::Age7_9, AgeMode::Age10_12}) {
        expect(core::ageModeFromString(core::toString(mode)) == mode,
               "toString/ageModeFromString 往返一致");
        expect(!core::displayNameZh(mode).empty(), "中文展示名非空");
    }
    expect(!core::ageModeFromString("").has_value(), "空串不可解析");
    expect(!core::ageModeFromString("age_99").has_value(), "未知标识不可解析");
    expect(core::kDefaultAgeMode == AgeMode::Age7_9, "默认档为 7-9 标准模式");

    // 周岁 -> 年龄段: 边界逐一验证 (4/6 归启蒙, 7/9 归标准, 10/12 归进阶)
    expect(core::ageModeFromAgeYears(4) == AgeMode::Age4_6, "4 岁 -> 启蒙模式");
    expect(core::ageModeFromAgeYears(6) == AgeMode::Age4_6, "6 岁 -> 启蒙模式");
    expect(core::ageModeFromAgeYears(7) == AgeMode::Age7_9, "7 岁 -> 标准模式");
    expect(core::ageModeFromAgeYears(9) == AgeMode::Age7_9, "9 岁 -> 标准模式");
    expect(core::ageModeFromAgeYears(10) == AgeMode::Age10_12, "10 岁 -> 进阶模式");
    expect(core::ageModeFromAgeYears(12) == AgeMode::Age10_12, "12 岁 -> 进阶模式");
    expect(!core::ageModeFromAgeYears(3).has_value(), "3 岁超出适龄范围");
    expect(!core::ageModeFromAgeYears(13).has_value(), "13 岁超出适龄范围");
    expect(!core::ageModeFromAgeYears(-1).has_value(), "负数年龄非法");

    // ---- 2. 年龄段设置的 SQLite 往返 ----------------------------------
    {
        progress::ProgressStore store(db_path);
        expect(progress::getAgeMode(store) == AgeMode::Age7_9,
               "从未设置时返回默认档 (标准模式)");
        progress::setAgeMode(store, AgeMode::Age4_6);
        expect(progress::getAgeMode(store) == AgeMode::Age4_6, "设置启蒙模式后立即可读");
        progress::setAgeMode(store, AgeMode::Age10_12);
        expect(progress::getAgeMode(store) == AgeMode::Age10_12, "覆盖为进阶模式");
    }
    {
        progress::ProgressStore store(db_path);  // 重开连接: 验证真正落盘
        expect(progress::getAgeMode(store) == AgeMode::Age10_12, "年龄段跨连接持久化");

        // 脏值兜底: 手改数据库/未来档位不能毒化 UI, 一律回默认档
        store.setSetting(progress::kAgeModeSettingKey, "age_100_200");
        expect(progress::getAgeMode(store) == AgeMode::Age7_9, "脏值回退默认档");
    }

    // ---- 2b. 界面设置 (字号三档 / 减少动效) 的 SQLite 往返 --------------
    {
        progress::ProgressStore store(db_path);
        expect(progress::getFontScalePercent(store) == 100, "从未设置时字号为标准档 100%");
        expect(!progress::getReduceMotion(store), "从未设置时动效开启");
        expect(progress::isValidFontScalePercent(125) &&
                   !progress::isValidFontScalePercent(137),
               "档位校验: 125 合法, 137 非法");

        progress::setFontScalePercent(store, 125);
        progress::setReduceMotion(store, true);
        expect(progress::getFontScalePercent(store) == 125, "字号 125% 立即可读");
        expect(progress::getReduceMotion(store), "减少动效开启后立即可读");

        progress::setFontScalePercent(store, 137);  // 非法档位不落盘
        expect(progress::getFontScalePercent(store) == 125, "非法档位被忽略, 保留原档");

        store.setSetting(progress::kFontScaleSettingKey, "abc");  // 脏值兜底
        expect(progress::getFontScalePercent(store) == 100, "字号脏值回退标准档");
    }
    {
        progress::ProgressStore store(db_path);  // 重开连接: 验证真正落盘
        expect(progress::getReduceMotion(store), "减少动效跨连接持久化");
    }

    // ---- 2c. 步骤朗读总开关 (§4.2 tts_enabled) 的 SQLite 往返 ----------
    {
        progress::ProgressStore store(db_path);
        expect(progress::getTtsEnabled(store), "从未设置时朗读默认开");
        progress::setTtsEnabled(store, false);
        expect(!progress::getTtsEnabled(store), "关闭朗读后立即可读");
        progress::setTtsEnabled(store, true);
        expect(progress::getTtsEnabled(store), "重新开启朗读");

        // 脏值兜底: 非 "0" 一律按开处理 (不毒化朗读功能)
        store.setSetting(progress::kTtsEnabledSettingKey, "banana");
        expect(progress::getTtsEnabled(store), "脏值按默认开兜底");
        progress::setTtsEnabled(store, false);
    }
    {
        progress::ProgressStore store(db_path);  // 重开连接: 验证真正落盘
        expect(!progress::getTtsEnabled(store), "朗读开关跨连接持久化");
    }

    // ---- 3. NullTts: 无叠音语义 ---------------------------------------
    {
        tts::NullTts null_tts;
        expect(!null_tts.available(), "NullTts 不可发声");
        expect(null_tts.name() == "null", "NullTts 后端名为 null");
        expect(!null_tts.speaking() && null_tts.speakCount() == 0, "初始静默");

        null_tts.speak("把三角片靠在墙边");
        expect(null_tts.speaking(), "speak 后处于朗读中");
        expect(null_tts.lastText() == "把三角片靠在墙边", "记录朗读文本");

        // 切步再朗读: 新文本直接替换旧文本 (同一时刻只有一段在读)
        null_tts.speak("盖上屋顶");
        expect(null_tts.speakCount() == 2 && null_tts.lastText() == "盖上屋顶",
               "第二次 speak 替换旧朗读 (无叠音)");

        null_tts.stop();
        expect(!null_tts.speaking(), "stop 停止朗读");
        null_tts.stop();
        expect(!null_tts.speaking(), "stop 幂等");

        null_tts.speak("");
        expect(!null_tts.speaking() && null_tts.speakCount() == 2,
               "空文本等价于 stop, 不计朗读次数");
    }

    // ---- 4. 系统 TTS 探测与降级 ---------------------------------------
    {
        const auto engine = tts::createSystemTts();
        expect(engine != nullptr, "createSystemTts 永不返回空指针");
        expect(!engine->name().empty(), "后端名称非空");
        std::printf("       (本机探测结果: %s, %s)\n",
                    std::string(engine->name()).c_str(),
                    engine->available() ? "可发声" : "静音降级");
        // 无论真实后端还是静音降级, speak/stop 都不得崩溃或抛异常
        engine->speak("测试");
        engine->stop();
        expect(true, "系统引擎 speak/stop 平稳返回");
    }
#if defined(__linux__)
    expect(tts::findExecutableInPath("sh").has_value(), "PATH 中能找到 sh");
    expect(!tts::findExecutableInPath("magtile_no_such_tool_xyz").has_value(),
           "不存在的命令返回 nullopt");
    expect(!tts::findExecutableInPath("").has_value(), "空命令名返回 nullopt");
#endif

    if (g_failures == 0) {
        std::printf("\n年龄分层与 TTS 单元测试全部通过\n");
        return 0;
    }
    std::printf("\n年龄分层与 TTS 单元测试失败: %d 项\n", g_failures);
    return 1;
}
