// =============================================================
// MagTile Studio - 应用入口
//
// 同一个可执行文件提供两种形态:
//   - CLI: 内容制作与质检 (catalog / validate / tutorial);
//   - GUI: tutorial --gui 在 3D 窗口中交互式跟随教程
//     (需要构建时开启 MAGTILE_BUILD_GL_RENDERER)。
//
// 用法:
//   magtile_app catalog  [--data-dir DIR]                查看磁力片形状目录
//   magtile_app validate <model.json> [--data-dir DIR]   物理与教程质检
//   magtile_app tutorial <model.json> [--gui] [--data-dir DIR]  分步教程
// =============================================================

#include <cstdio>
#include <cstdlib>
#include <exception>
#include <filesystem>
#include <string>
#include <vector>

#include "magtile/core/json_io.hpp"
#include "magtile/physics/physics_validator.hpp"
#include "magtile/tutorial/tutorial_engine.hpp"

#if defined(MAGTILE_HAS_GL_RENDERER)
#include <algorithm>
#include <unordered_set>

#include "magtile/physics/geometry.hpp"
#include "magtile/render/gl_renderer.hpp"
#endif

namespace {

namespace fs = std::filesystem;
using namespace magtile;

struct CliArgs {
    std::string command;
    std::string model_file;
    fs::path data_dir = "data";
    bool gui = false;
    long max_frames = 0;         ///< >0 时渲染指定帧数后自动退出 (冒烟测试)
    std::string screenshot_file; ///< 非空时在最后一帧保存 PPM 截图 (冒烟测试)
};

void printUsage() {
    std::printf(
        "MagTile Studio - 磁力片搭建教程\n"
        "\n"
        "用法:\n"
        "  magtile_app catalog  [--data-dir DIR]              查看磁力片形状目录\n"
        "  magtile_app validate <model.json> [--data-dir DIR] 校验模型物理规则与教程步骤\n"
        "  magtile_app tutorial <model.json> [--gui] [--data-dir DIR]\n"
        "                       分步教程: 默认在终端预览, --gui 打开 3D 交互窗口\n"
        "\n"
        "图形模式测试选项 (供 CI 冒烟测试):\n"
        "  --frames N          渲染 N 帧后自动退出\n"
        "  --screenshot FILE   退出前把画面保存为 PPM 图片\n");
}

bool parseArgs(int argc, char** argv, CliArgs& args) {
    if (argc < 2) return false;
    args.command = argv[1];

    std::vector<std::string> positional;
    for (int i = 2; i < argc; ++i) {
        const std::string arg = argv[i];
        if (arg == "--data-dir") {
            if (i + 1 >= argc) return false;
            args.data_dir = argv[++i];
        } else if (arg == "--gui") {
            args.gui = true;
        } else if (arg == "--frames") {
            if (i + 1 >= argc) return false;
            args.max_frames = std::strtol(argv[++i], nullptr, 10);
        } else if (arg == "--screenshot") {
            if (i + 1 >= argc) return false;
            args.screenshot_file = argv[++i];
        } else {
            positional.push_back(arg);
        }
    }
    if (args.command == "catalog") return positional.empty();
    if (args.command == "validate" || args.command == "tutorial") {
        if (positional.size() != 1) return false;
        args.model_file = positional[0];
        return true;
    }
    return false;
}

int runCatalog(const CliArgs& args) {
    const auto catalog = core::loadTileCatalog(args.data_dir / "tile_catalog.json");
    std::printf("磁力片形状目录 (共 %zu 种):\n\n", catalog.size());
    for (const auto& [type, shape] : catalog.shapes()) {
        std::printf("  %-22s %s  顶点 %zu 个, 磁力边 %zu 条, 面积 %.3f\n",
                    std::string(core::toString(type)).c_str(), shape.name_zh.c_str(),
                    shape.vertices.size(), shape.magnet_edge_indices.size(), shape.area());
        if (!shape.description_zh.empty()) {
            std::printf("      %s\n", shape.description_zh.c_str());
        }
    }
    return 0;
}

void printModelHeader(const core::ModelDefinition& model) {
    std::printf("模型: %s (%s)\n", model.name.c_str(), model.id.c_str());
    std::printf("难度: %d/5  磁力片: %d 片  步骤: %zu 步\n", model.difficulty,
                model.total_pieces, model.steps.size());
    std::printf("所需磁力片清单:\n");
    for (const auto& [type, count] : model.pieceCountByType()) {
        std::printf("  %s x %d\n", std::string(core::displayNameZh(type)).c_str(), count);
    }
    std::printf("\n");
}

int runValidate(const CliArgs& args) {
    const auto catalog = core::loadTileCatalog(args.data_dir / "tile_catalog.json");
    const auto model = core::loadModelDefinition(args.model_file);
    printModelHeader(model);

    int failures = 0;

    // 教程步骤一致性
    const auto step_problems = tutorial::TutorialEngine::checkConsistency(model);
    if (step_problems.empty()) {
        std::printf("[通过] 教程步骤一致性检查\n");
    } else {
        for (const auto& problem : step_problems) {
            std::printf("[错误] 步骤一致性: %s\n", problem.c_str());
            ++failures;
        }
    }

    // 物理规则 (最终成品 + 每一步中间状态)
    const physics::PhysicsValidator validator(catalog);
    const auto report = validator.validateModel(model);
    for (const auto& issue : report.issues) {
        const char* tag = issue.severity == physics::IssueSeverity::Error ? "错误" : "警告";
        std::printf("[%s] %s (%s)\n", tag, issue.message.c_str(), issue.code.c_str());
    }
    failures += static_cast<int>(report.errorCount());

    if (report.ok() && step_problems.empty()) {
        std::printf("[通过] 物理规则检查: 接地支撑 / 磁力连接 / 无重叠 / 重心稳定\n");

        // 补充统计信息, 方便内容制作人员核对
        std::vector<const core::TileInstance*> tiles;
        for (const auto& tile : model.final_assembly) tiles.push_back(&tile);
        const auto connections = validator.findConnections(tiles);
        std::printf("\n统计: 磁力连接 %zu 处, 校验含最终成品与 %zu 个中间步骤\n",
                    connections.size(), model.steps.size());
        std::printf("\n结论: 模型 %s 可发布\n", model.id.c_str());
        return 0;
    }

    std::printf("\n结论: 模型 %s 未通过质检 (%d 个错误, %zu 个警告)\n", model.id.c_str(),
                failures, report.warningCount());
    return 1;
}

#if defined(MAGTILE_HAS_GL_RENDERER)

/// 图形模式: 在 3D 窗口中交互式跟随分步教程。
int runTutorialGui(const CliArgs& args) {
    const auto catalog = core::loadTileCatalog(args.data_dir / "tile_catalog.json");
    auto model = core::loadModelDefinition(args.model_file);
    printModelHeader(model);

    // 内容有问题的模型直接拒绝进入图形教程
    const auto problems = tutorial::TutorialEngine::checkConsistency(model);
    if (!problems.empty()) {
        for (const auto& problem : problems) {
            std::fprintf(stderr, "[错误] 步骤一致性: %s\n", problem.c_str());
        }
        return 1;
    }

    tutorial::TutorialEngine engine(std::move(model));
    engine.nextStep();  // 打开窗口即进入第 1 步

    auto renderer = render::createOpenGLRenderer();
    if (!renderer->initialize(1440, 900, "MagTile Studio - " + engine.model().name)) {
        std::fprintf(stderr, "错误: 无法创建图形窗口 (需要支持 OpenGL 4.1 的显示环境)\n");
        return 1;
    }

    // 初始取景: 最终成品的包围盒
    {
        core::Vec3 bb_min{1e9, 1e9, 1e9}, bb_max{-1e9, -1e9, -1e9};
        for (const auto& tile : engine.model().final_assembly) {
            const auto world = physics::transformTile(tile, catalog.get(tile.type));
            for (const auto& v : world.vertices) {
                bb_min = {std::min(bb_min.x, v.x), std::min(bb_min.y, v.y),
                          std::min(bb_min.z, v.z)};
                bb_max = {std::max(bb_max.x, v.x), std::max(bb_max.y, v.y),
                          std::max(bb_max.z, v.z)};
            }
        }
        renderer->orbitCamera().frameBounds(bb_min, bb_max);
    }

    long frame_index = 0;
    while (!renderer->shouldClose()) {
        renderer->pollEvents();
        render::TutorialActions actions = renderer->consumeActions();

        // 本帧场景状态 (模型规模为数百片, 每帧重建集合开销可忽略)
        std::unordered_set<const core::TileInstance*> placed, added, referenced;
        for (const auto* tile : engine.visibleTiles()) placed.insert(tile);
        for (const auto* tile : engine.tilesAddedThisStep()) added.insert(tile);
        for (const auto* tile : engine.highlightTiles()) referenced.insert(tile);

        renderer->beginFrame(renderer->orbitCamera().toCamera());
        for (const auto& tile : engine.model().final_assembly) {
            render::RenderTile rt;
            rt.instance = &tile;
            rt.just_placed = added.count(&tile) > 0;
            rt.ghost = !rt.just_placed && placed.count(&tile) == 0;
            rt.highlighted = referenced.count(&tile) > 0;
            renderer->submitTile(rt, catalog.get(tile.type));
        }

        render::TutorialHudState hud;
        hud.model_name = engine.model().name;
        hud.step_number = engine.currentStepNumber();
        hud.step_count = engine.stepCount();
        hud.progress = engine.progress();
        hud.tiles_placed = static_cast<int>(placed.size());
        hud.tiles_total = static_cast<int>(engine.model().final_assembly.size());
        if (const core::BuildStep* step = engine.currentStep(); step != nullptr) {
            hud.description = step->description;
            hud.tip = step->tip;
        } else {
            hud.description = "转动视角熟悉最终成品, 点击 [下一步] 开始搭建。";
        }
        actions |= renderer->submitHud(hud);

        const bool last_frame = args.max_frames > 0 && frame_index + 1 >= args.max_frames;
        if (last_frame && !args.screenshot_file.empty()) {
            renderer->requestScreenshot(args.screenshot_file);
        }
        renderer->endFrame();

        // 帧末统一应用导航操作, 下一帧生效
        if (actions.reset) {
            engine.reset();
        } else if (actions.next_step) {
            engine.nextStep();
        } else if (actions.previous_step) {
            engine.previousStep();
        }

        ++frame_index;
        if (last_frame) break;
    }

    renderer->shutdown();
    return 0;
}

#else

int runTutorialGui(const CliArgs& /*args*/) {
    std::fprintf(stderr,
                 "错误: 本构建未包含图形渲染后端。\n"
                 "请以 -DMAGTILE_BUILD_GL_RENDERER=ON 重新构建 (默认开启)。\n");
    return 2;
}

#endif  // MAGTILE_HAS_GL_RENDERER

int runTutorial(const CliArgs& args) {
    if (args.gui) return runTutorialGui(args);
    const auto catalog = core::loadTileCatalog(args.data_dir / "tile_catalog.json");
    auto model = core::loadModelDefinition(args.model_file);
    printModelHeader(model);

    tutorial::TutorialEngine engine(std::move(model));
    while (engine.nextStep()) {
        const core::BuildStep* step = engine.currentStep();
        std::printf("第 %d/%d 步  [进度 %3.0f%%]\n", engine.currentStepNumber(),
                    engine.stepCount(), engine.progress() * 100.0);
        std::printf("  %s\n", step->description.c_str());
        if (!step->tip.empty()) {
            std::printf("  提示: %s\n", step->tip.c_str());
        }
        std::printf("  本步放置 %zu 片:", step->tiles_to_add.size());
        for (const auto* tile : engine.tilesAddedThisStep()) {
            std::printf(" %s(%s/%s)", tile->id.c_str(),
                        std::string(core::displayNameZh(tile->type)).c_str(),
                        std::string(core::displayNameZh(tile->color)).c_str());
        }
        std::printf("\n\n");
    }
    std::printf("教程结束, 共放置 %zu 片磁力片。\n", engine.visibleTiles().size());
    return 0;
}

}  // namespace

int main(int argc, char** argv) {
    CliArgs args;
    if (!parseArgs(argc, argv, args)) {
        printUsage();
        return 2;
    }

    try {
        if (args.command == "catalog") return runCatalog(args);
        if (args.command == "validate") return runValidate(args);
        if (args.command == "tutorial") return runTutorial(args);
    } catch (const std::exception& e) {
        std::fprintf(stderr, "错误: %s\n", e.what());
        return 1;
    }
    printUsage();
    return 2;
}
