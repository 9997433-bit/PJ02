// =============================================================
// MagTile Studio - 进度存档回归测试 (ctest: progress_roundtrip)
// 覆盖: 保存/读取往返、时长累加、完成标记、收藏切换、列表查询、
// 成就解锁、磁力片库存 (tile_inventory 表) 登记/读取/BOM 对照
// (canBuild / missingPieces)、v1 库存 JSON 迁移、跨连接持久化
// 与重置删除。
// 用法: magtile_progress_test <临时数据库文件>
// =============================================================

#include <cstdio>
#include <filesystem>
#include <string>
#include <system_error>

#include "magtile/core/model_definition.hpp"
#include "magtile/core/tile_instance.hpp"
#include "magtile/core/types.hpp"
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

/// 构造只填 final_assembly 片型统计的合成模型 (BOM 对照用)。
magtile::core::ModelDefinition makeModel(int squares, int triangles, int sectors) {
    magtile::core::ModelDefinition model;
    model.id = "bom_test_model";
    const auto append = [&](magtile::core::TileType type, int count, const char* prefix) {
        for (int i = 0; i < count; ++i) {
            magtile::core::TileInstance tile;
            tile.id = std::string(prefix) + std::to_string(i);
            tile.type = type;
            model.final_assembly.push_back(tile);
        }
    };
    append(magtile::core::TileType::Square, squares, "s");
    append(magtile::core::TileType::EquilateralTriangle, triangles, "t");
    append(magtile::core::TileType::Sector, sectors, "c");
    return model;
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
        expect(!store.hasInventory() && store.getInventory().empty(), "空库无库存记录");

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

        // ---- 磁力片库存 (tile_inventory 表) ----
        store.setInventory("square", 24);
        store.setInventory("equilateral_triangle", 16);
        auto inventory = store.getInventory();
        expect(inventory.size() == 2 && inventory["square"] == 24 &&
                   inventory["equilateral_triangle"] == 16,
               "库存登记与读取往返一致");
        store.setInventory("square", 30);
        expect(store.getInventory()["square"] == 30, "库存覆盖登记生效");
        store.setInventory("hexagon", 0);
        inventory = store.getInventory();
        expect(inventory.count("hexagon") == 1 && inventory.at("hexagon") == 0,
               "数量为 0 的登记保留记录 (明确没有 != 从未登记)");
        expect(store.hasInventory(), "登记后 hasInventory 为真");

        bool threw_shape = false;
        try {
            store.setInventory("not_a_shape", 3);
        } catch (const ProgressError&) {
            threw_shape = true;
        }
        expect(threw_shape, "未知形状标识被拒绝");
        bool threw_count = false;
        try {
            store.setInventory("square", -1);
        } catch (const ProgressError&) {
            threw_count = true;
        }
        expect(threw_count, "负数库存数量被拒绝");

        // ---- canBuild / missingPieces: 模型 BOM 对照 ----
        // 当前库存: square 30, equilateral_triangle 16, hexagon 0
        expect(store.canBuild(makeModel(20, 10, 0)), "库存足够时 canBuild 为真");
        expect(store.missingPieces(makeModel(20, 10, 0)).empty(), "库存足够时无缺片");

        const auto missing = store.missingPieces(makeModel(20, 20, 4));
        expect(!store.canBuild(makeModel(20, 20, 4)), "缺片时 canBuild 为假");
        expect(missing.size() == 2 &&
                   missing.at(magtile::core::TileType::EquilateralTriangle) == 4 &&
                   missing.at(magtile::core::TileType::Sector) == 4,
               "缺片清单按片型给出缺口数量 (含未登记片型)");
    }

    // ---- 重新打开数据库: 验证跨连接持久化 ----
    {
        ProgressStore store(db_file);
        const auto record = store.loadProgress("castle_foundation_01");
        expect(record.has_value() && record->current_step == 5 && record->play_seconds == 180 &&
                   record->favorited,
               "重开数据库后进度仍在");
        expect(store.isAchievementUnlocked("first_model_done"), "重开数据库后成就仍在");
        expect(store.getInventory()["square"] == 30, "重开数据库后库存仍在");

        // ---- v1 库存 JSON 迁移: settings 表遗留键在下次打开时迁入
        // tile_inventory 表 (已有记录优先, 非法条目丢弃, 键删除) ----
        store.setSetting("tile_inventory",
                         R"({"square":7,"rhombus":3,"bogus_shape":5,"trapezoid":-2})");

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

    // ---- 第三次打开: 验证 v1 库存 JSON 迁移 ----
    {
        ProgressStore store(db_file);
        const auto inventory = store.getInventory();
        expect(inventory.at("square") == 30, "迁移不覆盖已有的结构化库存记录");
        expect(inventory.count("rhombus") == 1 && inventory.at("rhombus") == 3,
               "遗留 JSON 中的合法条目已迁入 tile_inventory 表");
        expect(inventory.count("bogus_shape") == 0 && inventory.count("trapezoid") == 0,
               "未知形状与负数数量的遗留条目被丢弃");
        expect(!store.getSetting("tile_inventory").has_value(), "迁移后遗留 JSON 键已删除");
    }

    if (g_failures == 0) {
        std::printf("\n进度存档回归测试全部通过\n");
        return 0;
    }
    std::printf("\n进度存档回归测试失败 %d 项\n", g_failures);
    return 1;
}
