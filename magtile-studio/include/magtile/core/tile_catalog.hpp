#pragma once

// =============================================================
// MagTile Studio - 磁力片形状目录
// 形状几何数据从 data/tile_catalog.json 加载, 代码不硬编码顶点,
// 便于日后扩展非标准配件 (车轮、摩天轮支架等)。
// =============================================================

#include <map>
#include <string>
#include <vector>

#include "magtile/core/types.hpp"
#include "magtile/core/vec3.hpp"

namespace magtile::core {

/// 一种磁力片形状的几何与磁力属性。
struct TileShape {
    TileType type = TileType::Square;
    std::string name_zh;                ///< 中文名, 如 "正方形"
    std::string name_en;                ///< 英文名
    std::string description_zh;         ///< 中文说明
    std::vector<Vec2> vertices;         ///< 本地 XY 平面内的顶点 (逆时针, 凸多边形)
    std::vector<int> magnet_edge_indices;  ///< 带磁条的边索引 (边 i 连接顶点 i 与 i+1)

    [[nodiscard]] std::size_t edgeCount() const noexcept { return vertices.size(); }
    [[nodiscard]] bool isMagnetEdge(int edge_index) const noexcept;
    /// 多边形面积 (用于质心/重量估算, 认为各形状面密度一致)
    [[nodiscard]] double area() const noexcept;
};

/// 全部可用形状的目录。
class TileCatalog {
public:
    void addShape(TileShape shape);

    [[nodiscard]] const TileShape* find(TileType type) const noexcept;
    /// 与 find 相同, 但形状缺失时抛出 std::out_of_range (加载模型时形状必须存在)。
    [[nodiscard]] const TileShape& get(TileType type) const;

    [[nodiscard]] std::size_t size() const noexcept { return shapes_.size(); }
    [[nodiscard]] const std::map<TileType, TileShape>& shapes() const noexcept { return shapes_; }

private:
    std::map<TileType, TileShape> shapes_;
};

}  // namespace magtile::core
