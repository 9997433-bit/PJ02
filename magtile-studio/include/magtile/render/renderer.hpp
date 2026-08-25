#pragma once

// =============================================================
// MagTile Studio - 渲染层抽象接口
//
// 技术选型 (详见 docs/ARCHITECTURE.md):
// 正式渲染后端计划采用 GLFW + OpenGL 4.1 Core (三平台均原生支持,
// macOS 最高支持到 4.1), 通过本接口隔离, 后续可平滑替换为
// Vulkan / Metal 后端而不影响核心与教程模块。
// 当前阶段仅提供 NullRenderer (无窗口), 用于 CLI 校验与 CI。
// =============================================================

#include <memory>
#include <string>

#include "magtile/core/tile_catalog.hpp"
#include "magtile/core/tile_instance.hpp"
#include "magtile/core/vec3.hpp"

namespace magtile::render {

struct Camera {
    core::Vec3 eye{6.0, -6.0, 5.0};
    core::Vec3 target{0.0, 0.0, 1.0};
    core::Vec3 up{0.0, 0.0, 1.0};
    double fov_deg = 45.0;
};

/// 渲染一片磁力片所需的全部状态。
struct RenderTile {
    const core::TileInstance* instance = nullptr;
    bool highlighted = false;  ///< 教程参照高亮 (描边)
    bool ghost = false;        ///< 半透明幽灵片 (提示即将放置的位置)
};

/// 渲染后端接口。实现必须无状态泄漏地支持多次 initialize/shutdown。
class IRenderer {
public:
    virtual ~IRenderer() = default;

    virtual bool initialize(int width, int height, const std::string& window_title) = 0;
    virtual void shutdown() = 0;

    virtual void beginFrame(const Camera& camera) = 0;
    virtual void submitTile(const RenderTile& tile, const core::TileShape& shape) = 0;
    virtual void endFrame() = 0;

    /// 窗口是否请求关闭 (无窗口后端恒为 false)。
    [[nodiscard]] virtual bool shouldClose() const = 0;
};

/// 无窗口渲染器: 只统计提交数量并可输出文本摘要, 用于测试与 CLI。
[[nodiscard]] std::unique_ptr<IRenderer> createNullRenderer(bool verbose = false);

}  // namespace magtile::render
