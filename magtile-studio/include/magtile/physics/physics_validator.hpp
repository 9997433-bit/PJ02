#pragma once

// =============================================================
// MagTile Studio - 物理规则校验器
//
// 商业化教程内容的核心质量关卡: 每一个入库模型 (以及教程的每一个
// 中间步骤) 都必须通过本校验器, 保证用户照着教程搭建时不会出现
// 悬空、无法吸附、互相穿插或重心失稳的情况。
//
// 规则概览 (详见 docs/PHYSICS_RULES.md):
//   R1 接地支撑: 每片磁力片必须存在一条经由磁力连接到达地面的支撑路径
//   R2 磁力连接: 相邻磁力片必须通过等长磁力边完全贴合吸附
//   R3 无重叠:   任意两片磁力片不得在同一平面上互相穿插
//   R4 重心稳定: 整体重心的水平投影须落在接地区域凸包内 (基础版)
// =============================================================

#include <string>
#include <vector>

#include "magtile/core/model_definition.hpp"
#include "magtile/core/tile_catalog.hpp"
#include "magtile/core/tile_instance.hpp"

namespace magtile::physics {

enum class IssueSeverity {
    Error,    ///< 违反物理规则, 模型不可发布
    Warning,  ///< 不影响可搭性, 但建议修正
};

/// 单条校验结果。code 为稳定的机器可读标识, message 为中文描述。
struct ValidationIssue {
    IssueSeverity severity = IssueSeverity::Error;
    std::string code;                    ///< 如 "floating_tile"、"tile_overlap"
    std::string message;                 ///< 中文描述, 可直接展示给内容制作人员
    std::vector<std::string> tile_ids;   ///< 涉及的磁力片 id
};

struct ValidationReport {
    std::vector<ValidationIssue> issues;

    [[nodiscard]] bool ok() const noexcept { return errorCount() == 0; }
    [[nodiscard]] std::size_t errorCount() const noexcept;
    [[nodiscard]] std::size_t warningCount() const noexcept;
    void merge(const ValidationReport& other);
};

/// 校验参数。长度单位与世界坐标一致 (1.0 = 正方形边长, 约 70mm)。
struct PhysicsConfig {
    double connect_tolerance = 0.02;   ///< 磁力边端点吸附容差 (约 1.4mm)
    double ground_tolerance = 0.02;    ///< 接地判定容差
    double overlap_tolerance = 0.02;   ///< 重叠判定的最小穿插深度
    double coplanar_tolerance = 0.02;  ///< 共面判定容差
    double stability_margin = 0.15;    ///< 重心允许超出接地凸包的水平距离 (磁力吸附提供的裕量)
};

/// 已识别的一条磁力连接 (a、b 为 final_assembly 下标)。
struct MagnetConnection {
    std::size_t tile_a = 0;
    std::size_t tile_b = 0;
    std::size_t edge_a = 0;
    std::size_t edge_b = 0;
};

class PhysicsValidator {
public:
    explicit PhysicsValidator(const core::TileCatalog& catalog, PhysicsConfig config = {});

    /// 校验一组磁力片构成的静态组合 (R1~R4)。
    /// context 为报告信息前缀, 例如 "步骤 3 完成后"。
    [[nodiscard]] ValidationReport validateAssembly(
        const std::vector<const core::TileInstance*>& tiles,
        const std::string& context = {}) const;

    /// 校验完整模型: 最终成品 + 每个教程步骤完成后的中间状态。
    /// 逐步校验保证教程任意时刻的半成品都物理成立 (不会搭到一半塌掉)。
    [[nodiscard]] ValidationReport validateModel(const core::ModelDefinition& model) const;

    /// 枚举组合中的全部磁力连接 (供渲染层画吸附提示、教程层做讲解)。
    [[nodiscard]] std::vector<MagnetConnection> findConnections(
        const std::vector<const core::TileInstance*>& tiles) const;

    [[nodiscard]] const PhysicsConfig& config() const noexcept { return config_; }

private:
    const core::TileCatalog* catalog_;
    PhysicsConfig config_;
};

}  // namespace magtile::physics
