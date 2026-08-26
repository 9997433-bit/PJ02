// =============================================================
// MagTile Studio - 家长门单元测试 (ctest: parent_gate)
// 覆盖 SECURITY_AND_PRIVACY.md §6.2 要求单测的三个域:
//   1. 题目生成域: 乘法题操作数范围、题面格式、随机化;
//   2. 验证逻辑: 中文大写数字转换/解析 (含 "壹拾" / "拾" 变体)、
//      正确/错误答案、非法输入;
//   3. 冷却状态机与内存会话: 3 次答错 -> 60s 冷却、冷却期拒答、
//      期满重置; 会话 15 分钟有效、到期/手动结束失效。
// 时间全部通过显式 time_point 注入, 测试不真实等待。
// =============================================================

#include <chrono>
#include <cstdio>
#include <set>
#include <string>

#include "magtile/core/parent_gate.hpp"

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

int main() {
    using magtile::core::ParentGate;
    using magtile::core::ParentGateResult;
    using namespace std::chrono_literals;

    const ParentGate::Clock::time_point t0 = ParentGate::Clock::now();

    // ---- 1. 中文大写数字转换 ----------------------------------------
    expect(ParentGate::toChineseUppercase(0) == "零", "0 -> 零");
    expect(ParentGate::toChineseUppercase(7) == "柒", "7 -> 柒");
    expect(ParentGate::toChineseUppercase(10) == "壹拾", "10 -> 壹拾");
    expect(ParentGate::toChineseUppercase(21) == "贰拾壹", "21 -> 贰拾壹");
    expect(ParentGate::toChineseUppercase(81) == "捌拾壹", "81 -> 捌拾壹");
    bool threw = false;
    try {
        (void)ParentGate::toChineseUppercase(100);
    } catch (const std::out_of_range&) {
        threw = true;
    }
    expect(threw, "超出 0~99 抛 out_of_range");

    // ---- 2. 中文大写数字解析 (含口语变体与非法输入) --------------------
    expect(ParentGate::parseChineseUppercase("贰拾壹") == 21, "解析 贰拾壹 -> 21");
    expect(ParentGate::parseChineseUppercase("壹拾贰") == 12, "解析 壹拾贰 -> 12");
    expect(ParentGate::parseChineseUppercase("拾贰") == 12, "口语变体 拾贰 -> 12");
    expect(ParentGate::parseChineseUppercase("拾") == 10, "口语变体 拾 -> 10");
    expect(ParentGate::parseChineseUppercase("肆拾") == 40, "解析 肆拾 -> 40");
    expect(ParentGate::parseChineseUppercase(" 玖 ") == 9, "忽略前后空白");
    expect(!ParentGate::parseChineseUppercase("").has_value(), "空串不可解析");
    expect(!ParentGate::parseChineseUppercase("21").has_value(), "阿拉伯数字不接受");
    expect(!ParentGate::parseChineseUppercase("二十一").has_value(), "小写中文数字不接受");
    expect(!ParentGate::parseChineseUppercase("拾拾").has_value(), "拾拾 非法");
    expect(!ParentGate::parseChineseUppercase("零拾").has_value(), "零拾 非法");
    expect(!ParentGate::parseChineseUppercase("壹贰叁肆").has_value(), "超长输入非法");

    // ---- 3. 题目生成域 ------------------------------------------------
    {
        ParentGate gate(ParentGate::kDefaultSessionDuration, /*seed=*/12345u);
        std::set<std::string> questions;
        for (int i = 0; i < 50; ++i) {
            gate.newChallenge();
            const std::string& question = gate.question();
            expect(!question.empty() && question.find("×") != std::string::npos &&
                       question.find('?') != std::string::npos,
                   "题面含 × 与 ? (乘法题)");
            const auto product = ParentGate::parseChineseUppercase(gate.expectedAnswer());
            expect(product.has_value() && *product >= 4 && *product <= 81,
                   "标准答案可解析且积在 [4, 81] (操作数 贰~玖)");
            questions.insert(question);
            if (g_failures > 0) break;  // 避免刷屏
        }
        expect(questions.size() >= 5, "50 道题至少 5 种不同题面 (随机化)");
    }

    // ---- 4. 验证逻辑 + 内存会话 ----------------------------------------
    {
        ParentGate gate(15min, /*seed=*/7u);
        expect(!gate.sessionActive(t0), "初始无家长会话");
        expect(gate.submitAnswer("零", t0) == ParentGateResult::WrongAnswer,
               "错误答案返回 WrongAnswer");
        expect(!gate.sessionActive(t0), "答错不开启会话");
        expect(gate.submitAnswer(gate.expectedAnswer(), t0) == ParentGateResult::Passed,
               "正确答案 (中文大写) 返回 Passed");
        expect(gate.sessionActive(t0), "答对后会话立即有效");
        expect(gate.sessionActive(t0 + 14min), "第 14 分钟会话仍有效");
        expect(gate.sessionRemainingSeconds(t0 + 14min) <= 60 + 1 &&
                   gate.sessionRemainingSeconds(t0 + 14min) > 0,
               "第 14 分钟剩余约 1 分钟");
        expect(!gate.sessionActive(t0 + 15min), "第 15 分钟整会话到期");
        expect(!gate.sessionActive(t0 + 16min), "到期后不再有效 (重启/过期不保留)");

        // 手动结束 (家长区 "锁定" / 离开家长区)
        expect(gate.submitAnswer(gate.expectedAnswer(), t0) == ParentGateResult::Passed,
               "可再次过门");
        gate.endSession();
        expect(!gate.sessionActive(t0), "endSession 立即失效");
    }

    // ---- 5. 冷却状态机 -------------------------------------------------
    {
        ParentGate gate(15min, /*seed=*/99u);
        expect(gate.attemptsRemaining() == 3, "初始 3 次尝试机会");
        expect(gate.submitAnswer("零", t0) == ParentGateResult::WrongAnswer, "第 1 次答错");
        expect(gate.attemptsRemaining() == 2, "剩 2 次");
        expect(gate.submitAnswer("零", t0 + 1s) == ParentGateResult::WrongAnswer, "第 2 次答错");
        expect(gate.submitAnswer("零", t0 + 2s) == ParentGateResult::CoolingDown,
               "第 3 次答错触发冷却");
        expect(gate.coolingDown(t0 + 3s), "冷却期内 coolingDown 为真");
        expect(gate.cooldownRemainingSeconds(t0 + 2s) >= 59, "冷却剩余约 60 秒");
        expect(gate.submitAnswer(gate.expectedAnswer(), t0 + 30s) ==
                   ParentGateResult::CoolingDown,
               "冷却期内即使答对也拒绝");
        expect(!gate.sessionActive(t0 + 30s), "冷却期提交不开启会话");
        expect(!gate.coolingDown(t0 + 63s), "60 秒后冷却结束");
        expect(gate.submitAnswer(gate.expectedAnswer(), t0 + 63s) == ParentGateResult::Passed,
               "冷却结束后答对通过");
        expect(gate.attemptsRemaining() == 3, "通过后尝试次数重置");
    }

    // ---- 6. 答对重置连续错误计数 ---------------------------------------
    {
        ParentGate gate(15min, /*seed=*/5u);
        (void)gate.submitAnswer("零", t0);
        (void)gate.submitAnswer("零", t0);
        expect(gate.submitAnswer(gate.expectedAnswer(), t0) == ParentGateResult::Passed,
               "两错一对仍可通过");
        gate.endSession();
        gate.newChallenge();
        expect(gate.attemptsRemaining() == 3, "答对后连续错误计数清零");
    }

    if (g_failures == 0) {
        std::printf("\n家长门单元测试全部通过\n");
        return 0;
    }
    std::printf("\n家长门单元测试失败: %d 项\n", g_failures);
    return 1;
}
