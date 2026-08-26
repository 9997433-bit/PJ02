// =============================================================
// MagTile Studio - 家长门 (Parent Gate) 实现
// 设计与安全要求见 include/magtile/core/parent_gate.hpp 头注释、
// docs/UI_UX_SPEC.md §9 与 docs/SECURITY_AND_PRIVACY.md §6。
// =============================================================

#include "magtile/core/parent_gate.hpp"

#include <array>
#include <stdexcept>
#include <vector>

namespace magtile::core {

namespace {

/// 中文大写数字 0~9 (财务体, 每个都是 3 字节 UTF-8)。
constexpr std::array<std::string_view, 10> kUppercaseDigits = {
    "零", "壹", "贰", "叁", "肆", "伍", "陆", "柒", "捌", "玖"};

constexpr std::string_view kTen = "拾";

/// 把 UTF-8 文本切成单个码点的子串序列; 只需要处理本模块用到的
/// 3 字节 CJK 字符与 1 字节 ASCII (空白), 其他长度按首字节推断。
std::size_t utf8CharLength(unsigned char lead) {
    if (lead < 0x80) return 1;
    if ((lead >> 5) == 0x6) return 2;
    if ((lead >> 4) == 0xE) return 3;
    if ((lead >> 3) == 0x1E) return 4;
    return 1;  // 非法首字节: 按 1 字节前进, 解析自然失败
}

/// 单个中文大写数字 -> 0~9; 非数字返回 nullopt。
std::optional<int> digitValue(std::string_view ch) {
    for (int i = 0; i < 10; ++i) {
        if (ch == kUppercaseDigits[static_cast<std::size_t>(i)]) return i;
    }
    return std::nullopt;
}

}  // namespace

ParentGate::ParentGate(Clock::duration session_duration, unsigned seed)
    : session_duration_(session_duration), rng_state_(seed == 0 ? 0x9E3779B9u : seed) {
    newChallenge();
}

// xorshift32: 题目随机化不需要密码学强度, 避免持有 <random> 引擎成员
int ParentGate::nextRandomInRange(int min_inclusive, int max_inclusive) {
    rng_state_ ^= rng_state_ << 13;
    rng_state_ ^= rng_state_ >> 17;
    rng_state_ ^= rng_state_ << 5;
    const int span = max_inclusive - min_inclusive + 1;
    return min_inclusive + static_cast<int>(rng_state_ % static_cast<unsigned>(span));
}

void ParentGate::newChallenge() {
    // 贰~玖: 排除 0/1 的平凡乘法, 积落在 [4, 81]
    const int lhs = nextRandomInRange(2, 9);
    const int rhs = nextRandomInRange(2, 9);
    product_ = lhs * rhs;
    question_ = std::string(kUppercaseDigits[static_cast<std::size_t>(lhs)]) + " × " +
                std::string(kUppercaseDigits[static_cast<std::size_t>(rhs)]) + " = ?";
    expected_answer_ = toChineseUppercase(product_);
}

ParentGateResult ParentGate::submitAnswer(std::string_view answer, Clock::time_point now) {
    if (coolingDown(now)) return ParentGateResult::CoolingDown;
    // 冷却期满: 重置本轮尝试计数
    if (cooldown_until_.has_value()) {
        cooldown_until_.reset();
        consecutive_failures_ = 0;
    }

    const std::optional<int> value = parseChineseUppercase(answer);
    if (value.has_value() && *value == product_) {
        consecutive_failures_ = 0;
        session_expires_at_ = now + session_duration_;
        return ParentGateResult::Passed;
    }

    ++consecutive_failures_;
    if (consecutive_failures_ >= kMaxAttempts) {
        cooldown_until_ = now + kCooldownDuration;
        return ParentGateResult::CoolingDown;
    }
    return ParentGateResult::WrongAnswer;
}

bool ParentGate::coolingDown(Clock::time_point now) const {
    return cooldown_until_.has_value() && now < *cooldown_until_;
}

int ParentGate::cooldownRemainingSeconds(Clock::time_point now) const {
    if (!coolingDown(now)) return 0;
    const auto ms =
        std::chrono::duration_cast<std::chrono::milliseconds>(*cooldown_until_ - now).count();
    return static_cast<int>((ms + 999) / 1000);  // 向上取整
}

bool ParentGate::sessionActive(Clock::time_point now) const {
    return session_expires_at_.has_value() && now < *session_expires_at_;
}

int ParentGate::sessionRemainingSeconds(Clock::time_point now) const {
    if (!sessionActive(now)) return 0;
    const auto ms =
        std::chrono::duration_cast<std::chrono::milliseconds>(*session_expires_at_ - now).count();
    return static_cast<int>((ms + 999) / 1000);  // 向上取整
}

void ParentGate::endSession() noexcept { session_expires_at_.reset(); }

std::string ParentGate::toChineseUppercase(int value) {
    if (value < 0 || value > 99) {
        throw std::out_of_range("toChineseUppercase 仅支持 0~99");
    }
    if (value < 10) return std::string(kUppercaseDigits[static_cast<std::size_t>(value)]);
    const int tens = value / 10;
    const int ones = value % 10;
    std::string text = std::string(kUppercaseDigits[static_cast<std::size_t>(tens)]);
    text += kTen;
    if (ones != 0) text += kUppercaseDigits[static_cast<std::size_t>(ones)];
    return text;
}

std::optional<int> ParentGate::parseChineseUppercase(std::string_view text) {
    // 切分为码点序列 (忽略 ASCII 空白)
    std::vector<std::string_view> chars;
    std::size_t pos = 0;
    while (pos < text.size()) {
        const std::size_t len = utf8CharLength(static_cast<unsigned char>(text[pos]));
        if (pos + len > text.size()) return std::nullopt;
        const std::string_view ch = text.substr(pos, len);
        pos += len;
        if (ch == " " || ch == "\t" || ch == "\n" || ch == "\r") continue;
        chars.push_back(ch);
    }
    if (chars.empty() || chars.size() > 3) return std::nullopt;

    // 形式: [digit] | [拾] | [拾 digit] | [digit 拾] | [digit 拾 digit]
    const auto isTen = [](std::string_view ch) { return ch == kTen; };

    if (chars.size() == 1) {
        if (isTen(chars[0])) return 10;  // 口语省略形 "拾"
        return digitValue(chars[0]);
    }
    if (chars.size() == 2) {
        if (isTen(chars[0])) {  // "拾贰" -> 12
            const auto ones = digitValue(chars[1]);
            if (ones.has_value() && *ones != 0) return 10 + *ones;
            return std::nullopt;
        }
        if (isTen(chars[1])) {  // "贰拾" -> 20
            const auto tens = digitValue(chars[0]);
            if (tens.has_value() && *tens != 0) return *tens * 10;
            return std::nullopt;
        }
        return std::nullopt;
    }
    // 三字符: "贰拾壹" -> 21
    const auto tens = digitValue(chars[0]);
    const auto ones = digitValue(chars[2]);
    if (isTen(chars[1]) && tens.has_value() && *tens != 0 && ones.has_value() && *ones != 0) {
        return *tens * 10 + *ones;
    }
    return std::nullopt;
}

}  // namespace magtile::core
