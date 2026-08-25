#include "magtile/progress/subscription_settings.hpp"

namespace magtile::progress {

void setSubscriptionActive(ProgressStore& store, bool active, const std::string& product_id) {
    store.setSetting(kSubscriptionActiveSettingKey, active ? "1" : "0");
    store.setSetting(kSubscriptionProductSettingKey, active ? product_id : "");
}

bool getSubscriptionActive(const ProgressStore& store) {
    // 只有显式写 "1" 才算订阅有效: 缺键 / 脏值按未订阅兜底 (宁可锁)
    const auto stored = store.getSetting(kSubscriptionActiveSettingKey);
    return stored.has_value() && *stored == "1";
}

std::string getSubscriptionProductId(const ProgressStore& store) {
    if (!getSubscriptionActive(store)) return {};
    return store.getSetting(kSubscriptionProductSettingKey).value_or(std::string{});
}

}  // namespace magtile::progress
