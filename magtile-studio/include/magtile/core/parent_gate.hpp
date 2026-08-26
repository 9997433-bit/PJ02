#pragma once

// =============================================================
// MagTile Studio - 家长门 (Parent Gate)
//
// 儿童区与家长区之间的强制关卡: 订阅 / 设置 / 外链 / 账号 / 数据
// 操作前必须由成人通过算术题验证 (UI_UX_SPEC.md §9,
// SECURITY_AND_PRIVACY.md §6)。本模块是纯逻辑层, 独立可复用,
// 不依赖任何 UI / 平台, 便于单元测试 (题目生成域 / 验证逻辑 /
// 冷却状态机) 与跨平台外壳共享。
//
// 当前实现范围 (商用 stub):
//   - 乘法题随机生成 (贰~玖 两个个位数相乘), 题面以中文数字展示;
//   - 答案要求中文大写数字 (如 21 -> "贰拾壹"), 显著高于学龄儿童
//     的认读能力, 满足 Apple Kids / Play 家庭政策的 parental gate;
//   - 连续 3 次答错 -> 60 秒冷却 (状态只存内存, 重启即清 —— 门的
//     目标是拦儿童, 不是拦成人攻击者);
//   - 通过后开启家长会话, 默认 15 分钟, 只存内存不落盘, 防止
//     重启绕过 ("已通过" 标记永不持久化)。
// 后续 (M3): 可选 4 位 PIN (PBKDF2 加盐哈希) 取代算术题。
// =============================================================

#include <chrono>
#include <optional>
#include <random>  // std::random_device (构造函数默认种子)
#include <string>
#include <string_view>

namespace magtile::core {

/// 家长门一次答案提交的结果。
enum class ParentGateResult {
    Passed,       ///< 答对, 家长会话已开启
    WrongAnswer,  ///< 答错 (尚未触发冷却)
    CoolingDown,  ///< 冷却期内, 提交被拒绝 (含触发冷却的那次答错)
};

/// 家长门状态机: 题目生成 + 答案验证 + 冷却 + 内存会话。
///
/// 所有时间相关接口都接受显式的 `now` 参数 (steady_clock), 生产
/// 代码用默认实参即可, 单元测试可注入虚拟时间。
class ParentGate {
public:
    using Clock = std::chrono::steady_clock;

    /// 家长会话默认有效期: 15 分钟 (只存内存, 重启即失效)。
    static constexpr std::chrono::minutes kDefaultSessionDuration{15};
    /// 连续答错多少次触发冷却。
    static constexpr int kMaxAttempts = 3;
    /// 冷却时长 (温和的 "休息一下", 见 UI_UX_SPEC.md §9.1)。
    static constexpr std::chrono::seconds kCooldownDuration{60};

    /// @param session_duration 通过后家长会话的有效期
    /// @param seed 随机种子; 测试可传固定值获得可复现题目
    explicit ParentGate(Clock::duration session_duration = kDefaultSessionDuration,
                        unsigned seed = std::random_device{}());

    // ---- 题目 -------------------------------------------------------

    /// 生成一道新的乘法题 (每次进门时调用, 题目随机化防背题)。
    void newChallenge();

    /// 当前题面 (中文数字), 如 "叁 × 柒 = ?"。
    [[nodiscard]] const std::string& question() const noexcept { return question_; }

    /// 当前题目的标准答案 (中文大写数字, 如 "贰拾壹")。
    /// 供单元测试与自动化冒烟使用; 门拦截的对象是儿童而非攻击者。
    [[nodiscard]] const std::string& expectedAnswer() const noexcept { return expected_answer_; }

    // ---- 验证与冷却 --------------------------------------------------

    /// 提交答案 (中文大写数字)。答对开启家长会话; 连续答错
    /// kMaxAttempts 次进入冷却, 冷却期内一律返回 CoolingDown。
    ParentGateResult submitAnswer(std::string_view answer, Clock::time_point now = Clock::now());

    /// 是否处于冷却期。
    [[nodiscard]] bool coolingDown(Clock::time_point now = Clock::now()) const;

    /// 冷却剩余秒数 (向上取整; 非冷却期返回 0)。
    [[nodiscard]] int cooldownRemainingSeconds(Clock::time_point now = Clock::now()) const;

    /// 本轮剩余可尝试次数 (冷却结束后重置为 kMaxAttempts)。
    [[nodiscard]] int attemptsRemaining() const noexcept {
        return kMaxAttempts - consecutive_failures_;
    }

    // ---- 家长会话 (只存内存) -----------------------------------------

    /// 家长会话是否仍然有效。
    [[nodiscard]] bool sessionActive(Clock::time_point now = Clock::now()) const;

    /// 会话剩余秒数 (向上取整; 无有效会话返回 0)。
    [[nodiscard]] int sessionRemainingSeconds(Clock::time_point now = Clock::now()) const;

    /// 立即结束家长会话 (家长区 "锁定" 按钮 / 离开家长区时调用)。
    void endSession() noexcept;

    // ---- 中文大写数字工具 (0 ~ 99) -----------------------------------

    /// 整数 -> 规范中文大写数字, 如 21 -> "贰拾壹", 10 -> "壹拾"。
    /// 超出 [0, 99] 抛 std::out_of_range。
    [[nodiscard]] static std::string toChineseUppercase(int value);

    /// 中文大写数字 -> 整数; 接受 "壹拾贰" 与口语省略形 "拾贰",
    /// 忽略前后空白; 无法解析返回 nullopt。
    [[nodiscard]] static std::optional<int> parseChineseUppercase(std::string_view text);

private:
    // 题目状态
    std::string question_;
    std::string expected_answer_;
    int product_ = 0;

    // 冷却状态机 (只存内存)
    int consecutive_failures_ = 0;
    std::optional<Clock::time_point> cooldown_until_;

    // 家长会话 (只存内存, 永不落盘)
    Clock::duration session_duration_;
    std::optional<Clock::time_point> session_expires_at_;

    unsigned rng_state_;  ///< xorshift 状态 (避免在头文件暴露 <random> 引擎)
    [[nodiscard]] int nextRandomInRange(int min_inclusive, int max_inclusive);
};

}  // namespace magtile::core
