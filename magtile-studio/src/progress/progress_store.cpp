#include "magtile/progress/progress_store.hpp"

#include <chrono>
#include <utility>

#include <nlohmann/json.hpp>
#include <sqlite3.h>

namespace magtile::progress {
namespace {

/// 当前 schema 版本 (PRAGMA user_version); 结构变更时递增并补迁移分支。
/// v1 -> v2: 磁力片库存从 settings 表的 JSON 字符串迁入结构化的
/// tile_inventory 表 (shape_id, count), 供 canBuild BOM 对照查询。
constexpr int kSchemaVersion = 2;

/// v1 时代磁力片库存 JSON 在 settings 表中的键名 (迁移后删除)。
constexpr const char* kLegacyTileInventoryKey = "tile_inventory";

[[nodiscard]] std::int64_t nowSeconds() {
    return std::chrono::duration_cast<std::chrono::seconds>(
               std::chrono::system_clock::now().time_since_epoch())
        .count();
}

/// 执行不取结果集的 SQL (建表 / PRAGMA 等)。
void exec(sqlite3* db, const char* sql) {
    char* error_message = nullptr;
    if (sqlite3_exec(db, sql, nullptr, nullptr, &error_message) != SQLITE_OK) {
        std::string message = error_message != nullptr ? error_message : "未知错误";
        sqlite3_free(error_message);
        throw ProgressError("进度存档 SQL 执行失败: " + message);
    }
}

/// sqlite3_stmt 的 RAII 包装: 预编译 + 参数绑定 + 逐行读取。
class Statement {
public:
    Statement(sqlite3* db, const char* sql) {
        if (sqlite3_prepare_v2(db, sql, -1, &stmt_, nullptr) != SQLITE_OK) {
            throw ProgressError(std::string("进度存档 SQL 预编译失败: ") + sqlite3_errmsg(db));
        }
    }
    ~Statement() { sqlite3_finalize(stmt_); }
    Statement(const Statement&) = delete;
    Statement& operator=(const Statement&) = delete;

    void bindText(int index, const std::string& value) {
        // SQLITE_TRANSIENT: 让 SQLite 立即复制字符串, 不依赖调用方生命周期
        check(sqlite3_bind_text(stmt_, index, value.c_str(), -1, SQLITE_TRANSIENT));
    }
    void bindInt64(int index, std::int64_t value) {
        check(sqlite3_bind_int64(stmt_, index, value));
    }

    /// 执行一步; 返回 true 表示读到一行结果, false 表示执行完毕。
    bool step() {
        const int rc = sqlite3_step(stmt_);
        if (rc == SQLITE_ROW) return true;
        if (rc == SQLITE_DONE) return false;
        throw ProgressError(std::string("进度存档 SQL 执行失败: ") +
                            sqlite3_errmsg(sqlite3_db_handle(stmt_)));
    }

    [[nodiscard]] std::string columnText(int column) const {
        const unsigned char* text = sqlite3_column_text(stmt_, column);
        return text != nullptr ? reinterpret_cast<const char*>(text) : "";
    }
    [[nodiscard]] std::int64_t columnInt64(int column) const {
        return sqlite3_column_int64(stmt_, column);
    }
    [[nodiscard]] bool columnIsNull(int column) const {
        return sqlite3_column_type(stmt_, column) == SQLITE_NULL;
    }

private:
    void check(int rc) {
        if (rc != SQLITE_OK) {
            throw ProgressError(std::string("进度存档 SQL 参数绑定失败: ") +
                                sqlite3_errmsg(sqlite3_db_handle(stmt_)));
        }
    }

    sqlite3_stmt* stmt_ = nullptr;
};

/// 从 SELECT model_id, current_step, completed_at, play_seconds,
/// favorited, updated_at 的当前行组装 Progress。
Progress readProgressRow(const Statement& stmt) {
    Progress progress;
    progress.model_id = stmt.columnText(0);
    progress.current_step = static_cast<int>(stmt.columnInt64(1));
    progress.completed_at = stmt.columnIsNull(2) ? 0 : stmt.columnInt64(2);
    progress.play_seconds = stmt.columnInt64(3);
    progress.favorited = stmt.columnInt64(4) != 0;
    progress.updated_at = stmt.columnInt64(5);
    return progress;
}

constexpr const char* kProgressColumns =
    "model_id, current_step, completed_at, play_seconds, favorited, updated_at";

}  // namespace

ProgressStore::ProgressStore(const std::filesystem::path& db_file) {
    // SQLite 不会创建父目录, 这里代劳 (平台外壳只需注入目标路径)
    const std::filesystem::path parent = db_file.parent_path();
    if (!parent.empty()) {
        std::filesystem::create_directories(parent);
    }

    // sqlite3_open 要求 UTF-8 路径; u8string 保证 Windows 非 ASCII 路径正确
    const auto utf8_path = db_file.u8string();
    if (sqlite3_open(reinterpret_cast<const char*>(utf8_path.c_str()), &db_) != SQLITE_OK) {
        const std::string message = db_ != nullptr ? sqlite3_errmsg(db_) : "内存不足";
        sqlite3_close(db_);
        db_ = nullptr;
        throw ProgressError("无法打开进度存档 " + db_file.string() + ": " + message);
    }
    // 未来 GUI 与同步线程并发访问时等待锁而非立即失败
    sqlite3_busy_timeout(db_, 3000);

    try {
        initializeSchema();
    } catch (...) {
        sqlite3_close(db_);
        db_ = nullptr;
        throw;
    }
}

ProgressStore::~ProgressStore() {
    sqlite3_close(db_);
}

ProgressStore::ProgressStore(ProgressStore&& other) noexcept : db_(other.db_) {
    other.db_ = nullptr;
}

ProgressStore& ProgressStore::operator=(ProgressStore&& other) noexcept {
    if (this != &other) {
        sqlite3_close(db_);
        db_ = other.db_;
        other.db_ = nullptr;
    }
    return *this;
}

void ProgressStore::initializeSchema() {
    int existing_version = 0;
    {
        Statement query(db_, "PRAGMA user_version;");
        if (query.step()) {
            existing_version = static_cast<int>(query.columnInt64(0));
        }
    }
    if (existing_version > kSchemaVersion) {
        throw ProgressError("进度存档来自更新版本的应用 (schema v" +
                            std::to_string(existing_version) + " > v" +
                            std::to_string(kSchemaVersion) + "), 拒绝降级写入");
    }

    exec(db_,
         "CREATE TABLE IF NOT EXISTS model_progress ("
         "  model_id      TEXT PRIMARY KEY,"          // 对应 data/models/<id>.json
         "  current_step  INTEGER NOT NULL DEFAULT 0,"
         "  completed_at  INTEGER,"                   // unix 秒, NULL = 未完成
         "  play_seconds  INTEGER NOT NULL DEFAULT 0,"
         "  favorited     INTEGER NOT NULL DEFAULT 0,"
         "  updated_at    INTEGER NOT NULL"           // 同步冲突判定用
         ");"
         "CREATE TABLE IF NOT EXISTS achievements ("
         "  id          TEXT PRIMARY KEY,"
         "  unlocked_at INTEGER NOT NULL"
         ");"
         "CREATE TABLE IF NOT EXISTS settings ("
         "  key   TEXT PRIMARY KEY,"
         "  value TEXT NOT NULL"
         ");"
         "CREATE TABLE IF NOT EXISTS tile_inventory ("
         "  shape_id TEXT PRIMARY KEY,"               // core::toString(TileType)
         "  count    INTEGER NOT NULL CHECK(count >= 0)"
         ");");

    // v1 遗留的库存 JSON (settings 表) 迁入 tile_inventory 表。
    // 按键存在性触发而非版本号, 幂等且顺带覆盖 "v2 库被旧版本写回" 的情形。
    migrateLegacyInventoryJson();

    if (existing_version < kSchemaVersion) {
        // v0 (新建库) -> v2: 上面的建表语句即全部内容;
        // v1 -> v2: 增加 tile_inventory 表 + 上方的 JSON 迁移
        exec(db_, "PRAGMA user_version = 2;");
    }
}

void ProgressStore::migrateLegacyInventoryJson() {
    const auto legacy_json = getSetting(kLegacyTileInventoryKey);
    if (!legacy_json.has_value()) return;

    // 旧格式为 UI 层约定的扁平对象 {"square": 24, ...}; 只迁移能识别的
    // 片型与非负数量, 其余条目丢弃 (该格式从未有过正式 UI 写入方)。
    const auto parsed = nlohmann::json::parse(*legacy_json, nullptr, /*allow_exceptions=*/false);
    if (parsed.is_object()) {
        for (const auto& [shape_id, value] : parsed.items()) {
            if (!core::tileTypeFromString(shape_id).has_value()) continue;
            if (!value.is_number_integer() || value.get<std::int64_t>() < 0) continue;
            // 已有结构化记录优先, 不被旧 JSON 覆盖
            Statement stmt(db_,
                           "INSERT INTO tile_inventory (shape_id, count) VALUES (?1, ?2) "
                           "ON CONFLICT(shape_id) DO NOTHING;");
            stmt.bindText(1, shape_id);
            stmt.bindInt64(2, value.get<std::int64_t>());
            stmt.step();
        }
    }
    Statement remove(db_, "DELETE FROM settings WHERE key = ?1;");
    remove.bindText(1, kLegacyTileInventoryKey);
    remove.step();
}

void ProgressStore::ensureRow(const std::string& model_id, std::int64_t now) {
    Statement stmt(db_,
                   "INSERT INTO model_progress (model_id, updated_at) VALUES (?1, ?2) "
                   "ON CONFLICT(model_id) DO NOTHING;");
    stmt.bindText(1, model_id);
    stmt.bindInt64(2, now);
    stmt.step();
}

void ProgressStore::saveProgress(const std::string& model_id, int step,
                                 std::int64_t play_seconds) {
    if (model_id.empty()) throw ProgressError("模型 id 不能为空");
    if (step < 0) throw ProgressError("步骤序号不能为负数");
    if (play_seconds < 0) throw ProgressError("游玩秒数不能为负数");

    // play_seconds 为本次新增时长, 累加到历史总时长 (只增不减, 可与云端合并)
    Statement stmt(db_,
                   "INSERT INTO model_progress (model_id, current_step, play_seconds, updated_at) "
                   "VALUES (?1, ?2, ?3, ?4) "
                   "ON CONFLICT(model_id) DO UPDATE SET "
                   "  current_step = excluded.current_step,"
                   "  play_seconds = model_progress.play_seconds + excluded.play_seconds,"
                   "  updated_at   = excluded.updated_at;");
    stmt.bindText(1, model_id);
    stmt.bindInt64(2, step);
    stmt.bindInt64(3, play_seconds);
    stmt.bindInt64(4, nowSeconds());
    stmt.step();
}

std::optional<Progress> ProgressStore::loadProgress(const std::string& model_id) const {
    Statement stmt(db_, "SELECT model_id, current_step, completed_at, play_seconds, "
                        "favorited, updated_at FROM model_progress WHERE model_id = ?1;");
    stmt.bindText(1, model_id);
    if (!stmt.step()) return std::nullopt;
    return readProgressRow(stmt);
}

void ProgressStore::markCompleted(const std::string& model_id) {
    const std::int64_t now = nowSeconds();
    ensureRow(model_id, now);
    // COALESCE: 保留首次完成时刻, 重复调用不覆盖
    Statement stmt(db_,
                   "UPDATE model_progress SET "
                   "  completed_at = COALESCE(completed_at, ?2),"
                   "  updated_at   = ?2 "
                   "WHERE model_id = ?1;");
    stmt.bindText(1, model_id);
    stmt.bindInt64(2, now);
    stmt.step();
}

bool ProgressStore::toggleFavorite(const std::string& model_id) {
    const std::int64_t now = nowSeconds();
    ensureRow(model_id, now);
    {
        Statement stmt(db_,
                       "UPDATE model_progress SET "
                       "  favorited  = 1 - favorited,"
                       "  updated_at = ?2 "
                       "WHERE model_id = ?1;");
        stmt.bindText(1, model_id);
        stmt.bindInt64(2, now);
        stmt.step();
    }
    Statement query(db_, "SELECT favorited FROM model_progress WHERE model_id = ?1;");
    query.bindText(1, model_id);
    return query.step() && query.columnInt64(0) != 0;
}

bool ProgressStore::resetProgress(const std::string& model_id) {
    Statement stmt(db_, "DELETE FROM model_progress WHERE model_id = ?1;");
    stmt.bindText(1, model_id);
    stmt.step();
    return sqlite3_changes(db_) > 0;
}

std::vector<Progress> ProgressStore::queryProgressList(const char* sql) const {
    Statement stmt(db_, sql);
    std::vector<Progress> result;
    while (stmt.step()) {
        result.push_back(readProgressRow(stmt));
    }
    return result;
}

std::vector<Progress> ProgressStore::listInProgress() const {
    return queryProgressList(
        ("SELECT " + std::string(kProgressColumns) +
         " FROM model_progress WHERE completed_at IS NULL"
         " ORDER BY updated_at DESC, model_id;")
            .c_str());
}

std::vector<Progress> ProgressStore::listCompleted() const {
    return queryProgressList(
        ("SELECT " + std::string(kProgressColumns) +
         " FROM model_progress WHERE completed_at IS NOT NULL"
         " ORDER BY completed_at DESC, model_id;")
            .c_str());
}

void ProgressStore::unlockAchievement(const std::string& achievement_id) {
    if (achievement_id.empty()) throw ProgressError("成就 id 不能为空");
    // OR IGNORE: 保留首次解锁时刻, 重复解锁不覆盖
    Statement stmt(db_, "INSERT OR IGNORE INTO achievements (id, unlocked_at) VALUES (?1, ?2);");
    stmt.bindText(1, achievement_id);
    stmt.bindInt64(2, nowSeconds());
    stmt.step();
}

bool ProgressStore::isAchievementUnlocked(const std::string& achievement_id) const {
    Statement stmt(db_, "SELECT 1 FROM achievements WHERE id = ?1;");
    stmt.bindText(1, achievement_id);
    return stmt.step();
}

std::vector<Achievement> ProgressStore::listAchievements() const {
    Statement stmt(db_, "SELECT id, unlocked_at FROM achievements ORDER BY unlocked_at DESC, id;");
    std::vector<Achievement> result;
    while (stmt.step()) {
        Achievement achievement;
        achievement.id = stmt.columnText(0);
        achievement.unlocked_at = stmt.columnInt64(1);
        result.push_back(std::move(achievement));
    }
    return result;
}

void ProgressStore::setInventory(const std::string& shape_id, int count) {
    if (!core::tileTypeFromString(shape_id).has_value()) {
        throw ProgressError("未知的磁力片形状标识: " + shape_id +
                            " (合法值见 magtile_app catalog)");
    }
    if (count < 0) throw ProgressError("磁力片数量不能为负数");

    Statement stmt(db_,
                   "INSERT INTO tile_inventory (shape_id, count) VALUES (?1, ?2) "
                   "ON CONFLICT(shape_id) DO UPDATE SET count = excluded.count;");
    stmt.bindText(1, shape_id);
    stmt.bindInt64(2, count);
    stmt.step();
}

std::map<std::string, int> ProgressStore::getInventory() const {
    Statement stmt(db_, "SELECT shape_id, count FROM tile_inventory ORDER BY shape_id;");
    std::map<std::string, int> inventory;
    while (stmt.step()) {
        inventory[stmt.columnText(0)] = static_cast<int>(stmt.columnInt64(1));
    }
    return inventory;
}

bool ProgressStore::hasInventory() const {
    Statement stmt(db_, "SELECT 1 FROM tile_inventory LIMIT 1;");
    return stmt.step();
}

std::map<core::TileType, int> ProgressStore::missingPieces(
    const core::ModelDefinition& model) const {
    const auto inventory = getInventory();
    std::map<core::TileType, int> missing;
    for (const auto& [type, needed] : model.pieceCountByType()) {
        const auto it = inventory.find(std::string(core::toString(type)));
        const int owned = it != inventory.end() ? it->second : 0;
        if (owned < needed) missing[type] = needed - owned;
    }
    return missing;
}

bool ProgressStore::canBuild(const core::ModelDefinition& model) const {
    return missingPieces(model).empty();
}

void ProgressStore::setSetting(const std::string& key, const std::string& value) {
    if (key.empty()) throw ProgressError("设置键名不能为空");
    Statement stmt(db_,
                   "INSERT INTO settings (key, value) VALUES (?1, ?2) "
                   "ON CONFLICT(key) DO UPDATE SET value = excluded.value;");
    stmt.bindText(1, key);
    stmt.bindText(2, value);
    stmt.step();
}

std::optional<std::string> ProgressStore::getSetting(const std::string& key) const {
    Statement stmt(db_, "SELECT value FROM settings WHERE key = ?1;");
    stmt.bindText(1, key);
    if (!stmt.step()) return std::nullopt;
    return stmt.columnText(0);
}

std::map<std::string, std::string> ProgressStore::listSettings() const {
    Statement stmt(db_, "SELECT key, value FROM settings ORDER BY key;");
    std::map<std::string, std::string> settings;
    while (stmt.step()) {
        settings[stmt.columnText(0)] = stmt.columnText(1);
    }
    return settings;
}

void ProgressStore::clearAllData() {
    // 家长「清除本地数据」(SECURITY_AND_PRIVACY.md §4 C4/Z8): 四张表
    // 在单个事务里原子清空; sqlite3_exec 中途失败会自动回滚未提交
    // 事务, 这里再显式 ROLLBACK 兜底 (忽略其结果), 保证连接不滞留在
    // 事务中。表结构与 PRAGMA user_version 保留 —— 清完即空档首启态。
    try {
        exec(db_,
             "BEGIN IMMEDIATE;"
             "DELETE FROM model_progress;"
             "DELETE FROM achievements;"
             "DELETE FROM tile_inventory;"
             "DELETE FROM settings;"
             "COMMIT;");
    } catch (...) {
        char* ignored = nullptr;
        sqlite3_exec(db_, "ROLLBACK;", nullptr, nullptr, &ignored);
        sqlite3_free(ignored);
        throw;
    }
}

}  // namespace magtile::progress
