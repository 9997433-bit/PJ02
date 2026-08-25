// =============================================================
// MagTile Studio - GLFW + OpenGL 4.1 Core 渲染后端实现
//
// 渲染管线概览 (每帧):
//   1. submitTile 阶段: 磁力片经 physics::transformTile 展开为世界
//      坐标几何并缓存;
//   2. endFrame 阶段: 按视线方向由远及近排序 (画家算法), 把每片
//      挤出成带厚度的薄板 (真实磁力片约 5mm 厚), 填充半透明彩色;
//   3. 高亮描边以不透明色带 (面内边框) 绘制, 避开 Core Profile
//      下 glLineWidth > 1 的兼容性限制;
//   4. Dear ImGui 绘制教程 HUD (步骤说明 / 进度 / 导航按钮)。
//
// 半透明策略: 磁力片整体按质心深度排序后关闭深度写入绘制, 对本
// 应用的规模 (数百片凸多边形) 视觉效果稳定且实现简单。
// =============================================================

#include "magtile/render/gl_renderer.hpp"

#include <algorithm>
#include <array>
#include <cmath>
#include <cstdio>
#include <filesystem>
#include <string>
#include <vector>

#define GLFW_INCLUDE_NONE
#include <GLFW/glfw3.h>

#include <imgui.h>
#include <imgui_impl_glfw.h>
#include <imgui_impl_opengl3.h>

#include "gl_api.hpp"
#include "magtile/physics/geometry.hpp"

namespace magtile::render {
namespace {

using namespace glapi;
using core::Vec3;

// ---- 渲染参数 ----------------------------------------------------
constexpr float kTileThickness = 0.06f;   ///< 磁力片厚度 (世界单位, ≈4mm 实物)
constexpr float kOutlineWidth = 0.07f;    ///< 高亮描边色带宽度
constexpr int kGridHalfExtent = 12;       ///< 地面网格半径 (格)
constexpr double kRotateSpeedDegPerPx = 0.32;
constexpr float kClearColor[3] = {0.90f, 0.925f, 0.95f};

// ---- 小型 4x4 矩阵 (列主序, 可直接传 glUniformMatrix4fv) -----------
struct Mat4 {
    std::array<float, 16> m{};

    static Mat4 perspective(double fov_deg, double aspect, double z_near, double z_far) {
        const double f = 1.0 / std::tan(fov_deg * 0.5 * core::kDegToRad);
        Mat4 r;
        r.m[0] = static_cast<float>(f / aspect);
        r.m[5] = static_cast<float>(f);
        r.m[10] = static_cast<float>((z_far + z_near) / (z_near - z_far));
        r.m[11] = -1.0f;
        r.m[14] = static_cast<float>(2.0 * z_far * z_near / (z_near - z_far));
        return r;
    }

    static Mat4 lookAt(const Vec3& eye, const Vec3& target, const Vec3& up) {
        const Vec3 f = (target - eye).normalized();
        const Vec3 s = f.cross(up).normalized();
        const Vec3 u = s.cross(f);
        Mat4 r;
        r.m = {static_cast<float>(s.x),  static_cast<float>(u.x),  static_cast<float>(-f.x), 0.0f,
               static_cast<float>(s.y),  static_cast<float>(u.y),  static_cast<float>(-f.y), 0.0f,
               static_cast<float>(s.z),  static_cast<float>(u.z),  static_cast<float>(-f.z), 0.0f,
               static_cast<float>(-s.dot(eye)), static_cast<float>(-u.dot(eye)),
               static_cast<float>(f.dot(eye)), 1.0f};
        return r;
    }

    Mat4 operator*(const Mat4& o) const {
        Mat4 r;
        for (int col = 0; col < 4; ++col) {
            for (int row = 0; row < 4; ++row) {
                float sum = 0.0f;
                for (int k = 0; k < 4; ++k) sum += m[k * 4 + row] * o.m[col * 4 + k];
                r.m[col * 4 + row] = sum;
            }
        }
        return r;
    }
};

// ---- 颜色 --------------------------------------------------------
struct Rgba {
    float r = 1.0f, g = 1.0f, b = 1.0f, a = 1.0f;
};

/// 磁力片半透明彩色 ABS 的基准色。
Rgba tileBaseColor(core::TileColor color) {
    switch (color) {
        case core::TileColor::Red: return {0.91f, 0.22f, 0.25f, 1.0f};
        case core::TileColor::Orange: return {0.98f, 0.55f, 0.15f, 1.0f};
        case core::TileColor::Yellow: return {0.99f, 0.83f, 0.18f, 1.0f};
        case core::TileColor::Green: return {0.28f, 0.75f, 0.36f, 1.0f};
        case core::TileColor::Cyan: return {0.20f, 0.74f, 0.82f, 1.0f};
        case core::TileColor::Blue: return {0.23f, 0.46f, 0.90f, 1.0f};
        case core::TileColor::Purple: return {0.58f, 0.36f, 0.86f, 1.0f};
        case core::TileColor::Pink: return {0.95f, 0.48f, 0.70f, 1.0f};
        case core::TileColor::Clear: return {0.85f, 0.90f, 0.94f, 1.0f};
        case core::TileColor::Gray: return {0.55f, 0.58f, 0.62f, 1.0f};
    }
    return {0.7f, 0.7f, 0.7f, 1.0f};
}

Rgba mix(const Rgba& a, const Rgba& b, float t) {
    return {a.r + (b.r - a.r) * t, a.g + (b.g - a.g) * t, a.b + (b.b - a.b) * t,
            a.a + (b.a - a.a) * t};
}

// ---- 着色器 ------------------------------------------------------
// 顶点已在 CPU 侧变换到世界坐标, 只需一个视图投影矩阵。
const char* const kVertexShaderSrc = R"GLSL(#version 410 core
layout(location = 0) in vec3 a_position;
layout(location = 1) in vec3 a_normal;
layout(location = 2) in vec4 a_color;
uniform mat4 u_view_proj;
out vec3 v_normal;
out vec3 v_world_pos;
out vec4 v_color;
void main() {
    v_normal = a_normal;
    v_world_pos = a_position;
    v_color = a_color;
    gl_Position = u_view_proj * vec4(a_position, 1.0);
}
)GLSL";

// 双面受光 + 边缘增亮, 模拟半透明彩色塑料的通透感。
const char* const kFragmentShaderSrc = R"GLSL(#version 410 core
in vec3 v_normal;
in vec3 v_world_pos;
in vec4 v_color;
uniform vec3 u_camera_pos;
uniform int u_unlit;
out vec4 frag_color;
void main() {
    if (u_unlit == 1) {
        frag_color = v_color;
        return;
    }
    vec3 n = normalize(v_normal);
    vec3 light_dir = normalize(vec3(0.35, 0.25, 0.9));
    float diffuse = abs(dot(n, light_dir));
    vec3 view_dir = normalize(u_camera_pos - v_world_pos);
    float rim = pow(1.0 - abs(dot(n, view_dir)), 2.0);
    vec3 color = v_color.rgb * (0.5 + 0.5 * diffuse) + vec3(0.22) * rim;
    float alpha = clamp(v_color.a + 0.18 * rim * v_color.a, 0.0, 1.0);
    frag_color = vec4(color, alpha);
}
)GLSL";

/// 顶点布局: 位置 3f + 法向 3f + 颜色 4f。
constexpr int kFloatsPerVertex = 10;

void appendVertex(std::vector<float>& out, const Vec3& p, const Vec3& n, const Rgba& c) {
    out.insert(out.end(), {static_cast<float>(p.x), static_cast<float>(p.y),
                           static_cast<float>(p.z), static_cast<float>(n.x),
                           static_cast<float>(n.y), static_cast<float>(n.z), c.r, c.g, c.b, c.a});
}

GLuint compileShader(GLenum type, const char* source) {
    const GLuint shader = glCreateShader(type);
    glShaderSource(shader, 1, &source, nullptr);
    glCompileShader(shader);
    GLint ok = 0;
    glGetShaderiv(shader, GL_COMPILE_STATUS, &ok);
    if (ok == 0) {
        std::array<GLchar, 1024> log{};
        glGetShaderInfoLog(shader, static_cast<GLsizei>(log.size()), nullptr, log.data());
        std::fprintf(stderr, "[render] 着色器编译失败:\n%s\n", log.data());
        glDeleteShader(shader);
        return 0;
    }
    return shader;
}

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
    void requestScreenshot(const std::string& ppm_path) override { screenshot_path_ = ppm_path; }

private:
    struct PendingTile {
        physics::TransformedTile geometry;
        RenderTile state;
        Rgba base_color;
        double depth = 0.0;  ///< 沿视线方向的距离, 用于画家算法排序
    };

    bool createShaderProgram();
    void createBuffers();
    void buildGridGeometry();
    void setupImGui();
    void drawVertexBuffer(GLuint vao, GLuint vbo, const std::vector<float>& data, GLenum mode,
                          bool unlit);
    void appendTileGeometry(const PendingTile& tile);
    void appendOutlineBand(const physics::TransformedTile& geom, const Rgba& color);
    [[nodiscard]] bool keyPressed(int key);
    void writeScreenshot();

    // 窗口与上下文
    GLFWwindow* window_ = nullptr;
    bool glfw_initialized_ = false;
    bool imgui_initialized_ = false;

    // GL 资源
    GLuint program_ = 0;
    GLint u_view_proj_ = -1;
    GLint u_camera_pos_ = -1;
    GLint u_unlit_ = -1;
    GLuint tile_vao_ = 0, tile_vbo_ = 0;
    GLuint outline_vao_ = 0, outline_vbo_ = 0;
    GLuint grid_vao_ = 0, grid_vbo_ = 0;
    GLsizei grid_vertex_count_ = 0;

    // 相机与交互
    OrbitCamera camera_;
    TutorialActions pending_actions_{};
    double last_mouse_x_ = 0.0, last_mouse_y_ = 0.0;
    double scroll_delta_ = 0.0;
    std::array<bool, GLFW_KEY_LAST + 1> key_was_down_{};

    // 帧状态
    Camera frame_camera_{};
    Vec3 view_forward_{0.0, 1.0, 0.0};
    std::vector<PendingTile> pending_tiles_;
    std::vector<float> tile_vertices_;
    std::vector<float> outline_vertices_;
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

    if (!glapi::loadFunctions(glfwGetProcAddress)) {
        shutdown();
        return false;
    }
    std::printf("[render] OpenGL %s @ %s\n", glGetString(GL_VERSION), glGetString(GL_RENDERER));

    if (!createShaderProgram()) {
        shutdown();
        return false;
    }
    createBuffers();
    buildGridGeometry();

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
        if (program_ != 0) glDeleteProgram(program_);
        const GLuint vaos[] = {tile_vao_, outline_vao_, grid_vao_};
        const GLuint vbos[] = {tile_vbo_, outline_vbo_, grid_vbo_};
        glDeleteVertexArrays(3, vaos);
        glDeleteBuffers(3, vbos);
        program_ = 0;
        tile_vao_ = outline_vao_ = grid_vao_ = 0;
        tile_vbo_ = outline_vbo_ = grid_vbo_ = 0;

        glfwDestroyWindow(window_);
        window_ = nullptr;
    }
    if (glfw_initialized_) {
        glfwTerminate();
        glfw_initialized_ = false;
    }
}

bool GlRenderer::createShaderProgram() {
    const GLuint vs = compileShader(GL_VERTEX_SHADER, kVertexShaderSrc);
    const GLuint fs = compileShader(GL_FRAGMENT_SHADER, kFragmentShaderSrc);
    if (vs == 0 || fs == 0) return false;

    program_ = glCreateProgram();
    glAttachShader(program_, vs);
    glAttachShader(program_, fs);
    glLinkProgram(program_);
    glDeleteShader(vs);
    glDeleteShader(fs);

    GLint ok = 0;
    glGetProgramiv(program_, GL_LINK_STATUS, &ok);
    if (ok == 0) {
        std::array<GLchar, 1024> log{};
        glGetProgramInfoLog(program_, static_cast<GLsizei>(log.size()), nullptr, log.data());
        std::fprintf(stderr, "[render] 着色器链接失败:\n%s\n", log.data());
        return false;
    }
    u_view_proj_ = glGetUniformLocation(program_, "u_view_proj");
    u_camera_pos_ = glGetUniformLocation(program_, "u_camera_pos");
    u_unlit_ = glGetUniformLocation(program_, "u_unlit");
    return true;
}

void GlRenderer::createBuffers() {
    const auto makeVertexArray = [](GLuint& vao, GLuint& vbo) {
        glGenVertexArrays(1, &vao);
        glGenBuffers(1, &vbo);
        glBindVertexArray(vao);
        glBindBuffer(GL_ARRAY_BUFFER, vbo);
        const GLsizei stride = kFloatsPerVertex * static_cast<GLsizei>(sizeof(float));
        glEnableVertexAttribArray(0);
        glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, stride, nullptr);
        glEnableVertexAttribArray(1);
        glVertexAttribPointer(1, 3, GL_FLOAT, GL_FALSE, stride,
                              reinterpret_cast<const void*>(3 * sizeof(float)));
        glEnableVertexAttribArray(2);
        glVertexAttribPointer(2, 4, GL_FLOAT, GL_FALSE, stride,
                              reinterpret_cast<const void*>(6 * sizeof(float)));
    };
    makeVertexArray(tile_vao_, tile_vbo_);
    makeVertexArray(outline_vao_, outline_vbo_);
    makeVertexArray(grid_vao_, grid_vbo_);
    glBindVertexArray(0);
}

void GlRenderer::buildGridGeometry() {
    const Rgba minor{0.72f, 0.76f, 0.80f, 0.55f};
    const Rgba major{0.58f, 0.63f, 0.69f, 0.75f};
    const Rgba axis_x{0.85f, 0.38f, 0.38f, 0.9f};
    const Rgba axis_y{0.35f, 0.72f, 0.42f, 0.9f};
    const Vec3 up{0.0, 0.0, 1.0};
    const double ext = kGridHalfExtent;

    std::vector<float> lines;
    for (int i = -kGridHalfExtent; i <= kGridHalfExtent; ++i) {
        const Rgba color = (i % 4 == 0) ? major : minor;
        // 平行于 X 轴的线 (i == 0 即 X 轴本身)
        const Rgba cx = (i == 0) ? axis_x : color;
        appendVertex(lines, {-ext, static_cast<double>(i), 0.0}, up, cx);
        appendVertex(lines, {ext, static_cast<double>(i), 0.0}, up, cx);
        // 平行于 Y 轴的线
        const Rgba cy = (i == 0) ? axis_y : color;
        appendVertex(lines, {static_cast<double>(i), -ext, 0.0}, up, cy);
        appendVertex(lines, {static_cast<double>(i), ext, 0.0}, up, cy);
    }
    grid_vertex_count_ = static_cast<GLsizei>(lines.size() / kFloatsPerVertex);
    glBindBuffer(GL_ARRAY_BUFFER, grid_vbo_);
    glBufferData(GL_ARRAY_BUFFER, static_cast<GLsizeiptr>(lines.size() * sizeof(float)),
                 lines.data(), GL_STATIC_DRAW);
}

void GlRenderer::setupImGui() {
    IMGUI_CHECKVERSION();
    ImGui::CreateContext();
    ImGuiIO& io = ImGui::GetIO();
    io.IniFilename = nullptr;  // HUD 布局固定, 不落盘配置

    ImGui::StyleColorsLight();
    ImGuiStyle& style = ImGui::GetStyle();
    style.WindowRounding = 8.0f;
    style.FrameRounding = 6.0f;
    style.WindowBorderSize = 0.0f;

    if (const char* font_path = findCjkFontPath(); font_path != nullptr) {
        io.Fonts->AddFontFromFileTTF(font_path, 19.0f, nullptr,
                                     io.Fonts->GetGlyphRangesChineseSimplifiedCommon());
        std::printf("[render] HUD 字体: %s\n", font_path);
    } else {
        io.Fonts->AddFontDefault();
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
    frame_camera_ = camera;
    view_forward_ = (camera.target - camera.eye).normalized();
    pending_tiles_.clear();
    tile_vertices_.clear();
    outline_vertices_.clear();

    glfwGetFramebufferSize(window_, &fb_width_, &fb_height_);
    glViewport(0, 0, fb_width_, fb_height_);
    glClearColor(kClearColor[0], kClearColor[1], kClearColor[2], 1.0f);
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT);

    ImGui_ImplOpenGL3_NewFrame();
    ImGui_ImplGlfw_NewFrame();
    ImGui::NewFrame();
}

void GlRenderer::submitTile(const RenderTile& tile, const core::TileShape& shape) {
    if (tile.instance == nullptr) return;

    PendingTile pending;
    pending.geometry = physics::transformTile(*tile.instance, shape);
    pending.state = tile;
    pending.base_color = tileBaseColor(tile.instance->color);
    pending.depth = (pending.geometry.centroid - frame_camera_.eye).dot(view_forward_);
    pending_tiles_.push_back(std::move(pending));
}

/// 把一片磁力片挤出成带厚度的薄板并写入三角形缓冲。
void GlRenderer::appendTileGeometry(const PendingTile& tile) {
    const auto& geom = tile.geometry;
    const std::size_t n = geom.vertices.size();
    if (n < 3) return;

    // ---- 根据教程状态决定填充颜色 ----------------------------------
    Rgba fill = tile.base_color;
    if (tile.state.ghost) {
        // 未放置: 褪色 + 高度透明, 只提示最终轮廓
        fill = mix(fill, {0.62f, 0.65f, 0.70f, 1.0f}, 0.55f);
        fill.a = 0.10f;
    } else {
        fill.a = 0.55f;
        if (tile.state.just_placed) {
            // 本步新增: 呼吸动画引导视线
            const auto pulse =
                static_cast<float>(0.5 + 0.5 * std::sin(glfwGetTime() * 2.0 * 3.14159265 * 1.2));
            fill = mix(fill, {1.0f, 1.0f, 1.0f, fill.a}, 0.12f);
            fill.a = 0.50f + 0.28f * pulse;
        } else if (tile.state.highlighted) {
            fill = mix(fill, {1.0f, 1.0f, 1.0f, fill.a}, 0.10f);
        }
    }

    const Vec3 offset = geom.normal * (kTileThickness * 0.5);
    // 顶面 (法向 normal), 扇形三角化 (形状均为凸多边形)
    for (std::size_t i = 1; i + 1 < n; ++i) {
        appendVertex(tile_vertices_, geom.vertices[0] + offset, geom.normal, fill);
        appendVertex(tile_vertices_, geom.vertices[i] + offset, geom.normal, fill);
        appendVertex(tile_vertices_, geom.vertices[i + 1] + offset, geom.normal, fill);
    }
    // 底面 (法向 -normal), 顶点逆序保持一致的绕向约定
    const Vec3 neg_normal = geom.normal * -1.0;
    for (std::size_t i = 1; i + 1 < n; ++i) {
        appendVertex(tile_vertices_, geom.vertices[0] - offset, neg_normal, fill);
        appendVertex(tile_vertices_, geom.vertices[i + 1] - offset, neg_normal, fill);
        appendVertex(tile_vertices_, geom.vertices[i] - offset, neg_normal, fill);
    }
    // 侧面
    for (std::size_t i = 0; i < n; ++i) {
        const Vec3& a = geom.vertices[i];
        const Vec3& b = geom.vertices[(i + 1) % n];
        const Vec3 side_normal = (b - a).cross(geom.normal).normalized();
        const Vec3 a_top = a + offset, a_bot = a - offset;
        const Vec3 b_top = b + offset, b_bot = b - offset;
        appendVertex(tile_vertices_, a_bot, side_normal, fill);
        appendVertex(tile_vertices_, b_bot, side_normal, fill);
        appendVertex(tile_vertices_, b_top, side_normal, fill);
        appendVertex(tile_vertices_, a_bot, side_normal, fill);
        appendVertex(tile_vertices_, b_top, side_normal, fill);
        appendVertex(tile_vertices_, a_top, side_normal, fill);
    }
}

/// 在顶面与底面沿边缘绘制不透明色带作为高亮描边。
/// (Core Profile 前向兼容上下文中 glLineWidth > 1 不可用, 色带方案
/// 三平台一致且宽度可控。)
void GlRenderer::appendOutlineBand(const physics::TransformedTile& geom, const Rgba& color) {
    const std::size_t n = geom.vertices.size();
    if (n < 3) return;

    // 色带略微悬浮于表面, 保证绘制在填充之上
    const double lift = kTileThickness * 0.5 + 0.004;
    for (int side = 0; side < 2; ++side) {
        const Vec3 face_normal = (side == 0) ? geom.normal : geom.normal * -1.0;
        const Vec3 offset = face_normal * lift;
        for (std::size_t i = 0; i < n; ++i) {
            const Vec3& a = geom.vertices[i];
            const Vec3& b = geom.vertices[(i + 1) % n];
            // 指向多边形内部的单位向量 (顶点逆时针绕 normal 排列)
            const Vec3 inward = geom.normal.cross(b - a).normalized();
            const Vec3 a_in = a + inward * kOutlineWidth;
            const Vec3 b_in = b + inward * kOutlineWidth;
            appendVertex(outline_vertices_, a + offset, face_normal, color);
            appendVertex(outline_vertices_, b + offset, face_normal, color);
            appendVertex(outline_vertices_, b_in + offset, face_normal, color);
            appendVertex(outline_vertices_, a + offset, face_normal, color);
            appendVertex(outline_vertices_, b_in + offset, face_normal, color);
            appendVertex(outline_vertices_, a_in + offset, face_normal, color);
        }
    }
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
        ImGui::Text("%s", hud.model_name.c_str());
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

void GlRenderer::drawVertexBuffer(GLuint vao, GLuint vbo, const std::vector<float>& data,
                                  GLenum mode, bool unlit) {
    if (data.empty()) return;
    glBindVertexArray(vao);
    glBindBuffer(GL_ARRAY_BUFFER, vbo);
    glBufferData(GL_ARRAY_BUFFER, static_cast<GLsizeiptr>(data.size() * sizeof(float)),
                 data.data(), GL_DYNAMIC_DRAW);
    glUniform1i(u_unlit_, unlit ? 1 : 0);
    glDrawArrays(mode, 0, static_cast<GLsizei>(data.size() / kFloatsPerVertex));
}

void GlRenderer::endFrame() {
    if (window_ == nullptr) return;
    if (fb_width_ <= 0 || fb_height_ <= 0) {  // 窗口最小化
        ImGui::EndFrame();
        glfwSwapBuffers(window_);
        return;
    }

    // ---- 由远及近排序 (画家算法) ------------------------------------
    std::sort(pending_tiles_.begin(), pending_tiles_.end(),
              [](const PendingTile& a, const PendingTile& b) { return a.depth > b.depth; });
    for (const PendingTile& tile : pending_tiles_) {
        appendTileGeometry(tile);
        if (tile.state.just_placed) {
            const auto pulse =
                static_cast<float>(0.5 + 0.5 * std::sin(glfwGetTime() * 2.0 * 3.14159265 * 1.2));
            appendOutlineBand(tile.geometry, {1.0f, 0.52f, 0.08f, 0.75f + 0.25f * pulse});
        } else if (tile.state.highlighted && !tile.state.ghost) {
            appendOutlineBand(tile.geometry, {1.0f, 0.80f, 0.18f, 0.95f});
        }
    }

    // ---- 场景绘制 ---------------------------------------------------
    const double aspect = static_cast<double>(fb_width_) / fb_height_;
    const Mat4 view = Mat4::lookAt(frame_camera_.eye, frame_camera_.target, frame_camera_.up);
    const Mat4 proj = Mat4::perspective(frame_camera_.fov_deg, aspect, 0.05, 300.0);
    const Mat4 view_proj = proj * view;
    const float camera_pos[3] = {static_cast<float>(frame_camera_.eye.x),
                                 static_cast<float>(frame_camera_.eye.y),
                                 static_cast<float>(frame_camera_.eye.z)};

    glUseProgram(program_);
    glUniformMatrix4fv(u_view_proj_, 1, GL_FALSE, view_proj.m.data());
    glUniform3fv(u_camera_pos_, 1, camera_pos);

    glEnable(GL_MULTISAMPLE);
    glEnable(GL_BLEND);
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA);
    glEnable(GL_DEPTH_TEST);
    glDepthFunc(GL_LEQUAL);
    glDisable(GL_CULL_FACE);  // 半透明薄板双面可见

    // 地面网格 (静态缓冲) 写入深度, 从下方观察时可正确遮挡
    glDepthMask(GL_TRUE);
    glBindVertexArray(grid_vao_);
    glUniform1i(u_unlit_, 1);
    glDrawArrays(GL_LINES, 0, grid_vertex_count_);

    // 半透明磁力片: 已排序, 关闭深度写入
    glDepthMask(GL_FALSE);
    drawVertexBuffer(tile_vao_, tile_vbo_, tile_vertices_, GL_TRIANGLES, false);
    // 高亮描边色带最后绘制, 始终可见
    drawVertexBuffer(outline_vao_, outline_vbo_, outline_vertices_, GL_TRIANGLES, true);
    glDepthMask(GL_TRUE);

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
