#include "magtile/tutorial/tutorial_engine.hpp"

#include <set>
#include <sstream>
#include <utility>

namespace magtile::tutorial {

using core::BuildStep;
using core::TileInstance;

TutorialEngine::TutorialEngine(core::ModelDefinition model) : model_(std::move(model)) {}

int TutorialEngine::stepCount() const noexcept {
    return static_cast<int>(model_.steps.size());
}

bool TutorialEngine::nextStep() {
    if (current_step_ >= stepCount()) return false;
    ++current_step_;
    return true;
}

bool TutorialEngine::previousStep() {
    if (current_step_ <= 0) return false;
    --current_step_;
    return true;
}

bool TutorialEngine::goToStep(int step_number) {
    if (step_number < 0 || step_number > stepCount()) return false;
    current_step_ = step_number;
    return true;
}

const BuildStep* TutorialEngine::currentStep() const {
    if (current_step_ <= 0 || current_step_ > stepCount()) return nullptr;
    return &model_.steps[static_cast<std::size_t>(current_step_ - 1)];
}

std::vector<const TileInstance*> TutorialEngine::visibleTiles() const {
    return model_.tilesUpToStep(current_step_);
}

std::vector<const TileInstance*> TutorialEngine::tilesAddedThisStep() const {
    std::vector<const TileInstance*> result;
    if (const BuildStep* step = currentStep()) {
        for (const auto& tile_id : step->tiles_to_add) {
            if (const TileInstance* tile = model_.findTile(tile_id)) {
                result.push_back(tile);
            }
        }
    }
    return result;
}

std::vector<const TileInstance*> TutorialEngine::highlightTiles() const {
    std::vector<const TileInstance*> result;
    if (const BuildStep* step = currentStep()) {
        for (const auto& tile_id : step->highlight_tiles) {
            if (const TileInstance* tile = model_.findTile(tile_id)) {
                result.push_back(tile);
            }
        }
    }
    return result;
}

double TutorialEngine::progress() const noexcept {
    if (model_.final_assembly.empty()) return 0.0;
    std::size_t placed = 0;
    const int limit = current_step_;
    for (int i = 0; i < limit; ++i) {
        placed += model_.steps[static_cast<std::size_t>(i)].tiles_to_add.size();
    }
    return static_cast<double>(placed) / static_cast<double>(model_.final_assembly.size());
}

std::vector<std::string> TutorialEngine::checkConsistency(const core::ModelDefinition& model) {
    std::vector<std::string> problems;

    if (model.steps.empty()) {
        problems.emplace_back("模型没有任何教程步骤");
        return problems;
    }

    // 步骤序号必须从 1 开始连续递增
    for (std::size_t i = 0; i < model.steps.size(); ++i) {
        const int expected = static_cast<int>(i) + 1;
        if (model.steps[i].step_number != expected) {
            std::ostringstream oss;
            oss << "步骤序号不连续: 第 " << i + 1 << " 个步骤的 step_number 为 "
                << model.steps[i].step_number << ", 期望 " << expected;
            problems.push_back(oss.str());
        }
        if (model.steps[i].description.empty()) {
            std::ostringstream oss;
            oss << "第 " << expected << " 步缺少中文说明";
            problems.push_back(oss.str());
        }
        if (model.steps[i].tiles_to_add.empty()) {
            std::ostringstream oss;
            oss << "第 " << expected << " 步没有新增任何磁力片";
            problems.push_back(oss.str());
        }
    }

    // 每片磁力片必须恰好被一个步骤放置
    std::set<std::string> placed;
    for (const auto& step : model.steps) {
        for (const auto& tile_id : step.tiles_to_add) {
            if (model.findTile(tile_id) == nullptr) {
                problems.push_back("步骤引用了不存在的磁力片: " + tile_id);
            } else if (!placed.insert(tile_id).second) {
                problems.push_back("磁力片 " + tile_id + " 被多个步骤重复放置");
            }
        }
        for (const auto& tile_id : step.highlight_tiles) {
            if (model.findTile(tile_id) == nullptr) {
                problems.push_back("步骤高亮了不存在的磁力片: " + tile_id);
            }
        }
    }
    for (const auto& tile : model.final_assembly) {
        if (placed.find(tile.id) == placed.end()) {
            problems.push_back("磁力片 " + tile.id + " 未被任何步骤放置");
        }
    }

    return problems;
}

}  // namespace magtile::tutorial
