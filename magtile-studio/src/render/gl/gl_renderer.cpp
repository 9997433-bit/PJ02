// =============================================================
// MagTile Studio - GLFW + OpenGL 4.1 Core 渲染后端实现
//
// 3D 场景 (地面网格 / 半透明磁力片 / 高亮描边) 由无窗口的
// GlSceneRenderer 绘制 (gl_scene_renderer.cpp, 与 Qt 教程视口
// 共用同一实现, QT-3); 本文件负责 GLFW 窗口 / 输入 / 轨道相机
// 交互与 Dear ImGui 界面 (教程 HUD / 模型库 / 家长门 / 库存录入)。
// =============================================================

#include "magtile/render/gl_renderer.hpp"

#include <algorithm>
#include <array>
#include <cmath>
#include <cstdint>
#include <cstdio>
#include <filesystem>
#include <functional>
#include <iterator>
#include <string>
#include <string_view>
#include <unordered_map>
#include <utility>
#include <vector>

#ifndef GLFW_INCLUDE_NONE
#define GLFW_INCLUDE_NONE
#endif
#include <GLFW/glfw3.h>

#include <imgui.h>
#include <imgui_impl_glfw.h>
#include <imgui_impl_opengl3.h>

#include <stb/stb_image.h>

#include "gl_api.hpp"
#include "magtile/render/gl_scene_renderer.hpp"

namespace magtile::render {
namespace {

using namespace glapi;

// ---- 交互参数 ----------------------------------------------------
constexpr double kRotateSpeedDegPerPx = 0.32;

/// 查找系统中可用的中文字体 (HUD 步骤文案为中文)。
const char* findCjkFontPath() {
    static const char* candidates[] = {
#if defined(_WIN32)
        "C:/Windows/Fonts/msyh.ttc",
        "C:/Windows/Fonts/simhei.ttf",
        "C:/Windows/Fonts/simsun.ttc",
#elif defined(__APPLE__)
        "/System/Library/Fonts/PingFang.ttc",
        "/System/Library/Fonts/STHeiti Light.ttc",
        "/System/Library/Fonts/Hiragino Sans GB.ttc",
#else
        "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
        "/usr/share/fonts/noto-cjk/NotoSansCJK-Regular.ttc",
        "/usr/share/fonts/truetype/wqy/wqy-microhei.ttc",
        "/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc",
#endif
    };
    for (const char* path : candidates) {
        std::error_code ec;
        if (std::filesystem::exists(path, ec)) return path;
    }
    return nullptr;
}

void glfwErrorCallback(int error, const char* description) {
    std::fprintf(stderr, "[render] GLFW 错误 %d: %s\n", error, description);
}

// ---- 模型库界面辅助 ------------------------------------------------

/// 品牌与状态色 (模型库界面)。
constexpr ImU32 kColorGreen = IM_COL32(43, 158, 78, 255);      ///< 已完成
constexpr ImU32 kColorGold = IM_COL32(240, 173, 30, 255);      ///< 星级 / 收藏
constexpr ImU32 kColorInk = IM_COL32(38, 43, 54, 255);         ///< 主文字
constexpr ImU32 kColorExpansion = IM_COL32(217, 119, 6, 255);  ///< "需要扩展装" 角标 (琥珀)
constexpr ImU32 kColorSubscription = IM_COL32(122, 94, 216, 255);  ///< "订阅解锁" 角标 (温和紫,
                                                                   ///< 刻意不用红色表达 "锁")
const ImVec4 kAccentVec{0.28f, 0.44f, 0.93f, 1.0f};            ///< 品牌蓝

/// 主题标签 -> 卡片主题色: 规范主题 (tools/update_model_catalog.py
/// 推导, 与 tools/generate_thumbnails.py 占位图配色一致) 固定配色,
/// 其余从调色板哈希取色, 同一主题在任何一次运行中颜色稳定。
ImU32 themeColor32(const std::string& theme) {
    static const std::pair<const char*, ImU32> kKnown[] = {
        {"城堡王国", IM_COL32(103, 111, 219, 255)},
        {"建筑地标", IM_COL32(66, 133, 244, 255)},
        {"工程结构", IM_COL32(230, 124, 55, 255)},
        {"自然世界", IM_COL32(52, 168, 111, 255)},
        {"航天探索", IM_COL32(126, 87, 194, 255)},
        {"城市生活", IM_COL32(220, 88, 70, 255)},
        {"游乐园", IM_COL32(236, 64, 122, 255)},
        {"滚珠乐园", IM_COL32(0, 172, 193, 255)},
        {"海洋航行", IM_COL32(2, 136, 209, 255)},
        {"田园", IM_COL32(124, 179, 66, 255)},
        // 兼容旧目录/临时标签的固定配色
        {"城堡", IM_COL32(103, 111, 219, 255)},
        {"建筑基础", IM_COL32(66, 133, 244, 255)},
        {"进阶", IM_COL32(230, 124, 55, 255)},
        {"动物", IM_COL32(52, 168, 111, 255)},
        {"车辆", IM_COL32(220, 88, 70, 255)},
        {"太空", IM_COL32(126, 87, 194, 255)},
        {"入门", IM_COL32(38, 166, 154, 255)},
    };
    for (const auto& [name, color] : kKnown) {
        if (theme == name) return color;
    }
    static constexpr ImU32 kPalette[] = {
        IM_COL32(66, 133, 244, 255),  IM_COL32(219, 68, 55, 255),  IM_COL32(244, 160, 0, 255),
        IM_COL32(15, 157, 88, 255),   IM_COL32(171, 71, 188, 255), IM_COL32(0, 172, 193, 255),
    };
    const std::size_t index = std::hash<std::string>{}(theme) % std::size(kPalette);
    return kPalette[index];
}

/// 难度 -> 星级字符串, 如 3 -> "★★★☆☆"。
std::string difficultyStars(int difficulty) {
    std::string stars;
    for (int i = 1; i <= 5; ++i) stars += (i <= difficulty) ? "★" : "☆";
    return stars;
}

/// 大小写不敏感 (仅 ASCII) 的子串匹配; 中文按 UTF-8 字节精确匹配。
bool matchesSearch(const std::string& haystack, const std::string& needle) {
    if (needle.empty()) return true;
    const auto lower = [](std::string text) {
        for (char& c : text) {
            if (c >= 'A' && c <= 'Z') c = static_cast<char>(c - 'A' + 'a');
        }
        return text;
    };
    return lower(haystack).find(lower(needle)) != std::string::npos;
}

/// 绿色圆底对勾角标 (字体无关, 直接用 DrawList 画)。
void drawCheckBadge(ImDrawList* draw_list, const ImVec2& center, float radius, ImU32 color) {
    draw_list->AddCircleFilled(center, radius, color);
    const ImU32 white = IM_COL32(255, 255, 255, 255);
    const float t = radius * 0.24f;
    draw_list->AddLine(ImVec2(center.x - radius * 0.42f, center.y + radius * 0.02f),
                       ImVec2(center.x - radius * 0.10f, center.y + radius * 0.36f), white, t);
    draw_list->AddLine(ImVec2(center.x - radius * 0.10f, center.y + radius * 0.36f),
                       ImVec2(center.x + radius * 0.46f, center.y - radius * 0.30f), white, t);
}

/// 主题色圆角小徽章 (占位为一个 ImGui item, 参与布局)。
void drawThemeBadge(const std::string& theme, ImU32 theme_color) {
    ImDrawList* draw_list = ImGui::GetWindowDrawList();
    const ImVec2 text_size = ImGui::CalcTextSize(theme.c_str());
    const ImVec2 pad{9.0f, 3.0f};
    const ImVec2 top_left = ImGui::GetCursorScreenPos();
    const ImVec2 bottom_right{top_left.x + text_size.x + pad.x * 2.0f,
                              top_left.y + text_size.y + pad.y * 2.0f};
    // 半透明主题色底 + 主题色文字, 视觉轻但辨识度高
    const ImU32 bg = (theme_color & 0x00FFFFFF) | 0x2E000000;
    draw_list->AddRectFilled(top_left, bottom_right, bg,
                             (bottom_right.y - top_left.y) * 0.5f);
    draw_list->AddText(ImVec2(top_left.x + pad.x, top_left.y + pad.y), theme_color,
                       theme.c_str());
    ImGui::Dummy(ImVec2(bottom_right.x - top_left.x, bottom_right.y - top_left.y));
}

// ---- 渲染器实现 ---------------------------------------------------
class GlRenderer final : public IWindowRenderer {
public:
    ~GlRenderer() override { shutdown(); }

    // ---- IRenderer ------------------------------------------------
    bool initialize(int width, int height, const std::string& window_title) override;
    void shutdown() override;
    void beginFrame(const Camera& camera) override;
    void submitTile(const RenderTile& tile, const core::TileShape& shape) override;
    void endFrame() override;
    [[nodiscard]] bool shouldClose() const override {
        return window_ == nullptr || glfwWindowShouldClose(window_) == GLFW_TRUE;
    }

    // ---- IWindowRenderer -------------------------------------------
    void pollEvents() override;
    [[nodiscard]] OrbitCamera& orbitCamera() noexcept override { return camera_; }
    [[nodiscard]] TutorialActions consumeActions() override {
        const TutorialActions actions = pending_actions_;
        pending_actions_ = {};
        return actions;
    }
    [[nodiscard]] TutorialActions submitHud(const TutorialHudState& hud) override;
    [[nodiscard]] LibraryActions submitLibrary(const std::vector<LibraryCard>& cards,
                                               core::AgeMode age_mode, bool inventory_configured,
                                               bool activate_buildable_filter) override;
    [[nodiscard]] InventoryOnboardingActions submitInventoryOnboarding() override;
    [[nodiscard]] SubscriptionPromptActions submitSubscriptionPrompt(
        const std::string& model_name) override;
    [[nodiscard]] InventoryEditorActions submitInventoryEditor(
        const std::vector<InventoryEditorRow>& rows) override;
    [[nodiscard]] ParentGateActions submitParentGate(const ParentGateState& state) override;
    [[nodiscard]] ParentAreaActions submitParentArea(int session_remaining_seconds) override;
    void requestScreenshot(const std::string& ppm_path) override { screenshot_path_ = ppm_path; }

private:
    void setupImGui();
    /// 模型卡片: 大卡 (网格) 与小卡 (继续搭建区), 点击写入 actions。
    void drawLibraryCard(const LibraryCard& card, const ImVec2& size, bool compact,
                         LibraryActions& actions);
    /// 库存录入: 一种片型一张卡 (中文名 + 大步进器 + 直接输入)。
    void drawInventoryCard(const InventoryEditorRow& row, const ImVec2& size,
                           InventoryEditorActions& actions);
    /// 缩略图纹理: 首次使用时从 PNG 加载并缓存, 失败缓存 0 (不重试)。
    [[nodiscard]] GLuint thumbnailTexture(const std::string& png_path);
    [[nodiscard]] bool keyPressed(int key);
    void writeScreenshot();

    // 窗口与上下文
    GLFWwindow* window_ = nullptr;
    bool glfw_initialized_ = false;
    bool imgui_initialized_ = false;

    // 字体 (正文 19px 为 ImGui 默认字体, 标题 28px 供模型库页眉)
    ImFont* font_title_ = nullptr;
    ImVector<ImWchar> glyph_ranges_;  ///< 字体图集构建期间必须保持存活

    // 模型库界面的跨帧 UI 状态 (搜索词与筛选条件)
    std::array<char, 128> library_search_{};
    int library_difficulty_filter_ = 0;  ///< 0 = 全部难度, 1~5 = 对应星级
    std::string library_theme_filter_;   ///< 空 = 全部主题
    bool library_favorites_only_ = false;
    bool library_core9_only_ = false;      ///< "只用核心 9 片": 只看基础套装能搭的模型
    bool library_buildable_only_ = false;  ///< "我能搭的": 只看库存足够的模型
    bool library_free_only_ = false;       ///< "免费模型": 只看免费层 (tags 含「免费」)
    /// 筛选行是否可见 (4-6 启蒙档隐藏): 订阅引导弹窗据此决定
    /// 是否提供「先看免费模型」一键切筛选
    bool library_filter_row_visible_ = true;

    // 家长门软键盘的跨帧输入缓冲 (中文大写数字; 提交/返回时清空)
    std::string parent_gate_input_;

    // 模型卡片缩略图纹理缓存 (路径 -> GL 纹理; 0 = 加载失败不再重试)
    std::unordered_map<std::string, GLuint> thumbnail_textures_;

    // 3D 场景渲染器 (着色器 / 顶点缓冲 / 网格, 与 Qt 教程视口共用实现)
    GlSceneRenderer scene_;

    // 相机与交互
    OrbitCamera camera_;
    TutorialActions pending_actions_{};
    double last_mouse_x_ = 0.0, last_mouse_y_ = 0.0;
    double scroll_delta_ = 0.0;
    std::array<bool, GLFW_KEY_LAST + 1> key_was_down_{};

    // 帧状态
    int fb_width_ = 0, fb_height_ = 0;
    std::string screenshot_path_;

    static void scrollCallback(GLFWwindow* window, double dx, double dy) {
        auto* self = static_cast<GlRenderer*>(glfwGetWindowUserPointer(window));
        if (self != nullptr) {
            self->scroll_delta_ += dy;
            (void)dx;
        }
    }
};

bool GlRenderer::initialize(int width, int height, const std::string& window_title) {
    if (window_ != nullptr) return true;

    glfwSetErrorCallback(glfwErrorCallback);
    if (glfwInit() != GLFW_TRUE) {
        std::fprintf(stderr, "[render] GLFW 初始化失败 (是否有可用的显示环境?)\n");
        return false;
    }
    glfw_initialized_ = true;

    // OpenGL 4.1 Core: 三平台交集 (macOS 上限), 前向兼容为 macOS 必需
    glfwWindowHint(GLFW_CONTEXT_VERSION_MAJOR, 4);
    glfwWindowHint(GLFW_CONTEXT_VERSION_MINOR, 1);
    glfwWindowHint(GLFW_OPENGL_PROFILE, GLFW_OPENGL_CORE_PROFILE);
    glfwWindowHint(GLFW_OPENGL_FORWARD_COMPAT, GLFW_TRUE);
    glfwWindowHint(GLFW_SAMPLES, 4);

    window_ = glfwCreateWindow(width, height, window_title.c_str(), nullptr, nullptr);
    if (window_ == nullptr) {
        std::fprintf(stderr, "[render] 创建窗口失败 (需要 OpenGL 4.1 支持)\n");
        shutdown();
        return false;
    }
    glfwMakeContextCurrent(window_);
    glfwSwapInterval(1);  // 垂直同步

    if (!scene_.initialize(glfwGetProcAddress)) {
        shutdown();
        return false;
    }
    std::printf("[render] OpenGL %s @ %s\n", glGetString(GL_VERSION), glGetString(GL_RENDERER));

    // 输入回调需在 ImGui 之前安装, ImGui 的 GLFW 后端会链式转发
    glfwSetWindowUserPointer(window_, this);
    glfwSetScrollCallback(window_, &GlRenderer::scrollCallback);
    glfwGetCursorPos(window_, &last_mouse_x_, &last_mouse_y_);

    setupImGui();
    return true;
}

void GlRenderer::shutdown() {
    if (imgui_initialized_) {
        ImGui_ImplOpenGL3_Shutdown();
        ImGui_ImplGlfw_Shutdown();
        ImGui::DestroyContext();
        imgui_initialized_ = false;
    }
    if (window_ != nullptr) {
        // GL 资源随上下文销毁, 仍显式删除以便调试工具追踪
        scene_.shutdown();
        for (const auto& cached : thumbnail_textures_) {
            if (cached.second != 0) glDeleteTextures(1, &cached.second);
        }
        thumbnail_textures_.clear();

        glfwDestroyWindow(window_);
        window_ = nullptr;
    }
    if (glfw_initialized_) {
        glfwTerminate();
        glfw_initialized_ = false;
    }
}

void GlRenderer::setupImGui() {
    IMGUI_CHECKVERSION();
    ImGui::CreateContext();
    ImGuiIO& io = ImGui::GetIO();
    io.IniFilename = nullptr;  // HUD 布局固定, 不落盘配置

    ImGui::StyleColorsLight();
    ImGuiStyle& style = ImGui::GetStyle();
    style.WindowRounding = 10.0f;
    style.ChildRounding = 12.0f;
    style.FrameRounding = 7.0f;
    style.GrabRounding = 7.0f;
    style.PopupRounding = 8.0f;
    style.WindowBorderSize = 0.0f;
    style.FramePadding = ImVec2(10.0f, 6.0f);
    style.ItemSpacing = ImVec2(10.0f, 8.0f);
    // 品牌蓝作为交互控件的主色 (模型库 + 教程 HUD 统一观感)
    ImVec4* colors = style.Colors;
    colors[ImGuiCol_Button] = ImVec4(0.28f, 0.44f, 0.93f, 0.12f);
    colors[ImGuiCol_ButtonHovered] = ImVec4(0.28f, 0.44f, 0.93f, 0.28f);
    colors[ImGuiCol_ButtonActive] = ImVec4(0.28f, 0.44f, 0.93f, 0.45f);
    colors[ImGuiCol_FrameBg] = ImVec4(0.93f, 0.94f, 0.97f, 1.0f);
    colors[ImGuiCol_FrameBgHovered] = ImVec4(0.88f, 0.90f, 0.96f, 1.0f);
    colors[ImGuiCol_FrameBgActive] = ImVec4(0.83f, 0.87f, 0.96f, 1.0f);
    colors[ImGuiCol_PlotHistogram] = ImVec4(0.28f, 0.44f, 0.93f, 1.0f);
    colors[ImGuiCol_CheckMark] = ImVec4(0.28f, 0.44f, 0.93f, 1.0f);

    if (const char* font_path = findCjkFontPath(); font_path != nullptr) {
        // 常用简体字形之外补充模型库界面用到的符号 (星级/角标/箭头)、
        // 家长门的中文大写数字 (财务体不在常用 2500 字表内) 与库存录入
        // 界面的片型用字 (菱形的 "菱" 同样不在常用表内)
        ImFontGlyphRangesBuilder ranges_builder;
        ranges_builder.AddRanges(io.Fonts->GetGlyphRangesChineseSimplifiedCommon());
        ranges_builder.AddText("★☆●○◆▶◀·×零壹贰叁肆伍陆柒捌玖拾菱");
        glyph_ranges_.clear();
        ranges_builder.BuildRanges(&glyph_ranges_);
        io.Fonts->AddFontFromFileTTF(font_path, 19.0f, nullptr, glyph_ranges_.Data);
        font_title_ = io.Fonts->AddFontFromFileTTF(font_path, 28.0f, nullptr, glyph_ranges_.Data);
        std::printf("[render] HUD 字体: %s\n", font_path);
    } else {
        io.Fonts->AddFontDefault();
        font_title_ = nullptr;
        std::fprintf(stderr, "[render] 警告: 未找到中文字体, HUD 中文可能无法显示\n");
    }

    ImGui_ImplGlfw_InitForOpenGL(window_, true);
    ImGui_ImplOpenGL3_Init("#version 410");
    imgui_initialized_ = true;
}

void GlRenderer::pollEvents() {
    if (window_ == nullptr) return;
    glfwPollEvents();

    const ImGuiIO& io = ImGui::GetIO();

    // ---- 鼠标 -> 轨道相机 ------------------------------------------
    double mx = 0.0, my = 0.0;
    glfwGetCursorPos(window_, &mx, &my);
    const double dx = mx - last_mouse_x_;
    const double dy = my - last_mouse_y_;
    last_mouse_x_ = mx;
    last_mouse_y_ = my;

    if (!io.WantCaptureMouse) {
        int win_w = 0, win_h = 0;
        glfwGetWindowSize(window_, &win_w, &win_h);
        const bool rotate = glfwGetMouseButton(window_, GLFW_MOUSE_BUTTON_LEFT) == GLFW_PRESS;
        const bool pan = glfwGetMouseButton(window_, GLFW_MOUSE_BUTTON_RIGHT) == GLFW_PRESS ||
                         glfwGetMouseButton(window_, GLFW_MOUSE_BUTTON_MIDDLE) == GLFW_PRESS;
        if (rotate) {
            camera_.rotate(-dx * kRotateSpeedDegPerPx, -dy * kRotateSpeedDegPerPx);
        } else if (pan) {
            camera_.pan(dx, dy, win_h);
        }
        if (scroll_delta_ != 0.0) camera_.zoom(scroll_delta_);
    }
    scroll_delta_ = 0.0;

    // ---- 键盘 -> 教程导航 / 视角 ------------------------------------
    if (!io.WantCaptureKeyboard) {
        if (keyPressed(GLFW_KEY_RIGHT) || keyPressed(GLFW_KEY_PAGE_DOWN) ||
            keyPressed(GLFW_KEY_SPACE)) {
            pending_actions_.next_step = true;
        }
        if (keyPressed(GLFW_KEY_LEFT) || keyPressed(GLFW_KEY_PAGE_UP)) {
            pending_actions_.previous_step = true;
        }
        if (keyPressed(GLFW_KEY_HOME)) pending_actions_.reset = true;
        if (keyPressed(GLFW_KEY_R)) camera_.resetView();
        if (keyPressed(GLFW_KEY_ESCAPE)) glfwSetWindowShouldClose(window_, GLFW_TRUE);
    }
}

bool GlRenderer::keyPressed(int key) {
    const bool down = glfwGetKey(window_, key) == GLFW_PRESS;
    const bool pressed = down && !key_was_down_[static_cast<std::size_t>(key)];
    key_was_down_[static_cast<std::size_t>(key)] = down;
    return pressed;
}

void GlRenderer::beginFrame(const Camera& camera) {
    glfwGetFramebufferSize(window_, &fb_width_, &fb_height_);
    scene_.begin(camera, fb_width_, fb_height_);

    ImGui_ImplOpenGL3_NewFrame();
    ImGui_ImplGlfw_NewFrame();
    ImGui::NewFrame();
}

void GlRenderer::submitTile(const RenderTile& tile, const core::TileShape& shape) {
    scene_.submitTile(tile, shape);
}

TutorialActions GlRenderer::submitHud(const TutorialHudState& hud) {
    TutorialActions actions;
    const ImGuiIO& io = ImGui::GetIO();
    const ImGuiWindowFlags overlay_flags =
        ImGuiWindowFlags_NoDecoration | ImGuiWindowFlags_AlwaysAutoResize |
        ImGuiWindowFlags_NoSavedSettings | ImGuiWindowFlags_NoFocusOnAppearing |
        ImGuiWindowFlags_NoNav | ImGuiWindowFlags_NoMove;

    // ---- 左上角: 模型信息与操作说明 ---------------------------------
    ImGui::SetNextWindowPos(ImVec2(14.0f, 14.0f));
    ImGui::SetNextWindowBgAlpha(0.72f);
    if (ImGui::Begin("##model_info", nullptr, overlay_flags)) {
        if (hud.show_back_button) {
            if (ImGui::Button("◀ 返回模型库")) actions.back_to_library = true;
            ImGui::SameLine();
        }
        ImGui::Text("%s", hud.model_name.c_str());
        if (hud.show_tts_toggle) {
            // 步骤朗读开关 (§4.2): 与 Qt 版设置页共用 "tts_enabled" 键,
            // 点击由应用层翻转并持久化; 引擎缺失时开关照常可调,
            // 只温和说明不禁用 (P3 零挫败, 与 Qt 版同一策略)
            if (ImGui::Button(hud.tts_enabled ? "朗读: 开" : "朗读: 关")) {
                actions.toggle_tts = true;
            }
            ImGui::SameLine();
            if (hud.tts_available) {
                ImGui::TextDisabled(hud.tts_enabled ? "切换步骤时朗读说明"
                                                    : "点击开启步骤朗读");
            } else {
                ImGui::TextDisabled("本机暂无语音引擎, 开关照常保存");
            }
        }
        ImGui::Separator();
        ImGui::TextDisabled("鼠标左键 旋转 | 右键 平移 | 滚轮 缩放 | R 重置视角");
        ImGui::TextDisabled("方向键 <- -> 切换步骤 | Home 从头开始 | Esc 退出");
    }
    ImGui::End();

    // ---- 底部: 步骤面板 --------------------------------------------
    const float panel_width = std::min(io.DisplaySize.x - 28.0f, 720.0f);
    ImGui::SetNextWindowPos(ImVec2(io.DisplaySize.x * 0.5f, io.DisplaySize.y - 18.0f),
                            ImGuiCond_Always, ImVec2(0.5f, 1.0f));
    ImGui::SetNextWindowSize(ImVec2(panel_width, 0.0f));
    ImGui::SetNextWindowBgAlpha(0.88f);
    if (ImGui::Begin("##step_panel", nullptr, overlay_flags)) {
        const bool finished = hud.step_count > 0 && hud.step_number >= hud.step_count;
        if (hud.step_number <= 0) {
            ImGui::Text("准备开始 (共 %d 步 / %d 片)", hud.step_count, hud.tiles_total);
        } else {
            ImGui::Text("第 %d / %d 步", hud.step_number, hud.step_count);
            ImGui::SameLine();
            ImGui::TextDisabled("  已放置 %d / %d 片", hud.tiles_placed, hud.tiles_total);
            if (finished) {
                ImGui::SameLine();
                ImGui::TextColored(ImVec4(0.16f, 0.62f, 0.32f, 1.0f), "  搭建完成!");
            }
        }
        ImGui::ProgressBar(static_cast<float>(hud.progress), ImVec2(-1.0f, 7.0f), "");
        ImGui::Spacing();
        ImGui::TextWrapped("%s", hud.description.c_str());
        if (!hud.tip.empty()) {
            ImGui::PushStyleColor(ImGuiCol_Text, ImVec4(0.72f, 0.48f, 0.05f, 1.0f));
            ImGui::TextWrapped("提示: %s", hud.tip.c_str());
            ImGui::PopStyleColor();
        }
        ImGui::Spacing();

        ImGui::BeginDisabled(hud.step_number <= 0);
        if (ImGui::Button("|< 重来", ImVec2(96.0f, 0.0f))) actions.reset = true;
        ImGui::SameLine();
        if (ImGui::Button("< 上一步", ImVec2(110.0f, 0.0f))) actions.previous_step = true;
        ImGui::EndDisabled();
        ImGui::SameLine();
        ImGui::BeginDisabled(finished);
        if (ImGui::Button("下一步 >", ImVec2(140.0f, 0.0f))) actions.next_step = true;
        ImGui::EndDisabled();
    }
    ImGui::End();
    return actions;
}

// ---- 模型库界面 ----------------------------------------------------

/// 截断到 UTF-8 字符边界并追加省略号 (卡片简介防溢出)。
static std::string truncateUtf8(const std::string& text, std::size_t max_bytes) {
    if (text.size() <= max_bytes) return text;
    std::size_t cut = max_bytes;
    while (cut > 0 && (static_cast<unsigned char>(text[cut]) & 0xC0) == 0x80) --cut;
    return text.substr(0, cut) + "…";
}

GLuint GlRenderer::thumbnailTexture(const std::string& png_path) {
    if (const auto it = thumbnail_textures_.find(png_path); it != thumbnail_textures_.end()) {
        return it->second;
    }
    GLuint texture = 0;
    int width = 0, height = 0, channels = 0;
    if (stbi_uc* pixels = stbi_load(png_path.c_str(), &width, &height, &channels, 4);
        pixels != nullptr) {
        glGenTextures(1, &texture);
        glBindTexture(GL_TEXTURE_2D, texture);
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR);
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR);
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_EDGE);
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE);
        glPixelStorei(GL_UNPACK_ALIGNMENT, 4);  // RGBA 行天然 4 字节对齐
        glTexImage2D(GL_TEXTURE_2D, 0, static_cast<GLint>(GL_RGBA8), width, height, 0, GL_RGBA,
                     GL_UNSIGNED_BYTE, pixels);
        glBindTexture(GL_TEXTURE_2D, 0);
        stbi_image_free(pixels);
    } else {
        std::fprintf(stderr, "[render] 警告: 缩略图加载失败 (%s): %s\n",
                     stbi_failure_reason(), png_path.c_str());
    }
    thumbnail_textures_.emplace(png_path, texture);  // 失败也缓存 0, 避免每帧重试
    return texture;
}

void GlRenderer::drawLibraryCard(const LibraryCard& card, const ImVec2& size, bool compact,
                                 LibraryActions& actions) {
    const ImU32 theme_color = themeColor32(card.theme);
    const ImVec4 ink = ImGui::ColorConvertU32ToFloat4(kColorInk);
    const float pad = 16.0f;
    // 大卡顶部为缩略图区 (缺图时显示主题色占位), 文字区整体下移
    const float thumb_height = compact ? 0.0f : std::floor(size.y * 0.365f);

    ImGui::PushStyleColor(ImGuiCol_ChildBg, ImVec4(1.0f, 1.0f, 1.0f, 1.0f));
    ImGui::PushStyleColor(ImGuiCol_Border, ImVec4(0.85f, 0.87f, 0.91f, 1.0f));
    ImGui::PushStyleVar(ImGuiStyleVar_ChildRounding, 12.0f);
    const std::string child_id = (compact ? "resume_" : "card_") + card.model_id;
    if (ImGui::BeginChild(child_id.c_str(), size, ImGuiChildFlags_Borders,
                          ImGuiWindowFlags_NoScrollbar | ImGuiWindowFlags_NoScrollWithMouse)) {
        ImDrawList* draw_list = ImGui::GetWindowDrawList();
        const ImVec2 origin = ImGui::GetWindowPos();

        // 整卡可点: 先提交并允许覆盖, 卡内的按钮 (收藏/继续) 优先响应
        ImGui::SetCursorPos(ImVec2(0.0f, 0.0f));
        ImGui::SetNextItemAllowOverlap();
        if (ImGui::InvisibleButton(("open_" + child_id).c_str(), size)) {
            actions.open_model_id = card.model_id;
        }
        const bool hovered = ImGui::IsItemHovered();
        if (hovered) ImGui::SetMouseCursor(ImGuiMouseCursor_Hand);

        // 顶部主题色条 + 悬停时主题色描边
        draw_list->AddRectFilled(origin, ImVec2(origin.x + size.x, origin.y + 5.0f), theme_color,
                                 12.0f, ImDrawFlags_RoundCornersTop);

        // ---- 缩略图区 (仅大卡): 主题色淡底 + 等比放置 PNG 缩略图 -------
        if (thumb_height > 0.0f) {
            const ImVec2 strip_min{origin.x + 1.0f, origin.y + 5.0f};
            const ImVec2 strip_max{origin.x + size.x - 1.0f, origin.y + 5.0f + thumb_height};
            draw_list->AddRectFilled(strip_min, strip_max,
                                     (theme_color & 0x00FFFFFF) | 0x16000000);
            const GLuint texture =
                card.thumbnail_path.empty() ? 0 : thumbnailTexture(card.thumbnail_path);
            if (texture != 0) {
                // 4:3 缩略图等比 contain, 两侧留主题色淡底不裁剪画面
                const float image_h = thumb_height - 8.0f;
                const float image_w =
                    std::min(image_h * (4.0f / 3.0f), strip_max.x - strip_min.x - 8.0f);
                const ImVec2 center{(strip_min.x + strip_max.x) * 0.5f,
                                    (strip_min.y + strip_max.y) * 0.5f};
                const ImVec2 image_min{center.x - image_w * 0.5f, center.y - image_h * 0.5f};
                const ImVec2 image_max{center.x + image_w * 0.5f, center.y + image_h * 0.5f};
                draw_list->AddImageRounded(
                    static_cast<ImTextureID>(static_cast<std::intptr_t>(texture)), image_min,
                    image_max, ImVec2(0.0f, 0.0f), ImVec2(1.0f, 1.0f),
                    IM_COL32(255, 255, 255, 255), 6.0f);
            } else {
                // 无缩略图: 居中主题名作占位 (与主题徽章同色系)
                const ImVec2 text_size = ImGui::CalcTextSize(card.theme.c_str());
                draw_list->AddText(
                    ImVec2((strip_min.x + strip_max.x - text_size.x) * 0.5f,
                           (strip_min.y + strip_max.y - text_size.y) * 0.5f),
                    (theme_color & 0x00FFFFFF) | 0x66000000, card.theme.c_str());
            }
        }

        if (hovered) {
            draw_list->AddRect(origin, ImVec2(origin.x + size.x, origin.y + size.y), theme_color,
                               12.0f, 0, 2.0f);
        }

        // ---- 标题行 -------------------------------------------------
        ImGui::SetCursorPos(ImVec2(pad, 14.0f + thumb_height));
        ImGui::TextColored(ink, "%s", card.name.c_str());
        if (card.completed) {
            ImGui::SameLine();
            const ImVec2 badge_pos = ImGui::GetCursorScreenPos();
            drawCheckBadge(draw_list, ImVec2(badge_pos.x + 10.0f, badge_pos.y + 10.0f), 9.0f,
                           kColorGreen);
            ImGui::Dummy(ImVec2(22.0f, 0.0f));
        }

        if (compact) {
            // ---- 小卡 (继续搭建区): 名称 / 进度条 / 继续按钮 ----------
            const std::string step_text = "第 " + std::to_string(card.current_step) + " / " +
                                          std::to_string(card.step_count) + " 步";
            const float step_text_w = ImGui::CalcTextSize(step_text.c_str()).x;
            ImGui::SetCursorPos(ImVec2(size.x - pad - step_text_w, 15.0f));
            ImGui::TextColored(kAccentVec, "%s", step_text.c_str());

            const float fraction =
                card.step_count > 0
                    ? static_cast<float>(card.current_step) / static_cast<float>(card.step_count)
                    : 0.0f;
            ImGui::SetCursorPos(ImVec2(pad, 46.0f));
            ImGui::ProgressBar(fraction, ImVec2(size.x - pad * 2.0f, 8.0f), "");

            ImGui::SetCursorPos(ImVec2(pad, 70.0f));
            ImGui::TextDisabled("难度 %s · %d 片", difficultyStars(card.difficulty).c_str(),
                                card.total_pieces);

            ImGui::SetCursorPos(ImVec2(size.x - pad - 126.0f, 64.0f));
            ImGui::PushStyleColor(ImGuiCol_Button, kAccentVec);
            ImGui::PushStyleColor(ImGuiCol_ButtonHovered, ImVec4(0.36f, 0.52f, 0.96f, 1.0f));
            ImGui::PushStyleColor(ImGuiCol_ButtonActive, ImVec4(0.22f, 0.36f, 0.82f, 1.0f));
            ImGui::PushStyleColor(ImGuiCol_Text, ImVec4(1.0f, 1.0f, 1.0f, 1.0f));
            if (ImGui::Button(("继续搭建 ▶##resume_" + card.model_id).c_str(),
                              ImVec2(126.0f, 32.0f))) {
                actions.open_model_id = card.model_id;
            }
            ImGui::PopStyleColor(4);
        } else {
            // ---- 大卡 (模型网格) ------------------------------------
            // 收藏星标 (标题行右侧, 缩略图之下)
            ImGui::SetCursorPos(ImVec2(size.x - 44.0f, 9.0f + thumb_height));
            ImGui::PushStyleColor(ImGuiCol_Button, ImVec4(0.0f, 0.0f, 0.0f, 0.0f));
            ImGui::PushStyleColor(ImGuiCol_ButtonHovered, ImVec4(0.94f, 0.68f, 0.12f, 0.18f));
            ImGui::PushStyleColor(ImGuiCol_ButtonActive, ImVec4(0.94f, 0.68f, 0.12f, 0.35f));
            ImGui::PushStyleColor(ImGuiCol_Text,
                                  card.favorited ? ImGui::ColorConvertU32ToFloat4(kColorGold)
                                                 : ImVec4(0.66f, 0.68f, 0.73f, 1.0f));
            if (ImGui::Button(((card.favorited ? "★##fav_" : "☆##fav_") + card.model_id).c_str(),
                              ImVec2(32.0f, 30.0f))) {
                actions.toggle_favorite_id = card.model_id;
            }
            ImGui::PopStyleColor(4);

            if (!card.name_en.empty()) {
                ImGui::SetCursorPos(ImVec2(pad, 41.0f + thumb_height));
                ImGui::TextDisabled("%s", card.name_en.c_str());
            }

            // 星级难度 + 片数/步数
            ImGui::SetCursorPos(ImVec2(pad, 66.0f + thumb_height));
            std::string filled, hollow;
            for (int i = 1; i <= 5; ++i) ((i <= card.difficulty) ? filled : hollow) += "★";
            ImGui::TextColored(ImGui::ColorConvertU32ToFloat4(kColorGold), "%s", filled.c_str());
            if (!hollow.empty()) {
                ImGui::SameLine(0.0f, 0.0f);
                ImGui::TextColored(ImVec4(0.80f, 0.82f, 0.86f, 1.0f), "%s", hollow.c_str());
            }
            ImGui::SameLine(0.0f, 12.0f);
            ImGui::TextDisabled("%d 片 · %d 步", card.total_pieces, card.step_count);

            // 主题徽章; 用到扩展片型的模型追加 "需要扩展装" 角标
            // (CONTENT_STRATEGY.md §2.5: 产品端据 BOM 分层展示购前提示)
            ImGui::SetCursorPos(ImVec2(pad, 92.0f + thumb_height));
            drawThemeBadge(card.theme, theme_color);
            if (card.bom_known && !card.core9_only) {
                ImGui::SameLine(0.0f, 8.0f);
                drawThemeBadge("需要扩展装", kColorExpansion);
                if (ImGui::IsItemHovered()) {
                    ImGui::SetTooltip("本模型用到基础套装之外的扩展片型");
                }
            }
            // 订阅内容: 温和的 "订阅解锁" 角标 (元数据照常可浏览,
            // 点击进入订阅引导而非教程, COMMERCIAL_PLAN §2.1)
            if (!card.free_tier) {
                ImGui::SameLine(0.0f, 8.0f);
                drawThemeBadge("订阅解锁", kColorSubscription);
                if (ImGui::IsItemHovered()) {
                    ImGui::SetTooltip("订阅内容: 简介和清单随时可以看, "
                                      "完整教程订阅后解锁");
                }
            }

            // 简介 (两行内, 超长截断)
            if (!card.description.empty()) {
                ImGui::SetCursorPos(ImVec2(pad, 124.0f + thumb_height));
                ImGui::PushTextWrapPos(size.x - pad);
                ImGui::TextDisabled("%s", truncateUtf8(card.description, 78).c_str());
                ImGui::PopTextWrapPos();
            }

            // ---- 底部状态行 ------------------------------------------
            ImGui::SetCursorPos(ImVec2(pad, size.y - 32.0f));
            if (card.completed) {
                ImGui::TextColored(ImGui::ColorConvertU32ToFloat4(kColorGreen),
                                   "已完成 · 点击可重新搭建");
            } else if (card.started) {
                const float fraction =
                    card.step_count > 0 ? static_cast<float>(card.current_step) /
                                              static_cast<float>(card.step_count)
                                        : 0.0f;
                ImGui::ProgressBar(fraction, ImVec2(size.x * 0.42f, 8.0f), "");
                ImGui::SameLine();
                ImGui::TextColored(kAccentVec, "第 %d / %d 步", card.current_step,
                                   card.step_count);
            } else if (!card.free_tier) {
                ImGui::TextColored(ImGui::ColorConvertU32ToFloat4(kColorSubscription),
                                   "订阅内容 · 点击了解怎么解锁");
            } else {
                ImGui::TextDisabled("未开始 · 点击开始搭建");
            }
        }
    }
    ImGui::EndChild();
    ImGui::PopStyleVar();
    ImGui::PopStyleColor(2);
}

LibraryActions GlRenderer::submitLibrary(const std::vector<LibraryCard>& cards,
                                         core::AgeMode age_mode, bool inventory_configured,
                                         bool activate_buildable_filter) {
    LibraryActions actions;
    const ImGuiIO& io = ImGui::GetIO();

    // 年龄分层 (UI_UX_SPEC.md §2): 启蒙 = 超大卡片无筛选;
    // 标准 = 难度/主题两个筛选器; 进阶 = 全量筛选 + 紧凑卡片
    const bool simple_layout = age_mode == core::AgeMode::Age4_6;
    const bool full_filters = age_mode == core::AgeMode::Age10_12;

    // 库存录入界面 "保存, 看看我能搭什么" 的一次性跳转: 强制开启筛选
    // (仅 10+ 进阶模式可见该筛选, 其余档位忽略)
    if (activate_buildable_filter && inventory_configured && full_filters) {
        library_buildable_only_ = true;
    }
    // 非进阶档位收起 收藏/核心 9 片/我能搭的 三个筛选: 状态同步清零,
    // 防止跨帧/跨档位残留的看不见的筛选悄悄过滤列表
    if (!full_filters) {
        library_favorites_only_ = false;
        library_core9_only_ = false;
        library_buildable_only_ = false;
    }
    // "免费模型" 筛选属于内容可及性, 标准档 (7-9) 起就展示; 4-6 启蒙档
    // 整行筛选隐藏, 同步清零 (同上防看不见的筛选), 订阅引导弹窗的
    // 「先看免费模型」按钮也随之隐藏 (见 submitSubscriptionPrompt)
    library_filter_row_visible_ = !simple_layout;
    if (simple_layout) {
        library_free_only_ = false;
    }

    // 主题筛选候选: 全部卡片标签去重, 保持出现顺序
    std::vector<std::string> all_tags;
    for (const auto& card : cards) {
        for (const auto& tag : card.tags) {
            if (std::find(all_tags.begin(), all_tags.end(), tag) == all_tags.end()) {
                all_tags.push_back(tag);
            }
        }
    }

    const float margin = 26.0f;
    const float panel_width = std::min(io.DisplaySize.x - margin * 2.0f, 1240.0f);
    const float panel_height = io.DisplaySize.y - margin * 2.0f;
    ImGui::SetNextWindowPos(ImVec2(io.DisplaySize.x * 0.5f, margin), ImGuiCond_Always,
                            ImVec2(0.5f, 0.0f));
    ImGui::SetNextWindowSize(ImVec2(panel_width, panel_height));
    ImGui::SetNextWindowBgAlpha(0.965f);
    ImGui::PushStyleVar(ImGuiStyleVar_WindowRounding, 16.0f);
    ImGui::PushStyleVar(ImGuiStyleVar_WindowPadding, ImVec2(26.0f, 22.0f));
    const ImGuiWindowFlags panel_flags = ImGuiWindowFlags_NoDecoration | ImGuiWindowFlags_NoMove |
                                         ImGuiWindowFlags_NoSavedSettings |
                                         ImGuiWindowFlags_NoFocusOnAppearing;
    if (ImGui::Begin("##library_screen", nullptr, panel_flags)) {
        // ---- 页眉 ----------------------------------------------------
        if (font_title_ != nullptr) ImGui::PushFont(font_title_);
        ImGui::TextColored(ImGui::ColorConvertU32ToFloat4(kColorInk), "MagTile Studio 模型库");
        if (font_title_ != nullptr) ImGui::PopFont();

        // 家长区入口: 刻意小尺寸 (全应用唯一低于 48dp 的可点元素,
        // 防儿童误入) + 家长门兜底, 见 UI_UX_SPEC.md §5.3 / §9
        const float entry_width = 96.0f;
        // 库存入口: 常驻页眉, 家长孩子都可用 (录库存不是家长区专属)
        const float inventory_entry_width = 128.0f;
        ImGui::SameLine(panel_width - 26.0f - entry_width - 10.0f - inventory_entry_width);
        if (ImGui::Button("我的磁力片##inventory_entry", ImVec2(inventory_entry_width, 32.0f))) {
            actions.open_inventory = true;
        }
        if (ImGui::IsItemHovered()) {
            ImGui::SetTooltip("登记家里有哪些磁力片, 模型库就能筛出 \"我能搭的\"");
        }
        ImGui::SameLine(panel_width - 26.0f - entry_width);
        ImGui::PushStyleColor(ImGuiCol_Button, ImVec4(0.42f, 0.45f, 0.52f, 0.12f));
        ImGui::PushStyleColor(ImGuiCol_Text, ImVec4(0.42f, 0.45f, 0.52f, 1.0f));
        if (ImGui::Button("家长区##parent_entry", ImVec2(entry_width, 32.0f))) {
            actions.open_parent_area = true;
        }
        ImGui::PopStyleColor(2);
        if (ImGui::IsItemHovered()) {
            ImGui::SetTooltip("订阅与设置 (需要家长完成验证)");
        }

        ImGui::TextDisabled("挑选一个模型, 跟随 3D 分步教程开始搭建 · 共 %d 个模型 · Esc 退出",
                            static_cast<int>(cards.size()));
        ImGui::Spacing();

        // ---- 筛选行: 搜索 / 难度 / 主题 / 收藏 -------------------------
        // 4-6 岁启蒙模式整行隐藏 (无搜索、无筛选, UI_UX_SPEC.md §2/§4.6)
        if (!simple_layout) {
            ImGui::SetNextItemWidth(300.0f);
            ImGui::InputTextWithHint("##library_search", "搜索模型名称…", library_search_.data(),
                                     library_search_.size());
            ImGui::SameLine();
            static const char* kDifficultyItems[] = {"全部难度", "★",     "★★",
                                                     "★★★",   "★★★★", "★★★★★"};
            ImGui::SetNextItemWidth(140.0f);
            if (ImGui::BeginCombo("##difficulty_filter",
                                  kDifficultyItems[library_difficulty_filter_])) {
                for (int i = 0; i < 6; ++i) {
                    if (ImGui::Selectable(kDifficultyItems[i], i == library_difficulty_filter_)) {
                        library_difficulty_filter_ = i;
                    }
                }
                ImGui::EndCombo();
            }
            ImGui::SameLine();
            ImGui::SetNextItemWidth(170.0f);
            const std::string theme_preview =
                library_theme_filter_.empty() ? "全部主题" : library_theme_filter_;
            if (ImGui::BeginCombo("##theme_filter", theme_preview.c_str())) {
                if (ImGui::Selectable("全部主题", library_theme_filter_.empty())) {
                    library_theme_filter_.clear();
                }
                for (const auto& tag : all_tags) {
                    if (ImGui::Selectable(tag.c_str(), tag == library_theme_filter_)) {
                        library_theme_filter_ = tag;
                    }
                }
                ImGui::EndCombo();
            }
            ImGui::SameLine();
            // "免费模型": 只看免费层 (目录 tags 含「免费」, 三端与
            // starter 打包同一口径, 见 docs/FREE_TIER_MANIFEST.md)。
            // 内容可及性筛选, 标准档 (7-9) 起就展示 —— 不同于收藏/
            // 核心 9 片等进阶专属维度, 订阅引导「先看免费模型」要在
            // 有筛选行的档位都能落地
            ImGui::Checkbox("免费模型", &library_free_only_);
            if (ImGui::IsItemHovered()) {
                ImGui::SetTooltip("只显示免费层的模型 (随时可搭); "
                                  "其余模型订阅后解锁教程, 依旧可以浏览");
            }
            // 收藏/核心 9 片/我能搭的 只在 10+ 进阶模式展示 (§2:
            // 7-9 标准模式筛选行保持精简)
            if (full_filters) {
                ImGui::SameLine();
                ImGui::Checkbox("只看收藏", &library_favorites_only_);
                ImGui::SameLine();
                // "只用核心 9 片": 只看基础套装 (核心 9 片型) 就能搭的模型
                // (与 Qt 版同一共享判定口径, 见 core::isCoreTile / TILE_CATALOG.md)
                ImGui::Checkbox("只用核心 9 片", &library_core9_only_);
                if (ImGui::IsItemHovered()) {
                    ImGui::SetTooltip("只显示基础套装 (核心 9 片型) 就能搭的模型, "
                                      "不需要任何扩展装");
                }
                ImGui::SameLine();
                // "我能搭的": 依据磁力片库存过滤 BOM 满足的模型 (§5.2);
                // 未登记库存时禁用并引导先去登记, 不显示全空列表
                if (inventory_configured) {
                    ImGui::Checkbox("我能搭的", &library_buildable_only_);
                    if (ImGui::IsItemHovered()) {
                        ImGui::SetTooltip("只显示现有磁力片库存足够搭建的模型");
                    }
                } else {
                    // 未登记库存: 筛选不可用, 就地给出图形录入入口 (§10 跳过
                    // 永远可见, 引导而非报错)
                    library_buildable_only_ = false;
                    ImGui::BeginDisabled();
                    bool unavailable = false;
                    ImGui::Checkbox("我能搭的", &unavailable);
                    ImGui::EndDisabled();
                    if (ImGui::IsItemHovered(ImGuiHoveredFlags_AllowWhenDisabled)) {
                        ImGui::SetTooltip("先登记家里的磁力片, 就能只看库存足够搭的模型");
                    }
                    ImGui::SameLine(0.0f, 4.0f);
                    ImGui::PushStyleColor(ImGuiCol_Text, kAccentVec);
                    if (ImGui::SmallButton("去登记 ▶##filter_go_inventory")) {
                        actions.open_inventory = true;
                    }
                    ImGui::PopStyleColor();
                }
            }
        }

        ImGui::Spacing();
        ImGui::Separator();
        ImGui::Spacing();

        ImGui::BeginChild("##library_scroll", ImVec2(0.0f, 0.0f), ImGuiChildFlags_None,
                          ImGuiWindowFlags_NoBackground);
        // 启蒙模式加大卡片间距, 防胖手指误触 (§4.1 间距 >= 8dp 从宽执行)
        const float spacing = simple_layout ? 24.0f : 16.0f;
        const float avail_width = ImGui::GetContentRegionAvail().x;
        const auto columnsFor = [&](float card_width) {
            return std::max(1, static_cast<int>((avail_width + spacing) /
                                                (card_width + spacing)));
        };

        // ---- 继续搭建 (进行中的模型, 不受筛选影响置顶展示) --------------
        std::vector<const LibraryCard*> in_progress;
        for (const auto& card : cards) {
            if (card.started && !card.completed) in_progress.push_back(&card);
        }
        if (!in_progress.empty()) {
            ImGui::TextColored(kAccentVec, "▶ 继续搭建");
            ImGui::SameLine();
            ImGui::TextDisabled("上次没搭完的模型 (%d 个)",
                                static_cast<int>(in_progress.size()));
            ImGui::Spacing();
            // 启蒙模式 "继续上次" 卡片同步放大 (首页大卡片, §4.6)
            const ImVec2 resume_size = simple_layout ? ImVec2{560.0f, 132.0f}
                                                     : ImVec2{392.0f, 106.0f};
            const int columns = columnsFor(resume_size.x);
            int index = 0;
            for (const LibraryCard* card : in_progress) {
                drawLibraryCard(*card, resume_size, /*compact=*/true, actions);
                ++index;
                if (index % columns != 0 && index < static_cast<int>(in_progress.size())) {
                    ImGui::SameLine(0.0f, spacing);
                }
            }
            ImGui::Spacing();
            ImGui::Spacing();
        }

        // ---- 全部模型 (按搜索与筛选条件过滤) ---------------------------
        // 启蒙模式无筛选器, 忽略跨帧残留的筛选状态, 永远全量展示
        std::vector<const LibraryCard*> filtered;
        const std::string search = library_search_.data();
        for (const auto& card : cards) {
            if (!simple_layout) {
                if (library_difficulty_filter_ != 0 &&
                    card.difficulty != library_difficulty_filter_) {
                    continue;
                }
                if (!library_theme_filter_.empty() &&
                    std::find(card.tags.begin(), card.tags.end(), library_theme_filter_) ==
                        card.tags.end()) {
                    continue;
                }
                if (library_favorites_only_ && !card.favorited) continue;
                // "免费模型": 只留免费层 (订阅内容照常出现在全量列表)
                if (library_free_only_ && !card.free_tier) continue;
                // "只用核心 9 片": BOM 未知 (模型文件有问题) 的模型不进核心筛选
                if (library_core9_only_ && !(card.bom_known && card.core9_only)) continue;
                if (inventory_configured && library_buildable_only_ && !card.buildable) {
                    continue;
                }
                if (!matchesSearch(card.name, search) && !matchesSearch(card.name_en, search) &&
                    !matchesSearch(card.model_id, search)) {
                    continue;
                }
            }
            filtered.push_back(&card);
        }

        ImGui::TextColored(ImGui::ColorConvertU32ToFloat4(kColorInk), "全部模型");
        ImGui::SameLine();
        ImGui::TextDisabled("%d / %d 个", static_cast<int>(filtered.size()),
                            static_cast<int>(cards.size()));
        ImGui::Spacing();

        // 分龄卡片密度 (UI_UX_SPEC.md §2, 1240px 面板宽口径):
        //   4-6 启蒙 560px 超大卡片约每行 2 张 (图文放大便于辨认点按,
        //        卡片上部约 36% 为缩略图区, drawLibraryCard thumb_height);
        //   7-9 标准 300px 每行 3~4 张;
        //   10+ 进阶 252px 紧凑卡片每行 4~5 张。
        const ImVec2 card_size = simple_layout ? ImVec2{560.0f, 420.0f}
                                : full_filters ? ImVec2{252.0f, 330.0f}
                                               : ImVec2{300.0f, 340.0f};
        if (filtered.empty()) {
            ImGui::Dummy(ImVec2(0.0f, 36.0f));
            const char* empty_text = "没有找到匹配的模型, 试试清空搜索或放宽筛选条件";
            const float text_width = ImGui::CalcTextSize(empty_text).x;
            ImGui::SetCursorPosX(std::max(0.0f, (avail_width - text_width) * 0.5f));
            ImGui::TextDisabled("%s", empty_text);

            // 「我能搭的」空态推荐 (§5.2): 无视其他筛选, 从库存足够
            // 搭建的模型里按难度升序 (同难度片数少者优先) 推荐 3 个,
            // 不让孩子面对一句"没有结果"就停下
            if (library_buildable_only_ && inventory_configured) {
                std::vector<const LibraryCard*> recommended;
                for (const auto& card : cards) {
                    if (card.buildable) recommended.push_back(&card);
                }
                std::stable_sort(recommended.begin(), recommended.end(),
                                 [](const LibraryCard* a, const LibraryCard* b) {
                                     if (a->difficulty != b->difficulty) {
                                         return a->difficulty < b->difficulty;
                                     }
                                     return a->total_pieces < b->total_pieces;
                                 });
                if (recommended.size() > 3) recommended.resize(3);
                if (!recommended.empty()) {
                    ImGui::Spacing();
                    ImGui::Spacing();
                    ImGui::TextColored(ImGui::ColorConvertU32ToFloat4(kColorGreen),
                                       "✓ 不过这几个现在就能搭:");
                    ImGui::Spacing();
                    const int rec_columns = columnsFor(card_size.x);
                    int rec_index = 0;
                    for (const LibraryCard* card : recommended) {
                        drawLibraryCard(*card, card_size, /*compact=*/false, actions);
                        ++rec_index;
                        if (rec_index % rec_columns != 0 &&
                            rec_index < static_cast<int>(recommended.size())) {
                            ImGui::SameLine(0.0f, spacing);
                        }
                    }
                }
            }
        } else {
            const int columns = columnsFor(card_size.x);
            int index = 0;
            for (const LibraryCard* card : filtered) {
                drawLibraryCard(*card, card_size, /*compact=*/false, actions);
                ++index;
                if (index % columns != 0 && index < static_cast<int>(filtered.size())) {
                    ImGui::SameLine(0.0f, spacing);
                }
            }
        }
        ImGui::EndChild();
    }
    ImGui::End();
    ImGui::PopStyleVar(2);
    return actions;
}

InventoryOnboardingActions GlRenderer::submitInventoryOnboarding() {
    InventoryOnboardingActions actions;
    const ImGuiIO& io = ImGui::GetIO();

    // ImGui 原生模态弹窗: 自带压暗遮罩并阻断其下窗口 (模型库) 的输入
    if (!ImGui::IsPopupOpen("##inventory_onboarding")) {
        ImGui::OpenPopup("##inventory_onboarding");
    }
    ImGui::SetNextWindowPos(ImVec2(io.DisplaySize.x * 0.5f, io.DisplaySize.y * 0.5f),
                            ImGuiCond_Always, ImVec2(0.5f, 0.5f));
    ImGui::SetNextWindowSize(ImVec2(560.0f, 0.0f));  // 固定宽, 高度自适应
    ImGui::PushStyleVar(ImGuiStyleVar_WindowRounding, 16.0f);
    ImGui::PushStyleVar(ImGuiStyleVar_WindowPadding, ImVec2(30.0f, 26.0f));
    ImGui::PushStyleColor(ImGuiCol_ModalWindowDimBg, ImVec4(0.10f, 0.12f, 0.16f, 0.45f));
    const ImGuiWindowFlags flags = ImGuiWindowFlags_NoDecoration | ImGuiWindowFlags_NoMove |
                                   ImGuiWindowFlags_NoSavedSettings |
                                   ImGuiWindowFlags_AlwaysAutoResize;
    if (ImGui::BeginPopupModal("##inventory_onboarding", nullptr, flags)) {
        const float avail = ImGui::GetContentRegionAvail().x;

        if (font_title_ != nullptr) ImGui::PushFont(font_title_);
        ImGui::TextColored(ImGui::ColorConvertU32ToFloat4(kColorInk), "先登记家里的磁力片");
        if (font_title_ != nullptr) ImGui::PopFont();
        ImGui::Spacing();

        ImGui::PushTextWrapPos(avail);
        ImGui::TextUnformatted(
            "告诉我们家里有哪些磁力片, 模型库就能用「我能搭的」筛选出"
            "库存足够的模型, 开搭前也不会再因为缺片而中断。");
        ImGui::PopTextWrapPos();
        ImGui::Spacing();
        ImGui::Separator();
        ImGui::Spacing();

        ImGui::TextDisabled("照着盒子数一数就行, 大约 2 分钟; 之后随时可在 \"我的磁力片\" 修改。");
        ImGui::Spacing();

        // 主操作: 进入按片型计数的图形录入界面 (UI_UX_SPEC.md §10.2);
        // "稍后再说" 永远可见 —— 录库存不是付费墙 (§10 跳过永远可见)
        ImGui::PushStyleColor(ImGuiCol_Button, ImVec4(0.28f, 0.44f, 0.93f, 0.90f));
        ImGui::PushStyleColor(ImGuiCol_ButtonHovered, ImVec4(0.24f, 0.40f, 0.88f, 1.0f));
        ImGui::PushStyleColor(ImGuiCol_ButtonActive, ImVec4(0.20f, 0.35f, 0.80f, 1.0f));
        ImGui::PushStyleColor(ImGuiCol_Text, ImVec4(1.0f, 1.0f, 1.0f, 1.0f));
        if (ImGui::Button("现在登记 ▶##onboarding_start", ImVec2(avail, 52.0f))) {
            actions.start_entry = true;
            ImGui::CloseCurrentPopup();
        }
        ImGui::PopStyleColor(4);
        if (ImGui::Button("稍后再说##onboarding_dismiss", ImVec2(avail, 48.0f))) {
            actions.dismissed = true;
            ImGui::CloseCurrentPopup();
        }
        ImGui::EndPopup();
    }
    ImGui::PopStyleColor();
    ImGui::PopStyleVar(2);
    return actions;
}

SubscriptionPromptActions GlRenderer::submitSubscriptionPrompt(const std::string& model_name) {
    SubscriptionPromptActions actions;
    const ImGuiIO& io = ImGui::GetIO();

    // 与库存 onboarding 同一套模态弹窗骨架 (压暗遮罩 + 阻断库界面输入)。
    // 文案铁律 (UI_UX_SPEC.md §11/§12.2): 儿童侧只说 "请家长来解锁",
    // 无价格/无倒计时/无催促/不用红色; 免费层永久免费先说明白。
    if (!ImGui::IsPopupOpen("##subscription_prompt")) {
        ImGui::OpenPopup("##subscription_prompt");
    }
    ImGui::SetNextWindowPos(ImVec2(io.DisplaySize.x * 0.5f, io.DisplaySize.y * 0.5f),
                            ImGuiCond_Always, ImVec2(0.5f, 0.5f));
    ImGui::SetNextWindowSize(ImVec2(560.0f, 0.0f));  // 固定宽, 高度自适应
    ImGui::PushStyleVar(ImGuiStyleVar_WindowRounding, 16.0f);
    ImGui::PushStyleVar(ImGuiStyleVar_WindowPadding, ImVec2(30.0f, 26.0f));
    ImGui::PushStyleColor(ImGuiCol_ModalWindowDimBg, ImVec4(0.10f, 0.12f, 0.16f, 0.45f));
    const ImGuiWindowFlags flags = ImGuiWindowFlags_NoDecoration | ImGuiWindowFlags_NoMove |
                                   ImGuiWindowFlags_NoSavedSettings |
                                   ImGuiWindowFlags_AlwaysAutoResize;
    if (ImGui::BeginPopupModal("##subscription_prompt", nullptr, flags)) {
        const float avail = ImGui::GetContentRegionAvail().x;

        if (font_title_ != nullptr) ImGui::PushFont(font_title_);
        ImGui::TextColored(ImGui::ColorConvertU32ToFloat4(kColorInk), "这个模型在订阅内容里");
        if (font_title_ != nullptr) ImGui::PopFont();
        ImGui::Spacing();

        ImGui::PushTextWrapPos(avail);
        ImGui::TextUnformatted(("「" + model_name +
                                "」属于订阅内容: 简介和磁力片清单随时可以看, "
                                "完整的 3D 分步教程订阅后解锁。")
                                   .c_str());
        ImGui::Spacing();
        ImGui::TextUnformatted(
            "免费区的模型永久免费、随时可搭; 订阅会解锁全部模型, 还有每周上新。"
            "想解锁的话, 请家长到家长区看看订阅说明吧。");
        ImGui::PopTextWrapPos();
        ImGui::Spacing();
        ImGui::Separator();
        ImGui::Spacing();

        // 主操作: 进家长区 (先过家长门, 订阅说明在门后 —— §11 铁律);
        // 次操作: 一键切到「免费模型」筛选, 孩子不需要家长也有得搭
        ImGui::PushStyleColor(ImGuiCol_Button, ImVec4(0.48f, 0.37f, 0.85f, 0.90f));
        ImGui::PushStyleColor(ImGuiCol_ButtonHovered, ImVec4(0.44f, 0.33f, 0.80f, 1.0f));
        ImGui::PushStyleColor(ImGuiCol_ButtonActive, ImVec4(0.38f, 0.28f, 0.72f, 1.0f));
        ImGui::PushStyleColor(ImGuiCol_Text, ImVec4(1.0f, 1.0f, 1.0f, 1.0f));
        if (ImGui::Button("请家长来解锁 ▶##subscription_parent", ImVec2(avail, 52.0f))) {
            actions.open_parent_area = true;
            ImGui::CloseCurrentPopup();
        }
        ImGui::PopStyleColor(4);
        // 4-6 启蒙档筛选行整行隐藏, 一键切筛选无处落地 -> 不出此按钮
        if (library_filter_row_visible_ &&
            ImGui::Button("先看免费模型##subscription_browse_free", ImVec2(avail, 48.0f))) {
            actions.browse_free = true;
            library_free_only_ = true;  // 筛选状态归渲染器, 就地切换
            ImGui::CloseCurrentPopup();
        }
        if (ImGui::Button("回模型库##subscription_dismiss", ImVec2(avail, 44.0f))) {
            actions.dismissed = true;
            ImGui::CloseCurrentPopup();
        }
        ImGui::EndPopup();
    }
    ImGui::PopStyleColor();
    ImGui::PopStyleVar(2);
    return actions;
}

// ---- 库存录入界面 (UI_UX_SPEC.md §10.2) ------------------------------

/// 库存数量的界面上限: 防误触键盘/长按连加输出离谱数字
/// (存储层只校验 >= 0, 上限是纯 UI 约束)。
constexpr int kInventoryCountMax = 999;

void GlRenderer::drawInventoryCard(const InventoryEditorRow& row, const ImVec2& size,
                                   InventoryEditorActions& actions) {
    const float pad = 14.0f;
    ImGui::PushStyleColor(ImGuiCol_ChildBg, ImVec4(1.0f, 1.0f, 1.0f, 1.0f));
    ImGui::PushStyleColor(ImGuiCol_Border, ImVec4(0.85f, 0.87f, 0.91f, 1.0f));
    ImGui::PushStyleVar(ImGuiStyleVar_ChildRounding, 12.0f);
    const std::string child_id = "inv_" + row.shape_id;
    if (ImGui::BeginChild(child_id.c_str(), size, ImGuiChildFlags_Borders,
                          ImGuiWindowFlags_NoScrollbar | ImGuiWindowFlags_NoScrollWithMouse)) {
        // 标题行: 中文名 (拥有数量 > 0 时正色, 否则弱化)
        ImGui::SetCursorPos(ImVec2(pad, 12.0f));
        if (row.count > 0) {
            ImGui::TextColored(ImGui::ColorConvertU32ToFloat4(kColorInk), "%s",
                               row.name_zh.c_str());
        } else {
            ImGui::TextDisabled("%s", row.name_zh.c_str());
        }
        ImGui::SameLine();
        ImGui::TextDisabled("(%s)", row.shape_id.c_str());

        // 步进行: [-] [数量可直接输入] [+], 按钮 48dp 且支持长按连加
        // (UI_UX_SPEC.md §4.1 触控目标 / §10.2 步进器规范)
        const float button_side = 48.0f;
        const float input_width = size.x - pad * 2.0f - button_side * 2.0f - 16.0f;
        ImGui::SetCursorPos(ImVec2(pad, size.y - button_side - 12.0f));

        int new_count = row.count;
        ImGui::PushItemFlag(ImGuiItemFlags_ButtonRepeat, true);  // 长按连加/连减
        ImGui::BeginDisabled(row.count <= 0);
        if (ImGui::Button(("-##dec_" + row.shape_id).c_str(),
                          ImVec2(button_side, button_side))) {
            new_count = row.count - 1;
        }
        ImGui::EndDisabled();
        ImGui::SameLine(0.0f, 8.0f);
        ImGui::SetNextItemWidth(input_width);
        // 直接输入: InputInt 无内置 +/- (step=0), 数字键盘直接改数量
        int typed = row.count;
        ImGui::PushStyleVar(ImGuiStyleVar_FramePadding,
                            ImVec2(10.0f, (button_side - ImGui::GetTextLineHeight()) * 0.5f));
        if (ImGui::InputInt(("##count_" + row.shape_id).c_str(), &typed, 0, 0)) {
            new_count = typed;
        }
        ImGui::PopStyleVar();
        ImGui::SameLine(0.0f, 8.0f);
        ImGui::BeginDisabled(row.count >= kInventoryCountMax);
        if (ImGui::Button(("+##inc_" + row.shape_id).c_str(),
                          ImVec2(button_side, button_side))) {
            new_count = row.count + 1;
        }
        ImGui::EndDisabled();
        ImGui::PopItemFlag();

        new_count = std::clamp(new_count, 0, kInventoryCountMax);
        if (new_count != row.count) {
            actions.count_changes.emplace_back(row.shape_id, new_count);
        }
    }
    ImGui::EndChild();
    ImGui::PopStyleVar();
    ImGui::PopStyleColor(2);
}

InventoryEditorActions GlRenderer::submitInventoryEditor(
    const std::vector<InventoryEditorRow>& rows) {
    InventoryEditorActions actions;
    const ImGuiIO& io = ImGui::GetIO();

    const float margin = 26.0f;
    const float panel_width = std::min(io.DisplaySize.x - margin * 2.0f, 1240.0f);
    const float panel_height = io.DisplaySize.y - margin * 2.0f;
    ImGui::SetNextWindowPos(ImVec2(io.DisplaySize.x * 0.5f, margin), ImGuiCond_Always,
                            ImVec2(0.5f, 0.0f));
    ImGui::SetNextWindowSize(ImVec2(panel_width, panel_height));
    ImGui::SetNextWindowBgAlpha(0.965f);
    ImGui::PushStyleVar(ImGuiStyleVar_WindowRounding, 16.0f);
    ImGui::PushStyleVar(ImGuiStyleVar_WindowPadding, ImVec2(26.0f, 22.0f));
    const ImGuiWindowFlags panel_flags = ImGuiWindowFlags_NoDecoration | ImGuiWindowFlags_NoMove |
                                         ImGuiWindowFlags_NoSavedSettings |
                                         ImGuiWindowFlags_NoFocusOnAppearing;
    if (ImGui::Begin("##inventory_editor", nullptr, panel_flags)) {
        // ---- 页眉 ----------------------------------------------------
        if (font_title_ != nullptr) ImGui::PushFont(font_title_);
        ImGui::TextColored(ImGui::ColorConvertU32ToFloat4(kColorInk), "家里有哪些磁力片?");
        if (font_title_ != nullptr) ImGui::PopFont();
        ImGui::TextDisabled(
            "照着盒子数一数, 用 + / - 或直接输入数量; 保存后模型库就能筛出 \"我能搭的\"");
        ImGui::Spacing();
        ImGui::Separator();
        ImGui::Spacing();

        // ---- 片型卡片网格 (核心套装在前, 扩展包分组在后) ----------------
        // 底部固定操作条预留高度
        const float footer_height = 78.0f;
        ImGui::BeginChild("##inventory_scroll", ImVec2(0.0f, -footer_height),
                          ImGuiChildFlags_None, ImGuiWindowFlags_NoBackground);
        const float spacing = 16.0f;
        const float avail_width = ImGui::GetContentRegionAvail().x;
        const ImVec2 card_size{272.0f, 108.0f};
        const int columns = std::max(
            1, static_cast<int>((avail_width + spacing) / (card_size.x + spacing)));

        const auto drawGroup = [&](const char* title, const char* subtitle, bool expansion) {
            std::vector<const InventoryEditorRow*> group;
            for (const auto& row : rows) {
                if (row.expansion == expansion) group.push_back(&row);
            }
            if (group.empty()) return;
            ImGui::TextColored(ImGui::ColorConvertU32ToFloat4(kColorInk), "%s", title);
            ImGui::SameLine();
            ImGui::TextDisabled("%s", subtitle);
            ImGui::Spacing();
            int index = 0;
            for (const InventoryEditorRow* row : group) {
                drawInventoryCard(*row, card_size, actions);
                ++index;
                if (index % columns != 0 && index < static_cast<int>(group.size())) {
                    ImGui::SameLine(0.0f, spacing);
                }
            }
            ImGui::Spacing();
            ImGui::Spacing();
        };
        drawGroup("基础套装", "最常见的 9 种片型", /*expansion=*/false);
        drawGroup("扩展包", "没有就保持 0, 不影响基础模型", /*expansion=*/true);
        ImGui::EndChild();

        // ---- 底部操作条: 合计 + 返回 / 保存 / 保存并匹配 -----------------
        ImGui::Separator();
        int total = 0;
        for (const auto& row : rows) total += row.count;
        ImGui::Text("合计 %d 片", total);
        ImGui::SameLine();
        ImGui::TextDisabled("数量为 0 的片型也会记住 \"明确没有\"");

        const float action_width = 236.0f;
        const float back_width = 128.0f;
        ImGui::SameLine(std::max(
            0.0f, ImGui::GetContentRegionAvail().x + ImGui::GetCursorPosX() -
                      (back_width + action_width * 2.0f + 20.0f)));
        if (ImGui::Button("返回模型库##inventory_back", ImVec2(back_width, 48.0f))) {
            actions.back = true;
        }
        if (ImGui::IsItemHovered()) {
            ImGui::SetTooltip("不保存本次修改");
        }
        ImGui::SameLine(0.0f, 10.0f);
        if (ImGui::Button("保存库存##inventory_save", ImVec2(action_width, 48.0f))) {
            actions.save = true;
        }
        ImGui::SameLine(0.0f, 10.0f);
        ImGui::PushStyleColor(ImGuiCol_Button, ImVec4(0.28f, 0.44f, 0.93f, 0.90f));
        ImGui::PushStyleColor(ImGuiCol_ButtonHovered, ImVec4(0.24f, 0.40f, 0.88f, 1.0f));
        ImGui::PushStyleColor(ImGuiCol_ButtonActive, ImVec4(0.20f, 0.35f, 0.80f, 1.0f));
        ImGui::PushStyleColor(ImGuiCol_Text, ImVec4(1.0f, 1.0f, 1.0f, 1.0f));
        if (ImGui::Button("保存, 看看我能搭什么 ▶##inventory_save_match",
                          ImVec2(action_width, 48.0f))) {
            actions.save_and_match = true;
        }
        ImGui::PopStyleColor(4);
    }
    ImGui::End();
    ImGui::PopStyleVar(2);
    return actions;
}

ParentGateActions GlRenderer::submitParentGate(const ParentGateState& state) {
    ParentGateActions actions;
    const ImGuiIO& io = ImGui::GetIO();

    ImGui::SetNextWindowPos(ImVec2(io.DisplaySize.x * 0.5f, io.DisplaySize.y * 0.5f),
                            ImGuiCond_Always, ImVec2(0.5f, 0.5f));
    ImGui::SetNextWindowSize(ImVec2(480.0f, 0.0f));  // 固定宽, 高度自适应
    ImGui::SetNextWindowBgAlpha(0.975f);
    ImGui::PushStyleVar(ImGuiStyleVar_WindowRounding, 16.0f);
    ImGui::PushStyleVar(ImGuiStyleVar_WindowPadding, ImVec2(30.0f, 26.0f));
    const ImGuiWindowFlags flags = ImGuiWindowFlags_NoDecoration | ImGuiWindowFlags_NoMove |
                                   ImGuiWindowFlags_NoSavedSettings |
                                   ImGuiWindowFlags_AlwaysAutoResize;
    if (ImGui::Begin("##parent_gate", nullptr, flags)) {
        const float avail = ImGui::GetContentRegionAvail().x;
        const auto centeredText = [&](const char* text) {
            ImGui::SetCursorPosX(
                std::max(0.0f, (ImGui::GetWindowWidth() - ImGui::CalcTextSize(text).x) * 0.5f));
            ImGui::TextUnformatted(text);
        };

        if (font_title_ != nullptr) ImGui::PushFont(font_title_);
        centeredText("请家长来完成");
        if (font_title_ != nullptr) ImGui::PopFont();
        ImGui::PushStyleColor(ImGuiCol_Text, ImVec4(0.48f, 0.51f, 0.58f, 1.0f));
        centeredText("订阅与设置只对家长开放, 请作答后进入家长区");
        ImGui::PopStyleColor();
        ImGui::Spacing();
        ImGui::Separator();
        ImGui::Spacing();

        if (state.cooldown_seconds > 0) {
            // ---- 冷却: 温和的 "休息一下", 无惩罚文案 (P3 零挫败) ------
            parent_gate_input_.clear();
            ImGui::Dummy(ImVec2(0.0f, 10.0f));
            if (font_title_ != nullptr) ImGui::PushFont(font_title_);
            centeredText("休息一下");
            if (font_title_ != nullptr) ImGui::PopFont();
            char cooldown_text[64];
            std::snprintf(cooldown_text, sizeof(cooldown_text), "%d 秒后可以再试一次",
                          state.cooldown_seconds);
            ImGui::PushStyleColor(ImGuiCol_Text, ImVec4(0.48f, 0.51f, 0.58f, 1.0f));
            centeredText(cooldown_text);
            ImGui::PopStyleColor();
            ImGui::Dummy(ImVec2(0.0f, 14.0f));
            if (ImGui::Button("返回模型库##gate_back", ImVec2(avail, 48.0f))) {
                actions.dismissed = true;
            }
        } else {
            // ---- 题面 + 中文大写数字软键盘 ----------------------------
            if (font_title_ != nullptr) ImGui::PushFont(font_title_);
            centeredText(state.question.c_str());
            if (font_title_ != nullptr) ImGui::PopFont();
            ImGui::PushStyleColor(ImGuiCol_Text, ImVec4(0.48f, 0.51f, 0.58f, 1.0f));
            centeredText("请用中文大写数字作答 (例: 贰拾壹)");
            ImGui::PopStyleColor();
            ImGui::Spacing();

            // 答案展示框
            {
                ImDrawList* draw_list = ImGui::GetWindowDrawList();
                const ImVec2 top_left = ImGui::GetCursorScreenPos();
                const ImVec2 bottom_right{top_left.x + avail, top_left.y + 46.0f};
                draw_list->AddRectFilled(top_left, bottom_right,
                                         IM_COL32(237, 239, 245, 255), 10.0f);
                const bool empty = parent_gate_input_.empty();
                const char* text = empty ? "点击下方数字键输入" : parent_gate_input_.c_str();
                const ImVec2 text_size = ImGui::CalcTextSize(text);
                draw_list->AddText(ImVec2(top_left.x + (avail - text_size.x) * 0.5f,
                                          top_left.y + (46.0f - text_size.y) * 0.5f),
                                   empty ? IM_COL32(150, 155, 165, 255) : kColorInk, text);
                ImGui::Dummy(ImVec2(avail, 46.0f));
            }

            if (state.wrong_answer) {
                char retry_text[96];
                std::snprintf(retry_text, sizeof(retry_text),
                              "还差一点, 再试一次吧 (还可尝试 %d 次)", state.attempts_remaining);
                ImGui::PushStyleColor(ImGuiCol_Text, ImVec4(0.86f, 0.49f, 0.13f, 1.0f));
                centeredText(retry_text);
                ImGui::PopStyleColor();
            }
            ImGui::Spacing();

            // 软键盘: 家长门不依赖物理键盘/输入法 (平板同款交互)
            static constexpr const char* kKeypad[4][3] = {
                {"壹", "贰", "叁"}, {"肆", "伍", "陆"}, {"柒", "捌", "玖"}, {"零", "拾", "退格"}};
            const float key_spacing = 8.0f;
            const float key_width = (avail - key_spacing * 2.0f) / 3.0f;
            for (const auto& row : kKeypad) {
                for (int col = 0; col < 3; ++col) {
                    if (col > 0) ImGui::SameLine(0.0f, key_spacing);
                    const std::string label = std::string(row[col]) + "##gate_key";
                    if (ImGui::Button(label.c_str(), ImVec2(key_width, 48.0f))) {
                        if (std::string_view(row[col]) == "退格") {
                            // 键盘只产生 3 字节 CJK 字符, 退格按整字删除
                            if (parent_gate_input_.size() >= 3) {
                                parent_gate_input_.resize(parent_gate_input_.size() - 3);
                            }
                        } else if (parent_gate_input_.size() < 4 * 3) {
                            parent_gate_input_ += row[col];
                        }
                    }
                }
            }

            ImGui::Spacing();
            const float button_width = (avail - 10.0f) * 0.5f;
            ImGui::BeginDisabled(parent_gate_input_.empty());
            ImGui::PushStyleColor(ImGuiCol_Button, ImVec4(0.28f, 0.44f, 0.93f, 0.90f));
            ImGui::PushStyleColor(ImGuiCol_ButtonHovered, ImVec4(0.24f, 0.40f, 0.88f, 1.0f));
            ImGui::PushStyleColor(ImGuiCol_ButtonActive, ImVec4(0.20f, 0.35f, 0.80f, 1.0f));
            ImGui::PushStyleColor(ImGuiCol_Text, ImVec4(1.0f, 1.0f, 1.0f, 1.0f));
            if (ImGui::Button("确认##gate_submit", ImVec2(button_width, 48.0f))) {
                actions.submitted = true;
                actions.answer = parent_gate_input_;
                parent_gate_input_.clear();
            }
            ImGui::PopStyleColor(4);
            ImGui::EndDisabled();
            ImGui::SameLine(0.0f, 10.0f);
            if (ImGui::Button("返回##gate_dismiss", ImVec2(button_width, 48.0f))) {
                actions.dismissed = true;
                parent_gate_input_.clear();
            }
        }
    }
    ImGui::End();
    ImGui::PopStyleVar(2);
    return actions;
}

ParentAreaActions GlRenderer::submitParentArea(int session_remaining_seconds) {
    ParentAreaActions actions;
    const ImGuiIO& io = ImGui::GetIO();

    ImGui::SetNextWindowPos(ImVec2(io.DisplaySize.x * 0.5f, io.DisplaySize.y * 0.5f),
                            ImGuiCond_Always, ImVec2(0.5f, 0.5f));
    ImGui::SetNextWindowSize(ImVec2(560.0f, 0.0f));
    ImGui::SetNextWindowBgAlpha(0.975f);
    ImGui::PushStyleVar(ImGuiStyleVar_WindowRounding, 16.0f);
    ImGui::PushStyleVar(ImGuiStyleVar_WindowPadding, ImVec2(30.0f, 26.0f));
    const ImGuiWindowFlags flags = ImGuiWindowFlags_NoDecoration | ImGuiWindowFlags_NoMove |
                                   ImGuiWindowFlags_NoSavedSettings |
                                   ImGuiWindowFlags_AlwaysAutoResize;
    if (ImGui::Begin("##parent_area", nullptr, flags)) {
        const float avail = ImGui::GetContentRegionAvail().x;

        if (font_title_ != nullptr) ImGui::PushFont(font_title_);
        ImGui::TextColored(ImGui::ColorConvertU32ToFloat4(kColorInk), "家长中心");
        if (font_title_ != nullptr) ImGui::PopFont();
        ImGui::TextDisabled("家长会话剩余 %d 分 %02d 秒 · 只保存在内存, 退出应用即失效",
                            session_remaining_seconds / 60, session_remaining_seconds % 60);
        ImGui::Spacing();
        ImGui::Separator();
        ImGui::Spacing();

        // ---- 占位分区 (M3 商用功能, 见 UI_UX_SPEC.md §9.2 / §11) ------
        ImGui::TextColored(kAccentVec, "订阅");
        ImGui::TextDisabled("全库订阅与恢复购买将在正式版开放; 儿童界面不显示任何价格。");
        ImGui::BeginDisabled();
        (void)ImGui::Button("订阅管理 (即将上线)##sub_placeholder", ImVec2(avail, 44.0f));
        ImGui::EndDisabled();
        ImGui::Spacing();

        ImGui::TextColored(kAccentVec, "设置");
        ImGui::TextDisabled("年龄段模式 / 音量与朗读 / 磁力片库存管理 / 进度重置。");
        ImGui::BeginDisabled();
        (void)ImGui::Button("打开设置 (即将上线)##settings_placeholder", ImVec2(avail, 44.0f));
        ImGui::EndDisabled();
        ImGui::Spacing();

        ImGui::TextColored(kAccentVec, "隐私与数据");
        ImGui::TextDisabled("本应用不采集儿童个人信息; 数据导出与一键清除将在此提供。");
        ImGui::Spacing();
        ImGui::Separator();
        ImGui::Spacing();

        const float button_width = (avail - 10.0f) * 0.5f;
        if (ImGui::Button("返回模型库##area_back", ImVec2(button_width, 48.0f))) {
            actions.back_to_library = true;
        }
        ImGui::SameLine(0.0f, 10.0f);
        if (ImGui::Button("锁定家长区##area_lock", ImVec2(button_width, 48.0f))) {
            actions.lock_now = true;
        }
        if (ImGui::IsItemHovered()) {
            ImGui::SetTooltip("立即结束家长会话, 再次进入需重新验证");
        }
    }
    ImGui::End();
    ImGui::PopStyleVar(2);
    return actions;
}

void GlRenderer::endFrame() {
    if (window_ == nullptr) return;
    if (fb_width_ <= 0 || fb_height_ <= 0) {  // 窗口最小化
        ImGui::EndFrame();
        glfwSwapBuffers(window_);
        return;
    }

    // ---- 3D 场景 (排序 / 挤出 / 绘制由 GlSceneRenderer 完成) ----------
    scene_.end(glfwGetTime());

    // ---- HUD ---------------------------------------------------------
    ImGui::Render();
    ImGui_ImplOpenGL3_RenderDrawData(ImGui::GetDrawData());

    if (!screenshot_path_.empty()) {
        writeScreenshot();
        screenshot_path_.clear();
    }
    glfwSwapBuffers(window_);
}

/// 把当前后缓冲保存为 PPM (P6) 图片, 仅用于自动化冒烟测试。
void GlRenderer::writeScreenshot() {
    std::vector<unsigned char> pixels(
        static_cast<std::size_t>(fb_width_) * static_cast<std::size_t>(fb_height_) * 3);
    glPixelStorei(GL_PACK_ALIGNMENT, 1);
    glReadPixels(0, 0, fb_width_, fb_height_, GL_RGB, GL_UNSIGNED_BYTE, pixels.data());

    std::FILE* file = std::fopen(screenshot_path_.c_str(), "wb");
    if (file == nullptr) {
        std::fprintf(stderr, "[render] 警告: 无法写入截图 %s\n", screenshot_path_.c_str());
        return;
    }
    std::fprintf(file, "P6\n%d %d\n255\n", fb_width_, fb_height_);
    // OpenGL 原点在左下, 图片原点在左上, 逐行翻转
    const std::size_t row_bytes = static_cast<std::size_t>(fb_width_) * 3;
    for (int y = fb_height_ - 1; y >= 0; --y) {
        std::fwrite(pixels.data() + static_cast<std::size_t>(y) * row_bytes, 1, row_bytes, file);
    }
    std::fclose(file);
    std::printf("[render] 截图已保存: %s\n", screenshot_path_.c_str());
}

}  // namespace

std::unique_ptr<IWindowRenderer> createOpenGLRenderer() {
    return std::make_unique<GlRenderer>();
}

}  // namespace magtile::render
