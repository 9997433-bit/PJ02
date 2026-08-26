#pragma once

// =============================================================
// MagTile Studio - 分步教程引擎
// 驱动 "上一步 / 下一步" 交互, 向渲染层提供当前应显示与高亮的
// 磁力片集合。引擎本身与 UI / 渲染后端完全解耦。
// =============================================================

#include <string>
#include <vector>

#include "magtile/core/model_definition.hpp"

namespace magtile::tutorial {

class TutorialEngine {
public:
    explicit TutorialEngine(core::ModelDefinition model);

    // ---- 步骤导航 -------------------------------------------------
    [[nodiscard]] int stepCount() const noexcept;
    /// 当前步骤序号, 1 起; 0 表示尚未开始 (仅显示空场景)。
    [[nodiscard]] int currentStepNumber() const noexcept { return current_step_; }
    [[nodiscard]] bool isFinished() const noexcept { return current_step_ >= stepCount(); }

    bool nextStep();      ///< 已在最后一步时返回 false
    bool previousStep();  ///< 已在开始处时返回 false
    void reset() noexcept { current_step_ = 0; }
    bool goToStep(int step_number);  ///< 跳转到指定步骤 (0 ~ stepCount)

    // ---- 场景查询 (渲染层使用) ------------------------------------
    [[nodiscard]] const core::BuildStep* currentStep() const;  ///< 未开始时返回 nullptr
    /// 当前步骤完成后场景中的全部磁力片 (按放置顺序)。
    [[nodiscard]] std::vector<const core::TileInstance*> visibleTiles() const;
    /// 本步骤新增的磁力片 (渲染层以动画 / 闪烁引导用户放置)。
    [[nodiscard]] std::vector<const core::TileInstance*> tilesAddedThisStep() const;
    /// 本步骤需要高亮的参照磁力片。
    [[nodiscard]] std::vector<const core::TileInstance*> highlightTiles() const;
    /// 完成进度 0.0 ~ 1.0 (按已放置磁力片数量计)。
    [[nodiscard]] double progress() const noexcept;

    [[nodiscard]] const core::ModelDefinition& model() const noexcept { return model_; }

    // ---- 内容质检 -------------------------------------------------
    /// 检查步骤数据一致性 (序号连续、引用存在、不重复、全覆盖),
    /// 返回中文问题列表; 为空表示通过。物理校验见 PhysicsValidator。
    [[nodiscard]] static std::vector<std::string> checkConsistency(
        const core::ModelDefinition& model);

private:
    core::ModelDefinition model_;
    int current_step_ = 0;  ///< 0 = 未开始; n = 第 n 步已完成放置
};

}  // namespace magtile::tutorial
