// =============================================================
// MagTile Studio - 应用入口
//
// 同一个可执行文件提供两种形态:
//   - CLI: 内容制作与质检 (catalog / validate / tutorial / library);
//   - GUI: 商业版应用 —— library --gui 打开模型库主界面,
//     点击卡片进入 3D 交互教程, 进度自动写入存档;
//     tutorial --gui 直接打开单个模型的教程窗口
//     (均需构建时开启 MAGTILE_BUILD_GL_RENDERER)。
//
// 用法:
//   magtile_app library  [--gui] [--data-dir DIR] [--db FILE]    模型库 (商业版主入口)
//   magtile_app catalog  [--data-dir DIR]                查看磁力片形状目录
//   magtile_app validate <model.json> [--data-dir DIR]   物理与教程质检
//   magtile_app tutorial <model.json> [--gui] [--data-dir DIR]  分步教程
//   magtile_app progress list|show|reset [...] [--db FILE]      进度存档
//   magtile_app inventory set|show|match [...] [--db FILE]      磁力片库存
//   magtile_app settings set-age 4|7|10 | show [--db FILE]      年龄段模式等设置
// =============================================================

#include <algorithm>
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <ctime>
#include <exception>
#include <filesystem>
#include <map>
#include <string>
#include <vector>

#include "magtile/core/age_mode.hpp"
#include "magtile/core/json_io.hpp"
#include "magtile/core/model_catalog.hpp"
#include "magtile/core/tile_catalog.hpp"
#include "magtile/physics/physics_validator.hpp"
#include "magtile/progress/age_settings.hpp"
#include "magtile/progress/progress_store.hpp"
#include "magtile/tts/tts_engine.hpp"
#include "magtile/tutorial/tutorial_engine.hpp"

#if defined(MAGTILE_HAS_GL_RENDERER)
#include <chrono>
#include <unordered_map>
#include <unordered_set>
#include <utility>

#include "magtile/core/parent_gate.hpp"
#include "magtile/physics/geometry.hpp"
#include "magtile/render/gl_renderer.hpp"
#endif

namespace {

namespace fs = std::filesystem;
using namespace magtile;

struct CliArgs {
    std::string command;
    std::string model_file;
    fs::path data_dir = "data";
    bool gui = false;
    bool core_only = false;      ///< --core-only: 只列核心 9 片型 / 只用核心片的模型
    int start_step = 1;          ///< 图形模式的起始步骤
    long max_frames = 0;         ///< >0 时渲染指定帧数后自动退出 (冒烟测试)
    std::string screenshot_file; ///< 非空时在最后一帧保存 PPM 图片 (冒烟测试)
    std::string progress_action; ///< progress 子命令: list / show / reset
    std::string model_id;        ///< progress show/reset 的目标模型 id
    std::string inventory_action;  ///< inventory 子命令: set / show / match
    std::vector<std::string> inventory_pairs;  ///< inventory set 的 <形状 数量> 对
    std::string settings_action;  ///< settings 子命令: set-age / show
    std::string settings_value;   ///< settings set-age 的年龄参数 (周岁)
    std::string profile;          ///< validate 的物理校验档位 (default / strict)
    bool tts = false;            ///< --tts: 教程切步时朗读步骤说明 (系统 TTS)
    std::string open_model;      ///< library --gui: 启动后直接打开的模型 id
    bool open_parent_gate = false;  ///< library --gui: 启动即显示家长门 (评审/冒烟)
    bool open_inventory = false;    ///< library --gui: 启动即打开库存录入界面
    std::string smoke_inventory;    ///< 冒烟自动驾驶: "square=40,rectangle=8" 经图形
                                    ///< 录入路径写入并保存 (供 CI 验证图形写库存)
    fs::path db_file;            ///< 进度存档路径; 为空时用平台默认路径
};

void printUsage() {
    std::printf(
        "MagTile Studio - 磁力片搭建教程\n"
        "\n"
        "用法:\n"
        "  magtile_app library  [--gui] [--core-only] [--data-dir DIR] [--db FILE]\n"
        "                       模型库 (商业版主入口): --gui 打开图形界面, 浏览/搜索/\n"
        "                       筛选模型卡片并进入教程; 默认在终端列出模型与进度;\n"
        "                       --core-only 只列基础套装 (核心 9 片型) 就能搭的模型\n"
        "  magtile_app catalog  [--core-only] [--data-dir DIR]  查看磁力片形状目录\n"
        "                       (--core-only 只列核心 9 片型)\n"
        "  magtile_app validate <model.json> [--data-dir DIR] [--profile default|strict]\n"
        "                       校验模型物理规则与教程步骤; --profile strict 使用弱磁\n"
        "                       严格档 (悬挂额定 120g/边长, 安全系数 0.7, 面向磁力较弱\n"
        "                       的品牌与旧片, 详见 docs/PHYSICS_RULES.md)\n"
        "  magtile_app tutorial <model.json> [--gui] [--data-dir DIR]\n"
        "                       分步教程: 默认在终端预览, --gui 打开 3D 交互窗口\n"
        "  magtile_app progress list                          查看全部教程进度与成就\n"
        "  magtile_app progress show  <model_id>              查看单个模型的进度详情\n"
        "  magtile_app progress reset <model_id>              重置单个模型的进度\n"
        "  magtile_app inventory set <形状 数量>...            登记家里的磁力片库存\n"
        "                       (示例: inventory set square 40 equilateral_triangle 24;\n"
        "                        形状标识见 magtile_app catalog)\n"
        "  magtile_app inventory show                         查看已登记的磁力片库存\n"
        "  magtile_app inventory match [--data-dir DIR]       对照库存列出能搭建的模型\n"
        "  magtile_app settings set-age <周岁>                 设置孩子年龄段模式\n"
        "                       (4~6 启蒙 / 7~9 标准 / 10~12 进阶, 示例: set-age 4)\n"
        "  magtile_app settings show                          查看当前设置与 TTS 后端\n"
        "\n"
        "教程选项:\n"
        "  --tts               切换步骤时朗读步骤说明 (系统 TTS, 无后端时静音;\n"
        "                       4-6 岁启蒙模式下模型库教程自动开启)\n"
        "\n"
        "图形模式选项:\n"
        "  --step N            (tutorial) 从第 N 步开始 (默认 1)\n"
        "  --open MODEL_ID     (library) 启动后直接进入指定模型的教程\n"
        "  --parent-gate       (library) 启动即显示家长门界面 (评审/冒烟测试)\n"
        "  --inventory         (library) 启动即打开磁力片库存录入界面\n"
        "  --smoke-inventory SPEC\n"
        "                      (library) 冒烟自动驾驶: 经图形录入路径把 SPEC\n"
        "                      (如 square=40,rectangle=8) 写入并保存 (供 CI 测试)\n"
        "  --frames N          渲染 N 帧后自动退出 (供 CI 冒烟测试)\n"
        "  --screenshot FILE   退出前把画面保存为 PPM 图片 (供 CI 冒烟测试)\n"
        "\n"
        "进度存档选项:\n"
        "  --db FILE           指定存档数据库文件 (默认平台存档目录, 见 docs/PROGRESS.md)\n");
}

bool parseArgs(int argc, char** argv, CliArgs& args) {
    if (argc < 2) return false;
    args.command = argv[1];

    std::vector<std::string> positional;
    for (int i = 2; i < argc; ++i) {
        const std::string arg = argv[i];
        if (arg == "--data-dir") {
            if (i + 1 >= argc) return false;
            args.data_dir = argv[++i];
        } else if (arg == "--gui") {
            args.gui = true;
        } else if (arg == "--core-only") {
            args.core_only = true;
        } else if (arg == "--step") {
            if (i + 1 >= argc) return false;
            args.start_step = static_cast<int>(std::strtol(argv[++i], nullptr, 10));
        } else if (arg == "--frames") {
            if (i + 1 >= argc) return false;
            args.max_frames = std::strtol(argv[++i], nullptr, 10);
        } else if (arg == "--screenshot") {
            if (i + 1 >= argc) return false;
            args.screenshot_file = argv[++i];
        } else if (arg == "--open") {
            if (i + 1 >= argc) return false;
            args.open_model = argv[++i];
        } else if (arg == "--parent-gate") {
            args.open_parent_gate = true;
        } else if (arg == "--inventory") {
            args.open_inventory = true;
        } else if (arg == "--smoke-inventory") {
            if (i + 1 >= argc) return false;
            args.smoke_inventory = argv[++i];
        } else if (arg == "--tts") {
            args.tts = true;
        } else if (arg == "--profile") {
            if (i + 1 >= argc) return false;
            args.profile = argv[++i];
        } else if (arg == "--db") {
            if (i + 1 >= argc) return false;
            args.db_file = argv[++i];
        } else {
            positional.push_back(arg);
        }
    }
    if (args.command == "catalog" || args.command == "library") return positional.empty();
    if (args.command == "validate" || args.command == "tutorial") {
        if (positional.size() != 1) return false;
        args.model_file = positional[0];
        return true;
    }
    if (args.command == "progress") {
        if (positional.empty()) return false;
        args.progress_action = positional[0];
        if (args.progress_action == "list") return positional.size() == 1;
        if (args.progress_action == "show" || args.progress_action == "reset") {
            if (positional.size() != 2) return false;
            args.model_id = positional[1];
            return true;
        }
        return false;
    }
    if (args.command == "inventory") {
        if (positional.empty()) return false;
        args.inventory_action = positional[0];
        if (args.inventory_action == "show" || args.inventory_action == "match") {
            return positional.size() == 1;
        }
        if (args.inventory_action == "set") {
            // set 之后是 <形状 数量> 对: 至少一对且必须成对出现
            if (positional.size() < 3 || (positional.size() - 1) % 2 != 0) return false;
            args.inventory_pairs.assign(positional.begin() + 1, positional.end());
            return true;
        }
        return false;
    }
    if (args.command == "settings") {
        if (positional.empty()) return false;
        args.settings_action = positional[0];
        if (args.settings_action == "show") return positional.size() == 1;
        if (args.settings_action == "set-age") {
            if (positional.size() != 2) return false;
            args.settings_value = positional[1];
            return true;
        }
        return false;
    }
    return false;
}

int runCatalog(const CliArgs& args) {
    const auto catalog = core::loadTileCatalog(args.data_dir / "tile_catalog.json");
    // --core-only: 只列核心 9 片型 (基础套装, tier=core), 供内容制作
    // 与免费层选品核对 (docs/TILE_CATALOG.md / CONTENT_STRATEGY.md §2.5)
    std::size_t core_count = 0;
    for (const auto& [type, shape] : catalog.shapes()) {
        (void)shape;
        if (core::isCoreTile(catalog, type)) ++core_count;
    }
    if (args.core_only) {
        std::printf("磁力片形状目录 (核心 9 片型, 共 %zu 种; 全目录 %zu 种):\n\n", core_count,
                    catalog.size());
    } else {
        std::printf("磁力片形状目录 (共 %zu 种, 其中核心 %zu 种):\n\n", catalog.size(),
                    core_count);
    }
    for (const auto& [type, shape] : catalog.shapes()) {
        if (args.core_only && !core::isCoreTile(catalog, type)) continue;
        std::printf("  %-22s %s [%s]%s  顶点 %zu 个, 磁力边 %zu 条, 面积 %.3f\n",
                    std::string(core::toString(type)).c_str(), shape.name_zh.c_str(),
                    shape.tier.c_str(), shape.hollow ? " (镂空)" : "",
                    shape.vertices.size(), shape.magnet_edge_indices.size(), shape.area());
        if (!shape.description_zh.empty()) {
            std::printf("      %s\n", shape.description_zh.c_str());
        }
    }
    return 0;
}

void printModelHeader(const core::ModelDefinition& model) {
    std::printf("模型: %s (%s)\n", model.name.c_str(), model.id.c_str());
    std::printf("难度: %d/5  磁力片: %d 片  步骤: %zu 步\n", model.difficulty,
                model.total_pieces, model.steps.size());
    std::printf("所需磁力片清单:\n");
    for (const auto& [type, count] : model.pieceCountByType()) {
        std::printf("  %s x %d\n", std::string(core::displayNameZh(type)).c_str(), count);
    }
    std::printf("\n");
}

int runValidate(const CliArgs& args) {
    // --profile: 物理校验参数档位。默认档按官方基准品牌实测标定;
    // strict (strict_consumer) 弱磁严格档按弱磁品牌/旧片标定, 供
    // "换个牌子的磁力片也搭得起来" 的余量校验 (docs/PHYSICS_RULES.md §5)。
    const auto profile_config = physics::configForProfile(args.profile);
    if (!profile_config.has_value()) {
        std::fprintf(stderr, "错误: 未知校验档位 \"%s\" (可用: default, strict)\n",
                     args.profile.c_str());
        return 2;
    }

    const auto catalog = core::loadTileCatalog(args.data_dir / "tile_catalog.json");
    const auto model = core::loadModelDefinition(args.model_file);
    printModelHeader(model);

    if (!args.profile.empty() && args.profile != "default" && args.profile != "standard") {
        std::printf(
            "校验档位: strict_consumer (弱磁严格档: 悬挂额定 %.0fg/单位边长, "
            "抗碰撞安全系数 %.0f%%)\n\n",
            profile_config->hanging_capacity_per_edge,
            profile_config->knock_safety_factor * 100.0);
    }

    int failures = 0;

    // 教程步骤一致性
    const auto step_problems = tutorial::TutorialEngine::checkConsistency(model);
    if (step_problems.empty()) {
        std::printf("[通过] 教程步骤一致性检查\n");
    } else {
        for (const auto& problem : step_problems) {
            std::printf("[错误] 步骤一致性: %s\n", problem.c_str());
            ++failures;
        }
    }

    // 物理规则 (最终成品 + 每一步中间状态)
    const physics::PhysicsValidator validator(catalog, *profile_config);
    const auto report = validator.validateModel(model);
    for (const auto& issue : report.issues) {
        const char* tag = issue.severity == physics::IssueSeverity::Error ? "错误" : "警告";
        std::printf("[%s] %s (%s)\n", tag, issue.message.c_str(), issue.code.c_str());
    }
    failures += static_cast<int>(report.errorCount());

    if (report.ok() && step_problems.empty()) {
        std::printf(
            "[通过] 物理规则检查: 接地支撑 / 磁力连接 / 无重叠 / 重心稳定 / "
            "悬挂承重 / 悬臂力矩 / 装配可达 / 结构冗余\n");

        // 补充统计信息, 方便内容制作人员核对
        std::vector<const core::TileInstance*> tiles;
        for (const auto& tile : model.final_assembly) tiles.push_back(&tile);
        const auto connections = validator.findConnections(tiles);
        std::printf("\n统计: 磁力连接 %zu 处, 校验含最终成品与 %zu 个中间步骤\n",
                    connections.size(), model.steps.size());

        // 高难模型: 自动校验之外强烈建议实物复核 (人手感知的失效模式
        // 无法完全仿真, 见 docs/PHYSICS_RULES.md "人工复核工作流")
        if (model.difficulty >= 4) {
            std::printf(
                "\n[提示] 本模型难度 %d/5: 自动校验通过不等于实搭万无一失, "
                "发布前请按 docs/PHYSICS_RULES.md 的\"人工复核工作流\"完成实物复核\n",
                model.difficulty);
        }
        std::printf("\n结论: 模型 %s 可发布\n", model.id.c_str());
        return 0;
    }

    std::printf("\n结论: 模型 %s 未通过质检 (%d 个错误, %zu 个警告)\n", model.id.c_str(),
                failures, report.warningCount());
    return 1;
}

// ---- 进度存档 (progress list / show / reset) ---------------------

/// 平台默认存档路径 (docs/PLATFORM_ARCHITECTURE.md §5.1)。
/// 路径由平台外壳注入是核心库的铁律, CLI 即桌面外壳, 在此落实;
/// 测试与多存档场景用 --db 覆盖。
fs::path defaultProgressDbPath() {
#if defined(_WIN32)
    if (const char* appdata = std::getenv("APPDATA"); appdata != nullptr && *appdata != '\0') {
        return fs::path(appdata) / "MagTile" / "progress.db";
    }
#elif defined(__APPLE__)
    if (const char* home = std::getenv("HOME"); home != nullptr && *home != '\0') {
        return fs::path(home) / "Library" / "Application Support" / "MagTile" / "progress.db";
    }
#else
    if (const char* xdg = std::getenv("XDG_DATA_HOME"); xdg != nullptr && *xdg != '\0') {
        return fs::path(xdg) / "magtile" / "progress.db";
    }
    if (const char* home = std::getenv("HOME"); home != nullptr && *home != '\0') {
        return fs::path(home) / ".local" / "share" / "magtile" / "progress.db";
    }
#endif
    return fs::path("magtile_progress.db");  // 兜底: 当前目录
}

std::string formatTimestamp(std::int64_t unix_seconds) {
    if (unix_seconds <= 0) return "-";
    const std::time_t time = static_cast<std::time_t>(unix_seconds);
    std::tm tm_buffer{};
#if defined(_WIN32)
    localtime_s(&tm_buffer, &time);
#else
    localtime_r(&time, &tm_buffer);
#endif
    char text[32];
    std::strftime(text, sizeof(text), "%Y-%m-%d %H:%M", &tm_buffer);
    return text;
}

std::string formatPlaySeconds(std::int64_t seconds) {
    if (seconds < 60) return std::to_string(seconds) + " 秒";
    if (seconds < 3600) return std::to_string(seconds / 60) + " 分钟";
    return std::to_string(seconds / 3600) + " 小时 " + std::to_string(seconds % 3600 / 60) + " 分";
}

void printProgressLine(const progress::Progress& record) {
    std::printf("  %s %-28s 第 %d 步  累计 %s  最近 %s\n",
                record.favorited ? "★" : " ", record.model_id.c_str(), record.current_step,
                formatPlaySeconds(record.play_seconds).c_str(),
                formatTimestamp(record.updated_at).c_str());
}

int runProgress(const CliArgs& args) {
    const fs::path db_file = args.db_file.empty() ? defaultProgressDbPath() : args.db_file;
    progress::ProgressStore store(db_file);

    if (args.progress_action == "list") {
        std::printf("进度存档: %s\n\n", db_file.string().c_str());

        const auto in_progress = store.listInProgress();
        std::printf("进行中 (%zu 个):\n", in_progress.size());
        if (in_progress.empty()) std::printf("  (暂无)\n");
        for (const auto& record : in_progress) printProgressLine(record);

        const auto completed = store.listCompleted();
        std::printf("\n已完成 (%zu 个):\n", completed.size());
        if (completed.empty()) std::printf("  (暂无)\n");
        for (const auto& record : completed) {
            std::printf("  %s %-28s 完成于 %s  累计 %s\n", record.favorited ? "★" : " ",
                        record.model_id.c_str(), formatTimestamp(record.completed_at).c_str(),
                        formatPlaySeconds(record.play_seconds).c_str());
        }

        const auto achievements = store.listAchievements();
        std::printf("\n已解锁成就 (%zu 个):\n", achievements.size());
        if (achievements.empty()) std::printf("  (暂无)\n");
        for (const auto& achievement : achievements) {
            std::printf("  %-30s 解锁于 %s\n", achievement.id.c_str(),
                        formatTimestamp(achievement.unlocked_at).c_str());
        }
        return 0;
    }

    if (args.progress_action == "show") {
        const auto record = store.loadProgress(args.model_id);
        if (!record.has_value()) {
            std::printf("模型 %s 暂无进度记录\n", args.model_id.c_str());
            return 1;
        }
        std::printf("模型: %s\n", record->model_id.c_str());
        if (record->isCompleted()) {
            std::printf("状态: 已完成 (%s)\n", formatTimestamp(record->completed_at).c_str());
        } else {
            std::printf("状态: 进行中, 已完成到第 %d 步\n", record->current_step);
        }
        std::printf("收藏: %s\n", record->favorited ? "是" : "否");
        std::printf("累计游玩: %s\n", formatPlaySeconds(record->play_seconds).c_str());
        std::printf("最近游玩: %s\n", formatTimestamp(record->updated_at).c_str());
        return 0;
    }

    // reset: 幂等操作, 无记录也算成功
    if (store.resetProgress(args.model_id)) {
        std::printf("已重置模型 %s 的进度\n", args.model_id.c_str());
    } else {
        std::printf("模型 %s 暂无进度记录, 无需重置\n", args.model_id.c_str());
    }
    return 0;
}

// ---- 磁力片库存 (inventory set / show / match) --------------------

/// 按形状目录的固定顺序打印库存清单 (只列已登记的形状) 与总片数。
void printInventory(const std::map<std::string, int>& inventory) {
    int total = 0;
    std::printf("磁力片库存 (%zu 种形状):\n", inventory.size());
    // 按 TileType 枚举顺序输出, 与 catalog 命令的形状目录一致
    for (int i = 0; i < core::kTileTypeCount; ++i) {
        const auto type = static_cast<core::TileType>(i);
        const auto it = inventory.find(std::string(core::toString(type)));
        if (it == inventory.end()) continue;
        std::printf("  %-22s %-8s x %d\n", it->first.c_str(),
                    std::string(core::displayNameZh(type)).c_str(), it->second);
        total += it->second;
    }
    std::printf("合计: %d 片\n", total);
}

/// 缺片清单的单行摘要, 如 "正方形x4, 六边形x2"。
std::string formatMissing(const std::map<core::TileType, int>& missing) {
    std::string text;
    for (const auto& [type, count] : missing) {
        if (!text.empty()) text += ", ";
        text += std::string(core::displayNameZh(type)) + "x" + std::to_string(count);
    }
    return text;
}

/// inventory match: 对照库存与每个模型的 BOM, 列出能搭建的模型;
/// 差片的模型按缺片总数升序列出 (最接近能搭的排前面)。
int runInventoryMatch(const CliArgs& args, progress::ProgressStore& store) {
    if (!store.hasInventory()) {
        std::printf("尚未登记磁力片库存, 无法匹配。\n");
        std::printf("先登记: magtile_app inventory set square 40 equilateral_triangle 24 ...\n");
        return 1;
    }
    const auto entries = core::loadModelCatalog(args.data_dir);

    struct MatchResult {
        const core::ModelCatalogEntry* entry = nullptr;
        std::map<core::TileType, int> missing;
        int missing_total = 0;
    };
    std::vector<MatchResult> buildable, short_of;
    int load_failures = 0;
    for (const auto& entry : entries) {
        try {
            const auto model = core::loadModelDefinition(entry.file);
            MatchResult result;
            result.entry = &entry;
            result.missing = store.missingPieces(model);
            for (const auto& [type, count] : result.missing) {
                (void)type;
                result.missing_total += count;
            }
            (result.missing.empty() ? buildable : short_of).push_back(std::move(result));
        } catch (const std::exception& e) {
            std::fprintf(stderr, "[警告] 跳过模型 %s: %s\n", entry.id.c_str(), e.what());
            ++load_failures;
        }
    }
    std::sort(short_of.begin(), short_of.end(),
              [](const MatchResult& a, const MatchResult& b) {
                  if (a.missing_total != b.missing_total) {
                      return a.missing_total < b.missing_total;
                  }
                  return a.entry->id < b.entry->id;
              });

    std::printf("库存匹配: 共 %zu 个模型, 能搭 %zu 个\n\n", entries.size(), buildable.size());
    std::printf("能搭的模型 (%zu 个):\n", buildable.size());
    if (buildable.empty()) std::printf("  (暂无 —— 从下面缺片最少的模型补起最划算)\n");
    for (const auto& result : buildable) {
        std::string stars;
        for (int i = 1; i <= result.entry->difficulty; ++i) stars += "★";
        std::printf("  ✓ %-24s %s  难度 %s  %d 片 / %d 步\n", result.entry->id.c_str(),
                    result.entry->name.c_str(), stars.c_str(), result.entry->total_pieces,
                    result.entry->step_count);
    }

    if (!short_of.empty()) {
        std::printf("\n还差一点的模型 (%zu 个, 按缺片数升序):\n", short_of.size());
        for (const auto& result : short_of) {
            std::printf("  · %-24s %s  还缺 %d 片: %s\n", result.entry->id.c_str(),
                        result.entry->name.c_str(), result.missing_total,
                        formatMissing(result.missing).c_str());
        }
    }
    return load_failures > 0 ? 1 : 0;
}

int runInventory(const CliArgs& args) {
    const fs::path db_file = args.db_file.empty() ? defaultProgressDbPath() : args.db_file;
    progress::ProgressStore store(db_file);

    if (args.inventory_action == "match") return runInventoryMatch(args, store);

    if (args.inventory_action == "set") {
        for (std::size_t i = 0; i + 1 < args.inventory_pairs.size(); i += 2) {
            const std::string& shape_id = args.inventory_pairs[i];
            const std::string& count_text = args.inventory_pairs[i + 1];
            char* end = nullptr;
            const long count = std::strtol(count_text.c_str(), &end, 10);
            if (end == count_text.c_str() || *end != '\0' || count < 0 || count > 100000) {
                std::fprintf(stderr, "错误: \"%s\" 不是合法的磁力片数量 (非负整数)\n",
                             count_text.c_str());
                return 1;
            }
            store.setInventory(shape_id, static_cast<int>(count));  // 形状标识由存储层校验
        }
        std::printf("已登记 %zu 种形状的库存\n\n", args.inventory_pairs.size() / 2);
    }

    // set 与 show 都以当前库存收尾, 方便立即核对
    const auto inventory = store.getInventory();
    if (inventory.empty()) {
        std::printf("尚未登记磁力片库存。\n");
        std::printf("用法: magtile_app inventory set square 40 equilateral_triangle 24 ...\n");
        std::printf("      (形状标识见 magtile_app catalog)\n");
        return 0;
    }
    printInventory(inventory);
    if (args.inventory_action == "show") {
        std::printf("\n提示: magtile_app inventory match 可对照库存列出能搭建的模型\n");
    }
    return 0;
}

// ---- 设置 (settings set-age / show) --------------------------------

/// settings 命令: 年龄段模式切换与设置总览 (UI_UX_SPEC.md §2 / §8)。
/// 正式产品中年龄段切换位于家长门之后的家长区; CLI 是桌面外壳的
/// 内容制作与评审入口, 不做门禁。
int runSettings(const CliArgs& args) {
    const fs::path db_file = args.db_file.empty() ? defaultProgressDbPath() : args.db_file;
    progress::ProgressStore store(db_file);

    if (args.settings_action == "set-age") {
        char* end = nullptr;
        const long age_years = std::strtol(args.settings_value.c_str(), &end, 10);
        const auto mode = (end != args.settings_value.c_str() && *end == '\0')
                              ? core::ageModeFromAgeYears(static_cast<int>(age_years))
                              : std::nullopt;
        if (!mode.has_value()) {
            std::fprintf(stderr,
                         "错误: \"%s\" 不在适龄范围 (4~12 周岁)。示例: settings set-age 4\n",
                         args.settings_value.c_str());
            return 2;
        }
        progress::setAgeMode(store, *mode);
        std::printf("年龄段模式已切换: %s\n", std::string(core::displayNameZh(*mode)).c_str());
        return 0;
    }

    // show: 设置总览 (年龄段 + TTS 后端探测结果)
    const auto tts_engine = tts::createSystemTts();
    std::printf("设置 (%s):\n", db_file.string().c_str());
    std::printf("  年龄段模式: %s\n",
                std::string(core::displayNameZh(progress::getAgeMode(store))).c_str());
    std::printf("  TTS 朗读后端: %s%s\n", std::string(tts_engine->name()).c_str(),
                tts_engine->available() ? "" : " (本机无可用朗读器, 已静音降级)");
    return 0;
}

#if defined(MAGTILE_HAS_GL_RENDERER)

/// 初始取景: 最终成品的包围盒。
void frameModelBounds(render::IWindowRenderer& renderer, const core::TileCatalog& catalog,
                      const core::ModelDefinition& model) {
    core::Vec3 bb_min{1e9, 1e9, 1e9}, bb_max{-1e9, -1e9, -1e9};
    for (const auto& tile : model.final_assembly) {
        const auto world = physics::transformTile(tile, catalog.get(tile.type));
        for (const auto& v : world.vertices) {
            bb_min = {std::min(bb_min.x, v.x), std::min(bb_min.y, v.y), std::min(bb_min.z, v.z)};
            bb_max = {std::max(bb_max.x, v.x), std::max(bb_max.y, v.y), std::max(bb_max.z, v.z)};
        }
    }
    renderer.orbitCamera().frameBounds(bb_min, bb_max);
}

/// 教程会话的结束原因。
enum class TutorialExit {
    WindowClosed,   ///< 用户关闭窗口 / Esc
    BackToLibrary,  ///< 点击 "返回模型库" (仅库内会话)
    FrameBudget,    ///< --frames 帧预算耗尽 (冒烟测试)
};

/// 在已初始化的窗口中运行一次交互式教程会话。
///
/// store 非空时把进度写入存档: 每次步骤变化落盘当前步骤与游玩时长
/// 增量, 走到最后一步即记完成 (并解锁首个模型完成成就)。
/// tts 非空时进入/切换步骤即朗读步骤说明 (speak 内部先停旧朗读,
/// 保证无叠音, UI_UX_SPEC.md §4.2); 会话结束停止朗读。
/// frame_index 与调用方共享 --frames 帧预算 (模型库 + 教程连续计数)。
TutorialExit runTutorialSession(render::IWindowRenderer& renderer,
                                const core::TileCatalog& catalog,
                                tutorial::TutorialEngine& engine,
                                progress::ProgressStore* store, tts::ITtsEngine* tts,
                                bool from_library, const CliArgs& args, long& frame_index) {
    using Clock = std::chrono::steady_clock;
    Clock::time_point last_flush_time = Clock::now();
    int last_saved_step = engine.currentStepNumber();

    // 进度落盘: 写入当前步骤与自上次落盘以来的游玩秒数
    const auto flushProgress = [&](int step) {
        if (store == nullptr) return;
        const Clock::time_point now = Clock::now();
        const auto seconds =
            std::chrono::duration_cast<std::chrono::seconds>(now - last_flush_time).count();
        store->saveProgress(engine.model().id, step, seconds);
        last_flush_time = now;
        last_saved_step = step;
    };
    // 会话开始即建档, 模型库立刻能显示 "进行中"
    flushProgress(last_saved_step);

    // TTS: 朗读当前步骤说明; 会话结束时停止 (离开教程不能还在说话)
    const auto speakCurrentStep = [&]() {
        if (tts == nullptr) return;
        if (const core::BuildStep* step = engine.currentStep(); step != nullptr) {
            tts->speak(step->description);
        } else {
            tts->stop();  // 第 0 步 (未开始) 无步骤说明
        }
    };
    const auto stopSpeaking = [&]() {
        if (tts != nullptr) tts->stop();
    };
    int last_spoken_step = engine.currentStepNumber();
    speakCurrentStep();  // 进入教程即朗读恢复到的步骤

    while (!renderer.shouldClose()) {
        renderer.pollEvents();
        render::TutorialActions actions = renderer.consumeActions();

        // 本帧场景状态 (模型规模为数百片, 每帧重建集合开销可忽略)
        std::unordered_set<const core::TileInstance*> placed, added, referenced;
        for (const auto* tile : engine.visibleTiles()) placed.insert(tile);
        for (const auto* tile : engine.tilesAddedThisStep()) added.insert(tile);
        for (const auto* tile : engine.highlightTiles()) referenced.insert(tile);

        renderer.beginFrame(renderer.orbitCamera().toCamera());
        for (const auto& tile : engine.model().final_assembly) {
            render::RenderTile rt;
            rt.instance = &tile;
            rt.just_placed = added.count(&tile) > 0;
            rt.ghost = !rt.just_placed && placed.count(&tile) == 0;
            rt.highlighted = referenced.count(&tile) > 0;
            renderer.submitTile(rt, catalog.get(tile.type));
        }

        render::TutorialHudState hud;
        hud.model_name = engine.model().name;
        hud.step_number = engine.currentStepNumber();
        hud.step_count = engine.stepCount();
        hud.progress = engine.progress();
        hud.tiles_placed = static_cast<int>(placed.size());
        hud.tiles_total = static_cast<int>(engine.model().final_assembly.size());
        hud.show_back_button = from_library;
        if (const core::BuildStep* step = engine.currentStep(); step != nullptr) {
            hud.description = step->description;
            hud.tip = step->tip;
        } else {
            hud.description = "转动视角熟悉最终成品, 点击 [下一步] 开始搭建。";
        }
        actions |= renderer.submitHud(hud);

        const bool last_frame = args.max_frames > 0 && frame_index + 1 >= args.max_frames;
        if (last_frame && !args.screenshot_file.empty()) {
            renderer.requestScreenshot(args.screenshot_file);
        }
        renderer.endFrame();

        // 帧末统一应用导航操作, 下一帧生效
        if (actions.reset) {
            engine.reset();
        } else if (actions.next_step) {
            engine.nextStep();
        } else if (actions.previous_step) {
            engine.previousStep();
        }

        // 步骤变化 -> 朗读新步骤 (与进度落盘解耦: 无存档的直开教程也要朗读)
        if (engine.currentStepNumber() != last_spoken_step) {
            last_spoken_step = engine.currentStepNumber();
            speakCurrentStep();
        }

        // 步骤变化 -> 进度落盘; 走到最后一步 -> 记完成 + 首次完成成就
        if (store != nullptr && engine.currentStepNumber() != last_saved_step) {
            flushProgress(engine.currentStepNumber());
            if (engine.stepCount() > 0 && engine.currentStepNumber() >= engine.stepCount()) {
                store->markCompleted(engine.model().id);
                if (!store->isAchievementUnlocked("first_model_completed")) {
                    store->unlockAchievement("first_model_completed");
                }
            }
        }

        ++frame_index;
        if (actions.back_to_library && from_library) {
            flushProgress(engine.currentStepNumber());
            stopSpeaking();
            return TutorialExit::BackToLibrary;
        }
        if (last_frame) {
            flushProgress(engine.currentStepNumber());
            stopSpeaking();
            return TutorialExit::FrameBudget;
        }
    }

    flushProgress(engine.currentStepNumber());
    stopSpeaking();
    return TutorialExit::WindowClosed;
}

/// 图形模式: 在 3D 窗口中交互式跟随分步教程 (单模型直开, 内容工具用)。
int runTutorialGui(const CliArgs& args) {
    const auto catalog = core::loadTileCatalog(args.data_dir / "tile_catalog.json");
    auto model = core::loadModelDefinition(args.model_file);
    printModelHeader(model);

    // 内容有问题的模型直接拒绝进入图形教程
    const auto problems = tutorial::TutorialEngine::checkConsistency(model);
    if (!problems.empty()) {
        for (const auto& problem : problems) {
            std::fprintf(stderr, "[错误] 步骤一致性: %s\n", problem.c_str());
        }
        return 1;
    }

    tutorial::TutorialEngine engine(std::move(model));
    // 打开窗口即进入起始步骤 (缺省第 1 步)
    if (!engine.goToStep(args.start_step)) engine.nextStep();

    auto renderer = render::createOpenGLRenderer();
    if (!renderer->initialize(1440, 900, "MagTile Studio - " + engine.model().name)) {
        std::fprintf(stderr, "错误: 无法创建图形窗口 (需要支持 OpenGL 4.1 的显示环境)\n");
        return 1;
    }
    frameModelBounds(*renderer, catalog, engine.model());

    // --tts: 切步朗读步骤说明 (直开教程无存档, 只认显式开关)
    std::unique_ptr<tts::ITtsEngine> tts_engine;
    if (args.tts) {
        tts_engine = tts::createSystemTts();
        std::printf("[tts] 朗读后端: %s%s\n", std::string(tts_engine->name()).c_str(),
                    tts_engine->available() ? "" : " (无可用朗读器, 静音降级)");
    }

    long frame_index = 0;
    runTutorialSession(*renderer, catalog, engine, /*store=*/nullptr, tts_engine.get(),
                       /*from_library=*/false, args, frame_index);
    renderer->shutdown();
    return 0;
}

/// 商业版主界面: 模型库 (卡片网格 / 搜索筛选 / 继续搭建), 点击卡片
/// 在同一窗口进入 3D 教程, 返回后回到模型库; 进度实时写入存档。
int runLibraryGui(const CliArgs& args) {
    const auto catalog = core::loadTileCatalog(args.data_dir / "tile_catalog.json");
    const auto entries = core::loadModelCatalog(args.data_dir);
    if (entries.empty()) {
        std::fprintf(stderr, "错误: 模型库为空 (data/model_catalog.json 与 data/models/ 均无模型)\n");
        return 1;
    }
    const fs::path db_file = args.db_file.empty() ? defaultProgressDbPath() : args.db_file;
    progress::ProgressStore store(db_file);

    // 年龄段模式 (家长在设置中选择, UI_UX_SPEC.md §2):
    //   - 4-6 岁启蒙模式: 模型库切超大卡片简化布局 + 教程自动朗读;
    //   - 其余档位: 标准布局, 朗读只认显式 --tts。
    const core::AgeMode age_mode = progress::getAgeMode(store);
    const bool simple_layout = age_mode == core::AgeMode::Age4_6;
    std::unique_ptr<tts::ITtsEngine> tts_engine;
    if (args.tts || age_mode == core::AgeMode::Age4_6) {
        tts_engine = tts::createSystemTts();
        std::printf("[tts] 朗读后端: %s%s\n", std::string(tts_engine->name()).c_str(),
                    tts_engine->available() ? "" : " (无可用朗读器, 静音降级)");
    }

    // ---- 片型分层: "只用核心 9 片" 筛选与 "需要扩展装" 角标 -------------
    // 启动时逐模型加载 BOM, 对照片型目录 tier 判定是否只用核心 9 片型
    // (与 Qt 版同一共享判定 core::isCoreTile); 模型文件有问题的按
    // "BOM 未知" 降级 (不进核心筛选也不显示角标), 不影响其余卡片。
    std::unordered_map<std::string, bool> core9_by_id;  // 无条目 = BOM 未知
    for (const auto& entry : entries) {
        try {
            const auto model = core::loadModelDefinition(entry.file);
            bool core9 = true;
            for (const auto& [type, count] : model.pieceCountByType()) {
                (void)count;
                if (!core::isCoreTile(catalog, type)) {
                    core9 = false;
                    break;
                }
            }
            core9_by_id.emplace(entry.id, core9);
        } catch (const std::exception&) {
            // 模型文件有问题由目录对账用例负责报告, 这里按 BOM 未知处理
        }
    }

    // ---- 磁力片库存: "我能搭的" 筛选 + 首启 onboarding -----------------
    // 已登记库存时对照每个模型的 BOM 预判 "能不能搭"; 库存经图形录入
    // 界面保存后就地重算 (模型 JSON 重新加载, 数百个模型量级毫秒完成)。
    bool inventory_configured = store.hasInventory();
    std::unordered_set<std::string> buildable_ids;
    const auto recomputeBuildable = [&]() {
        buildable_ids.clear();
        if (!inventory_configured) return;
        for (const auto& entry : entries) {
            try {
                if (store.canBuild(core::loadModelDefinition(entry.file))) {
                    buildable_ids.insert(entry.id);
                }
            } catch (const std::exception&) {
                // 模型文件有问题由目录对账用例负责报告, 这里按不可搭处理
            }
        }
    };
    recomputeBuildable();
    // 首启 onboarding: 从未登记库存且没看过提示时弹出, 主按钮直达图形
    // 录入界面; "稍后再说" 记入存档后不再打扰 (UI_UX_SPEC.md §10
    // 跳过永远可见, 录库存不是付费墙)。
    bool show_inventory_onboarding =
        !inventory_configured && !store.getSetting("inventory_onboarding_done").has_value();

    // ---- 库存录入界面 (UI_UX_SPEC.md §10.2) 的编辑状态 ------------------
    // rows 是编辑中的临时副本 (进入界面时从存档快照), 保存才落盘;
    // "返回" 直接丢弃, 与存档零交互。
    std::vector<render::InventoryEditorRow> inventory_rows;
    const auto openInventoryEditor = [&]() {
        inventory_rows.clear();
        const auto saved = store.getInventory();
        for (const auto& [type, shape] : catalog.shapes()) {
            render::InventoryEditorRow row;
            row.shape_id = std::string(core::toString(type));
            row.name_zh = shape.name_zh;
            row.expansion = shape.tier != "core";
            if (const auto it = saved.find(row.shape_id); it != saved.end()) {
                row.count = it->second;
            }
            inventory_rows.push_back(std::move(row));
        }
    };
    const auto saveInventoryRows = [&]() {
        for (const auto& row : inventory_rows) {
            store.setInventory(row.shape_id, row.count);
        }
        // 保存即完成 onboarding (含 count 全 0 的 "明确没有")
        store.setSetting("inventory_onboarding_done", "1");
        show_inventory_onboarding = false;
        inventory_configured = store.hasInventory();
        recomputeBuildable();
    };

    // --smoke-inventory "square=40,rectangle=8": CI 冒烟自动驾驶,
    // 模拟用户在图形录入界面修改数量并点击 "保存, 看看我能搭什么"
    // (走与真实点击完全相同的 action -> 保存 -> 重算筛选管线)。
    std::vector<std::pair<std::string, int>> smoke_inventory_pairs;
    if (!args.smoke_inventory.empty()) {
        const std::string& spec = args.smoke_inventory;
        std::size_t pos = 0;
        while (pos < spec.size()) {
            const std::size_t comma = spec.find(',', pos);
            const std::string token =
                spec.substr(pos, comma == std::string::npos ? std::string::npos : comma - pos);
            pos = comma == std::string::npos ? spec.size() : comma + 1;
            const std::size_t eq = token.find('=');
            char* end = nullptr;
            const long count =
                eq == std::string::npos ? -1 : std::strtol(token.c_str() + eq + 1, &end, 10);
            if (eq == 0 || eq == std::string::npos || end == token.c_str() + eq + 1 ||
                *end != '\0' || count < 0) {
                std::fprintf(stderr,
                             "错误: --smoke-inventory 片段 \"%s\" 不是 形状=数量 格式\n",
                             token.c_str());
                return 2;
            }
            smoke_inventory_pairs.emplace_back(token.substr(0, eq), static_cast<int>(count));
        }
    }
    int smoke_inventory_stage = 0;  // 0 = 注入修改, 1 = 注入保存, >=2 = 完成

    auto renderer = render::createOpenGLRenderer();
    if (!renderer->initialize(1440, 900, "MagTile Studio - 模型库")) {
        std::fprintf(stderr, "错误: 无法创建图形窗口 (需要支持 OpenGL 4.1 的显示环境)\n");
        return 1;
    }

    // --open <model_id>: 启动即进入指定模型 (深链 / 冒烟测试)
    std::string pending_open = args.open_model;

    // 家长门: 订阅/设置 (家长区) 前置强制关卡 (UI_UX_SPEC.md §9)。
    // 会话与冷却只存内存, 重启即失效, 不落盘 "已通过" 标记
    // (SECURITY_AND_PRIVACY.md §6.2)。
    enum class LibraryScreen { Cards, ParentGate, ParentArea, Inventory };
    // --parent-gate: 启动即显示家长门 (构造时已生成一道新题);
    // --inventory / --smoke-inventory: 启动即打开库存录入界面
    LibraryScreen screen =
        args.open_parent_gate ? LibraryScreen::ParentGate : LibraryScreen::Cards;
    if (args.open_inventory || !smoke_inventory_pairs.empty()) {
        openInventoryEditor();
        screen = LibraryScreen::Inventory;
    }
    core::ParentGate parent_gate;
    bool gate_wrong_answer = false;  // 上次提交答错, 用于门界面温和提示
    bool activate_buildable_filter = false;  // 一次性: "保存并匹配" 跳转帧开启筛选

    long frame_index = 0;
    while (!renderer->shouldClose()) {
        // ---- 教程会话: 有待打开的模型则切换到教程界面 -----------------
        if (!pending_open.empty()) {
            const std::string open_id = std::exchange(pending_open, std::string{});
            const auto entry_it = std::find_if(
                entries.begin(), entries.end(),
                [&](const core::ModelCatalogEntry& e) { return e.id == open_id; });
            if (entry_it == entries.end()) {
                std::fprintf(stderr, "[library] 未找到模型: %s\n", open_id.c_str());
                continue;
            }
            try {
                auto model = core::loadModelDefinition(entry_it->file);
                const auto problems = tutorial::TutorialEngine::checkConsistency(model);
                if (!problems.empty()) {
                    for (const auto& problem : problems) {
                        std::fprintf(stderr, "[错误] 步骤一致性: %s\n", problem.c_str());
                    }
                    continue;
                }
                tutorial::TutorialEngine engine(std::move(model));
                // 断点续搭: 从存档步骤继续; 已完成或无进度则从第 1 步开始
                int resume_step = 1;
                if (const auto record = store.loadProgress(open_id);
                    record.has_value() && !record->isCompleted()) {
                    resume_step = std::max(record->current_step, 1);
                }
                if (!engine.goToStep(resume_step)) engine.nextStep();
                frameModelBounds(*renderer, catalog, engine.model());

                const TutorialExit exit_reason = runTutorialSession(
                    *renderer, catalog, engine, &store, tts_engine.get(),
                    /*from_library=*/true, args, frame_index);
                if (exit_reason == TutorialExit::FrameBudget) break;
                // WindowClosed 由外层循环条件收尾; BackToLibrary 继续渲染库界面
            } catch (const std::exception& e) {
                std::fprintf(stderr, "[library] 打开模型失败: %s\n", e.what());
            }
            continue;
        }

        // ---- 模型库 / 家长门 / 家长区界面帧 -----------------------------
        renderer->pollEvents();
        (void)renderer->consumeActions();  // 库界面不使用教程键盘导航

        render::LibraryActions library_actions;
        render::InventoryOnboardingActions onboarding_actions;
        render::InventoryEditorActions inventory_actions;
        render::ParentGateActions gate_actions;
        render::ParentAreaActions area_actions;

        renderer->beginFrame(render::Camera{});  // 默认视角的空场景网格作背景
        if (screen == LibraryScreen::Cards) {
            std::vector<render::LibraryCard> cards;
            cards.reserve(entries.size());
            for (const auto& entry : entries) {
                render::LibraryCard card;
                card.model_id = entry.id;
                card.name = entry.name;
                card.name_en = entry.name_en;
                card.description = entry.description;
                card.difficulty = entry.difficulty;
                card.total_pieces = entry.total_pieces;
                card.step_count = entry.step_count;
                card.theme = entry.theme();
                card.tags = entry.tags;
                if (!entry.thumbnail.empty()) card.thumbnail_path = entry.thumbnail.string();
                if (const auto it = core9_by_id.find(entry.id); it != core9_by_id.end()) {
                    card.bom_known = true;
                    card.core9_only = it->second;
                }
                card.buildable = buildable_ids.count(entry.id) > 0;
                if (const auto record = store.loadProgress(entry.id); record.has_value()) {
                    card.completed = record->isCompleted();
                    // 收藏也会建档, "进行中" 只认真正搭过的 (步骤 > 0)
                    card.started = !card.completed && record->current_step > 0;
                    card.favorited = record->favorited;
                    card.current_step = record->current_step;
                }
                cards.push_back(std::move(card));
            }
            library_actions = renderer->submitLibrary(cards, simple_layout,
                                                      inventory_configured,
                                                      activate_buildable_filter);
            activate_buildable_filter = false;  // 一次性触发, 用过即清
            if (show_inventory_onboarding) {
                // onboarding 弹窗盖在模型库之上; 弹窗期间吞掉库界面操作
                onboarding_actions = renderer->submitInventoryOnboarding();
                library_actions = {};
            }
        } else if (screen == LibraryScreen::Inventory) {
            inventory_actions = renderer->submitInventoryEditor(inventory_rows);
            // 冒烟自动驾驶: 第 1 帧注入数量修改, 第 2 帧注入保存并匹配
            if (!smoke_inventory_pairs.empty() && smoke_inventory_stage <= 1) {
                if (smoke_inventory_stage == 0) {
                    inventory_actions.count_changes = smoke_inventory_pairs;
                } else {
                    inventory_actions.save_and_match = true;
                }
                ++smoke_inventory_stage;
            }
        } else if (screen == LibraryScreen::ParentGate) {
            render::ParentGateState gate_state;
            gate_state.question = parent_gate.question();
            gate_state.attempts_remaining = parent_gate.attemptsRemaining();
            gate_state.cooldown_seconds = parent_gate.cooldownRemainingSeconds();
            gate_state.wrong_answer = gate_wrong_answer;
            gate_actions = renderer->submitParentGate(gate_state);
        } else {
            area_actions = renderer->submitParentArea(parent_gate.sessionRemainingSeconds());
        }
        const bool last_frame = args.max_frames > 0 && frame_index + 1 >= args.max_frames;
        if (last_frame && !args.screenshot_file.empty()) {
            renderer->requestScreenshot(args.screenshot_file);
        }
        renderer->endFrame();
        ++frame_index;

        // ---- 帧末统一应用界面操作 --------------------------------------
        if (screen == LibraryScreen::Cards) {
            if (onboarding_actions.start_entry) {
                // 进入图形录入界面; 是否落盘 "已看过" 由保存动作决定
                // (中途返回的话下次启动还会温和提醒一次)
                show_inventory_onboarding = false;
                openInventoryEditor();
                screen = LibraryScreen::Inventory;
            }
            if (onboarding_actions.dismissed) {
                // 记入存档: 之后启动不再弹出 (录入入口常驻模型库页眉)
                store.setSetting("inventory_onboarding_done", "1");
                show_inventory_onboarding = false;
            }
            if (!library_actions.toggle_favorite_id.empty()) {
                store.toggleFavorite(library_actions.toggle_favorite_id);
            }
            if (!library_actions.open_model_id.empty()) {
                pending_open = library_actions.open_model_id;
            }
            if (library_actions.open_inventory) {
                openInventoryEditor();
                screen = LibraryScreen::Inventory;
            }
            if (library_actions.open_parent_area) {
                if (parent_gate.sessionActive()) {
                    screen = LibraryScreen::ParentArea;  // 15 分钟会话内免重复验证
                } else {
                    parent_gate.newChallenge();  // 每次进门都是新题, 防背题
                    gate_wrong_answer = false;
                    screen = LibraryScreen::ParentGate;
                }
            }
        } else if (screen == LibraryScreen::Inventory) {
            // 数量修改先落到编辑副本 (步进器与直接输入同一路径)
            for (const auto& [shape_id, count] : inventory_actions.count_changes) {
                for (auto& row : inventory_rows) {
                    if (row.shape_id == shape_id) {
                        row.count = count;
                        break;
                    }
                }
            }
            if (inventory_actions.save || inventory_actions.save_and_match) {
                saveInventoryRows();
                if (inventory_actions.save_and_match) activate_buildable_filter = true;
                screen = LibraryScreen::Cards;
            } else if (inventory_actions.back) {
                screen = LibraryScreen::Cards;  // 放弃编辑副本
            }
        } else if (screen == LibraryScreen::ParentGate) {
            if (gate_actions.submitted) {
                switch (parent_gate.submitAnswer(gate_actions.answer)) {
                    case core::ParentGateResult::Passed:
                        gate_wrong_answer = false;
                        screen = LibraryScreen::ParentArea;
                        break;
                    case core::ParentGateResult::WrongAnswer:
                        gate_wrong_answer = true;
                        break;
                    case core::ParentGateResult::CoolingDown:
                        gate_wrong_answer = false;  // 冷却界面自带温和提示
                        break;
                }
            }
            if (gate_actions.dismissed) {
                gate_wrong_answer = false;
                screen = LibraryScreen::Cards;
            }
        } else {
            if (area_actions.lock_now) parent_gate.endSession();
            if (area_actions.lock_now || area_actions.back_to_library) {
                screen = LibraryScreen::Cards;
            }
        }
        if (last_frame) break;
    }

    renderer->shutdown();
    return 0;
}

#else

int runTutorialGui(const CliArgs& /*args*/) {
    std::fprintf(stderr,
                 "错误: 本构建未包含图形渲染后端。\n"
                 "请以 -DMAGTILE_BUILD_GL_RENDERER=ON 重新构建 (默认开启)。\n");
    return 2;
}

int runLibraryGui(const CliArgs& /*args*/) {
    std::fprintf(stderr,
                 "错误: 本构建未包含图形渲染后端, 无法打开模型库界面。\n"
                 "请以 -DMAGTILE_BUILD_GL_RENDERER=ON 重新构建 (默认开启), "
                 "或不带 --gui 在终端查看模型库。\n");
    return 2;
}

#endif  // MAGTILE_HAS_GL_RENDERER

int runTutorial(const CliArgs& args) {
    if (args.gui) return runTutorialGui(args);
    const auto catalog = core::loadTileCatalog(args.data_dir / "tile_catalog.json");
    auto model = core::loadModelDefinition(args.model_file);
    printModelHeader(model);

    // --tts: 每步推进都朗读说明; speak 内部先停旧朗读 (无叠音),
    // 终端预览逐步瞬时推进, 实际可听到的是最后一步 —— 主要用于
    // 快速验证后端发声与教程文案的口语化程度
    std::unique_ptr<tts::ITtsEngine> tts_engine;
    if (args.tts) {
        tts_engine = tts::createSystemTts();
        std::printf("[tts] 朗读后端: %s%s\n\n", std::string(tts_engine->name()).c_str(),
                    tts_engine->available() ? "" : " (无可用朗读器, 静音降级)");
    }

    tutorial::TutorialEngine engine(std::move(model));
    while (engine.nextStep()) {
        const core::BuildStep* step = engine.currentStep();
        if (tts_engine != nullptr) tts_engine->speak(step->description);
        std::printf("第 %d/%d 步  [进度 %3.0f%%]\n", engine.currentStepNumber(),
                    engine.stepCount(), engine.progress() * 100.0);
        std::printf("  %s\n", step->description.c_str());
        if (!step->tip.empty()) {
            std::printf("  提示: %s\n", step->tip.c_str());
        }
        std::printf("  本步放置 %zu 片:", step->tiles_to_add.size());
        for (const auto* tile : engine.tilesAddedThisStep()) {
            std::printf(" %s(%s/%s)", tile->id.c_str(),
                        std::string(core::displayNameZh(tile->type)).c_str(),
                        std::string(core::displayNameZh(tile->color)).c_str());
        }
        std::printf("\n\n");
    }
    std::printf("教程结束, 共放置 %zu 片磁力片。\n", engine.visibleTiles().size());
    return 0;
}

/// library (无 --gui): 终端列出模型库与进度, 并对账目录元数据与模型
/// 文件 (名称/难度/片数/步数), 不一致即非零退出 —— 兼作 CI 质量关卡,
/// 防止模型卡片信息与实际内容漂移。
int runLibrary(const CliArgs& args) {
    if (args.gui) return runLibraryGui(args);

    const auto entries = core::loadModelCatalog(args.data_dir);
    const fs::path db_file = args.db_file.empty() ? defaultProgressDbPath() : args.db_file;
    progress::ProgressStore store(db_file);

    // --core-only: 只列基础套装 (核心 9 片型) 就能搭的模型 —— 判定
    // 口径与图形版筛选一致 (core::isCoreTile, 目录 tier 优先)。
    // 目录/模型对账照常覆盖全库, 过滤只影响列表输出。
    const auto catalog = core::loadTileCatalog(args.data_dir / "tile_catalog.json");

    if (args.core_only) {
        std::printf("MagTile Studio 模型库 (只用核心 9 片型的模型, 全库 %zu 个):\n\n",
                    entries.size());
    } else {
        std::printf("MagTile Studio 模型库 (%zu 个模型):\n\n", entries.size());
    }
    int failures = 0;
    std::size_t listed = 0;
    for (const auto& entry : entries) {
        bool core9_only = true;
        try {
            const auto model = core::loadModelDefinition(entry.file);
            if (model.name != entry.name || model.difficulty != entry.difficulty ||
                model.total_pieces != entry.total_pieces ||
                static_cast<int>(model.steps.size()) != entry.step_count) {
                std::printf(
                    "[错误] %s: 目录元数据与模型文件不一致\n"
                    "       目录: %s / 难度 %d / %d 片 / %d 步\n"
                    "       文件: %s / 难度 %d / %d 片 / %zu 步\n",
                    entry.id.c_str(), entry.name.c_str(), entry.difficulty, entry.total_pieces,
                    entry.step_count, model.name.c_str(), model.difficulty, model.total_pieces,
                    model.steps.size());
                ++failures;
                continue;
            }
            for (const auto& [type, count] : model.pieceCountByType()) {
                (void)count;
                if (!core::isCoreTile(catalog, type)) {
                    core9_only = false;
                    break;
                }
            }
        } catch (const std::exception& e) {
            std::printf("[错误] %s: 模型文件加载失败: %s\n", entry.id.c_str(), e.what());
            ++failures;
            continue;
        }
        if (args.core_only && !core9_only) continue;
        ++listed;

        std::string stars;
        for (int i = 1; i <= entry.difficulty; ++i) stars += "★";
        std::string status = "未开始";
        std::string favorite_mark = " ";
        if (const auto record = store.loadProgress(entry.id); record.has_value()) {
            if (record->favorited) favorite_mark = "★";
            if (record->isCompleted()) {
                status = "已完成 ✓";
            } else if (record->current_step > 0) {
                status = "进行中 (第 " + std::to_string(record->current_step) + "/" +
                         std::to_string(entry.step_count) + " 步)";
            }
        }
        std::printf("  %s %-24s %s  难度 %s  %d 片 / %d 步  主题: %s  [%s]\n",
                    favorite_mark.c_str(), entry.id.c_str(), entry.name.c_str(), stars.c_str(),
                    entry.total_pieces, entry.step_count, entry.theme().c_str(), status.c_str());
    }

    if (failures > 0) {
        std::printf("\n结论: 模型库目录有 %d 个条目未通过对账\n", failures);
        return 1;
    }
    if (args.core_only) {
        std::printf("\n结论: 全库 %zu 个模型中 %zu 个只用核心 9 片型 (目录对账通过)\n",
                    entries.size(), listed);
    } else {
        std::printf("\n结论: 模型库目录与模型文件一致 (%zu 个模型)\n", entries.size());
    }
    std::printf("提示: magtile_app library --gui 打开图形模型库\n");
    return 0;
}

}  // namespace

int main(int argc, char** argv) {
    CliArgs args;
    if (!parseArgs(argc, argv, args)) {
        printUsage();
        return 2;
    }

    try {
        if (args.command == "catalog") return runCatalog(args);
        if (args.command == "validate") return runValidate(args);
        if (args.command == "tutorial") return runTutorial(args);
        if (args.command == "progress") return runProgress(args);
        if (args.command == "inventory") return runInventory(args);
        if (args.command == "settings") return runSettings(args);
        if (args.command == "library") return runLibrary(args);
    } catch (const std::exception& e) {
        std::fprintf(stderr, "错误: %s\n", e.what());
        return 1;
    }
    printUsage();
    return 2;
}
