#pragma once

// =============================================================
// MagTile Studio - 无窗口 OpenGL 磁力片场景渲染器 (公共接口)
//
// 只负责把磁力片 3D 场景 (地面网格 + 半透明彩色薄板 + 高亮描边)
// 画进 "当前已绑定" 的 framebuffer, 不创建窗口、不处理输入、不含
// ImGui —— 因此可同时服务两个外壳:
//   - GLFW + ImGui 版 (gl_renderer.cpp): 画进默认 framebuffer;
//   - Qt/QML 版 (QQuickFramebufferObject): 画进 Qt 场景图分配的
//     FBO (QT-3 教程视口, 见 docs/QT_UI_PLAN.md)。
// GL 入口经调用方提供的解析器在运行时加载 (GLFW 用
// glfwGetProcAddress, Qt 用 QOpenGLContext::getProcAddress),
// 本头文件不暴露任何 GLFW / Qt / 系统 GL 类型。
//
// 注意: GL 函数指针表是进程级全局的 (gl_api.hpp), 一个进程内只
// 应存在一种 GL 上下文提供方 (两个外壳是不同的可执行文件)。
// =============================================================

#include <vector>

#include "magtile/render/renderer.hpp"

namespace magtile::render {

class GlSceneRenderer {
public:
    /// GL 入口解析回调 (与 glfwGetProcAddress /
    /// QOpenGLContext::getProcAddress 签名兼容)。
    using GlProc = void (*)();
    using ProcResolver = GlProc (*)(const char* name);

    GlSceneRenderer() = default;
    ~GlSceneRenderer();

    GlSceneRenderer(const GlSceneRenderer&) = delete;
    GlSceneRenderer& operator=(const GlSceneRenderer&) = delete;

    /// 解析 GL 入口并创建着色器 / 顶点缓冲 / 地面网格。必须在目标
    /// GL 上下文为 current 时调用; 重复调用为幂等空操作。
    /// 失败时向 stderr 输出原因并返回 false (调用方温和降级)。
    [[nodiscard]] bool initialize(ProcResolver resolver);

    /// 释放全部 GL 资源; 须在原上下文仍为 current 时调用。
    void shutdown();

    [[nodiscard]] bool ready() const noexcept { return initialized_; }

    /// 开始一帧: 设置视口并清屏 (画进当前绑定的 framebuffer)。
    void begin(const Camera& camera, int fb_width, int fb_height);

    /// 提交一片磁力片 (语义与 IRenderer::submitTile 一致)。
    void submitTile(const RenderTile& tile, const core::TileShape& shape);

    /// 结束一帧: 按视线深度排序 (画家算法)、挤出薄板并绘制
    /// 网格 + 磁力片 + 高亮描边。time_seconds 驱动 "本步新增"
    /// 的呼吸动画 (调用方传入单调递增的秒数即可)。
    void end(double time_seconds);

private:
    struct GlObjects;  // GL 句柄与帧缓存 (实现内部类型, 见 .cpp)

    bool initialized_ = false;
    GlObjects* gl_ = nullptr;
};

}  // namespace magtile::render
