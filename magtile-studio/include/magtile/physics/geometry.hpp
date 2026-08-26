#pragma once

// =============================================================
// MagTile Studio - 物理校验所需的几何工具
// =============================================================

#include <vector>

#include "magtile/core/tile_catalog.hpp"
#include "magtile/core/tile_instance.hpp"
#include "magtile/core/vec3.hpp"

namespace magtile::physics {

using core::Vec2;
using core::Vec3;

/// 磁力片变换到世界坐标后的几何快照。
struct TransformedTile {
    const core::TileInstance* instance = nullptr;
    const core::TileShape* shape = nullptr;
    std::vector<Vec3> vertices;      ///< 世界坐标顶点 (逆时针)
    Vec3 normal;                     ///< 单位法向量 (朝向由顶点绕序决定)
    Vec3 centroid;                   ///< 面质心 (世界坐标)
    double area = 0.0;               ///< 面积
    double min_z = 0.0;              ///< 最低点高度, 用于接地判断

    /// 第 i 条边的两个端点 (世界坐标)。
    [[nodiscard]] std::pair<Vec3, Vec3> edge(std::size_t i) const;
    [[nodiscard]] std::size_t edgeCount() const noexcept { return vertices.size(); }
    [[nodiscard]] bool isMagnetEdge(std::size_t i) const noexcept;
};

/// 应用实例的旋转与平移, 生成世界坐标几何。
[[nodiscard]] TransformedTile transformTile(const core::TileInstance& instance,
                                            const core::TileShape& shape);

/// 判断两片是否共面 (法向平行且平面距离小于 tolerance)。
[[nodiscard]] bool areCoplanar(const TransformedTile& a, const TransformedTile& b,
                               double tolerance);

/// 共面凸多边形重叠检测 (分离轴定理)。
/// 仅当两多边形在所有分离轴上的重叠量都超过 tolerance 时判定为重叠,
/// 因此共享一条边的相邻磁力片不会被误判。调用方需先保证共面。
[[nodiscard]] bool coplanarPolygonsOverlap(const TransformedTile& a, const TransformedTile& b,
                                           double tolerance);

/// 二维点集凸包 (Andrew 单调链), 返回逆时针顶点; 少于 3 点时原样返回去重结果。
[[nodiscard]] std::vector<Vec2> convexHull2D(std::vector<Vec2> points);

/// 点到凸包的带符号距离: 包内为负 (取到边界最近距离的相反数), 包外为正。
/// 凸包退化为线段/点时返回点到该线段/点的距离。
[[nodiscard]] double signedDistanceToHull(const Vec2& point, const std::vector<Vec2>& hull);

}  // namespace magtile::physics
