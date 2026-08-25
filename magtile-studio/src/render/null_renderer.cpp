#include <cstdio>

#include "magtile/render/renderer.hpp"

namespace magtile::render {
namespace {

/// 无窗口渲染器: 用于 CLI 工具、单元测试与 CI 环境。
/// 正式的 GLFW + OpenGL 后端将以同样的接口在 render 模块中实现。
class NullRenderer final : public IRenderer {
public:
    explicit NullRenderer(bool verbose) : verbose_(verbose) {}

    bool initialize(int width, int height, const std::string& window_title) override {
        if (verbose_) {
            std::printf("[render] NullRenderer 初始化 %dx%d \"%s\"\n", width, height,
                        window_title.c_str());
        }
        initialized_ = true;
        return true;
    }

    void shutdown() override { initialized_ = false; }

    void beginFrame(const Camera& /*camera*/) override { frame_tile_count_ = 0; }

    void submitTile(const RenderTile& tile, const core::TileShape& shape) override {
        ++frame_tile_count_;
        if (verbose_ && tile.instance != nullptr) {
            std::printf("[render]   %s (%s)%s%s\n", tile.instance->id.c_str(),
                        shape.name_zh.c_str(), tile.highlighted ? " [高亮]" : "",
                        tile.ghost ? " [虚影]" : "");
        }
    }

    void endFrame() override {
        if (verbose_) {
            std::printf("[render] 本帧提交磁力片 %zu 片\n", frame_tile_count_);
        }
    }

    [[nodiscard]] bool shouldClose() const override { return false; }

private:
    bool verbose_ = false;
    bool initialized_ = false;
    std::size_t frame_tile_count_ = 0;
};

}  // namespace

std::unique_ptr<IRenderer> createNullRenderer(bool verbose) {
    return std::make_unique<NullRenderer>(verbose);
}

}  // namespace magtile::render
