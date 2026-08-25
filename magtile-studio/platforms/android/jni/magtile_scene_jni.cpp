// =============================================================
// MagTile Studio - Android 3D 教程视口 JNI 桥
// (绑定 com.magtile.studio.TutorialSceneNative)
//
// 复用与桌面 GLFW/ImGui、Qt FBO 教程视口完全同一份场景渲染器
// render::GlSceneRenderer (magtile_render_scene, 着色器版本头按
// 上下文自动切到 300 es) 与 tutorial::TutorialEngine 步骤语义:
// 当前步新增片橙色描边 + 呼吸动画, 未放片 ghost 淡化轮廓 ——
// 与桌面三端同一口径 (docs/PLATFORM_ARCHITECTURE.md 渲染矩阵)。
//
// 线程模型 (GLSurfaceView 双线程):
//   - GL 渲染线程: surfaceCreated / drawFrame (GL 资源只在此线程);
//   - 主线程 / 工作线程: loadScene / setStep / 手势 (只改会话状态)。
//   会话状态 (引擎 / 相机 / 场景片快照) 由 SceneSession.mutex 保护;
//   GL 资源 (着色器 / VBO) 不进会话, 仅渲染线程可见, 无需加锁。
//
// GL 入口解析: JNI 库链接 libGLESv3.so, GLES3 核心入口都是真实
// 导出符号, dlsym(RTLD_DEFAULT) 即可解析 (与 GLFW 的
// glfwGetProcAddress / Qt 的 getProcAddress 同一角色), 不依赖 EGL
// 扩展查询。上下文丢失恢复 (Home 后返回等): surfaceCreated 重建
// GlSceneRenderer 对象 —— 旧对象析构只回收堆内存, 不碰已随旧上下
// 文销毁的 GL 资源 (GlSceneRenderer 析构注释约定的路径)。
// =============================================================

#include <jni.h>

#include <dlfcn.h>

#include <algorithm>
#include <cmath>
#include <cstdio>
#include <exception>
#include <filesystem>
#include <memory>
#include <mutex>
#include <optional>
#include <string>
#include <unordered_set>
#include <utility>
#include <vector>

#if defined(__ANDROID__)
#include <android/log.h>
#define MAGTILE_SCENE_LOGE(...) \
    __android_log_print(ANDROID_LOG_ERROR, "MagTileScene", __VA_ARGS__)
#define MAGTILE_SCENE_LOGW(...) \
    __android_log_print(ANDROID_LOG_WARN, "MagTileScene", __VA_ARGS__)
#else
#define MAGTILE_SCENE_LOGE(...) ((void)0)
#define MAGTILE_SCENE_LOGW(...) ((void)0)
#endif

#include "magtile/core/json_io.hpp"
#include "magtile/core/model_catalog.hpp"
#include "magtile/core/model_definition.hpp"
#include "magtile/core/tile_catalog.hpp"
#include "magtile/physics/geometry.hpp"
#include "magtile/render/gl_scene_renderer.hpp"
#include "magtile/render/orbit_camera.hpp"
#include "magtile/tutorial/tutorial_engine.hpp"

namespace {

/// 轨道相机旋转手感 (deg/逻辑像素): 与 Qt 教程视口 / GL 版
/// kRotateSpeedDegPerPx 同一数值; Kotlin 侧把触点位移换算成 dp
/// (密度无关) 后传入, 不同屏幕密度下手感一致。
constexpr double kRotateSpeedDegPerPx = 0.32;

std::string sceneToUtf8(JNIEnv* env, jstring value) {
    if (value == nullptr) return {};
    const char* chars = env->GetStringUTFChars(value, nullptr);
    std::string result = (chars != nullptr) ? chars : "";
    if (chars != nullptr) env->ReleaseStringUTFChars(value, chars);
    return result;
}

/// 教程渲染会话 (进程级单例, 同一时刻只有一个教程页在前台)。
struct SceneSession {
    std::mutex mutex;
    std::optional<magtile::core::TileCatalog> catalog;
    std::unique_ptr<magtile::tutorial::TutorialEngine> engine;
    magtile::render::OrbitCamera camera;

    /// 场景片快照 (与 Qt TutorialViewport::SceneTile 同构): 实例按值
    /// 保存, shape 指向本会话的 catalog (同生命周期)。
    struct SceneTile {
        magtile::core::TileInstance instance;
        const magtile::core::TileShape* shape = nullptr;
        bool highlighted = false;
        bool ghost = false;
        bool just_placed = false;
    };
    std::vector<SceneTile> tiles;
};

SceneSession& sceneSession() {
    static SceneSession session;
    return session;
}

/// 按当前步重建场景片快照 (调用方需已持有 session.mutex; 口径与
/// Qt TutorialViewport::rebuildSceneTiles 完全一致): 本步新增
/// just_placed (橙色描边 + 呼吸), 未放片 ghost (淡化轮廓提示),
/// 参照片 highlighted (琥珀描边)。
void rebuildSceneTiles(SceneSession& session) {
    session.tiles.clear();
    if (session.engine == nullptr || !session.catalog.has_value()) return;

    std::unordered_set<const magtile::core::TileInstance*> placed, added, referenced;
    for (const auto* tile : session.engine->visibleTiles()) placed.insert(tile);
    for (const auto* tile : session.engine->tilesAddedThisStep()) added.insert(tile);
    for (const auto* tile : session.engine->highlightTiles()) referenced.insert(tile);

    const auto& assembly = session.engine->model().final_assembly;
    session.tiles.reserve(assembly.size());
    for (const auto& tile : assembly) {
        SceneSession::SceneTile scene_tile;
        scene_tile.instance = tile;
        scene_tile.shape = &session.catalog->get(tile.type);
        scene_tile.just_placed = added.count(&tile) > 0;
        scene_tile.ghost = !scene_tile.just_placed && placed.count(&tile) == 0;
        scene_tile.highlighted = referenced.count(&tile) > 0;
        session.tiles.push_back(std::move(scene_tile));
    }
}

// ---- GL 渲染线程侧状态 (只在 GLSurfaceView 渲染线程访问, 不加锁) ----

std::unique_ptr<magtile::render::GlSceneRenderer> g_renderer;

/// GL 入口解析 (dlsym 查已链接的 libGLESv3 导出符号)。
magtile::render::GlSceneRenderer::GlProc resolveGlProc(const char* name) {
    return reinterpret_cast<magtile::render::GlSceneRenderer::GlProc>(
        ::dlsym(RTLD_DEFAULT, name));
}

}  // namespace

extern "C" {

// =============================================================
// 会话管理 (主线程 / 工作线程)
// =============================================================

/// 加载教程场景 (data_dir 为解包后的数据目录, model_id 经模型库目录
/// 解析到模型 JSON —— 与 getTutorialSteps 同一口径): 加载片型目录 +
/// 模型, 创建教程引擎, 按最终成品包围盒取景, 并跳到断点步
/// resume_step (0 = 从头 -> 第 1 步, 越界夹到 [1, stepCount])。
/// 返回教程步骤数; 失败 (文件问题 / 步骤一致性问题, 与桌面同策略
/// 不进 3D 教程) 返回 -1 并写 logcat, 视口温和降级为只画地面网格,
/// 文字分步照常可用 (P3 零挫败)。
JNIEXPORT jint JNICALL Java_com_magtile_studio_TutorialSceneNative_loadScene(
    JNIEnv* env, jobject /*thiz*/, jstring data_dir, jstring model_id, jint resume_step) {
    auto& session = sceneSession();
    std::lock_guard<std::mutex> lock(session.mutex);
    session.engine.reset();
    session.tiles.clear();
    session.catalog.reset();
    try {
        const std::filesystem::path dir(sceneToUtf8(env, data_dir));
        const std::string id = sceneToUtf8(env, model_id);

        // 模型文件经模型库目录解析 (只认仍在库中的模型)
        const std::filesystem::path* model_file = nullptr;
        const auto entries = magtile::core::loadModelCatalog(dir);
        for (const auto& entry : entries) {
            if (entry.id == id) {
                model_file = &entry.file;
                break;
            }
        }
        if (model_file == nullptr) {
            MAGTILE_SCENE_LOGE("loadScene: 模型 %s 不在模型库目录中", id.c_str());
            return -1;
        }

        auto catalog = magtile::core::loadTileCatalog(dir / "tile_catalog.json");
        magtile::core::ModelDefinition model =
            magtile::core::loadModelDefinition(*model_file);

        // 内容有问题的模型不进 3D 教程 (与桌面 GL/Qt 一致, 质检工具负责报告)
        const auto problems = magtile::tutorial::TutorialEngine::checkConsistency(model);
        if (!problems.empty()) {
            for (const auto& problem : problems) {
                MAGTILE_SCENE_LOGW("loadScene 步骤一致性: %s", problem.c_str());
            }
            return -1;
        }

        session.catalog = std::move(catalog);
        session.engine =
            std::make_unique<magtile::tutorial::TutorialEngine>(std::move(model));

        // 初始取景: 最终成品的包围盒 (与桌面 frameModelBounds 一致)
        magtile::core::Vec3 bb_min{1e9, 1e9, 1e9}, bb_max{-1e9, -1e9, -1e9};
        for (const auto& tile : session.engine->model().final_assembly) {
            const auto world =
                magtile::physics::transformTile(tile, session.catalog->get(tile.type));
            for (const auto& v : world.vertices) {
                bb_min = {std::min(bb_min.x, v.x), std::min(bb_min.y, v.y),
                          std::min(bb_min.z, v.z)};
                bb_max = {std::max(bb_max.x, v.x), std::max(bb_max.y, v.y),
                          std::max(bb_max.z, v.z)};
            }
        }
        session.camera = magtile::render::OrbitCamera();
        session.camera.frameBounds(bb_min, bb_max);

        // 断点续搭: 0 = 从头 -> 第 1 步; 越界由 goToStep 拒绝后回退第 1 步
        const int step_count = session.engine->stepCount();
        const int start_step =
            std::clamp(std::max(static_cast<int>(resume_step), 1), 1, step_count);
        if (!session.engine->goToStep(start_step)) session.engine->nextStep();
        rebuildSceneTiles(session);
        return static_cast<jint>(step_count);
    } catch (const std::exception& e) {
        MAGTILE_SCENE_LOGE("loadScene 失败: %s", e.what());
        session.engine.reset();
        session.tiles.clear();
        session.catalog.reset();
        return -1;
    }
}

/// 跳到指定步 (1..stepCount, 与 TutorialActivity 的 "当前展示步"
/// 同一语义: 第 n 步的新增片以描边 + 呼吸态显示): 越界夹到合法
/// 区间; 场景未加载时为空操作。
JNIEXPORT void JNICALL Java_com_magtile_studio_TutorialSceneNative_setStep(
    JNIEnv* /*env*/, jobject /*thiz*/, jint step) {
    auto& session = sceneSession();
    std::lock_guard<std::mutex> lock(session.mutex);
    if (session.engine == nullptr) return;
    const int clamped =
        std::clamp(static_cast<int>(step), 1, std::max(session.engine->stepCount(), 1));
    if (clamped == session.engine->currentStepNumber()) return;
    if (session.engine->goToStep(clamped)) rebuildSceneTiles(session);
}

/// 释放会话 (教程页销毁时调用): 只清引擎 / 片快照 / 目录; GL 资源
/// 随视口的 EGL 上下文由系统回收, 不在此处触碰。
JNIEXPORT void JNICALL Java_com_magtile_studio_TutorialSceneNative_releaseScene(
    JNIEnv* /*env*/, jobject /*thiz*/) {
    auto& session = sceneSession();
    std::lock_guard<std::mutex> lock(session.mutex);
    session.engine.reset();
    session.tiles.clear();
    session.catalog.reset();
}

// =============================================================
// 轨道相机手势 (与 Qt 教程视口同口径, 常量单一来源在原生层)
// =============================================================

/// 单指拖动 = 轨道旋转: dx/dy 为逻辑像素 (dp) 位移, 换算系数
/// kRotateSpeedDegPerPx 与桌面鼠标左键拖动 / Qt 触屏单指完全一致。
JNIEXPORT void JNICALL Java_com_magtile_studio_TutorialSceneNative_dragRotate(
    JNIEnv* /*env*/, jobject /*thiz*/, jdouble dx, jdouble dy) {
    auto& session = sceneSession();
    std::lock_guard<std::mutex> lock(session.mutex);
    session.camera.rotate(-dx * kRotateSpeedDegPerPx, -dy * kRotateSpeedDegPerPx);
}

/// 双指捏合 = 缩放: spread_ratio 为本帧指距 / 上帧指距, 经对数换算
/// 成等效滚轮格数 (OrbitCamera::kZoomStepFactor, 12%/格) —— 与 Qt
/// 触屏捏合 / 桌面滚轮共用同一缩放口径, 指距张大一倍成品恰好放大一倍。
JNIEXPORT void JNICALL Java_com_magtile_studio_TutorialSceneNative_pinchZoom(
    JNIEnv* /*env*/, jobject /*thiz*/, jdouble spread_ratio) {
    if (!(spread_ratio > 0.0)) return;  // 非法/NaN 比值直接忽略
    auto& session = sceneSession();
    std::lock_guard<std::mutex> lock(session.mutex);
    session.camera.zoom(std::log(spread_ratio) /
                        std::log(1.0 / magtile::render::OrbitCamera::kZoomStepFactor));
}

/// 双指同向滑动 = 平移: dx/dy 与 viewport_height 均为物理像素
/// (OrbitCamera::pan 按视口高换算世界距离, 只依赖两者比值,
/// 密度自然抵消), 口径与桌面右键拖动 / Qt 双指平移一致。
JNIEXPORT void JNICALL Java_com_magtile_studio_TutorialSceneNative_pan(
    JNIEnv* /*env*/, jobject /*thiz*/, jdouble dx, jdouble dy, jint viewport_height) {
    auto& session = sceneSession();
    std::lock_guard<std::mutex> lock(session.mutex);
    session.camera.pan(dx, dy, std::max(static_cast<int>(viewport_height), 1));
}

// =============================================================
// GL 渲染线程 (GLSurfaceView.Renderer 回调)
// =============================================================

/// 表面创建 / 上下文重建 (GL 线程, 上下文已 current): 重建场景渲染
/// 器并初始化 GL 资源。旧渲染器对象析构只回收堆内存 (旧上下文已随
/// 表面销毁, 其 GL 资源由驱动回收)。失败只写 logcat 并温和降级
/// (视口保持清屏色, 文字分步照常)。
JNIEXPORT void JNICALL Java_com_magtile_studio_TutorialSceneNative_surfaceCreated(
    JNIEnv* /*env*/, jobject /*thiz*/) {
    g_renderer = std::make_unique<magtile::render::GlSceneRenderer>();
    if (!g_renderer->initialize(&resolveGlProc)) {
        MAGTILE_SCENE_LOGE("3D 场景初始化失败 (GLES3 上下文?), 视口温和降级");
        g_renderer.reset();
    }
}

/// 绘制一帧 (GL 线程): 在会话锁内拷出相机并提交场景片。场景未加载
/// 时只画清屏 + 地面网格 (加载中的温和空态)。time_seconds 为单调
/// 递增秒数, 驱动本步新增片的呼吸动画 (与桌面同一实现)。
JNIEXPORT void JNICALL Java_com_magtile_studio_TutorialSceneNative_drawFrame(
    JNIEnv* /*env*/, jobject /*thiz*/, jint width, jint height, jdouble time_seconds) {
    if (g_renderer == nullptr || !g_renderer->ready()) return;
    if (width <= 0 || height <= 0) return;

    auto& session = sceneSession();
    std::lock_guard<std::mutex> lock(session.mutex);
    g_renderer->begin(session.camera.toCamera(), width, height);
    for (const SceneSession::SceneTile& tile : session.tiles) {
        if (tile.shape == nullptr) continue;
        magtile::render::RenderTile rt;
        rt.instance = &tile.instance;
        rt.highlighted = tile.highlighted;
        rt.ghost = tile.ghost;
        rt.just_placed = tile.just_placed;
        g_renderer->submitTile(rt, *tile.shape);
    }
    g_renderer->end(time_seconds);
}

}  // extern "C"
