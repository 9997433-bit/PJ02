#include "magtile/progress/achievements.hpp"

namespace magtile::progress {

std::vector<std::string> unlockAchievementsOnComplete(ProgressStore& store) {
    // listCompleted 只含 completed_at != 0 的行, 数量即已完成模型数
    // (与 Qt completed_count_ / JNI completed_count 展示口径同源)。
    const int completed_count = static_cast<int>(store.listCompleted().size());
    std::vector<std::string> newly_unlocked;
    for (const AchievementTier& tier : kAchievementTiers) {
        if (completed_count < tier.completed_threshold) continue;
        if (store.isAchievementUnlocked(tier.id)) continue;
        store.unlockAchievement(tier.id);
        newly_unlocked.emplace_back(tier.id);
    }
    return newly_unlocked;
}

}  // namespace magtile::progress
