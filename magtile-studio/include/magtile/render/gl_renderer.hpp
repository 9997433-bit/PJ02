#pragma once

// =============================================================
// MagTile Studio - GLFW + OpenGL 4.1 Core 渲染后端 (公共接口)
//
// 仅在 CMake 选项 MAGTILE_BUILD_GL_RENDERER=ON 时参与编译与链接;
// 链接 magtile_render_gl 的目标会获得 MAGTILE_HAS_GL_RENDERER 宏。
// 本头文件刻意不暴露任何 GLFW / OpenGL / ImGui 类型, 保证上层
// 代码只依赖抽象接口。
// =============================================================

#include <memory>
#include <string>

#include "magtile/render/orbit_camera.hpp"
#include "magtile/render/renderer.hpp"

namespace magtile::render {

/// 教程 HUD 一帧所需的全部展示状态, 由应用层每帧填充。
struct TutorialHudState {
    std::string model_name;
    int step_number = 0;      ///< 当前步骤, 0 = 尚未开始
    int step_count = 0;
    double progress = 0.0;    ///< 0.0 ~ 1.0
    std::string description;  ///< 当前步骤中文说明
    std::string tip;          ///< 可选提示, 为空则不显示
    int tiles_placed = 0;
    int tiles_total = 0;
};

/// 一帧内用户发出的教程导航操作 (键盘与 HUD 按钮来源合并)。
struct TutorialActions {
    bool next_step = false;
    bool previous_step = false;
    bool reset = false;  ///< 回到未开始状态 (第 0 步)

    TutorialActions& operator|=(const TutorialActions& o) noexcept {
        next_step = next_step || o.next_step;
        previous_step = previous_step || o.previous_step;
        reset = reset || o.reset;
        return *this;
    }
};

/// 带窗口与交互能力的渲染后端接口。
///
/// 帧循环约定:
///   pollEvents -> consumeActions -> beginFrame -> submitTile* ->
///   submitHud -> endFrame
class IWindowRenderer : public IRenderer {
public:
    /// 处理窗口消息与鼠标输入; 轨道相机的旋转/平移/缩放在此更新。
    virtual void pollEvents() = 0;

    /// 轨道相机 (应用层用于初始取景 frameBounds)。
    [[nodiscard]] virtual OrbitCamera& orbitCamera() noexcept = 0;

    /// 取出自上次调用以来由键盘触发的教程导航操作。
    [[nodiscard]] virtual TutorialActions consumeActions() = 0;

    /// 绘制教程 HUD 并返回按钮触发的操作。须在 beginFrame 与
    /// endFrame 之间调用, 每帧至多一次。
    [[nodiscard]] virtual TutorialActions submitHud(const TutorialHudState& hud) = 0;

    /// 冒烟测试辅助: 请求在本帧 endFrame 时把画面保存为 PPM (P6)
    /// 图片。写入失败仅输出警告, 不影响渲染循环。
    virtual void requestScreenshot(const std::string& ppm_path) = 0;
};

/// 创建 GLFW + OpenGL 4.1 后端。窗口与 GL 上下文在 initialize 中
/// 创建, 环境不支持时 initialize 返回 false 并向 stderr 输出原因。
[[nodiscard]] std::unique_ptr<IWindowRenderer> createOpenGLRenderer();

}  // namespace magtile::render
