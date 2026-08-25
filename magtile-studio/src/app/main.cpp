// =============================================================
// MagTile Studio - 命令行入口
//
// 当前阶段提供内容制作与质检所需的 CLI; 图形界面版本将在渲染
// 后端 (GLFW + OpenGL) 落地后基于同一套核心库构建。
//
// 用法:
//   magtile_app catalog  [--data-dir DIR]           查看磁力片形状目录
//   magtile_app validate <model.json> [--data-dir DIR]  物理与教程质检
//   magtile_app tutorial <model.json> [--data-dir DIR]  预览分步教程
// =============================================================

#include <cstdio>
#include <exception>
#include <filesystem>
#include <string>
#include <vector>

#include "magtile/core/json_io.hpp"
#include "magtile/physics/physics_validator.hpp"
#include "magtile/tutorial/tutorial_engine.hpp"

namespace {

namespace fs = std::filesystem;
using namespace magtile;

struct CliArgs {
    std::string command;
    std::string model_file;
    fs::path data_dir = "data";
};

void printUsage() {
    std::printf(
        "MagTile Studio - 磁力片搭建教程内容工具\n"
        "\n"
        "用法:\n"
        "  magtile_app catalog  [--data-dir DIR]              查看磁力片形状目录\n"
        "  magtile_app validate <model.json> [--data-dir DIR] 校验模型物理规则与教程步骤\n"
        "  magtile_app tutorial <model.json> [--data-dir DIR] 在终端预览分步教程\n");
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

int runTutorial(const CliArgs& args) {
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
