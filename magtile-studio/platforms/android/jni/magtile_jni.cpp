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
//
// 说明: 渲染循环 (GLSurfaceView / Vulkan) 与逐步教程交互接口后续在此扩展。
// =============================================================

#include <jni.h>

#include <algorithm>
#include <exception>
#include <map>
#include <mutex>
#include <optional>
#include <sstream>
#include <string>
#include <utility>

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
#include "magtile/core/model_definition.hpp"
#include "magtile/core/tile_catalog.hpp"
#include "magtile/core/types.hpp"
#include "magtile/physics/physics_validator.hpp"
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
///                     "bom_known","core9_only","can_build","missing_total"},
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

}  // extern "C"
