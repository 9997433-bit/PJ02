#include "magtile/core/age_mode.hpp"

namespace magtile::core {

std::string_view toString(AgeMode mode) noexcept {
    switch (mode) {
        case AgeMode::Age4_6: return "age_4_6";
        case AgeMode::Age7_9: return "age_7_9";
        case AgeMode::Age10_12: return "age_10_12";
    }
    return "age_7_9";  // 防御: 枚举外脏值按默认档处理
}

std::string_view displayNameZh(AgeMode mode) noexcept {
    switch (mode) {
        case AgeMode::Age4_6: return "4-6 岁 · 启蒙模式";
        case AgeMode::Age7_9: return "7-9 岁 · 标准模式";
        case AgeMode::Age10_12: return "10-12 岁 · 进阶模式";
    }
    return "7-9 岁 · 标准模式";
}

std::optional<AgeMode> ageModeFromString(std::string_view name) noexcept {
    if (name == "age_4_6") return AgeMode::Age4_6;
    if (name == "age_7_9") return AgeMode::Age7_9;
    if (name == "age_10_12") return AgeMode::Age10_12;
    return std::nullopt;
}

std::optional<AgeMode> ageModeFromAgeYears(int age_years) noexcept {
    if (age_years >= 4 && age_years <= 6) return AgeMode::Age4_6;
    if (age_years >= 7 && age_years <= 9) return AgeMode::Age7_9;
    if (age_years >= 10 && age_years <= 12) return AgeMode::Age10_12;
    return std::nullopt;  // 产品适龄范围 4~12 岁之外
}

}  // namespace magtile::core
