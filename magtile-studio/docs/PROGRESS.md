# 进度存档模块 (magtile::progress)

本文档描述本地进度存档模块的设计与用法: 数据库结构、C++ API、CLI 命令与测试。该模块落实 [PLATFORM_ARCHITECTURE.md](PLATFORM_ARCHITECTURE.md) §5.1 "本地优先" 数据方案 —— 无账号、无网络时功能 100% 可用, 云同步 (§5.2) 是未来的可选增值。

## 1. 定位与设计原则

- **模块**: `magtile::progress`, 属于共享核心库 `magtile_core`, 公共头文件 `include/magtile/progress/progress_store.hpp`。
- **引擎**: SQLite 3 (公有领域), amalgamation 内嵌于 `third_party/sqlite3/`, 全平台 (含 Android NDK) 统一自编译, 不依赖系统 sqlite 开发包, 构建不需要网络。
- **单文件数据库**: 一个 `progress.db` 就是用户的全部存档, 易备份、易迁移、易云同步。
- **路径由外壳注入**: 核心库不猜平台路径。CLI 作为桌面外壳按平台惯例注入默认路径, 平台外壳 (Qt / Android) 各自注入自己的存档目录。

| 平台 | CLI 默认存档路径 |
| --- | --- |
| Windows | `%APPDATA%/MagTile/progress.db` |
| macOS | `~/Library/Application Support/MagTile/progress.db` |
| Linux | `$XDG_DATA_HOME/magtile/progress.db` (缺省 `~/.local/share/magtile/progress.db`) |
| Android | `Context.getFilesDir()` 下, 由平台外壳注入 |

所有 CLI 进度命令都支持 `--db FILE` 覆盖默认路径 (测试与多存档场景)。

- **可同步的写入语义**: `play_seconds` 只累加、`completed_at`/成就解锁时刻只记首次, 全部满足"只增不减", 未来与云端按 `max` 合并即可, 不需要复杂冲突解决 (见架构文档 §5.2)。
- **schema 版本**: 记录在 `PRAGMA user_version` (当前 v1)。打开旧版本库时自动迁移; 遇到比应用更新的版本号则拒绝写入, 防止旧应用损坏新存档。

## 2. 数据库结构 (schema v1)

```sql
-- 每个模型的教程进度
CREATE TABLE model_progress (
  model_id      TEXT PRIMARY KEY,   -- 对应 data/models/<id>.json
  current_step  INTEGER NOT NULL DEFAULT 0,
  completed_at  INTEGER,            -- unix 秒, NULL = 未完成
  play_seconds  INTEGER NOT NULL DEFAULT 0,  -- 累计游玩秒数, 只增不减
  favorited     INTEGER NOT NULL DEFAULT 0,  -- 0/1 收藏标记
  updated_at    INTEGER NOT NULL    -- 最近更新 unix 秒, 同步冲突判定用
);

-- 已解锁成就 (未解锁的成就不落库)
CREATE TABLE achievements (
  id          TEXT PRIMARY KEY,     -- 成就标识, 如 "first_model_done"
  unlocked_at INTEGER NOT NULL      -- 首次解锁 unix 秒
);

-- 通用键值设置; 磁力片库存 JSON 存于 key = 'tile_inventory'
CREATE TABLE settings (
  key   TEXT PRIMARY KEY,
  value TEXT NOT NULL
);
```

## 3. C++ API

`ProgressStore` 独占一条 SQLite 连接, 构造即建库建表 (父目录不存在时自动创建); 失败抛 `ProgressError` (what() 为中文)。禁止拷贝, 允许移动。

| 方法 | 语义 |
| --- | --- |
| `saveProgress(model_id, step, play_seconds)` | 记录进度: `current_step` 覆盖为新值, `play_seconds` 为**本次新增**的游玩秒数, 累加到历史总时长 |
| `loadProgress(model_id) -> optional<Progress>` | 读取单个模型进度, 无记录返回 `nullopt` |
| `markCompleted(model_id)` | 标记完成; 重复调用不覆盖首次完成时刻 |
| `toggleFavorite(model_id) -> bool` | 切换收藏, 返回切换后状态; 无记录时先创建 |
| `resetProgress(model_id) -> bool` | 删除进度记录, 返回是否确有记录被删除 |
| `listInProgress()` | 进行中的模型, 按最近游玩倒序 |
| `listCompleted()` | 已完成的模型, 按完成时间倒序 |
| `unlockAchievement(id)` / `isAchievementUnlocked(id)` / `listAchievements()` | 成就解锁 (幂等, 保留首次时刻)、查询与列表 |
| `saveTileInventory(json)` / `loadTileInventory()` | 用户拥有的磁力片库存, JSON 字符串整存整取 (结构由 UI 层约定, 核心库不解析) |
| `setSetting(key, value)` / `getSetting(key)` | 通用键值设置, 供音量 / 语言等杂项复用 |

`Progress` 结构体与 `model_progress` 表一一对应, `isCompleted()` 即 `completed_at != 0`。

典型用法 (平台外壳在教程会话结束时):

```cpp
magtile::progress::ProgressStore store(shell.saveDir() / "progress.db");
store.saveProgress(model.id, engine.currentStepNumber(), session_seconds);
if (engine.isFinished()) store.markCompleted(model.id);
```

## 4. CLI 命令

```bash
magtile_app progress list                    # 全部进度: 进行中 / 已完成 / 已解锁成就
magtile_app progress show  <model_id>        # 单个模型详情 (无记录时退出码 1)
magtile_app progress reset <model_id>        # 重置单个模型 (幂等, 无记录也算成功)
# 均支持 --db FILE 指定存档文件
```

示例输出 (`progress list`):

```
进度存档: /home/user/.local/share/magtile/progress.db

进行中 (1 个):
  ★ castle_foundation_01         第 5 步  累计 3 分钟  最近 2026-08-25 13:31

已完成 (1 个):
    rainbow_bridge_01            完成于 2026-08-25 13:31  累计 5 分钟

已解锁成就 (1 个):
  first_model_done               解锁于 2026-08-25 13:31
```

## 5. 测试

| CTest 用例 | 内容 |
| --- | --- |
| `progress_roundtrip` | C++ 回归测试 (`tests/test_progress_roundtrip.cpp`): 保存/读取往返、时长累加、完成标记幂等、收藏切换、进行中/已完成列表、成就解锁幂等、库存 JSON 往返、**关库重开后的持久化**、重置删除、非法输入拒绝 |
| `progress_cli_smoke` | CLI 冒烟: 空库 `progress list` 必须正常退出 (同时覆盖建库建表路径) |

```bash
ctest --test-dir build -R progress --output-on-failure
```

## 6. 第三方组件

SQLite 3 amalgamation (`third_party/sqlite3/sqlite3.c` + `sqlite3.h`), 版本 3.53.4, [公有领域](https://www.sqlite.org/copyright.html)。编译选项: `SQLITE_THREADSAFE=1` (未来 GUI + 同步线程)、`SQLITE_OMIT_LOAD_EXTENSION` (免 `-ldl`)、`SQLITE_DQS=0`、`SQLITE_OMIT_DEPRECATED`、`SQLITE_DEFAULT_MEMSTATUS=0`。升级方法: 从 sqlite.org 下载新版 amalgamation 覆盖两个文件即可。
