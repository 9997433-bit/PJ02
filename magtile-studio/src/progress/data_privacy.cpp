#include "magtile/progress/data_privacy.hpp"

#include <chrono>

#include <nlohmann/json.hpp>

namespace magtile::progress {
namespace {

nlohmann::json progressRowJson(const Progress& row) {
    return {
        {"model_id", row.model_id},
        {"current_step", row.current_step},
        {"completed_at", row.completed_at},
        {"play_seconds", row.play_seconds},
        {"favorited", row.favorited},
        {"updated_at", row.updated_at},
    };
}

}  // namespace

std::string exportLocalDataJson(const ProgressStore& store) {
    nlohmann::json root;
    root["format"] = kExportFormatId;
    root["format_version"] = kExportFormatVersion;
    root["exported_at"] = std::chrono::duration_cast<std::chrono::seconds>(
                              std::chrono::system_clock::now().time_since_epoch())
                              .count();

    // model_progress 全表 = 未完成 (listInProgress) + 已完成 (listCompleted),
    // 两个列表按 completed_at 是否为空互斥且合并覆盖全表
    nlohmann::json progress_rows = nlohmann::json::array();
    for (const Progress& row : store.listInProgress()) {
        progress_rows.push_back(progressRowJson(row));
    }
    for (const Progress& row : store.listCompleted()) {
        progress_rows.push_back(progressRowJson(row));
    }
    root["model_progress"] = std::move(progress_rows);

    nlohmann::json achievements = nlohmann::json::array();
    for (const Achievement& achievement : store.listAchievements()) {
        achievements.push_back({
            {"id", achievement.id},
            {"unlocked_at", achievement.unlocked_at},
        });
    }
    root["achievements"] = std::move(achievements);

    nlohmann::json inventory = nlohmann::json::object();
    for (const auto& [shape_id, count] : store.getInventory()) {
        inventory[shape_id] = count;
    }
    root["tile_inventory"] = std::move(inventory);

    nlohmann::json settings = nlohmann::json::object();
    for (const auto& [key, value] : store.listSettings()) {
        settings[key] = value;
    }
    root["settings"] = std::move(settings);

    return root.dump(2);
}

}  // namespace magtile::progress
