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
#include <vector>

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
    bool show_back_button = false;  ///< 从模型库进入时显示 "返回模型库"
};

/// 一帧内用户发出的教程导航操作 (键盘与 HUD 按钮来源合并)。
struct TutorialActions {
    bool next_step = false;
    bool previous_step = false;
    bool reset = false;            ///< 回到未开始状态 (第 0 步)
    bool back_to_library = false;  ///< 返回模型库 (仅库内会话有效)

    TutorialActions& operator|=(const TutorialActions& o) noexcept {
        next_step = next_step || o.next_step;
        previous_step = previous_step || o.previous_step;
        reset = reset || o.reset;
        back_to_library = back_to_library || o.back_to_library;
        return *this;
    }
};

/// 模型库界面: 一张模型卡片的展示状态 (元数据 + 进度存档快照)。
struct LibraryCard {
    std::string model_id;
    std::string name;
    std::string name_en;
    std::string description;
    int difficulty = 1;   ///< 1~5, 以星级展示
    int total_pieces = 0;
    int step_count = 0;
    std::string theme;    ///< 主题标签 (决定卡片主题色与角标)
    std::vector<std::string> tags;

    // ---- 来自进度存档 -------------------------------------------
    bool started = false;    ///< 有进度记录且未完成 (显示 "继续搭建")
    bool completed = false;  ///< 已完成 (显示绿色对勾)
    bool favorited = false;
    int current_step = 0;    ///< started 时: 已搭到第几步
};

/// 模型库界面一帧内用户发出的操作 (为空字符串 = 无操作)。
struct LibraryActions {
    std::string open_model_id;       ///< 点击卡片 / 继续搭建: 打开该模型教程
    std::string toggle_favorite_id;  ///< 点击收藏星标: 切换收藏状态
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

    /// 绘制模型库界面 (卡片网格 / 搜索 / 筛选 / 继续搭建) 并返回
    /// 用户操作。搜索与筛选状态由渲染器内部跨帧保持, 应用层每帧
    /// 提交全量卡片即可。须在 beginFrame 与 endFrame 之间调用,
    /// 每帧至多一次, 与 submitHud 互斥 (二者分属不同界面)。
    [[nodiscard]] virtual LibraryActions submitLibrary(const std::vector<LibraryCard>& cards) = 0;

    /// 冒烟测试辅助: 请求在本帧 endFrame 时把画面保存为 PPM (P6)
    /// 图片。写入失败仅输出警告, 不影响渲染循环。
    virtual void requestScreenshot(const std::string& ppm_path) = 0;
};

/// 创建 GLFW + OpenGL 4.1 后端。窗口与 GL 上下文在 initialize 中
/// 创建, 环境不支持时 initialize 返回 false 并向 stderr 输出原因。
[[nodiscard]] std::unique_ptr<IWindowRenderer> createOpenGLRenderer();

}  // namespace magtile::render
