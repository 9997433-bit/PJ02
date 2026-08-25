#include "magtile/progress/ui_settings.hpp"

#include <string>

namespace magtile::progress {

bool isValidFontScalePercent(int percent) noexcept {
    for (const int tier : kFontScaleTiers) {
        if (percent == tier) return true;
    }
    return false;
}

void setFontScalePercent(ProgressStore& store, int percent) {
    if (!isValidFontScalePercent(percent)) return;
    store.setSetting(kFontScaleSettingKey, std::to_string(percent));
}

int getFontScalePercent(const ProgressStore& store) {
    const auto stored = store.getSetting(kFontScaleSettingKey);
    if (!stored.has_value()) return 100;
    // 脏值 (手改数据库 / 未来版本新增档位) 按标准档兜底, 不让存档毒化 UI
    try {
        const int percent = std::stoi(*stored);
        return isValidFontScalePercent(percent) ? percent : 100;
    } catch (const std::exception&) {
        return 100;
    }
}

void setReduceMotion(ProgressStore& store, bool reduce) {
    store.setSetting(kReduceMotionSettingKey, reduce ? "1" : "0");
}

bool getReduceMotion(const ProgressStore& store) {
    const auto stored = store.getSetting(kReduceMotionSettingKey);
    return stored.has_value() && *stored == "1";
}

}  // namespace magtile::progress
