#include "magtile/progress/physical_set_settings.hpp"

#include <set>

#include <nlohmann/json.hpp>

namespace magtile::progress {
namespace {

std::vector<std::string> parseOwnedSetsJson(const std::string& raw) {
    const auto parsed = nlohmann::json::parse(raw, nullptr, /*allow_exceptions=*/false);
    if (!parsed.is_array()) return {};

    std::vector<std::string> result;
    std::set<std::string> seen;
    for (const auto& item : parsed) {
        if (!item.is_string()) continue;
        const std::string id = item.get<std::string>();
        if (id.empty() || !seen.insert(id).second) continue;
        result.push_back(id);
    }
    return result;
}

}  // namespace

void setOwnedPhysicalSets(ProgressStore& store, const std::vector<std::string>& set_ids) {
    nlohmann::json array = nlohmann::json::array();
    std::set<std::string> seen;
    for (const auto& id : set_ids) {
        if (id.empty() || !seen.insert(id).second) continue;
        array.push_back(id);
    }
    store.setSetting(kOwnedPhysicalSetsSettingKey, array.dump());
}

std::vector<std::string> getOwnedPhysicalSets(const ProgressStore& store) {
    const auto raw = store.getSetting(kOwnedPhysicalSetsSettingKey);
    if (!raw.has_value()) return {};
    return parseOwnedSetsJson(*raw);
}

}  // namespace magtile::progress
