#include "magtile/progress/age_settings.hpp"

namespace magtile::progress {

void setAgeMode(ProgressStore& store, core::AgeMode mode) {
    store.setSetting(kAgeModeSettingKey, std::string(core::toString(mode)));
}

core::AgeMode getAgeMode(const ProgressStore& store) {
    const auto stored = store.getSetting(kAgeModeSettingKey);
    if (!stored.has_value()) return core::kDefaultAgeMode;
    // 脏值 (手改数据库 / 未来版本新增档位) 按默认档兜底, 不让存档毒化 UI
    return core::ageModeFromString(*stored).value_or(core::kDefaultAgeMode);
}

}  // namespace magtile::progress
