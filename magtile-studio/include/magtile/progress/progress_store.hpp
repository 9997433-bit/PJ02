#pragma once

// =============================================================
// MagTile Studio - 本地进度存档 (SQLite3)
// 记录每个模型的教程进度、完成状态、收藏、成就与磁力片库存,
// 对应 docs/PLATFORM_ARCHITECTURE.md §5.1 "本地优先" 数据方案。
//
// 设计要点:
//   - 单文件 SQLite 数据库, 全平台一致, 易备份易同步;
//   - 存档路径由调用方 (平台外壳 / CLI) 注入, 核心库不猜路径;
//   - play_seconds 与 completed_at 语义 "只增不减", 天然可与
//     云端按 max 合并 (见架构文档 §5.2 冲突解决策略);
//   - schema 版本记录在 PRAGMA user_version, 供未来迁移使用。
// 依赖 third_party/sqlite3 amalgamation, 仅在 .cpp 中包含。
// =============================================================

#include <cstdint>
#include <filesystem>
#include <optional>
#include <stdexcept>
#include <string>
#include <vector>

struct sqlite3;  // 前置声明, 避免向使用方暴露 sqlite3.h

namespace magtile::progress {

/// 存档读写失败时抛出, what() 为中文错误信息。
class ProgressError : public std::runtime_error {
public:
    using std::runtime_error::runtime_error;
};

/// 单个模型的教程进度 (对应 model_progress 表的一行)。
struct Progress {
    std::string model_id;            ///< 对应 data/models/<id>.json
    int current_step = 0;            ///< 已完成到第几步, 0 = 刚开始
    std::int64_t completed_at = 0;   ///< 完成时刻 unix 秒; 0 = 未完成
    std::int64_t play_seconds = 0;   ///< 累计游玩秒数 (只增不减)
    bool favorited = false;          ///< 是否收藏
    std::int64_t updated_at = 0;     ///< 最近更新时刻 unix 秒 (同步冲突判定用)

    [[nodiscard]] bool isCompleted() const noexcept { return completed_at != 0; }
};

/// 已解锁的成就 (对应 achievements 表的一行)。
struct Achievement {
    std::string id;                  ///< 成就标识, 如 "first_model_done"
    std::int64_t unlocked_at = 0;    ///< 解锁时刻 unix 秒
};

/// 进度存档: 独占一条 SQLite 连接, 构造即建库建表。
/// 所有写操作立即落盘 (无显式事务批量需求, 教程场景写入频率极低)。
class ProgressStore {
public:
    /// 打开 (不存在则创建) 存档数据库; 父目录不存在时自动创建。
    explicit ProgressStore(const std::filesystem::path& db_file);
    ~ProgressStore();

    // 独占数据库连接: 禁止拷贝, 允许移动
    ProgressStore(const ProgressStore&) = delete;
    ProgressStore& operator=(const ProgressStore&) = delete;
    ProgressStore(ProgressStore&& other) noexcept;
    ProgressStore& operator=(ProgressStore&& other) noexcept;

    // ---- 教程进度 -------------------------------------------------
    /// 记录进度: 更新当前步骤, 并把 play_seconds 累加到历史时长上
    /// (play_seconds 为本次新增的游玩秒数, 而非总时长)。
    void saveProgress(const std::string& model_id, int step, std::int64_t play_seconds);
    /// 读取单个模型的进度; 无记录时返回 std::nullopt。
    [[nodiscard]] std::optional<Progress> loadProgress(const std::string& model_id) const;
    /// 标记模型已完成 (记录首次完成时刻, 重复调用不覆盖)。
    void markCompleted(const std::string& model_id);
    /// 切换收藏状态 (无记录时先创建), 返回切换后的状态。
    bool toggleFavorite(const std::string& model_id);
    /// 删除单个模型的进度记录; 返回是否确有记录被删除。
    bool resetProgress(const std::string& model_id);
    /// 进行中的模型 (未完成), 按最近游玩时间倒序。
    [[nodiscard]] std::vector<Progress> listInProgress() const;
    /// 已完成的模型, 按完成时间倒序。
    [[nodiscard]] std::vector<Progress> listCompleted() const;

    // ---- 成就 -----------------------------------------------------
    /// 解锁成就 (记录首次解锁时刻, 重复调用不覆盖)。
    void unlockAchievement(const std::string& achievement_id);
    [[nodiscard]] bool isAchievementUnlocked(const std::string& achievement_id) const;
    /// 全部已解锁成就, 按解锁时间倒序。
    [[nodiscard]] std::vector<Achievement> listAchievements() const;

    // ---- 设置 / 磁力片库存 -----------------------------------------
    /// 保存用户拥有的磁力片库存 (JSON 字符串, 结构由 UI 层约定)。
    void saveTileInventory(const std::string& inventory_json);
    /// 读取磁力片库存 JSON; 从未保存过时返回 std::nullopt。
    [[nodiscard]] std::optional<std::string> loadTileInventory() const;
    /// 通用键值设置 (settings 表), 供音量 / 语言等杂项复用。
    void setSetting(const std::string& key, const std::string& value);
    [[nodiscard]] std::optional<std::string> getSetting(const std::string& key) const;

private:
    void initializeSchema();
    /// 确保 model_progress 中存在 model_id 的行 (不存在则插入空进度)。
    void ensureRow(const std::string& model_id, std::int64_t now);
    [[nodiscard]] std::vector<Progress> queryProgressList(const char* sql) const;

    sqlite3* db_ = nullptr;
};

}  // namespace magtile::progress
