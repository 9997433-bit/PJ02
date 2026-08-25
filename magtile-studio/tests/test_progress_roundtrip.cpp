// =============================================================
// MagTile Studio - 进度存档回归测试 (ctest: progress_roundtrip)
// 覆盖: 保存/读取往返、时长累加、完成标记、收藏切换、列表查询、
// 成就解锁、磁力片库存 JSON 往返、跨连接持久化与重置删除。
// 用法: magtile_progress_test <临时数据库文件>
// =============================================================

#include <cstdio>
#include <filesystem>
#include <string>
#include <system_error>

#include "magtile/progress/progress_store.hpp"

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

int main(int argc, char** argv) {
    if (argc != 2) {
        std::fprintf(stderr, "用法: %s <临时数据库文件>\n", argv[0]);
        return 2;
    }
    const std::filesystem::path db_file = argv[1];
    std::error_code ec;
    std::filesystem::remove(db_file, ec);  // 清除上次运行残留, 保证测试可重复

    using magtile::progress::ProgressError;
    using magtile::progress::ProgressStore;

    {
        ProgressStore store(db_file);

        // ---- 空库行为 ----
        expect(!store.loadProgress("castle_foundation_01").has_value(), "空库无进度记录");
        expect(store.listInProgress().empty() && store.listCompleted().empty(), "空库列表为空");
        expect(!store.loadTileInventory().has_value(), "空库无库存记录");

        // ---- 保存 / 读取往返 ----
        store.saveProgress("castle_foundation_01", 3, 120);
        auto record = store.loadProgress("castle_foundation_01");
        expect(record.has_value(), "保存后可读取");
        expect(record->current_step == 3, "读取步骤与保存一致");
        expect(record->play_seconds == 120, "读取时长与保存一致");
        expect(!record->isCompleted() && !record->favorited, "新记录未完成且未收藏");
        expect(record->updated_at > 0, "记录了更新时间戳");

        // 再次保存: 步骤覆盖, 时长累加 (play_seconds 语义为本次新增)
        store.saveProgress("castle_foundation_01", 5, 60);
        record = store.loadProgress("castle_foundation_01");
        expect(record->current_step == 5 && record->play_seconds == 180, "步骤覆盖且时长累加");

        // ---- 完成标记 ----
        store.saveProgress("rainbow_bridge_01", 8, 300);
        store.markCompleted("rainbow_bridge_01");
        record = store.loadProgress("rainbow_bridge_01");
        expect(record->isCompleted(), "完成标记生效");
        const auto first_completed_at = record->completed_at;
        store.markCompleted("rainbow_bridge_01");
        record = store.loadProgress("rainbow_bridge_01");
        expect(record->completed_at == first_completed_at, "重复完成不覆盖首次完成时刻");

        // ---- 收藏切换 ----
        expect(store.toggleFavorite("castle_foundation_01"), "首次切换为已收藏");
        expect(!store.toggleFavorite("castle_foundation_01"), "再次切换取消收藏");
        expect(store.toggleFavorite("castle_foundation_01"), "第三次切换恢复收藏");

        // ---- 列表查询 ----
        const auto in_progress = store.listInProgress();
        const auto completed = store.listCompleted();
        expect(in_progress.size() == 1 && in_progress[0].model_id == "castle_foundation_01",
               "进行中列表只含未完成模型");
        expect(completed.size() == 1 && completed[0].model_id == "rainbow_bridge_01",
               "已完成列表只含完成模型");

        // ---- 成就 ----
        expect(!store.isAchievementUnlocked("first_model_done"), "未解锁的成就查询为否");
        store.unlockAchievement("first_model_done");
        store.unlockAchievement("first_model_done");  // 重复解锁应幂等
        expect(store.isAchievementUnlocked("first_model_done"), "成就解锁生效");
        expect(store.listAchievements().size() == 1, "重复解锁不产生重复记录");

        // ---- 磁力片库存 JSON 往返 ----
        const std::string inventory = R"({"square":24,"triangle_eq":16})";
        store.saveTileInventory(inventory);
        expect(store.loadTileInventory() == inventory, "库存 JSON 往返一致");
        store.saveTileInventory(R"({"square":30})");
        expect(store.loadTileInventory() == std::string(R"({"square":30})"), "库存覆盖保存生效");
    }

    // ---- 重新打开数据库: 验证跨连接持久化 ----
    {
        ProgressStore store(db_file);
        const auto record = store.loadProgress("castle_foundation_01");
        expect(record.has_value() && record->current_step == 5 && record->play_seconds == 180 &&
                   record->favorited,
               "重开数据库后进度仍在");
        expect(store.isAchievementUnlocked("first_model_done"), "重开数据库后成就仍在");
        expect(store.loadTileInventory().has_value(), "重开数据库后库存仍在");

        // ---- 重置删除 ----
        expect(store.resetProgress("castle_foundation_01"), "重置已有记录返回 true");
        expect(!store.loadProgress("castle_foundation_01").has_value(), "重置后记录消失");
        expect(!store.resetProgress("castle_foundation_01"), "重置不存在的记录返回 false");

        // ---- 非法输入拒绝 ----
        bool threw = false;
        try {
            store.saveProgress("castle_foundation_01", -1, 0);
        } catch (const ProgressError&) {
            threw = true;
        }
        expect(threw, "负数步骤序号被拒绝");
    }

    if (g_failures == 0) {
        std::printf("\n进度存档回归测试全部通过\n");
        return 0;
    }
    std::printf("\n进度存档回归测试失败 %d 项\n", g_failures);
    return 1;
}
