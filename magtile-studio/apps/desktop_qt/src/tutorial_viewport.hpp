#pragma once

// =============================================================
// MagTile Studio (Qt) - 3D 教程视口 (QT-3 核心屏 ★)
//
// QQuickFramebufferObject 集成无窗口场景渲染器 GlSceneRenderer
// (magtile_render_scene, 与 GLFW/ImGui 版共用同一份 3D 绘制实现):
//   - GUI 线程 (本类): 教程引擎 (上一步/下一步/跳步)、轨道相机
//     (拖动旋转 / 右键平移 / 滚轮缩放)、进度自动存档 (ProgressStore,
//     与 CLI/GL 版共用同一 SQLite);
//   - 渲染线程 (FboRenderer): synchronize 拷贝场景快照, render 在
//     Qt 场景图分配的 FBO 里画 网格 + 已放置片 + 本步新片呼吸高亮
//     + 未来片 ghost (docs/UI_UX_SPEC.md §6)。
//
// 要求场景图跑在 OpenGL 后端 (main.cpp 设 QQuickWindow::
// setGraphicsApi(OpenGL), 亦可用环境变量 QSG_RHI_BACKEND=opengl)。
// 会话输入 (modelFile/dataDir/dbFile/resumeStep) 由 TutorialPage
// 在组件创建时一次性注入; 退出时 finishSession 落盘进度 (析构
// 兜底), 与 GL 版 "返回即存档, 不弹确认框" 行为一致 (§4.4)。
//
// 只读预览模式 (previewMode=true, QT-1 详情页 §5.4): 同一视口的
// 轻量用法 —— 直接加载模型最终态展示成品全貌, 不显示 ghost/步骤
// 高亮/呼吸动画, 不开进度存档 (纯看不写); 轨道相机交互 (拖动旋转/
// 滚轮缩放/右键平移) 与教程模式完全一致。
// =============================================================

#include <QElapsedTimer>
#include <QQuickFramebufferObject>
#include <QString>
#include <QtQml/qqmlregistration.h>
#include <memory>
#include <vector>

#include "magtile/core/tile_catalog.hpp"
#include "magtile/core/tile_instance.hpp"
#include "magtile/progress/progress_store.hpp"
#include "magtile/render/orbit_camera.hpp"
#include "magtile/tutorial/tutorial_engine.hpp"

namespace magtile::qtui {

// 注意: 不能标 final —— QML 引擎经 QQmlElement<T> 派生本类完成创建
class TutorialViewport : public QQuickFramebufferObject {
    Q_OBJECT
    QML_ELEMENT

    // ---- 会话输入 (进入教程页时设置, componentComplete 后生效) ------
    Q_PROPERTY(QString modelFile READ modelFile WRITE setModelFile NOTIFY sourceChanged)
    Q_PROPERTY(QString dataDir READ dataDir WRITE setDataDir NOTIFY sourceChanged)
    Q_PROPERTY(QString dbFile READ dbFile WRITE setDbFile NOTIFY sourceChanged)
    /// 进入时恢复到的步骤 (0 = 从头开始 -> 第 1 步)。
    Q_PROPERTY(int resumeStep READ resumeStep WRITE setResumeStep NOTIFY sourceChanged)
    /// 只读预览 (详情页): 加载最终态, 无 ghost/高亮, 不写进度存档。
    Q_PROPERTY(bool previewMode READ previewMode WRITE setPreviewMode NOTIFY sourceChanged)

    // ---- 会话状态 (只读, 步骤面板数据源) -----------------------------
    Q_PROPERTY(bool sessionReady READ sessionReady NOTIFY stateChanged)
    Q_PROPERTY(QString statusText READ statusText NOTIFY stateChanged)
    Q_PROPERTY(QString modelName READ modelName NOTIFY stateChanged)
    Q_PROPERTY(int stepNumber READ stepNumber NOTIFY stateChanged)
    Q_PROPERTY(int stepCount READ stepCount NOTIFY stateChanged)
    Q_PROPERTY(QString stepDescription READ stepDescription NOTIFY stateChanged)
    Q_PROPERTY(QString stepTip READ stepTip NOTIFY stateChanged)
    Q_PROPERTY(double progress READ progress NOTIFY stateChanged)
    Q_PROPERTY(int tilesPlaced READ tilesPlaced NOTIFY stateChanged)
    Q_PROPERTY(int tilesTotal READ tilesTotal NOTIFY stateChanged)
    Q_PROPERTY(bool finished READ finished NOTIFY stateChanged)

public:
    explicit TutorialViewport(QQuickItem* parent = nullptr);
    ~TutorialViewport() override;

    [[nodiscard]] Renderer* createRenderer() const override;

    // ---- 属性访问 ---------------------------------------------------
    [[nodiscard]] QString modelFile() const { return model_file_; }
    void setModelFile(const QString& path);
    [[nodiscard]] QString dataDir() const { return data_dir_; }
    void setDataDir(const QString& path);
    [[nodiscard]] QString dbFile() const { return db_file_; }
    void setDbFile(const QString& path);
    [[nodiscard]] int resumeStep() const noexcept { return resume_step_; }
    void setResumeStep(int step);
    [[nodiscard]] bool previewMode() const noexcept { return preview_mode_; }
    void setPreviewMode(bool preview);

    [[nodiscard]] bool sessionReady() const noexcept { return engine_ != nullptr; }
    [[nodiscard]] QString statusText() const { return status_text_; }
    [[nodiscard]] QString modelName() const;
    [[nodiscard]] int stepNumber() const;
    [[nodiscard]] int stepCount() const;
    [[nodiscard]] QString stepDescription() const;
    [[nodiscard]] QString stepTip() const;
    [[nodiscard]] double progress() const;
    [[nodiscard]] int tilesPlaced() const;
    [[nodiscard]] int tilesTotal() const;
    [[nodiscard]] bool finished() const;

    // ---- 步骤导航 (QML 按钮 / 键盘调用) ------------------------------
    Q_INVOKABLE void nextStep();
    Q_INVOKABLE void previousStep();
    /// 回到第 0 步 (只看 ghost 轮廓, "转动视角熟悉成品")。
    Q_INVOKABLE void restart();
    /// 恢复到进入教程时的取景 (整个成品进入视野)。
    Q_INVOKABLE void resetView();
    /// 退出前落盘进度 (幂等; 析构亦会兜底调用)。
    Q_INVOKABLE void finishSession();

signals:
    void sourceChanged();
    void stateChanged();

protected:
    void componentComplete() override;
    void mousePressEvent(QMouseEvent* event) override;
    void mouseMoveEvent(QMouseEvent* event) override;
    void wheelEvent(QWheelEvent* event) override;

private:
    friend class TutorialFboRenderer;

    /// 渲染线程消费的一片磁力片快照 (实例按值拷贝, 形状指向
    /// shared_ptr 持有的片型目录, 目录换代时旧快照仍安全)。
    struct SceneTile {
        core::TileInstance instance;
        const core::TileShape* shape = nullptr;
        bool highlighted = false;
        bool ghost = false;
        bool just_placed = false;
    };

    /// 加载片型目录与模型并启动教程会话 (componentComplete 后调用;
    /// 失败时 sessionReady=false 并给出温和的 statusText)。
    void startSession();
    /// 步骤变化后的统一处理: 重建场景快照、落盘进度、发状态信号。
    void applyStepChange();
    /// 把当前引擎状态展开为渲染快照 (visible/added/highlight 三集合)。
    void rebuildSceneTiles();
    /// 进度落盘: 当前步骤 + 自上次落盘以来的游玩秒数。
    void flushProgress();

    // 会话输入
    QString model_file_;
    QString data_dir_;
    QString db_file_;
    int resume_step_ = 0;
    bool preview_mode_ = false;

    // 会话状态 (GUI 线程)
    std::shared_ptr<core::TileCatalog> tile_catalog_;
    std::unique_ptr<tutorial::TutorialEngine> engine_;
    std::unique_ptr<progress::ProgressStore> store_;  ///< 打开失败为空 (只降级不崩溃)
    QString status_text_;
    render::OrbitCamera camera_;
    QPointF last_mouse_pos_;
    QElapsedTimer flush_clock_;  ///< 距上次进度落盘的游玩时长
    int last_saved_step_ = -1;
    bool session_flushed_ = false;

    // 渲染线程同步 (synchronize 期间 GUI 线程被阻塞, 读取安全)
    std::vector<SceneTile> scene_tiles_;
    quint64 scene_version_ = 0;  ///< 场景快照代数 (步骤变化时 +1)
};

}  // namespace magtile::qtui
