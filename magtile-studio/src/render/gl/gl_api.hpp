#pragma once

// =============================================================
// MagTile Studio - 最小 OpenGL 4.1 Core 函数加载器
//
// 只声明本渲染后端实际使用的入口, 通过 GLFW 的 glfwGetProcAddress
// 在运行时解析, 因此无需 glad 等生成式加载器, 也不包含系统 GL 头
// (避免各平台头文件差异)。所有符号收敛在 magtile::render::glapi
// 命名空间内, 不污染全局命名空间。
// =============================================================

#include <cstddef>
#include <cstdint>

namespace magtile::render::glapi {

// ---- 基础类型 (与 khrplatform 定义一致) --------------------------
using GLenum = std::uint32_t;
using GLboolean = std::uint8_t;
using GLbitfield = std::uint32_t;
using GLint = std::int32_t;
using GLuint = std::uint32_t;
using GLsizei = std::int32_t;
using GLfloat = float;
using GLchar = char;
using GLubyte = std::uint8_t;
using GLsizeiptr = std::ptrdiff_t;
using GLintptr = std::ptrdiff_t;

// ---- 本后端用到的常量 -------------------------------------------
inline constexpr GLboolean GL_FALSE = 0;
inline constexpr GLboolean GL_TRUE = 1;
inline constexpr GLenum GL_LINES = 0x0001;
inline constexpr GLenum GL_TRIANGLES = 0x0004;
inline constexpr GLenum GL_DEPTH_BUFFER_BIT = 0x00000100;
inline constexpr GLenum GL_COLOR_BUFFER_BIT = 0x00004000;
inline constexpr GLenum GL_LESS = 0x0201;
inline constexpr GLenum GL_LEQUAL = 0x0203;
inline constexpr GLenum GL_SRC_ALPHA = 0x0302;
inline constexpr GLenum GL_ONE_MINUS_SRC_ALPHA = 0x0303;
inline constexpr GLenum GL_CULL_FACE = 0x0B44;
inline constexpr GLenum GL_DEPTH_TEST = 0x0B71;
inline constexpr GLenum GL_BLEND = 0x0BE2;
inline constexpr GLenum GL_UNPACK_ALIGNMENT = 0x0CF5;
inline constexpr GLenum GL_PACK_ALIGNMENT = 0x0D05;
inline constexpr GLenum GL_TEXTURE_2D = 0x0DE1;
inline constexpr GLenum GL_UNSIGNED_BYTE = 0x1401;
inline constexpr GLenum GL_FLOAT = 0x1406;
inline constexpr GLenum GL_RGB = 0x1907;
inline constexpr GLenum GL_RGBA = 0x1908;
inline constexpr GLenum GL_VERSION = 0x1F02;
inline constexpr GLenum GL_RENDERER = 0x1F01;
inline constexpr GLenum GL_LINEAR = 0x2601;
inline constexpr GLenum GL_TEXTURE_MAG_FILTER = 0x2800;
inline constexpr GLenum GL_TEXTURE_MIN_FILTER = 0x2801;
inline constexpr GLenum GL_TEXTURE_WRAP_S = 0x2802;
inline constexpr GLenum GL_TEXTURE_WRAP_T = 0x2803;
inline constexpr GLenum GL_RGBA8 = 0x8058;
inline constexpr GLenum GL_CLAMP_TO_EDGE = 0x812F;
inline constexpr GLenum GL_MULTISAMPLE = 0x809D;
inline constexpr GLenum GL_ARRAY_BUFFER = 0x8892;
inline constexpr GLenum GL_DYNAMIC_DRAW = 0x88E8;
inline constexpr GLenum GL_STATIC_DRAW = 0x88E4;
inline constexpr GLenum GL_FRAGMENT_SHADER = 0x8B30;
inline constexpr GLenum GL_VERTEX_SHADER = 0x8B31;
inline constexpr GLenum GL_COMPILE_STATUS = 0x8B81;
inline constexpr GLenum GL_LINK_STATUS = 0x8B82;
inline constexpr GLenum GL_INFO_LOG_LENGTH = 0x8B84;

// ---- 函数指针表 --------------------------------------------------
// X(返回值, 名称, 形参列表)
#define MAGTILE_GL_FUNCTION_LIST(X)                                                          \
    X(void, glEnable, (GLenum cap))                                                          \
    X(void, glDisable, (GLenum cap))                                                         \
    X(void, glBlendFunc, (GLenum sfactor, GLenum dfactor))                                   \
    X(void, glDepthFunc, (GLenum func))                                                      \
    X(void, glDepthMask, (GLboolean flag))                                                   \
    X(void, glClearColor, (GLfloat r, GLfloat g, GLfloat b, GLfloat a))                      \
    X(void, glClear, (GLbitfield mask))                                                      \
    X(void, glViewport, (GLint x, GLint y, GLsizei width, GLsizei height))                   \
    X(void, glLineWidth, (GLfloat width))                                                    \
    X(void, glPixelStorei, (GLenum pname, GLint param))                                      \
    X(void, glReadPixels,                                                                    \
      (GLint x, GLint y, GLsizei width, GLsizei height, GLenum format, GLenum type,          \
       void* pixels))                                                                        \
    X(const GLubyte*, glGetString, (GLenum name))                                            \
    X(GLuint, glCreateShader, (GLenum type))                                                 \
    X(void, glShaderSource,                                                                  \
      (GLuint shader, GLsizei count, const GLchar* const* string, const GLint* length))      \
    X(void, glCompileShader, (GLuint shader))                                                \
    X(void, glGetShaderiv, (GLuint shader, GLenum pname, GLint * params))                    \
    X(void, glGetShaderInfoLog,                                                              \
      (GLuint shader, GLsizei buf_size, GLsizei * length, GLchar * info_log))                \
    X(void, glDeleteShader, (GLuint shader))                                                 \
    X(GLuint, glCreateProgram, (void))                                                       \
    X(void, glAttachShader, (GLuint program, GLuint shader))                                 \
    X(void, glLinkProgram, (GLuint program))                                                 \
    X(void, glGetProgramiv, (GLuint program, GLenum pname, GLint * params))                  \
    X(void, glGetProgramInfoLog,                                                             \
      (GLuint program, GLsizei buf_size, GLsizei * length, GLchar * info_log))               \
    X(void, glDeleteProgram, (GLuint program))                                               \
    X(void, glUseProgram, (GLuint program))                                                  \
    X(GLint, glGetUniformLocation, (GLuint program, const GLchar* name))                     \
    X(void, glUniformMatrix4fv,                                                              \
      (GLint location, GLsizei count, GLboolean transpose, const GLfloat* value))            \
    X(void, glUniform3fv, (GLint location, GLsizei count, const GLfloat* value))             \
    X(void, glUniform1i, (GLint location, GLint v0))                                         \
    X(void, glUniform1f, (GLint location, GLfloat v0))                                       \
    X(void, glGenVertexArrays, (GLsizei n, GLuint * arrays))                                 \
    X(void, glBindVertexArray, (GLuint array))                                               \
    X(void, glDeleteVertexArrays, (GLsizei n, const GLuint* arrays))                         \
    X(void, glGenBuffers, (GLsizei n, GLuint * buffers))                                     \
    X(void, glBindBuffer, (GLenum target, GLuint buffer))                                    \
    X(void, glBufferData, (GLenum target, GLsizeiptr size, const void* data, GLenum usage))  \
    X(void, glDeleteBuffers, (GLsizei n, const GLuint* buffers))                             \
    X(void, glEnableVertexAttribArray, (GLuint index))                                       \
    X(void, glVertexAttribPointer,                                                           \
      (GLuint index, GLint size, GLenum type, GLboolean normalized, GLsizei stride,          \
       const void* pointer))                                                                 \
    X(void, glDrawArrays, (GLenum mode, GLint first, GLsizei count))                         \
    X(void, glGenTextures, (GLsizei n, GLuint * textures))                                   \
    X(void, glBindTexture, (GLenum target, GLuint texture))                                  \
    X(void, glTexParameteri, (GLenum target, GLenum pname, GLint param))                     \
    X(void, glTexImage2D,                                                                    \
      (GLenum target, GLint level, GLint internal_format, GLsizei width, GLsizei height,     \
       GLint border, GLenum format, GLenum type, const void* pixels))                        \
    X(void, glDeleteTextures, (GLsizei n, const GLuint* textures))

#define MAGTILE_GL_DECLARE(ret, name, params) extern ret(*name) params;
MAGTILE_GL_FUNCTION_LIST(MAGTILE_GL_DECLARE)
#undef MAGTILE_GL_DECLARE

/// 入口解析回调, 与 glfwGetProcAddress 签名兼容。
using GlProc = void (*)();
using ProcResolver = GlProc (*)(const char* name);

/// 解析全部函数指针。任一入口缺失则返回 false 并向 stderr 输出
/// 缺失符号名 (调用方应放弃初始化)。
[[nodiscard]] bool loadFunctions(ProcResolver resolver);

}  // namespace magtile::render::glapi
