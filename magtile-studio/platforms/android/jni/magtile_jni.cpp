// =============================================================
// MagTile Studio - Android JNI 包装层
//
// 模型库链路 (绑定 com.magtile.studio.MainActivity):
//   loadCatalog(catalogPath)      -> 加载磁力片形状目录, 返回形状数
//   listModels(dataDir)           -> 模型库目录 (卡片元数据 + core-9 判定
//                                    + 库存已登记时的「我能搭的」判定), 返回 JSON 字符串
//   validateModel(jsonPath)       -> 加载模型并跑完整物理校验, 返回中文摘要
//   getTutorialStepCount()        -> 最近一次成功加载模型的教程步骤数
//
// 进度存档 / 磁力片库存链路 (绑定 com.magtile.studio.MagTileNative,
// 直接复用核心库 progress::ProgressStore —— 与桌面 CLI / GL / Qt
// 同一份 SQLite schema, tile_inventory 表):
//   openProgressStore(dbPath)     -> 打开 (不存在则创建) 进度存档数据库
//   inventoryRows()               -> 库存录入界面数据源 JSON (全部片型 + 已存数量)
//   saveInventory(countsJson)     -> 保存库存快照 ({"square":3,...} upsert)
//   canBuildModel(jsonPath)       -> 库存是否足够搭建 (1/0; 未登记/失败 -1)
//   missingPiecesJson(jsonPath)   -> 缺片清单 JSON (片型 + 缺几片 + 中文摘要)
//   ageModeId()                   -> 年龄段模式标识 (settings 表 age_mode 键,
//                                    与桌面同键; 未设置/脏值回默认档 age_7_9)
//   setAgeModeId(modeId)          -> 保存年龄段模式 (未知标识忽略并返回 false)
//   progressOverviewJson(dataDir) -> 进度页/成就墙数据源 JSON (三格统计 +
//                                    进行中/已完成/收藏列表 + 徽章墙,
//                                    口径与桌面 Qt StudioBackend 一致)
//
// 分步教程链路 (绑定 com.magtile.studio.MagTileNative, 供
// TutorialActivity 步骤浏览使用; 3D 视口链路见 magtile_scene_jni.cpp):
//   getTutorialSteps(dataDir, modelId) -> 教程步骤 JSON (步序 + 中文
//                                    说明/提示 + 片数增量/累计)
//   savedTutorialStep(modelId)    -> 存档中的当前步 (断点续搭; 无记录 0)
//   saveTutorialStep(modelId, step, stepCount, playSeconds)
//                                 -> 写当前步到进度存档 (与桌面共库
//                                    schema; 走到最后一步记完成 + 首搭成就)
//
// 家长门链路 (绑定 com.magtile.studio.MagTileNative, 直接复用
// core::ParentGate —— 与桌面 GL/Qt 同一状态机: 乘法题 + 中文大写数字
// 答案 + 3 次答错 60 秒冷却 + 15 分钟内存会话, UI_UX_SPEC.md §9;
// 会话/冷却只存内存, 永不落盘, 防重启绕过):
//   parentGateOpenJson()          -> 进门出新题, 返回门状态 JSON
//   parentGateSubmitJson(answer)  -> 提交答案, 返回结果 + 剩余次数/冷却
//   parentGateSessionActive()     -> 家长会话是否仍有效 (免重复验证)
//
// 说明: 3D 教程视口链路 (场景加载 / 设步 / 相机手势 / GLES3 渲染循环,
// 绑定 com.magtile.studio.TutorialSceneNative) 在 magtile_scene_jni.cpp。
// =============================================================

#include <jni.h>

#include <algorithm>
#include <cstdint>
#include <ctime>
#include <exception>
#include <map>
#include <mutex>
#include <optional>
#include <set>
#include <sstream>
#include <string>
#include <utility>
#include <vector>

#include <nlohmann/json.hpp>

#if defined(__ANDROID__)
#include <android/log.h>
#define MAGTILE_LOGE(...) \
    __android_log_print(ANDROID_LOG_ERROR, "MagTileNative", __VA_ARGS__)
#else
#define MAGTILE_LOGE(...) ((void)0)
#endif

#include "magtile/core/json_io.hpp"
#include "magtile/core/model_catalog.hpp"
#include "magtile/core/parent_gate.hpp"
#include "magtile/core/model_definition.hpp"
#include "magtile/core/tile_catalog.hpp"
#include "magtile/core/types.hpp"
#include "magtile/core/age_mode.hpp"
#include "magtile/physics/physics_validator.hpp"
#include "magtile/progress/age_settings.hpp"
#include "magtile/progress/progress_store.hpp"
#include "magtile/tutorial/tutorial_engine.hpp"

namespace {

/// 进程级原生上下文。脚手架阶段以单例承载目录、进度存档与最近加载的
/// 模型; 接入渲染/多文档后再演进为按会话句柄管理。
struct NativeContext {
    std::mutex mutex;
    std::optional<magtile::core::TileCatalog> catalog;
    std::optional<magtile::core::ModelDefinition> model;
    /// 进度存档 (SQLite, 与桌面同一 schema); 打开失败保持空 —— 只影响
    /// 库存 / 进度功能, 模型库照常可浏览 (P3 零挫败, 与桌面同策略)。
    std::optional<magtile::progress::ProgressStore> store;
};

NativeContext& context() {
    static NativeContext ctx;
    return ctx;
}

/// 家长门状态 (UI_UX_SPEC.md §9): 题目/冷却/会话全部由共享状态机
/// core::ParentGate 负责, 只存内存永不落盘 ("已通过" 标记不持久化,
/// 防重启绕过 —— 与桌面 GL/Qt 同策略)。默认构造即 15 分钟会话
/// (kDefaultSessionDuration)。独立于 NativeContext 加自己的锁:
/// 门交互发生在主线程, 不能被工作线程的重 IO (listModels 等) 卡住。
struct ParentGateContext {
    std::mutex mutex;
    magtile::core::ParentGate gate;
};

ParentGateContext& gateContext() {
    static ParentGateContext ctx;
    return ctx;
}

/// 门状态 JSON (调用方需已持有 gate mutex): 题面为中文数字 (BMP,
/// 可安全过 NewStringUTF), 冷却/尝试次数供 Kotlin 侧渲染温和提示。
nlohmann::json gateStateJson(const magtile::core::ParentGate& gate) {
    return {
        {"question", gate.question()},
        {"attempts_remaining", gate.attemptsRemaining()},
        {"cooldown_seconds", gate.cooldownRemainingSeconds()},
        {"session_active", gate.sessionActive()},
    };
}

std::string toUtf8(JNIEnv* env, jstring value) {
    if (value == nullptr) {
        return {};
    }
    const char* chars = env->GetStringUTFChars(value, nullptr);
    std::string result = (chars != nullptr) ? chars : "";
    if (chars != nullptr) {
        env->ReleaseStringUTFChars(value, chars);
    }
    return result;
}

jstring toJString(JNIEnv* env, const std::string& value) {
    return env->NewStringUTF(value.c_str());
}

/// 与桌面录入界面一致的数量上限 (纯 UI 约束, 存储层只校验 >= 0)。
constexpr int kInventoryCountMax = 999;

/// 片型中文名: 目录 name_zh 优先, 目录不可用时退回 displayNameZh
/// (与 Qt InventoryBackend / StudioBackend::shapeNameZh 同一口径)。
std::string shapeNameZh(const NativeContext& ctx, magtile::core::TileType type) {
    if (ctx.catalog.has_value()) {
        if (const magtile::core::TileShape* shape = ctx.catalog->find(type);
            shape != nullptr && !shape->name_zh.empty()) {
            return shape->name_zh;
        }
    }
    return std::string(magtile::core::displayNameZh(type));
}

/// 磁力片库存快照 (调用方需已持有 ctx.mutex)。
struct InventorySnapshot {
    bool configured = false;  ///< 是否登记过库存 (含 0 数量的 "明确没有")
    std::map<magtile::core::TileType, int> counts;
};

InventorySnapshot snapshotInventory(NativeContext& ctx) {
    InventorySnapshot snapshot;
    if (!ctx.store.has_value()) {
        return snapshot;
    }
    try {
        snapshot.configured = ctx.store->hasInventory();
        for (const auto& [shape_id, count] : ctx.store->getInventory()) {
            if (const auto type = magtile::core::tileTypeFromString(shape_id)) {
                snapshot.counts[*type] = count;
            }
        }
    } catch (const magtile::progress::ProgressError& e) {
        MAGTILE_LOGE("读取库存失败: %s", e.what());
        snapshot = InventorySnapshot{};  // 读取失败按未登记处理, 界面照常可用
    }
    return snapshot;
}

/// 对照模型 BOM 与库存快照, 返回缺片清单 (片型 -> 缺几片); 空表 = 够搭。
/// 未登记的片型按 0 计 (与 ProgressStore::missingPieces / 桌面同口径)。
std::map<magtile::core::TileType, int> missingFor(
    const magtile::core::ModelDefinition& model, const InventorySnapshot& snapshot) {
    std::map<magtile::core::TileType, int> missing;
    for (const auto& [type, needed] : model.pieceCountByType()) {
        const auto it = snapshot.counts.find(type);
        const int have = (it == snapshot.counts.end()) ? 0 : it->second;
        if (needed > have) {
            missing[type] = needed - have;
        }
    }
    return missing;
}

// ---- 进度页 / 成就墙 (progressOverviewJson) ----------------------------

/// 成就徽章档位 (与桌面 Qt StudioBackend 的 kAchievementDefs 同一份
/// 定义: 只与搭建行为挂钩, 按完成模型数 1/3/10/30 分档, §4.5)。
/// first_model_completed 与完成链路写档 id 同名; 其余档位按已完成数
/// 在展示层判定达成, 不新增写库触发点 (触发统一收口留待成就系统
/// 完整落地)。emoji 不在此处下发: 徽章 emoji 为增补平面字符, 而
/// NewStringUTF 只接受 Modified UTF-8 (BMP), 由 Kotlin 侧按 id 映射。
struct AchievementDef {
    const char* id;
    const char* name;
    const char* condition;    ///< 一句话达成条件 (未点亮时展示, §7.1)
    int completed_threshold;  ///< 达成所需的已完成模型数
};
constexpr AchievementDef kAchievementDefs[] = {
    {"first_model_completed", "首搭达成", "完成第 1 个模型", 1},
    {"three_models_completed", "小小建造家", "完成 3 个模型", 3},
    {"ten_models_completed", "建造能手", "完成 10 个模型", 10},
    {"thirty_models_completed", "磁力片大师", "完成 30 个模型", 30},
};

/// unix 秒 -> "8月20日" (今年) / "2025年8月20日" (往年); 无记录返回
/// 空串。本地时区, 措辞与桌面 Qt dayText 一致。
std::string dayTextZh(std::int64_t unix_seconds) {
    if (unix_seconds <= 0) return {};
    const std::time_t t = static_cast<std::time_t>(unix_seconds);
    std::tm day{};
    localtime_r(&t, &day);
    std::time_t now_t = std::time(nullptr);
    std::tm now{};
    localtime_r(&now_t, &now);
    std::string text;
    if (day.tm_year != now.tm_year) {
        text += std::to_string(day.tm_year + 1900) + "年";
    }
    text += std::to_string(day.tm_mon + 1) + "月" + std::to_string(day.tm_mday) + "日";
    return text;
}

/// 累计游玩时长 -> "用时 23 分钟" 式温和摘要; 不足 1 分钟返回空串
/// (界面直接隐藏, 不显示 "0 分钟" 这类扫兴数字; 与桌面 Qt playText 一致)。
std::string playTextZh(std::int64_t play_seconds) {
    if (play_seconds < 60) return {};
    const std::int64_t minutes = play_seconds / 60;
    if (minutes < 60) return "用时 " + std::to_string(minutes) + " 分钟";
    return "用时 " + std::to_string(minutes / 60) + " 小时 " +
           std::to_string(minutes % 60) + " 分";
}

}  // namespace

extern "C" {

/// 加载 data/tile_catalog.json (路径由 Kotlin 侧解包 assets 后传入)。
/// 返回目录中的形状数量; 失败返回 -1 并写 logcat。
JNIEXPORT jint JNICALL Java_com_magtile_studio_MainActivity_loadCatalog(
    JNIEnv* env, jobject /*thiz*/, jstring catalog_path) {
    auto& ctx = context();
    std::lock_guard<std::mutex> lock(ctx.mutex);
    try {
        ctx.catalog = magtile::core::loadTileCatalog(toUtf8(env, catalog_path));
        return static_cast<jint>(ctx.catalog->size());
    } catch (const std::exception& e) {
        MAGTILE_LOGE("loadCatalog 失败: %s", e.what());
        ctx.catalog.reset();
        return -1;
    }
}

/// 加载 data 目录下的模型库目录 (model_catalog.json, 缺失时自动扫描
/// models/*.json), 返回 UTF-8 JSON 字符串供 Kotlin 侧 (org.json) 解析:
///   成功: {"inventory_configured": bool,
///          "models":[{"id","name","name_en","description","difficulty",
///                     "total_pieces","step_count","theme","file",
///                     "bom_known","core9_only","can_build","missing_total",
///                     "free"},
///                    ...]}
///   失败: {"error":"中文错误信息"}
/// 卡片展示元数据外, 逐模型加载 BOM 做两项判定 (与桌面 GL/Qt 同口径):
///   - 「只用核心 9 片」: core::isCoreTile 共享判定 (目录 tier 优先,
///     形状缺失退回代码内白名单);
///   - 「我能搭的」: 库存已登记 (openProgressStore 后 tile_inventory
///     表非空) 时对照 BOM 得出 can_build 与 missing_total (缺几片);
///     未登记时 inventory_configured=false, can_build 恒 false,
///     Kotlin 侧应禁用该筛选并引导录入。
/// 模型文件有问题的按 "BOM 未知" 降级 (bom_known=false, 不进核心
/// 筛选也不显示角标, 不进「我能搭的」), 不影响其余卡片。
/// 139 模型量级后台线程百毫秒完成 (与桌面 GL 启动逐模型判定同策略)。
/// file 为模型 JSON 绝对路径, 可直接传给 validateModel()。
JNIEXPORT jstring JNICALL Java_com_magtile_studio_MainActivity_listModels(
    JNIEnv* env, jobject /*thiz*/, jstring data_dir) {
    auto& ctx = context();
    std::lock_guard<std::mutex> lock(ctx.mutex);
    try {
        const std::vector<magtile::core::ModelCatalogEntry> entries =
            magtile::core::loadModelCatalog(toUtf8(env, data_dir));
        const InventorySnapshot inventory = snapshotInventory(ctx);

        nlohmann::json models = nlohmann::json::array();
        for (const auto& entry : entries) {
            bool bom_known = false;
            bool core9_only = false;
            bool can_build = false;
            int missing_total = 0;
            try {
                const auto model = magtile::core::loadModelDefinition(entry.file);
                core9_only = true;
                for (const auto& [type, count] : model.pieceCountByType()) {
                    (void)count;
                    const bool is_core =
                        ctx.catalog.has_value()
                            ? magtile::core::isCoreTile(*ctx.catalog, type)
                            : magtile::core::isCoreTileFallback(type);
                    if (!is_core) {
                        core9_only = false;
                        break;
                    }
                }
                if (inventory.configured) {
                    for (const auto& [type, count] : missingFor(model, inventory)) {
                        (void)type;
                        missing_total += count;
                    }
                    can_build = (missing_total == 0);
                }
                bom_known = true;
            } catch (const std::exception&) {
                // 模型文件有问题由目录对账用例负责报告, 这里按 BOM 未知处理
            }
            models.push_back({
                {"id", entry.id},
                {"name", entry.name},
                {"name_en", entry.name_en},
                {"description", entry.description},
                {"difficulty", entry.difficulty},
                {"total_pieces", entry.total_pieces},
                {"step_count", entry.step_count},
                {"theme", entry.theme()},
                {"file", entry.file.string()},
                {"bom_known", bom_known},
                {"core9_only", core9_only},
                {"can_build", bom_known && can_build},
                {"missing_total", missing_total},
                // 免费层判定与 CLI/GL/Qt 同一口径 (core::isFreeTierModel,
                // 目录 tags 含「免费」); 非免费只作温和提示, 不锁浏览
                {"free", magtile::core::isFreeTierModel(entry)},
            });
        }
        const nlohmann::json root = {
            {"inventory_configured", inventory.configured},
            {"models", std::move(models)},
        };
        // dump() 输出标准 UTF-8; 目录内容均为基本多文种平面字符,
        // 与 NewStringUTF 要求的 Modified UTF-8 编码一致。
        return toJString(env, root.dump());
    } catch (const std::exception& e) {
        MAGTILE_LOGE("listModels 失败: %s", e.what());
        const nlohmann::json error = {{"error", std::string("错误: ") + e.what()}};
        return toJString(env, error.dump());
    }
}

/// 加载模型 JSON 并执行完整物理校验 (R1~R8, 含每个教程步骤的中间态)。
/// 返回中文摘要字符串; 需先调用 loadCatalog()。
/// 成功加载的模型保留在原生上下文中, 供 getTutorialStepCount() 查询。
JNIEXPORT jstring JNICALL Java_com_magtile_studio_MainActivity_validateModel(
    JNIEnv* env, jobject /*thiz*/, jstring json_path) {
    auto& ctx = context();
    std::lock_guard<std::mutex> lock(ctx.mutex);
    try {
        if (!ctx.catalog.has_value()) {
            return toJString(env, "错误: 请先调用 loadCatalog() 加载磁力片形状目录");
        }
        magtile::core::ModelDefinition model =
            magtile::core::loadModelDefinition(toUtf8(env, json_path));

        magtile::physics::PhysicsValidator validator(*ctx.catalog);
        const magtile::physics::ValidationReport report = validator.validateModel(model);

        std::ostringstream out;
        out << "模型 " << model.id << " (" << model.name << "): "
            << (report.ok() ? "校验通过" : "校验未通过")
            << " [" << report.errorCount() << " 错误 / "
            << report.warningCount() << " 警告]";
        for (const auto& issue : report.issues) {
            const bool is_error =
                issue.severity == magtile::physics::IssueSeverity::Error;
            out << '\n' << (is_error ? "[错误] " : "[警告] ")
                << issue.code << ": " << issue.message;
        }

        ctx.model = std::move(model);
        return toJString(env, out.str());
    } catch (const std::exception& e) {
        MAGTILE_LOGE("validateModel 失败: %s", e.what());
        return toJString(env, std::string("错误: ") + e.what());
    }
}

/// 返回最近一次成功加载模型的教程步骤数; 尚未加载模型时返回 -1。
JNIEXPORT jint JNICALL Java_com_magtile_studio_MainActivity_getTutorialStepCount(
    JNIEnv* /*env*/, jobject /*thiz*/) {
    auto& ctx = context();
    std::lock_guard<std::mutex> lock(ctx.mutex);
    if (!ctx.model.has_value()) {
        return -1;
    }
    const magtile::tutorial::TutorialEngine engine(*ctx.model);
    return static_cast<jint>(engine.stepCount());
}

// =============================================================
// 进度存档 / 磁力片库存 (绑定 com.magtile.studio.MagTileNative)
// 直接复用核心库 progress::ProgressStore —— 与桌面 CLI `inventory set`
// / GL / Qt 录入界面同一份 SQLite schema (tile_inventory 表),
// 存档文件互相兼容 (docs/PLATFORM_ARCHITECTURE.md §5.1)。
// =============================================================

/// 打开 (不存在则创建) 进度存档数据库; 父目录不存在时自动创建。
/// Kotlin 侧传 filesDir/progress.db。成功返回 true; 失败返回 false
/// 并写 logcat (只影响库存/进度功能, 模型库照常可浏览)。
JNIEXPORT jboolean JNICALL Java_com_magtile_studio_MagTileNative_openProgressStore(
    JNIEnv* env, jobject /*thiz*/, jstring db_path) {
    auto& ctx = context();
    std::lock_guard<std::mutex> lock(ctx.mutex);
    try {
        ctx.store.emplace(toUtf8(env, db_path));
        return JNI_TRUE;
    } catch (const std::exception& e) {
        MAGTILE_LOGE("openProgressStore 失败: %s", e.what());
        ctx.store.reset();
        return JNI_FALSE;
    }
}

/// 库存录入界面数据源: 全部片型一行一项, 按 TileType 枚举顺序
/// (核心 9 片型在前), 与 Qt InventoryBackend::rows() 同一构造口径:
///   {"configured": bool, "total": N,
///    "shapes":[{"id","name_zh","expansion","count"}, ...]}
/// 中文名与 core/expansion 分层以 tile_catalog.json 为准 (需先
/// loadCatalog), 目录不可用时退回 displayNameZh 与枚举位置。
/// 存档未打开时 configured=false、count 全 0, 界面照常可录入。
JNIEXPORT jstring JNICALL Java_com_magtile_studio_MagTileNative_inventoryRows(
    JNIEnv* env, jobject /*thiz*/) {
    auto& ctx = context();
    std::lock_guard<std::mutex> lock(ctx.mutex);
    const InventorySnapshot inventory = snapshotInventory(ctx);

    int total = 0;
    nlohmann::json shapes = nlohmann::json::array();
    for (int i = 0; i < magtile::core::kTileTypeCount; ++i) {
        const auto type = static_cast<magtile::core::TileType>(i);
        // 枚举顺序约定: 核心 9 片型在前 (types.hpp), 目录可用时以 tier 为准
        bool expansion = type >= magtile::core::TileType::Rhombus;
        if (ctx.catalog.has_value()) {
            if (const magtile::core::TileShape* shape = ctx.catalog->find(type);
                shape != nullptr) {
                expansion = shape->tier != "core";
            }
        }
        const auto it = inventory.counts.find(type);
        const int count = (it == inventory.counts.end()) ? 0 : it->second;
        total += count;
        shapes.push_back({
            {"id", std::string(magtile::core::toString(type))},
            {"name_zh", shapeNameZh(ctx, type)},
            {"expansion", expansion},
            {"count", count},
        });
    }
    const nlohmann::json root = {
        {"configured", inventory.configured},
        {"total", total},
        {"shapes", std::move(shapes)},
    };
    return toJString(env, root.dump());
}

/// 保存库存 (shapeId -> count 的完整快照 JSON, 如 {"square":12,...}):
/// 数量夹到 [0, 999], 未知片型标识跳过 (与 Qt InventoryBackend::save
/// 同一口径; count=0 也保留记录, "明确没有" 不再触发 onboarding)。
/// 成功返回 true; 存档未打开 / JSON 不合法 / 写入失败返回 false
/// (Kotlin 侧温和提示, 不弹 "失败")。
JNIEXPORT jboolean JNICALL Java_com_magtile_studio_MagTileNative_saveInventory(
    JNIEnv* env, jobject /*thiz*/, jstring counts_json) {
    auto& ctx = context();
    std::lock_guard<std::mutex> lock(ctx.mutex);
    if (!ctx.store.has_value()) {
        MAGTILE_LOGE("saveInventory 失败: 进度存档未打开");
        return JNI_FALSE;
    }
    try {
        const nlohmann::json counts = nlohmann::json::parse(toUtf8(env, counts_json));
        for (const auto& [shape_id, value] : counts.items()) {
            if (!magtile::core::tileTypeFromString(shape_id).has_value()) {
                continue;  // 未知标识跳过
            }
            const int count = std::clamp(value.get<int>(), 0, kInventoryCountMax);
            ctx.store->setInventory(shape_id, count);
        }
        return JNI_TRUE;
    } catch (const std::exception& e) {
        MAGTILE_LOGE("saveInventory 失败: %s", e.what());
        return JNI_FALSE;
    }
}

/// 库存是否足够搭建模型 (json_path 为模型 JSON 绝对路径, 即
/// listModels 返回的 file 字段): 1 = 够搭, 0 = 缺片;
/// -1 = 无法判定 (存档未打开 / 库存未登记 / 模型文件有问题)。
JNIEXPORT jint JNICALL Java_com_magtile_studio_MagTileNative_canBuildModel(
    JNIEnv* env, jobject /*thiz*/, jstring json_path) {
    auto& ctx = context();
    std::lock_guard<std::mutex> lock(ctx.mutex);
    const InventorySnapshot inventory = snapshotInventory(ctx);
    if (!inventory.configured) {
        return -1;
    }
    try {
        const auto model = magtile::core::loadModelDefinition(toUtf8(env, json_path));
        return missingFor(model, inventory).empty() ? 1 : 0;
    } catch (const std::exception& e) {
        MAGTILE_LOGE("canBuildModel 失败: %s", e.what());
        return -1;
    }
}

/// 缺片清单 (json_path 为模型 JSON 绝对路径):
///   成功: {"configured": bool, "can_build": bool, "missing_total": N,
///          "missing":[{"id","name_zh","count"}, ...],
///          "text": "缺 2 片正方形、1 片菱形"}   (够搭时 text 为空串)
///   失败: {"error":"中文错误信息"}
/// 库存未登记时 configured=false, can_build=false, missing 为空
/// (Kotlin 侧据此引导先去录入而非显示 "缺 N 片")。
/// text 措辞与桌面 Qt StudioBackend::missingText 一致。
JNIEXPORT jstring JNICALL Java_com_magtile_studio_MagTileNative_missingPiecesJson(
    JNIEnv* env, jobject /*thiz*/, jstring json_path) {
    auto& ctx = context();
    std::lock_guard<std::mutex> lock(ctx.mutex);
    const InventorySnapshot inventory = snapshotInventory(ctx);
    try {
        const auto model = magtile::core::loadModelDefinition(toUtf8(env, json_path));

        nlohmann::json missing = nlohmann::json::array();
        int missing_total = 0;
        std::string text;
        if (inventory.configured) {
            for (const auto& [type, count] : missingFor(model, inventory)) {
                const std::string name_zh = shapeNameZh(ctx, type);
                missing.push_back({
                    {"id", std::string(magtile::core::toString(type))},
                    {"name_zh", name_zh},
                    {"count", count},
                });
                missing_total += count;
                if (!text.empty()) text += "、";
                text += std::to_string(count) + " 片" + name_zh;
            }
            if (!text.empty()) text = "缺 " + text;
        }
        const nlohmann::json root = {
            {"configured", inventory.configured},
            {"can_build", inventory.configured && missing_total == 0},
            {"missing_total", missing_total},
            {"missing", std::move(missing)},
            {"text", std::move(text)},
        };
        return toJString(env, root.dump());
    } catch (const std::exception& e) {
        MAGTILE_LOGE("missingPiecesJson 失败: %s", e.what());
        const nlohmann::json error = {{"error", std::string("错误: ") + e.what()}};
        return toJString(env, error.dump());
    }
}

/// 当前年龄段模式标识 ("age_4_6" / "age_7_9" / "age_10_12"):
/// 经 progress::getAgeMode 读 settings 表 age_mode 键 —— 与桌面
/// GL/Qt/CLI (`settings set-age`) 同键同一份 SQLite 存档。
/// 存档未打开 / 从未设置 / 存量脏值一律返回默认档 age_7_9
/// (读取函数自带兜底), Kotlin 侧无需判空。
JNIEXPORT jstring JNICALL Java_com_magtile_studio_MagTileNative_ageModeId(
    JNIEnv* env, jobject /*thiz*/) {
    auto& ctx = context();
    std::lock_guard<std::mutex> lock(ctx.mutex);
    magtile::core::AgeMode mode = magtile::core::kDefaultAgeMode;
    if (ctx.store.has_value()) {
        try {
            mode = magtile::progress::getAgeMode(*ctx.store);
        } catch (const magtile::progress::ProgressError& e) {
            MAGTILE_LOGE("ageModeId 读取失败: %s", e.what());  // 按默认档兜底
        }
    }
    return toJString(env, std::string(magtile::core::toString(mode)));
}

/// 保存年龄段模式 (立即落盘, settings 表 age_mode 键): 未知标识
/// 返回 false 并忽略 (与桌面 SettingsBackend::setAgeModeId 一致);
/// 存档未打开 / 落盘失败仍返回 true —— 设置在本次运行内生效
/// (Kotlin 侧内存态即真相), 只是重启后回读不到 (温和降级同桌面)。
JNIEXPORT jboolean JNICALL Java_com_magtile_studio_MagTileNative_setAgeModeId(
    JNIEnv* env, jobject /*thiz*/, jstring mode_id) {
    const auto mode = magtile::core::ageModeFromString(toUtf8(env, mode_id));
    if (!mode.has_value()) {
        return JNI_FALSE;
    }
    auto& ctx = context();
    std::lock_guard<std::mutex> lock(ctx.mutex);
    if (ctx.store.has_value()) {
        try {
            magtile::progress::setAgeMode(*ctx.store, *mode);
        } catch (const magtile::progress::ProgressError& e) {
            MAGTILE_LOGE("setAgeModeId 落盘失败: %s", e.what());
        }
    }
    return JNI_TRUE;
}

/// 进度页「我的作品」/ 成就墙数据源 (data_dir 为解包后的数据目录,
/// 即 listModels 的同一入参; 读同一份 SQLite 进度存档, 口径与桌面
/// Qt StudioBackend 完全一致):
///   成功: {"store_ready": bool,
///          "completed_count": N, "in_progress_count": N,
///          "favorite_count": N, "achievement_count": N,
///          "in_progress":[{"id","name","current_step","step_count",
///                          "play_text"}, ...],          (最近游玩倒序)
///          "completed":[{"id","name","pieces","meta_text"}, ...],
///                                                        (完成时间倒序)
///          "favorites":[{"id","name"}, ...],             (目录顺序)
///          "achievements":[{"id","name","condition","unlocked",
///                           "unlocked_text"}, ...]}
///   失败: {"error":"中文错误信息"}
/// 口径要点 (与 Qt inProgressList/completedList/favoritesList/
/// achievementsList 同):
///   - 只统计仍在模型库目录中的模型; 进行中要求已真正开动
///     (current_step > 0) 且未完成;
///   - 徽章: 存档 achievements 表已解锁 或 已完成数达到档位阈值即点亮;
///     未点亮带一句话达成条件, 不下发进度百分比 (§7.1 防焦虑);
///     存档中额外成就以通用徽章补列, 永不缺席;
///   - 存档不可用时 store_ready=false, 列表为空、徽章全未点亮,
///     页面照常可看 (P3 零挫败)。
/// 徽章 emoji 由 Kotlin 侧按 id 映射 (增补平面字符不过 NewStringUTF)。
JNIEXPORT jstring JNICALL Java_com_magtile_studio_MagTileNative_progressOverviewJson(
    JNIEnv* env, jobject /*thiz*/, jstring data_dir) {
    auto& ctx = context();
    std::lock_guard<std::mutex> lock(ctx.mutex);
    try {
        const std::vector<magtile::core::ModelCatalogEntry> entries =
            magtile::core::loadModelCatalog(toUtf8(env, data_dir));
        std::map<std::string, const magtile::core::ModelCatalogEntry*> entry_by_id;
        for (const auto& entry : entries) {
            entry_by_id.emplace(entry.id, &entry);
        }

        // ---- 存档快照 (读取失败按空处理, 页面照常可看) ------------------
        bool store_ready = ctx.store.has_value();
        std::vector<magtile::progress::Progress> in_progress_rows;
        std::vector<magtile::progress::Progress> completed_rows;
        std::map<std::string, std::int64_t> unlocked;  // 成就 id -> 首次解锁时刻
        if (store_ready) {
            try {
                in_progress_rows = ctx.store->listInProgress();
                completed_rows = ctx.store->listCompleted();
                for (const auto& a : ctx.store->listAchievements()) {
                    unlocked.emplace(a.id, a.unlocked_at);
                }
            } catch (const magtile::progress::ProgressError& e) {
                MAGTILE_LOGE("progressOverviewJson 读取存档失败: %s", e.what());
                in_progress_rows.clear();
                completed_rows.clear();
                unlocked.clear();
                store_ready = false;
            }
        }

        // ---- 进行中 (最近游玩倒序; 只列已开动且仍在库中的) ---------------
        nlohmann::json in_progress = nlohmann::json::array();
        std::set<std::string> favorited_ids;
        for (const auto& p : in_progress_rows) {
            const auto it = entry_by_id.find(p.model_id);
            if (it == entry_by_id.end()) continue;
            if (p.favorited) favorited_ids.insert(p.model_id);
            if (p.current_step <= 0 || p.isCompleted()) continue;
            in_progress.push_back({
                {"id", it->second->id},
                {"name", it->second->name},
                {"current_step", p.current_step},
                {"step_count", it->second->step_count},
                {"play_text", playTextZh(p.play_seconds)},
            });
        }

        // ---- 已完成 (完成时间倒序; meta 措辞与桌面 completedList 一致) ---
        nlohmann::json completed = nlohmann::json::array();
        int completed_count = 0;
        for (const auto& p : completed_rows) {
            const auto it = entry_by_id.find(p.model_id);
            if (it == entry_by_id.end() || !p.isCompleted()) continue;
            if (p.favorited) favorited_ids.insert(p.model_id);
            ++completed_count;
            std::string meta;
            if (const std::string day = dayTextZh(p.completed_at); !day.empty()) {
                meta = day + " 完成";
            }
            if (const std::string play = playTextZh(p.play_seconds); !play.empty()) {
                if (!meta.empty()) meta += " · ";
                meta += play;
            }
            completed.push_back({
                {"id", it->second->id},
                {"name", it->second->name},
                {"pieces", it->second->total_pieces},
                {"meta_text", std::move(meta)},
            });
        }

        // ---- 我的收藏 (目录顺序, 与桌面 favoritesList 一致) --------------
        nlohmann::json favorites = nlohmann::json::array();
        for (const auto& entry : entries) {
            if (favorited_ids.count(entry.id) == 0) continue;
            favorites.push_back({{"id", entry.id}, {"name", entry.name}});
        }

        // ---- 成就墙 (已解锁 或 完成数达档位阈值即点亮) --------------------
        nlohmann::json achievements = nlohmann::json::array();
        int achievement_count = 0;
        for (const AchievementDef& def : kAchievementDefs) {
            const auto it = unlocked.find(def.id);
            const bool reached =
                it != unlocked.end() || completed_count >= def.completed_threshold;
            std::string when;
            if (it != unlocked.end() && it->second > 0) {
                when = "解锁于 " + dayTextZh(it->second);
            } else if (reached) {
                when = "已达成";
            }
            achievements.push_back({
                {"id", def.id},
                {"name", def.name},
                {"condition", def.condition},
                {"unlocked", reached},
                {"unlocked_text", std::move(when)},
            });
            if (reached) ++achievement_count;
            if (it != unlocked.end()) unlocked.erase(it);
        }
        // 存档中额外解锁的成就 (未来新增触发点): 通用徽章补列, 永不缺席
        for (const auto& [id, at] : unlocked) {
            achievements.push_back({
                {"id", id},
                {"name", id},
                {"condition", ""},
                {"unlocked", true},
                {"unlocked_text", at > 0 ? "解锁于 " + dayTextZh(at) : "已达成"},
            });
            ++achievement_count;
        }

        const nlohmann::json root = {
            {"store_ready", store_ready},
            {"completed_count", completed_count},
            {"in_progress_count", static_cast<int>(in_progress.size())},
            {"favorite_count", static_cast<int>(favorites.size())},
            {"achievement_count", achievement_count},
            {"in_progress", std::move(in_progress)},
            {"completed", std::move(completed)},
            {"favorites", std::move(favorites)},
            {"achievements", std::move(achievements)},
        };
        return toJString(env, root.dump());
    } catch (const std::exception& e) {
        MAGTILE_LOGE("progressOverviewJson 失败: %s", e.what());
        const nlohmann::json error = {{"error", std::string("错误: ") + e.what()}};
        return toJString(env, error.dump());
    }
}

// =============================================================
// 分步教程 (TutorialActivity 步骤浏览; 3D 视口见 magtile_scene_jni.cpp)
// =============================================================

/// 教程步骤数据源 (data_dir 为解包后的数据目录, model_id 为模型标识;
/// 经模型库目录解析到模型 JSON —— 与进度页"只认仍在库中的模型"同一
/// 口径, 目录条目缺失时温和报错而非崩溃):
///   成功: {"model_id","name","step_count","total_pieces",
///          "steps":[{"step_number","description","tip",
///                    "pieces_added","pieces_total"}, ...]}
///   失败: {"error":"中文错误信息"}
/// pieces_added = 本步骤新增磁力片数 (tiles_to_add 长度),
/// pieces_total = 截至本步骤累计已放片数 (末步 = total_pieces,
/// 加载时经 ModelDefinition 与 final_assembly 对账)。步骤文本均为
/// 基本多文种平面字符 (与目录简介同一约束), 可安全过 NewStringUTF。
JNIEXPORT jstring JNICALL Java_com_magtile_studio_MagTileNative_getTutorialSteps(
    JNIEnv* env, jobject /*thiz*/, jstring data_dir, jstring model_id) {
    auto& ctx = context();
    std::lock_guard<std::mutex> lock(ctx.mutex);
    try {
        const std::string id = toUtf8(env, model_id);
        const std::vector<magtile::core::ModelCatalogEntry> entries =
            magtile::core::loadModelCatalog(toUtf8(env, data_dir));
        const magtile::core::ModelCatalogEntry* found = nullptr;
        for (const auto& entry : entries) {
            if (entry.id == id) {
                found = &entry;
                break;
            }
        }
        if (found == nullptr) {
            const nlohmann::json error = {
                {"error", "错误: 模型 " + id + " 不在模型库目录中"}};
            return toJString(env, error.dump());
        }
        const magtile::core::ModelDefinition model =
            magtile::core::loadModelDefinition(found->file);

        nlohmann::json steps = nlohmann::json::array();
        int pieces_total = 0;
        for (const magtile::core::BuildStep& step : model.steps) {
            const int pieces_added = static_cast<int>(step.tiles_to_add.size());
            pieces_total += pieces_added;
            steps.push_back({
                {"step_number", step.step_number},
                {"description", step.description},
                {"tip", step.tip},
                {"pieces_added", pieces_added},
                {"pieces_total", pieces_total},
            });
        }
        const nlohmann::json root = {
            {"model_id", model.id},
            {"name", model.name},
            {"step_count", static_cast<int>(model.steps.size())},
            {"total_pieces", model.total_pieces},
            {"steps", std::move(steps)},
        };
        return toJString(env, root.dump());
    } catch (const std::exception& e) {
        MAGTILE_LOGE("getTutorialSteps 失败: %s", e.what());
        const nlohmann::json error = {{"error", std::string("错误: ") + e.what()}};
        return toJString(env, error.dump());
    }
}

/// 存档中该模型的当前步 (断点续搭入口): 无记录 / 存档未打开 / 读取
/// 失败一律返回 0 (从头开始, 温和降级不报错)。已完成模型的存档值
/// 为总步数 (桌面完成链路推到最后一步), Kotlin 侧据此进入完成态。
JNIEXPORT jint JNICALL Java_com_magtile_studio_MagTileNative_savedTutorialStep(
    JNIEnv* env, jobject /*thiz*/, jstring model_id) {
    auto& ctx = context();
    std::lock_guard<std::mutex> lock(ctx.mutex);
    if (!ctx.store.has_value()) {
        return 0;
    }
    try {
        const auto progress = ctx.store->loadProgress(toUtf8(env, model_id));
        return progress.has_value() ? std::max(progress->current_step, 0) : 0;
    } catch (const magtile::progress::ProgressError& e) {
        MAGTILE_LOGE("savedTutorialStep 读取失败: %s", e.what());
        return 0;
    }
}

/// 写教程进度到存档 (与桌面 Qt TutorialViewport::flushProgress /
/// applyStepChange 同一口径, 同一份 SQLite schema):
///   - saveProgress(modelId, step, playSeconds): step 为已完成到第几步,
///     playSeconds 为本次新增游玩秒数 (存储层累加, 只增不减);
///   - 走到最后一步 (step >= stepCount 且 stepCount > 0) 时记完成
///     (首次完成时刻不覆盖) + 解锁首搭成就 first_model_completed
///     (与桌面 GL/Qt 完成链路同名同口径)。
/// 存档未打开 / 写入失败返回 false (Kotlin 侧不打断搭建, 进度仍在
/// 内存中 —— P3 零挫败, 与桌面同策略)。
JNIEXPORT jboolean JNICALL Java_com_magtile_studio_MagTileNative_saveTutorialStep(
    JNIEnv* env, jobject /*thiz*/, jstring model_id, jint step, jint step_count,
    jlong play_seconds) {
    auto& ctx = context();
    std::lock_guard<std::mutex> lock(ctx.mutex);
    if (!ctx.store.has_value()) {
        return JNI_FALSE;
    }
    try {
        const std::string id = toUtf8(env, model_id);
        ctx.store->saveProgress(id, std::max(static_cast<int>(step), 0),
                                std::max(static_cast<std::int64_t>(play_seconds),
                                         std::int64_t{0}));
        if (step_count > 0 && step >= step_count) {
            ctx.store->markCompleted(id);
            if (!ctx.store->isAchievementUnlocked("first_model_completed")) {
                ctx.store->unlockAchievement("first_model_completed");
            }
        }
        return JNI_TRUE;
    } catch (const std::exception& e) {
        MAGTILE_LOGE("saveTutorialStep 失败: %s", e.what());
        return JNI_FALSE;
    }
}

// =============================================================
// 家长门 (UI_UX_SPEC.md §9, 绑定 com.magtile.studio.MagTileNative)
// 直接复用 core::ParentGate —— 与桌面 GL/Qt 完全同一状态机 (乘法题
// 生成 / 中文大写数字验证 / 3 次答错 60 秒冷却 / 15 分钟内存会话)。
// 会话与冷却只存内存, 永不落盘, 与 ProgressStore 无关。
// =============================================================

/// 进门 (无有效会话时调用): 出一道新的乘法题 (每次进门新题防背题,
/// 与桌面 ParentGateBackend::openGate 同口径), 返回门状态 JSON:
///   {"question":"叁 × 柒 = ?","attempts_remaining":N,
///    "cooldown_seconds":N,"session_active":bool}
/// 仍处于上一轮冷却期时 cooldown_seconds > 0, Kotlin 侧据此直接
/// 渲染温和的 "休息一下" 界面 (倒计时结束后再显示题面)。
JNIEXPORT jstring JNICALL Java_com_magtile_studio_MagTileNative_parentGateOpenJson(
    JNIEnv* env, jobject /*thiz*/) {
    auto& ctx = gateContext();
    std::lock_guard<std::mutex> lock(ctx.mutex);
    ctx.gate.newChallenge();
    return toJString(env, gateStateJson(ctx.gate).dump());
}

/// 提交答案 (中文大写数字, 如 "贰拾壹"; 核心状态机接受 "壹拾贰" /
/// 口语省略形 "拾贰" 变体并忽略前后空白), 返回结果 JSON:
///   {"result":"passed"|"wrong"|"cooling",
///    "attempts_remaining":N,"cooldown_seconds":N,"session_active":bool}
///   - passed:  答对, 15 分钟家长会话已开启 (kDefaultSessionDuration);
///   - wrong:   答错 (尚未触发冷却), Kotlin 侧温和提示 "再试一次吧";
///   - cooling: 冷却期内 (含触发冷却的那次答错), 温和提示稍后再试。
JNIEXPORT jstring JNICALL Java_com_magtile_studio_MagTileNative_parentGateSubmitJson(
    JNIEnv* env, jobject /*thiz*/, jstring answer) {
    auto& ctx = gateContext();
    std::lock_guard<std::mutex> lock(ctx.mutex);
    const char* result = "wrong";
    switch (ctx.gate.submitAnswer(toUtf8(env, answer))) {
        case magtile::core::ParentGateResult::Passed:
            result = "passed";
            break;
        case magtile::core::ParentGateResult::WrongAnswer:
            result = "wrong";
            break;
        case magtile::core::ParentGateResult::CoolingDown:
            result = "cooling";
            break;
    }
    nlohmann::json root = gateStateJson(ctx.gate);
    root["result"] = result;
    return toJString(env, root.dump());
}

/// 家长会话是否仍有效: true = 15 分钟守卫期内, 免重复验证直接进
/// 家长操作 (与桌面 Qt 会话守卫同策略; 时长读 core::ParentGate::
/// kDefaultSessionDuration, 会话只存内存, 重启即失效)。
JNIEXPORT jboolean JNICALL Java_com_magtile_studio_MagTileNative_parentGateSessionActive(
    JNIEnv* /*env*/, jobject /*thiz*/) {
    auto& ctx = gateContext();
    std::lock_guard<std::mutex> lock(ctx.mutex);
    return ctx.gate.sessionActive() ? JNI_TRUE : JNI_FALSE;
}

}  // extern "C"
