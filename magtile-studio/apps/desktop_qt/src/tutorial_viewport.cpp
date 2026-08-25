#include "tutorial_viewport.hpp"

#include <QLineF>
#include <QMouseEvent>
#include <QOpenGLContext>
#include <QOpenGLFramebufferObject>
#include <QOpenGLFramebufferObjectFormat>
#include <QTouchEvent>
#include <QWheelEvent>
#include <QtQuick/qquickopenglutils.h>
#include <algorithm>
#include <cmath>
#include <cstdio>
#include <exception>
#include <unordered_set>
#include <utility>
#include <vector>

#include "magtile/core/json_io.hpp"
#include "magtile/core/model_definition.hpp"
#include "magtile/physics/geometry.hpp"
#include "magtile/render/gl_scene_renderer.hpp"

namespace magtile::qtui {

namespace {

/// 轨道相机旋转手感 (与 GL 版 kRotateSpeedDegPerPx 一致)。
constexpr double kRotateSpeedDegPerPx = 0.32;

/// 捏合缩放的最小指距 (px): 双指过近时指距比值噪声过大 (微小抖动
/// 被放大成猛烈缩放), 低于该值的帧只重定基准不缩放。
constexpr double kMinPinchSpreadPx = 8.0;

/// GL 入口解析: Qt 场景图上下文 (render 线程调用, 上下文已 current)。
render::GlSceneRenderer::GlProc resolveGlProc(const char* name) {
    QOpenGLContext* context = QOpenGLContext::currentContext();
    if (context == nullptr) return nullptr;
    return reinterpret_cast<render::GlSceneRenderer::GlProc>(context->getProcAddress(name));
}

}  // namespace

// =============================================================
// 渲染线程侧: FBO 渲染器
// =============================================================
class TutorialFboRenderer final : public QQuickFramebufferObject::Renderer {
public:
    TutorialFboRenderer() { animation_clock_.start(); }

    ~TutorialFboRenderer() override {
        // Qt 在场景图上下文 current 时析构渲染器, 可安全回收 GL 资源
        scene_.shutdown();
    }

    QOpenGLFramebufferObject* createFramebufferObject(const QSize& size) override {
        QOpenGLFramebufferObjectFormat format;
        format.setAttachment(QOpenGLFramebufferObject::CombinedDepthStencil);
        format.setSamples(4);  // 与 GLFW 版 GLFW_SAMPLES 4 一致
        return new QOpenGLFramebufferObject(size, format);
    }

    /// GUI 线程被阻塞期间拷贝场景快照 (相机每帧拷, 磁力片按代数拷)。
    void synchronize(QQuickFramebufferObject* item) override {
        auto* viewport = static_cast<TutorialViewport*>(item);
        camera_ = viewport->camera_.toCamera();
        if (tiles_version_ != viewport->scene_version_) {
            tiles_version_ = viewport->scene_version_;
            tiles_ = viewport->scene_tiles_;                // 实例按值拷贝
            tile_catalog_keepalive_ = viewport->tile_catalog_;  // 片型目录保活
            animate_ = std::any_of(tiles_.begin(), tiles_.end(),
                                   [](const auto& t) { return t.just_placed; });
        }
    }

    void render() override {
        if (!scene_failed_ && !scene_.ready()) {
            if (!scene_.initialize(&resolveGlProc)) {
                scene_failed_ = true;
                std::fprintf(stderr,
                             "[qt-viewport] 3D 场景初始化失败 (场景图是否为 OpenGL 后端?)\n");
            }
        }
        const QOpenGLFramebufferObject* fbo = framebufferObject();
        if (!scene_failed_ && fbo != nullptr) {
            scene_.begin(camera_, fbo->width(), fbo->height());
            for (const TutorialViewport::SceneTile& tile : tiles_) {
                if (tile.shape == nullptr) continue;
                render::RenderTile rt;
                rt.instance = &tile.instance;
                rt.highlighted = tile.highlighted;
                rt.ghost = tile.ghost;
                rt.just_placed = tile.just_placed;
                scene_.submitTile(rt, *tile.shape);
            }
            scene_.end(static_cast<double>(animation_clock_.elapsed()) / 1000.0);
        }
        // 归还 GL 状态, 避免污染 Qt Quick 场景图后续绘制
        QQuickOpenGLUtils::resetOpenGLState();
        // 呼吸高亮动画: 有 "本步新增" 片时持续重绘 (随显示器刷新率节流)
        if (animate_ && !scene_failed_) update();
    }

private:
    render::GlSceneRenderer scene_;
    bool scene_failed_ = false;
    render::Camera camera_;
    std::vector<TutorialViewport::SceneTile> tiles_;
    std::shared_ptr<core::TileCatalog> tile_catalog_keepalive_;
    quint64 tiles_version_ = ~quint64{0};
    bool animate_ = false;
    QElapsedTimer animation_clock_;
};

// =============================================================
// GUI 线程侧: 教程会话 + 交互
// =============================================================

TutorialViewport::TutorialViewport(QQuickItem* parent) : QQuickFramebufferObject(parent) {
    setAcceptedMouseButtons(Qt::LeftButton | Qt::RightButton | Qt::MiddleButton);
    setAcceptTouchEvents(true);  // 触屏手势 (单指旋转/双指捏合缩放/双指平移)
    setMirrorVertically(true);  // GL 原点在左下, Qt 场景图纹理原点在左上
}

TutorialViewport::~TutorialViewport() {
    finishSession();  // 退出兜底存档 (正常路径 TutorialPage 已显式调用)
}

QQuickFramebufferObject::Renderer* TutorialViewport::createRenderer() const {
    return new TutorialFboRenderer();
}

void TutorialViewport::setModelFile(const QString& path) {
    if (model_file_ == path) return;
    model_file_ = path;
    emit sourceChanged();
    if (isComponentComplete()) startSession();
}

void TutorialViewport::setDataDir(const QString& path) {
    if (data_dir_ == path) return;
    data_dir_ = path;
    emit sourceChanged();
}

void TutorialViewport::setDbFile(const QString& path) {
    if (db_file_ == path) return;
    db_file_ = path;
    emit sourceChanged();
}

void TutorialViewport::setResumeStep(int step) {
    if (resume_step_ == step) return;
    resume_step_ = step;
    emit sourceChanged();
}

void TutorialViewport::setPreviewMode(bool preview) {
    if (preview_mode_ == preview) return;
    preview_mode_ = preview;
    emit sourceChanged();
    if (isComponentComplete()) startSession();
}

void TutorialViewport::componentComplete() {
    QQuickFramebufferObject::componentComplete();
    startSession();
}

// ---- 会话生命周期 ------------------------------------------------

void TutorialViewport::startSession() {
    engine_.reset();
    store_.reset();
    tile_catalog_.reset();
    scene_tiles_.clear();
    ++scene_version_;
    session_flushed_ = false;
    last_saved_step_ = -1;
    // 温和降级 (P3 零挫败): 打不开只说 "正在准备", 永不弹 "失败"
    status_text_ = preview_mode_
                       ? QStringLiteral("3D 预览正在准备中")
                       : QStringLiteral("这个教程正在准备中, 先去挑别的模型试试吧");

    if (model_file_.isEmpty() || data_dir_.isEmpty()) {
        emit stateChanged();
        update();
        return;
    }

    try {
        auto catalog = std::make_shared<core::TileCatalog>(core::loadTileCatalog(
            std::filesystem::path(data_dir_.toStdString()) / "tile_catalog.json"));
        core::ModelDefinition model =
            core::loadModelDefinition(std::filesystem::path(model_file_.toStdString()));

        // 内容有问题的模型不进教程 (与 GL 版一致), 具体问题走质检工具;
        // 只读预览只画 final_assembly, 步骤一致性问题不阻断成品展示
        const auto problems = tutorial::TutorialEngine::checkConsistency(model);
        if (!problems.empty()) {
            for (const auto& problem : problems) {
                std::fprintf(stderr, "[qt-viewport] 步骤一致性: %s\n", problem.c_str());
            }
            if (!preview_mode_) {
                emit stateChanged();
                update();
                return;
            }
        }

        tile_catalog_ = std::move(catalog);
        engine_ = std::make_unique<tutorial::TutorialEngine>(std::move(model));
    } catch (const std::exception& error) {
        std::fprintf(stderr, "[qt-viewport] 教程加载失败: %s\n", error.what());
        emit stateChanged();
        update();
        return;
    }

    // 断点续搭: 0 = 从头 -> 第 1 步; 越界由 goToStep 拒绝后回退第 1 步;
    // 只读预览直接跳到最后一步 (成品全貌)
    const int start_step = preview_mode_
                               ? engine_->stepCount()
                               : std::clamp(std::max(resume_step_, 1), 1, engine_->stepCount());
    if (!engine_->goToStep(start_step)) engine_->nextStep();

    // 初始取景: 最终成品的包围盒 (与 GL 版 frameModelBounds 一致)
    core::Vec3 bb_min{1e9, 1e9, 1e9}, bb_max{-1e9, -1e9, -1e9};
    for (const auto& tile : engine_->model().final_assembly) {
        const auto world = physics::transformTile(tile, tile_catalog_->get(tile.type));
        for (const auto& v : world.vertices) {
            bb_min = {std::min(bb_min.x, v.x), std::min(bb_min.y, v.y), std::min(bb_min.z, v.z)};
            bb_max = {std::max(bb_max.x, v.x), std::max(bb_max.y, v.y), std::max(bb_max.z, v.z)};
        }
    }
    camera_.frameBounds(bb_min, bb_max);

    // 进度存档: 与 CLI/GL 版共用同一 SQLite (多连接安全);
    // 打不开只影响存档, 教程照常可玩; 只读预览纯看不写, 不建档
    if (!preview_mode_ && !db_file_.isEmpty()) {
        try {
            store_ = std::make_unique<progress::ProgressStore>(
                std::filesystem::path(db_file_.toStdString()));
        } catch (const progress::ProgressError&) {
            store_.reset();
        }
    }
    flush_clock_.start();
    last_saved_step_ = engine_->currentStepNumber();
    flushProgress();  // 会话开始即建档, 模型库立刻显示 "进行中"

    status_text_.clear();
    rebuildSceneTiles();
    emit stateChanged();
    update();
}

void TutorialViewport::finishSession() {
    if (session_flushed_ || engine_ == nullptr) return;
    flushProgress();
    session_flushed_ = true;
}

void TutorialViewport::flushProgress() {
    if (store_ == nullptr || engine_ == nullptr) return;
    const auto seconds = flush_clock_.isValid() ? flush_clock_.elapsed() / 1000 : 0;
    try {
        store_->saveProgress(engine_->model().id, engine_->currentStepNumber(),
                             static_cast<std::int64_t>(seconds));
        flush_clock_.restart();
        last_saved_step_ = engine_->currentStepNumber();
    } catch (const progress::ProgressError&) {
        // 存档写入失败只降级 (进度仍在内存中), 不打断孩子搭建
    }
}

// ---- 步骤导航 ------------------------------------------------------

void TutorialViewport::nextStep() {
    if (engine_ == nullptr || !engine_->nextStep()) return;
    applyStepChange();
}

void TutorialViewport::previousStep() {
    if (engine_ == nullptr || !engine_->previousStep()) return;
    applyStepChange();
}

void TutorialViewport::restart() {
    if (engine_ == nullptr || engine_->currentStepNumber() == 0) return;
    engine_->reset();
    applyStepChange();
}

void TutorialViewport::resetView() {
    camera_.resetView();
    update();
}

void TutorialViewport::applyStepChange() {
    session_flushed_ = false;
    rebuildSceneTiles();

    // 步骤变化 -> 落盘; 走到最后一步 -> 记完成 + 首个完成成就
    if (store_ != nullptr && engine_->currentStepNumber() != last_saved_step_) {
        flushProgress();
        if (engine_->stepCount() > 0 && engine_->currentStepNumber() >= engine_->stepCount()) {
            try {
                store_->markCompleted(engine_->model().id);
                if (!store_->isAchievementUnlocked("first_model_completed")) {
                    store_->unlockAchievement("first_model_completed");
                }
            } catch (const progress::ProgressError&) {
                // 完成标记失败不打断庆祝 (下次进入仍可重试)
            }
        }
    }
    emit stateChanged();
    update();
}

void TutorialViewport::rebuildSceneTiles() {
    scene_tiles_.clear();
    ++scene_version_;
    if (engine_ == nullptr || tile_catalog_ == nullptr) return;

    // 只读预览不标注步骤状态 (空集合 -> 全部实体片, 无 ghost/高亮/呼吸)
    std::unordered_set<const core::TileInstance*> placed, added, referenced;
    if (!preview_mode_) {
        for (const auto* tile : engine_->visibleTiles()) placed.insert(tile);
        for (const auto* tile : engine_->tilesAddedThisStep()) added.insert(tile);
        for (const auto* tile : engine_->highlightTiles()) referenced.insert(tile);
    }

    scene_tiles_.reserve(engine_->model().final_assembly.size());
    for (const auto& tile : engine_->model().final_assembly) {
        SceneTile scene_tile;
        scene_tile.instance = tile;
        scene_tile.shape = &tile_catalog_->get(tile.type);
        scene_tile.just_placed = added.count(&tile) > 0;
        scene_tile.ghost = preview_mode_
                               ? false
                               : (!scene_tile.just_placed && placed.count(&tile) == 0);
        scene_tile.highlighted = referenced.count(&tile) > 0;
        scene_tiles_.push_back(std::move(scene_tile));
    }
}

// ---- 会话状态读取 ---------------------------------------------------

QString TutorialViewport::modelName() const {
    return engine_ != nullptr ? QString::fromStdString(engine_->model().name) : QString();
}

int TutorialViewport::stepNumber() const {
    return engine_ != nullptr ? engine_->currentStepNumber() : 0;
}

int TutorialViewport::stepCount() const {
    return engine_ != nullptr ? engine_->stepCount() : 0;
}

QString TutorialViewport::stepDescription() const {
    if (engine_ == nullptr) return {};
    if (const core::BuildStep* step = engine_->currentStep(); step != nullptr) {
        return QString::fromStdString(step->description);
    }
    return QStringLiteral("转一转视角, 先看看搭好的样子, 然后点「下一步」开始搭!");
}

QString TutorialViewport::stepTip() const {
    if (engine_ == nullptr) return {};
    if (const core::BuildStep* step = engine_->currentStep(); step != nullptr) {
        return QString::fromStdString(step->tip);
    }
    return {};
}

double TutorialViewport::progress() const {
    return engine_ != nullptr ? engine_->progress() : 0.0;
}

int TutorialViewport::tilesPlaced() const {
    return engine_ != nullptr ? static_cast<int>(engine_->visibleTiles().size()) : 0;
}

int TutorialViewport::tilesTotal() const {
    return engine_ != nullptr ? static_cast<int>(engine_->model().final_assembly.size()) : 0;
}

bool TutorialViewport::finished() const {
    return engine_ != nullptr && engine_->isFinished();
}

// ---- 轨道相机交互 (拖动旋转 / 右键·中键平移 / 滚轮缩放) ---------------

void TutorialViewport::mousePressEvent(QMouseEvent* event) {
    last_mouse_pos_ = event->position();
    event->accept();
}

void TutorialViewport::mouseMoveEvent(QMouseEvent* event) {
    const QPointF pos = event->position();
    const double dx = pos.x() - last_mouse_pos_.x();
    const double dy = pos.y() - last_mouse_pos_.y();
    last_mouse_pos_ = pos;

    if (event->buttons() & Qt::LeftButton) {
        camera_.rotate(-dx * kRotateSpeedDegPerPx, -dy * kRotateSpeedDegPerPx);
    } else if (event->buttons() & (Qt::RightButton | Qt::MiddleButton)) {
        camera_.pan(dx, dy, std::max(1, static_cast<int>(height())));
    }
    event->accept();
    update();
}

void TutorialViewport::wheelEvent(QWheelEvent* event) {
    const double steps = event->angleDelta().y() / 120.0;
    if (steps != 0.0) {
        camera_.zoom(steps);
        update();
    }
    event->accept();
}

// ---- 触屏手势 (单指旋转 / 双指捏合缩放 / 双指平移) --------------------
//
// 与鼠标交互并存: 本视口 setAcceptTouchEvents(true) 后触点在此消费,
// Qt 不再为这些触点合成鼠标事件 (不会与左键拖动重复驱动相机), 无触屏
// 设备根本走不到本函数, 桌面三键 + 滚轮操作完全不受影响。手势直接改
// 相机并请求重绘, 不经任何动画系统 —— 「减少动态效果」开关下照常可用
// (手势是输入不是装饰动画, UI_UX_SPEC §4.7)。previewMode 详情页预览
// 复用同一视口, 手势自动同样生效。
void TutorialViewport::touchEvent(QTouchEvent* event) {
    if (event->type() == QEvent::TouchCancel) {
        touch_point_count_ = 0;
        event->accept();
        return;
    }

    // 只统计仍按住的触点 (已抬起的不参与手势); 三指及以上取前两指
    std::vector<QPointF> active;
    active.reserve(static_cast<size_t>(event->points().size()));
    for (const QEventPoint& point : event->points()) {
        if (point.state() != QEventPoint::Released) active.push_back(point.position());
    }

    // 手指数变化 (落下/抬起第二指、3 指与 2 指互换) 的当帧只重定基准:
    // 基准点语义随手指数切换 (单指位置 <-> 双指中点), 跨口径求差会跳变
    const bool count_stable = static_cast<int>(active.size()) == touch_point_count_;

    if (active.size() == 1) {
        // 单指拖动 = 轨道旋转 (与鼠标左键拖动同口径同灵敏度)
        const QPointF pos = active.front();
        if (count_stable) {
            const double dx = pos.x() - last_touch_anchor_.x();
            const double dy = pos.y() - last_touch_anchor_.y();
            camera_.rotate(-dx * kRotateSpeedDegPerPx, -dy * kRotateSpeedDegPerPx);
            update();
        }
        last_touch_anchor_ = pos;
    } else if (active.size() >= 2) {
        const QPointF mid = (active[0] + active[1]) * 0.5;
        const double spread = QLineF(active[0], active[1]).length();
        if (count_stable) {
            // 双指捏合 = 缩放: 指距比经对数换算成等效滚轮格数, 与滚轮
            // 共用 OrbitCamera::kZoomStepFactor (12%/格) 同一缩放口径;
            // 净效果是相机距离随指距反比变化 —— 指距张大一倍, 成品
            // 视觉上恰好放大一倍, 缩放跟手不窜
            if (spread > kMinPinchSpreadPx && last_touch_spread_ > kMinPinchSpreadPx) {
                camera_.zoom(std::log(spread / last_touch_spread_) /
                             std::log(1.0 / render::OrbitCamera::kZoomStepFactor));
            }
            // 双指同向滑动 = 平移 (中点位移, 与鼠标右键拖动同口径)
            camera_.pan(mid.x() - last_touch_anchor_.x(), mid.y() - last_touch_anchor_.y(),
                        std::max(1, static_cast<int>(height())));
            update();
        }
        last_touch_anchor_ = mid;
        last_touch_spread_ = spread;
    }
    touch_point_count_ = static_cast<int>(active.size());

    // 显式收下事件 (含全部触点): TouchBegin 被接受本视口才能成为触点
    // 的独占抓取者, 后续 TouchUpdate/TouchEnd 才会继续送达
    event->accept();
}

void TutorialViewport::touchUngrabEvent() {
    // 触点抓取被夺走 (如手势中页面切换): 清基准, 下次触摸重新开始
    touch_point_count_ = 0;
    QQuickFramebufferObject::touchUngrabEvent();
}

}  // namespace magtile::qtui
