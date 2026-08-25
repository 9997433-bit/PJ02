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
#include <utility>
#include <vector>

#include "magtile/core/age_mode.hpp"
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
    std::string thumbnail_path;  ///< 缩略图 PNG 路径 (空 = 无, 显示主题色占位)

    // ---- 来自模型 BOM (对照片型目录 tier, 见 core::isCoreTile) ----
    bool bom_known = false;   ///< 模型 JSON 成功加载, core9_only 有效
    bool core9_only = false;  ///< BOM 只用核心 9 片型 (基础套装即可搭;
                              ///< false 且 bom_known 时卡片显示 "需要扩展装" 角标)

    // ---- 来自模型库目录 tags (见 core::isFreeTierModel) -----------
    bool free_tier = true;    ///< 免费层模型 (tags 含「免费」, COMMERCIAL_PLAN §2.1);
                              ///< false 时卡片显示温和「订阅解锁」角标, 点击由应用层
                              ///< 弹订阅引导而非进教程 (元数据照常可浏览)。缺省 true:
                              ///< 无标签数据时不上锁 (宁可放行, 不误锁免费内容)

    // ---- 来自进度存档 -------------------------------------------
    bool started = false;    ///< 有进度记录且未完成 (显示 "继续搭建")
    bool completed = false;  ///< 已完成 (显示绿色对勾)
    bool favorited = false;
    int current_step = 0;    ///< started 时: 已搭到第几步
    bool buildable = false;  ///< 磁力片库存足够搭建 ("我能搭的" 筛选依据;
                             ///< 仅在已登记库存时有意义)
};

/// 模型库界面一帧内用户发出的操作 (为空字符串 = 无操作)。
struct LibraryActions {
    std::string open_model_id;       ///< 点击卡片 / 继续搭建: 打开该模型教程
    std::string toggle_favorite_id;  ///< 点击收藏星标: 切换收藏状态
    bool open_parent_area = false;   ///< 点击 "家长区" 入口 (须先过家长门)
    bool open_inventory = false;     ///< 点击 "我的磁力片" / "去登记": 打开库存录入界面
};

/// 首启库存 onboarding 提示弹窗一帧内用户发出的操作。
struct InventoryOnboardingActions {
    bool start_entry = false;  ///< 点击 "现在登记": 进入库存录入界面
    bool dismissed = false;    ///< 点击 "稍后再说": 关闭提示 (应用层记入存档, 不再弹出)
};

/// 订阅引导弹窗 (点击订阅内容模型时出现) 一帧内用户发出的操作。
struct SubscriptionPromptActions {
    bool open_parent_area = false;  ///< 点击 "请家长来解锁": 进入家长区 (先过家长门)
    bool browse_free = false;       ///< 点击 "先看免费模型": 关闭弹窗并开启「免费模型」
                                    ///< 筛选 (筛选切换由渲染器内部完成)
    bool dismissed = false;         ///< 点击 "回模型库": 仅关闭弹窗
};

/// 库存录入界面: 一种片型一行的展示状态 (UI_UX_SPEC.md §10.2)。
/// 计数由应用层持有 (编辑中的临时副本), 渲染层每帧全量接收并把
/// 修改经 InventoryEditorActions::count_changes 交回, 保存与否由
/// 应用层决定 —— 与模型库界面同样的 "状态下行 / 操作上行" 约定。
struct InventoryEditorRow {
    std::string shape_id;   ///< 稳定片型标识 (core::toString, 如 "square")
    std::string name_zh;    ///< 中文名, 如 "正方形"
    bool expansion = false; ///< 扩展包片型 (界面按 核心套装 / 扩展包 分组)
    int count = 0;          ///< 当前编辑中的数量
};

/// 库存录入界面一帧内用户发出的操作。
struct InventoryEditorActions {
    /// 步进器 (+/-) 或直接输入产生的数量修改: <片型标识, 新数量>。
    std::vector<std::pair<std::string, int>> count_changes;
    bool save = false;            ///< 点击 "保存库存": 写入存档并返回模型库
    bool save_and_match = false;  ///< 点击 "保存, 看看我能搭什么": 保存并开启 "我能搭的" 筛选
    bool back = false;            ///< 点击 "返回": 放弃本次修改回到模型库
};

/// 家长门界面一帧的展示状态 (验证逻辑由应用层 core::ParentGate
/// 驱动, 渲染层只负责题面展示与中文大写数字软键盘输入)。
struct ParentGateState {
    std::string question;        ///< 题面 (中文数字), 如 "叁 × 柒 = ?"
    int attempts_remaining = 3;  ///< 本轮剩余尝试次数
    int cooldown_seconds = 0;    ///< >0 = 冷却中, 显示温和的 "休息一下"
    bool wrong_answer = false;   ///< 上次提交答错 (显示温和提示, 无惩罚文案)
};

/// 家长门界面一帧内用户发出的操作。
struct ParentGateActions {
    bool submitted = false;  ///< 点击 [确认]
    std::string answer;      ///< submitted 时: 软键盘拼出的中文大写数字答案
    bool dismissed = false;  ///< 点击 [返回]: 放弃验证回到模型库
};

/// 家长区 (家长门之后的占位页) 一帧内用户发出的操作。
struct ParentAreaActions {
    bool back_to_library = false;  ///< 返回模型库 (家长会话保持有效)
    bool lock_now = false;         ///< 立即锁定家长区 (结束家长会话)
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
    /// @param age_mode 年龄段模式, 决定卡片密度与筛选器收放
    ///        (UI_UX_SPEC.md §2, 由应用层按年龄段设置传入):
    ///        4-6 启蒙 = 超大卡片约每行 2 张 + 隐藏搜索/筛选行;
    ///        7-9 标准 = 每行 3~4 张 + 只留难度/主题筛选;
    ///        10+ 进阶 = 紧凑卡片每行 4~5 张 + 全量筛选。
    /// @param inventory_configured 是否已登记磁力片库存: 未登记时
    ///        "我能搭的" 筛选禁用并显示 "去登记" 引导 (UI_UX_SPEC.md §5.2)。
    /// @param activate_buildable_filter 本帧强制开启 "我能搭的" 筛选
    ///        (一次性触发, 供库存录入界面 "保存, 看看我能搭什么" 跳转用;
    ///        筛选状态照常由渲染器跨帧保持, 用户可随时取消勾选;
    ///        仅 10+ 进阶模式可见该筛选, 其余档位忽略)。
    [[nodiscard]] virtual LibraryActions submitLibrary(const std::vector<LibraryCard>& cards,
                                                       core::AgeMode age_mode,
                                                       bool inventory_configured,
                                                       bool activate_buildable_filter) = 0;

    /// 绘制首启库存 onboarding 提示弹窗 (价值说明 + "现在登记" 入口,
    /// UI_UX_SPEC.md §10.1) 并返回用户操作。带压暗遮罩, 须在
    /// submitLibrary 之后、endFrame 之前调用, 每帧至多一次。
    [[nodiscard]] virtual InventoryOnboardingActions submitInventoryOnboarding() = 0;

    /// 绘制订阅引导弹窗 (点击订阅内容模型时出现): 温和说明免费层
    /// 永久免费、订阅解锁全库, 无价格/无倒计时/无催促 (UI_UX_SPEC.md
    /// §11/§12.2, 儿童侧只说 "请家长来解锁") 并返回用户操作。带压暗
    /// 遮罩, 须在 submitLibrary 之后、endFrame 之前调用, 每帧至多
    /// 一次, 与 submitInventoryOnboarding 互斥 (同为库上层弹窗)。
    /// @param model_name 被点击的订阅内容模型中文名。
    [[nodiscard]] virtual SubscriptionPromptActions submitSubscriptionPrompt(
        const std::string& model_name) = 0;

    /// 绘制磁力片库存录入界面 (全部片型中文名 + 大号 +/- 步进器,
    /// 支持长按连加与直接输入, UI_UX_SPEC.md §10.2) 并返回用户操作。
    /// 须在 beginFrame 与 endFrame 之间调用, 每帧至多一次, 与
    /// submitHud / submitLibrary / submitParentGate 互斥 (分属不同界面)。
    [[nodiscard]] virtual InventoryEditorActions submitInventoryEditor(
        const std::vector<InventoryEditorRow>& rows) = 0;

    /// 绘制家长门界面 (算术题 + 中文大写数字软键盘) 并返回用户
    /// 操作。软键盘输入缓冲由渲染器跨帧保持, 提交/返回时自动清空。
    /// 须在 beginFrame 与 endFrame 之间调用, 每帧至多一次, 与
    /// submitHud / submitLibrary 互斥 (分属不同界面)。
    [[nodiscard]] virtual ParentGateActions submitParentGate(const ParentGateState& state) = 0;

    /// 绘制家长区占位页 (订阅管理 / 设置占位 + 会话剩余时间) 并
    /// 返回用户操作。调用约定同 submitParentGate。
    [[nodiscard]] virtual ParentAreaActions submitParentArea(int session_remaining_seconds) = 0;

    /// 冒烟测试辅助: 请求在本帧 endFrame 时把画面保存为 PPM (P6)
    /// 图片。写入失败仅输出警告, 不影响渲染循环。
    virtual void requestScreenshot(const std::string& ppm_path) = 0;
};

/// 创建 GLFW + OpenGL 4.1 后端。窗口与 GL 上下文在 initialize 中
/// 创建, 环境不支持时 initialize 返回 false 并向 stderr 输出原因。
[[nodiscard]] std::unique_ptr<IWindowRenderer> createOpenGLRenderer();

}  // namespace magtile::render
