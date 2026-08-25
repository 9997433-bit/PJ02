#pragma once

// =============================================================
// MagTile Studio - 物理规则校验器
//
// 商业化教程内容的核心质量关卡: 每一个入库模型 (以及教程的每一个
// 中间步骤) 都必须通过本校验器, 保证用户照着教程搭建时不会出现
// 悬空、无法吸附、互相穿插、重心失稳、悬挂超重、悬臂折断或
// "手伸不进去放不了" 的情况。
//
// 规则概览 (详见 docs/PHYSICS_RULES.md):
//   -- 几何/拓扑规则 (第一版) --
//   R1 接地支撑: 每片磁力片必须存在一条经由磁力连接到达地面的支撑路径
//   R2 磁力连接: 相邻磁力片必须通过等长磁力边完全贴合吸附
//   R3 无重叠:   任意两片磁力片不得在同一平面上互相穿插
//   R4 重心稳定: 整体重心的水平投影须落在接地区域凸包内 (基础版)
//   -- 静力学/工艺规则 (针对实搭掉落问题新增) --
//   R5 悬挂承重: 经由单条铰链线悬挂的磁力片总重不得超过磁力边承重预算
//   R6 悬臂力矩: 单边连接是铰链而非刚性节点, 悬挑结构的重力力矩
//               不得超过铰链线的抗弯矩预算 (三角斜撑/环状加固可豁免)
//   R7 装配可达: 按教程顺序逐片放置时, 每片在放下的那一刻必须有依托
//               (接地或吸附), 且不能被已完成结构完全包围 (手要伸得进去)
//   R8 结构冗余: 高层结构中警告单点失效连接与纯树状 (无环) 拓扑,
//               鼓励三角桁架 (Warning 级); 无环高墙超过
//               unbraced_wall_max_height 升级为 Error (阻断发布)
//
// R5/R6/R8 的静力学模型: 把每一组共线磁力边视为一条 "铰链线",
// 假想剪断这条铰链后与地面失去联系的子结构, 其全部重量 (R5) 与
// 绕铰链轴的重力力矩 (R6) 都要由这条铰链承担; 预算取实测额定值
// 乘以抗碰撞安全系数 (默认 0.8, 即保留 20% 抗震/碰撞裕量)。
// =============================================================

#include <optional>
#include <string>
#include <string_view>
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
///
/// 现有 code 一览:
///   floating_tile / isolated_tile / disconnected_assembly / tile_overlap
///   unstable_center_of_mass / no_ground_contact            (R1~R4)
///   hanging_chain_overload / hanging_chain_long            (R5)
///   cantilever_overload                                    (R6)
///   unplaceable_tile / enclosed_placement                  (R7)
///   single_point_of_failure / no_structural_redundancy
///   unbraced_wall_too_tall                                 (R8)
struct ValidationIssue {
    IssueSeverity severity = IssueSeverity::Error;
    std::string code;                    ///< 如 "floating_tile"、"cantilever_overload"
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

/// 校验参数。长度单位与世界坐标一致 (1.0 = 正方形边长, 约 70mm);
/// 质量单位为克, 按面积折算 (正方形磁力片实测约 30g)。
struct PhysicsConfig {
    // ---- 几何容差 (R1~R4) ---------------------------------------
    double connect_tolerance = 0.02;   ///< 磁力边端点吸附容差 (约 1.4mm)
    double ground_tolerance = 0.02;    ///< 接地判定容差
    double overlap_tolerance = 0.02;   ///< 重叠判定的最小穿插深度
    double coplanar_tolerance = 0.02;  ///< 共面判定容差
    double stability_margin = 0.15;    ///< 重心允许超出接地凸包的水平距离 (磁力吸附提供的裕量)

    // ---- 静力学参数 (R5/R6) --------------------------------------
    double tile_mass_per_area = 30.0;  ///< 面密度 g/单位面积 (正方形 1x1 约 30g)
    /// 单位长度磁力边的额定悬挂承重 (克)。实测一条标准边竖直悬挂约在
    /// 5 片正方形 (150g) 时脱落, 乘安全系数 0.8 后允许 120g ≈ 4 片。
    double hanging_capacity_per_edge = 150.0;
    int max_hanging_tiles_per_edge = 4;  ///< 单条铰链边悬挂链片数上限 (超出仅 Warning: 摇晃风险)
    /// 单位长度磁力边的额定抗弯矩 (克 x 世界单位)。实测单片正方形平挑
    /// 在墙顶 (力矩 30g x 0.5 = 15) 勉强稳住, 两片连挑 (力矩 60) 必掉,
    /// 取 25 为额定值, 乘安全系数 0.8 后预算 20。
    double hinge_moment_capacity_per_edge = 25.0;
    double knock_safety_factor = 0.8;    ///< 抗震/碰撞安全系数: 只允许用到额定承载的 80%
    double hanging_z_tolerance = 0.1;    ///< 悬挂判定: 子结构重心须低于铰链线至少此距离
    double collinear_tolerance = 0.02;   ///< 磁力边共线分组容差 (共线边合成一条铰链线)

    // ---- 结构冗余参数 (R8) ---------------------------------------
    double tall_structure_height = 2.5;    ///< 最高点达到此高度即视为高层结构, 启用 R8
    int spof_min_component_tiles = 3;      ///< 单点失效警告阈值: 单条连接独自支撑的最少片数
    /// 无桁架结构 (连接图纯树状, 零环路) 允许的最大高度。超过即 Error
    /// `unbraced_wall_too_tall`: 高墙没有任何三角桁架/闭合环加固时,
    /// 每个连接都是自由铰链, 实搭中轻碰即整面倒塌 —— 不再只是 Warning。
    double unbraced_wall_max_height = 4.0;

    // ---- 预设档位 -------------------------------------------------
    /// 弱磁严格档 (strict_consumer): 面向消费者手中磁力较弱的品牌 /
    /// 使用多年磁力衰减的旧片。悬挂额定承重从 150g 降到 120g/单位边长
    /// (实测弱磁品牌标准边约 4 片正方形即脱落), 抗碰撞安全系数从 0.8
    /// 收紧到 0.7 (儿童实际使用中的碰撞远多于成人测试)。
    /// 旗舰模型必须在本档位下依然全绿 (CMake 注册 validate_strict_* 用例)。
    [[nodiscard]] static PhysicsConfig strictConsumer();
};

/// 按档位名称查找预设校验参数:
///   "" / "default" / "standard"    -> 默认档 (官方基准品牌实测标定);
///   "strict" / "strict_consumer"   -> 弱磁严格档 (见 strictConsumer());
/// 未知名称返回 std::nullopt, 由调用方 (CLI) 报错。
[[nodiscard]] std::optional<PhysicsConfig> configForProfile(std::string_view name);

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

    /// 校验一组磁力片构成的静态组合 (R1~R6、R8)。
    /// context 为报告信息前缀, 例如 "步骤 3 完成后"。
    [[nodiscard]] ValidationReport validateAssembly(
        const std::vector<const core::TileInstance*>& tiles,
        const std::string& context = {}) const;

    /// R7 装配可达性: 按教程步骤内 tiles_to_add 的先后顺序逐片模拟放置,
    /// 检查每片在放下的那一刻 (1) 接地或能吸附到已放置磁力片;
    /// (2) 未被已完成结构完全包围 (从外部伸手可达)。
    /// 静态规则只保证 "结构成立", 本规则保证 "人手搭得出来"。
    [[nodiscard]] ValidationReport validatePlacements(const core::ModelDefinition& model) const;

    /// 校验完整模型: 最终成品 + 每个教程步骤完成后的中间状态 (R1~R6、R8)
    /// + 全程逐片放置可行性 (R7)。
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
