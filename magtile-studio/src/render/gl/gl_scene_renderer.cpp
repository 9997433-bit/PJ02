// =============================================================
// MagTile Studio - 无窗口 OpenGL 磁力片场景渲染器实现
//
// 渲染管线 (每帧):
//   1. submitTile: 磁力片经 physics::transformTile 展开为世界坐标
//      几何并缓存;
//   2. end: 按视线方向由远及近排序 (画家算法), 把每片挤出成带厚度
//      的薄板 (真实磁力片约 5mm 厚), 填充半透明彩色;
//   3. 高亮描边以不透明色带 (面内边框) 绘制, 避开 Core Profile 下
//      glLineWidth > 1 的兼容性限制。
//
// 半透明策略: 磁力片整体按质心深度排序后关闭深度写入绘制, 对本
// 应用的规模 (数百片凸多边形) 视觉效果稳定且实现简单。
// 本文件从 gl_renderer.cpp 抽出 (QT-3), 供 GLFW 外壳与 Qt FBO
// 教程视口共用; 窗口 / 输入 / ImGui 仍归各外壳自理。
// =============================================================

#include "magtile/render/gl_scene_renderer.hpp"

#include <algorithm>
#include <array>
#include <cmath>
#include <cstdio>
#include <cstring>
#include <vector>

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
// GLSL 主体在桌面 GL 4.1 Core 与 GLES 3.0 之间完全共享, 仅版本头
// 不同 (Android 教程视口经 EGL/GLES3 复用本渲染器, 与 Qt/ImGui
// 同一份绘制实现): 运行时按 GL_VERSION 是否为 "OpenGL ES" 选择。
// ES 侧补默认精度限定 (GLES 片元着色器无默认 float 精度)。
const char* const kShaderHeaderDesktop = "#version 410 core\n";
const char* const kShaderHeaderEs =
    "#version 300 es\n"
    "precision highp float;\n"
    "precision highp int;\n";

// 顶点已在 CPU 侧变换到世界坐标, 只需一个视图投影矩阵。
const char* const kVertexShaderSrc = R"GLSL(
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
const char* const kFragmentShaderSrc = R"GLSL(
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

GLuint compileShader(GLenum type, const char* header, const char* body) {
    const GLuint shader = glCreateShader(type);
    const char* sources[2] = {header, body};
    glShaderSource(shader, 2, sources, nullptr);
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

}  // namespace

// ---- GL 句柄与帧缓存 ------------------------------------------------
struct GlSceneRenderer::GlObjects {
    struct PendingTile {
        physics::TransformedTile geometry;
        RenderTile state;
        Rgba base_color;
        double depth = 0.0;  ///< 沿视线方向的距离, 用于画家算法排序
    };

    // GL 资源
    bool es_context = false;  ///< GLES 3.0 上下文 (Android); false = 桌面 GL 4.1
    GLuint program = 0;
    GLint u_view_proj = -1;
    GLint u_camera_pos = -1;
    GLint u_unlit = -1;
    GLuint tile_vao = 0, tile_vbo = 0;
    GLuint outline_vao = 0, outline_vbo = 0;
    GLuint grid_vao = 0, grid_vbo = 0;
    GLsizei grid_vertex_count = 0;

    // 帧状态
    Camera frame_camera{};
    Vec3 view_forward{0.0, 1.0, 0.0};
    std::vector<PendingTile> pending_tiles;
    std::vector<float> tile_vertices;
    std::vector<float> outline_vertices;
    int fb_width = 0, fb_height = 0;
    double anim_time = 0.0;

    bool createShaderProgram();
    void createBuffers();
    void buildGridGeometry();
    void appendTileGeometry(const PendingTile& tile);
    void appendOutlineBand(const physics::TransformedTile& geom, const Rgba& color);
    void drawVertexBuffer(GLuint vao, GLuint vbo, const std::vector<float>& data, GLenum mode,
                          bool unlit);
    void destroy();
};

bool GlSceneRenderer::GlObjects::createShaderProgram() {
    const char* header = es_context ? kShaderHeaderEs : kShaderHeaderDesktop;
    const GLuint vs = compileShader(GL_VERTEX_SHADER, header, kVertexShaderSrc);
    const GLuint fs = compileShader(GL_FRAGMENT_SHADER, header, kFragmentShaderSrc);
    if (vs == 0 || fs == 0) return false;

    program = glCreateProgram();
    glAttachShader(program, vs);
    glAttachShader(program, fs);
    glLinkProgram(program);
    glDeleteShader(vs);
    glDeleteShader(fs);

    GLint ok = 0;
    glGetProgramiv(program, GL_LINK_STATUS, &ok);
    if (ok == 0) {
        std::array<GLchar, 1024> log{};
        glGetProgramInfoLog(program, static_cast<GLsizei>(log.size()), nullptr, log.data());
        std::fprintf(stderr, "[render] 着色器链接失败:\n%s\n", log.data());
        return false;
    }
    u_view_proj = glGetUniformLocation(program, "u_view_proj");
    u_camera_pos = glGetUniformLocation(program, "u_camera_pos");
    u_unlit = glGetUniformLocation(program, "u_unlit");
    return true;
}

void GlSceneRenderer::GlObjects::createBuffers() {
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
    makeVertexArray(tile_vao, tile_vbo);
    makeVertexArray(outline_vao, outline_vbo);
    makeVertexArray(grid_vao, grid_vbo);
    glBindVertexArray(0);
}

void GlSceneRenderer::GlObjects::buildGridGeometry() {
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
    grid_vertex_count = static_cast<GLsizei>(lines.size() / kFloatsPerVertex);
    glBindBuffer(GL_ARRAY_BUFFER, grid_vbo);
    glBufferData(GL_ARRAY_BUFFER, static_cast<GLsizeiptr>(lines.size() * sizeof(float)),
                 lines.data(), GL_STATIC_DRAW);
}

/// 把一片磁力片挤出成带厚度的薄板并写入三角形缓冲。
void GlSceneRenderer::GlObjects::appendTileGeometry(const PendingTile& tile) {
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
                static_cast<float>(0.5 + 0.5 * std::sin(anim_time * 2.0 * 3.14159265 * 1.2));
            fill = mix(fill, {1.0f, 1.0f, 1.0f, fill.a}, 0.12f);
            fill.a = 0.50f + 0.28f * pulse;
        } else if (tile.state.highlighted) {
            fill = mix(fill, {1.0f, 1.0f, 1.0f, fill.a}, 0.10f);
        }
    }

    const Vec3 offset = geom.normal * (kTileThickness * 0.5);
    // 顶面 (法向 normal), 扇形三角化 (形状均为凸多边形)
    for (std::size_t i = 1; i + 1 < n; ++i) {
        appendVertex(tile_vertices, geom.vertices[0] + offset, geom.normal, fill);
        appendVertex(tile_vertices, geom.vertices[i] + offset, geom.normal, fill);
        appendVertex(tile_vertices, geom.vertices[i + 1] + offset, geom.normal, fill);
    }
    // 底面 (法向 -normal), 顶点逆序保持一致的绕向约定
    const Vec3 neg_normal = geom.normal * -1.0;
    for (std::size_t i = 1; i + 1 < n; ++i) {
        appendVertex(tile_vertices, geom.vertices[0] - offset, neg_normal, fill);
        appendVertex(tile_vertices, geom.vertices[i + 1] - offset, neg_normal, fill);
        appendVertex(tile_vertices, geom.vertices[i] - offset, neg_normal, fill);
    }
    // 侧面
    for (std::size_t i = 0; i < n; ++i) {
        const Vec3& a = geom.vertices[i];
        const Vec3& b = geom.vertices[(i + 1) % n];
        const Vec3 side_normal = (b - a).cross(geom.normal).normalized();
        const Vec3 a_top = a + offset, a_bot = a - offset;
        const Vec3 b_top = b + offset, b_bot = b - offset;
        appendVertex(tile_vertices, a_bot, side_normal, fill);
        appendVertex(tile_vertices, b_bot, side_normal, fill);
        appendVertex(tile_vertices, b_top, side_normal, fill);
        appendVertex(tile_vertices, a_bot, side_normal, fill);
        appendVertex(tile_vertices, b_top, side_normal, fill);
        appendVertex(tile_vertices, a_top, side_normal, fill);
    }
}

/// 在顶面与底面沿边缘绘制不透明色带作为高亮描边。
/// (Core Profile 前向兼容上下文中 glLineWidth > 1 不可用, 色带方案
/// 三平台一致且宽度可控。)
void GlSceneRenderer::GlObjects::appendOutlineBand(const physics::TransformedTile& geom,
                                                   const Rgba& color) {
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
            appendVertex(outline_vertices, a + offset, face_normal, color);
            appendVertex(outline_vertices, b + offset, face_normal, color);
            appendVertex(outline_vertices, b_in + offset, face_normal, color);
            appendVertex(outline_vertices, a + offset, face_normal, color);
            appendVertex(outline_vertices, b_in + offset, face_normal, color);
            appendVertex(outline_vertices, a_in + offset, face_normal, color);
        }
    }
}

void GlSceneRenderer::GlObjects::drawVertexBuffer(GLuint vao, GLuint vbo,
                                                  const std::vector<float>& data, GLenum mode,
                                                  bool unlit) {
    if (data.empty()) return;
    glBindVertexArray(vao);
    glBindBuffer(GL_ARRAY_BUFFER, vbo);
    glBufferData(GL_ARRAY_BUFFER, static_cast<GLsizeiptr>(data.size() * sizeof(float)),
                 data.data(), GL_DYNAMIC_DRAW);
    glUniform1i(u_unlit, unlit ? 1 : 0);
    glDrawArrays(mode, 0, static_cast<GLsizei>(data.size() / kFloatsPerVertex));
}

void GlSceneRenderer::GlObjects::destroy() {
    // GL 资源随上下文销毁, 仍显式删除以便调试工具追踪
    if (program != 0) glDeleteProgram(program);
    const GLuint vaos[] = {tile_vao, outline_vao, grid_vao};
    const GLuint vbos[] = {tile_vbo, outline_vbo, grid_vbo};
    glDeleteVertexArrays(3, vaos);
    glDeleteBuffers(3, vbos);
    program = 0;
    tile_vao = outline_vao = grid_vao = 0;
    tile_vbo = outline_vbo = grid_vbo = 0;
}

// ---- 公共接口 --------------------------------------------------------

GlSceneRenderer::~GlSceneRenderer() {
    // 上下文可能已随窗口销毁, 这里只回收堆内存; 正常路径应先 shutdown()
    delete gl_;
    gl_ = nullptr;
}

bool GlSceneRenderer::initialize(ProcResolver resolver) {
    if (initialized_) return true;
    if (!glapi::loadFunctions(resolver)) return false;

    gl_ = new GlObjects();
    // 上下文类型探测: GLES 的版本串以 "OpenGL ES" 开头 (调用时上下文
    // 已 current, glGetString 可安全调用); 桌面 GL 走原有 410 core 路径。
    const char* version = reinterpret_cast<const char*>(glGetString(GL_VERSION));
    gl_->es_context = (version != nullptr && std::strstr(version, "OpenGL ES") != nullptr);
    if (!gl_->createShaderProgram()) {
        shutdown();
        return false;
    }
    gl_->createBuffers();
    gl_->buildGridGeometry();
    initialized_ = true;
    return true;
}

void GlSceneRenderer::shutdown() {
    if (gl_ != nullptr) {
        gl_->destroy();
        delete gl_;
        gl_ = nullptr;
    }
    initialized_ = false;
}

void GlSceneRenderer::begin(const Camera& camera, int fb_width, int fb_height) {
    if (gl_ == nullptr) return;
    gl_->frame_camera = camera;
    gl_->view_forward = (camera.target - camera.eye).normalized();
    gl_->pending_tiles.clear();
    gl_->tile_vertices.clear();
    gl_->outline_vertices.clear();
    gl_->fb_width = fb_width;
    gl_->fb_height = fb_height;

    glViewport(0, 0, fb_width, fb_height);
    glClearColor(kClearColor[0], kClearColor[1], kClearColor[2], 1.0f);
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT);
}

void GlSceneRenderer::submitTile(const RenderTile& tile, const core::TileShape& shape) {
    if (gl_ == nullptr || tile.instance == nullptr) return;

    GlObjects::PendingTile pending;
    pending.geometry = physics::transformTile(*tile.instance, shape);
    pending.state = tile;
    pending.base_color = tileBaseColor(tile.instance->color);
    pending.depth = (pending.geometry.centroid - gl_->frame_camera.eye).dot(gl_->view_forward);
    gl_->pending_tiles.push_back(std::move(pending));
}

void GlSceneRenderer::end(double time_seconds) {
    if (gl_ == nullptr || gl_->fb_width <= 0 || gl_->fb_height <= 0) return;
    gl_->anim_time = time_seconds;

    // ---- 由远及近排序 (画家算法) ------------------------------------
    std::sort(gl_->pending_tiles.begin(), gl_->pending_tiles.end(),
              [](const GlObjects::PendingTile& a, const GlObjects::PendingTile& b) {
                  return a.depth > b.depth;
              });
    for (const GlObjects::PendingTile& tile : gl_->pending_tiles) {
        gl_->appendTileGeometry(tile);
        if (tile.state.just_placed) {
            const auto pulse =
                static_cast<float>(0.5 + 0.5 * std::sin(time_seconds * 2.0 * 3.14159265 * 1.2));
            gl_->appendOutlineBand(tile.geometry, {1.0f, 0.52f, 0.08f, 0.75f + 0.25f * pulse});
        } else if (tile.state.highlighted && !tile.state.ghost) {
            gl_->appendOutlineBand(tile.geometry, {1.0f, 0.80f, 0.18f, 0.95f});
        }
    }

    // ---- 场景绘制 ---------------------------------------------------
    const double aspect = static_cast<double>(gl_->fb_width) / gl_->fb_height;
    const Mat4 view =
        Mat4::lookAt(gl_->frame_camera.eye, gl_->frame_camera.target, gl_->frame_camera.up);
    const Mat4 proj = Mat4::perspective(gl_->frame_camera.fov_deg, aspect, 0.05, 300.0);
    const Mat4 view_proj = proj * view;
    const float camera_pos[3] = {static_cast<float>(gl_->frame_camera.eye.x),
                                 static_cast<float>(gl_->frame_camera.eye.y),
                                 static_cast<float>(gl_->frame_camera.eye.z)};

    glUseProgram(gl_->program);
    glUniformMatrix4fv(gl_->u_view_proj, 1, GL_FALSE, view_proj.m.data());
    glUniform3fv(gl_->u_camera_pos, 1, camera_pos);

    // GL_MULTISAMPLE 是桌面 GL 开关; GLES 无此枚举 (多重采样随
    // EGLConfig 自动生效), 跳过以免产生 GL_INVALID_ENUM
    if (!gl_->es_context) glEnable(GL_MULTISAMPLE);
    glEnable(GL_BLEND);
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA);
    // 锁住 alpha 通道: 清屏已写 1 (不透明), 绘制期间不再改写 —— 画进 Qt
    // 场景图 FBO 时, 半透明薄板若把自身 alpha 留在缓冲里, Qt Quick 合成
    // 阶段会把整张纹理再当半透明贴图透出底色 (发白)。GLFW 默认
    // framebuffer 不参与二次合成, 锁 alpha 无副作用。
    glColorMask(GL_TRUE, GL_TRUE, GL_TRUE, GL_FALSE);
    glEnable(GL_DEPTH_TEST);
    glDepthFunc(GL_LEQUAL);
    glDisable(GL_CULL_FACE);  // 半透明薄板双面可见

    // 地面网格 (静态缓冲) 写入深度, 从下方观察时可正确遮挡
    glDepthMask(GL_TRUE);
    glBindVertexArray(gl_->grid_vao);
    glUniform1i(gl_->u_unlit, 1);
    glDrawArrays(GL_LINES, 0, gl_->grid_vertex_count);

    // 半透明磁力片: 已排序, 关闭深度写入
    glDepthMask(GL_FALSE);
    gl_->drawVertexBuffer(gl_->tile_vao, gl_->tile_vbo, gl_->tile_vertices, GL_TRIANGLES, false);
    // 高亮描边色带最后绘制, 始终可见
    gl_->drawVertexBuffer(gl_->outline_vao, gl_->outline_vbo, gl_->outline_vertices, GL_TRIANGLES,
                          true);
    glDepthMask(GL_TRUE);
    glColorMask(GL_TRUE, GL_TRUE, GL_TRUE, GL_TRUE);  // 归还 alpha 写入 (ImGui/Qt 后续绘制)
    glBindVertexArray(0);
}

}  // namespace magtile::render
