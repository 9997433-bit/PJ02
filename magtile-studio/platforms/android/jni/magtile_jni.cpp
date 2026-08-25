// =============================================================
// MagTile Studio - Android JNI 包装层
//
// 向 Kotlin 侧 (com.magtile.studio.MainActivity) 暴露四个入口:
//   loadCatalog(catalogPath)      -> 加载磁力片形状目录, 返回形状数
//   listModels(dataDir)           -> 模型库目录 (卡片元数据), 返回 JSON 字符串
//   validateModel(jsonPath)       -> 加载模型并跑完整物理校验, 返回中文摘要
//   getTutorialStepCount()        -> 最近一次成功加载模型的教程步骤数
//
// 说明: 这是打通 "Kotlin -> JNI -> magtile_core" 链路的最小实现,
// 渲染循环 (GLSurfaceView / Vulkan) 与逐步教程交互接口后续在此扩展。
// =============================================================

#include <jni.h>

#include <exception>
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
#include "magtile/physics/physics_validator.hpp"
#include "magtile/tutorial/tutorial_engine.hpp"

namespace {

/// 进程级原生上下文。脚手架阶段以单例承载目录与最近加载的模型;
/// 接入渲染/多文档后再演进为按会话句柄管理。
struct NativeContext {
    std::mutex mutex;
    std::optional<magtile::core::TileCatalog> catalog;
    std::optional<magtile::core::ModelDefinition> model;
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
///   成功: {"models":[{"id","name","name_en","description","difficulty",
///                     "total_pieces","step_count","theme","file"}, ...]}
///   失败: {"error":"中文错误信息"}
/// 只含卡片展示元数据, 不加载几何与教程步骤 (模型库秒开);
/// file 为模型 JSON 绝对路径, 可直接传给 validateModel()。
JNIEXPORT jstring JNICALL Java_com_magtile_studio_MainActivity_listModels(
    JNIEnv* env, jobject /*thiz*/, jstring data_dir) {
    try {
        const std::vector<magtile::core::ModelCatalogEntry> entries =
            magtile::core::loadModelCatalog(toUtf8(env, data_dir));

        nlohmann::json models = nlohmann::json::array();
        for (const auto& entry : entries) {
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
            });
        }
        const nlohmann::json root = {{"models", std::move(models)}};
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

}  // extern "C"
