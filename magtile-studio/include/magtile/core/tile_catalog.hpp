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
    std::string tier = "core";          ///< 套装分层: core (核心 9 片型) / expansion (扩展)
    bool hollow = false;                ///< 中心镂空 (门框方); 仅语义标记 (教程/BOM),
                                        ///< 物理校验一律使用外框多边形
    std::string variant;                ///< 外观变体 (如 "window" / "door" / "wheeled"), 空 = 标准实心
    bool wheeled = false;               ///< 底面带滚动车轮 (车轮底座); 仅语义标记 (教程文案
                                        ///< 与车辆模型用), 拼接与物理校验按外框多边形处理
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

// ---- 核心 9 片型 (core-9) 判定 --------------------------------------
// 套装分层的事实来源是 data/tile_catalog.json 的 tier 字段
// (docs/TILE_CATALOG.md §3); 下面两个函数是全部 UI 外壳 (CLI / GL /
// Qt) 共用的判定入口, 保证 "只用核心片" 筛选与 "需要扩展装" 角标
// 在各端使用同一套口径。

/// 兜底白名单: 目录不可用 (加载失败 / 形状缺失) 时的核心 9 片型
/// 判定, 必须与 data/tile_catalog.json 的 tier=core 标注保持一致
/// (docs/TILE_CATALOG.md): square / large_square / window_square /
/// door_frame / equilateral_triangle / right_triangle /
/// isosceles_triangle / rectangle / wheel_base。
[[nodiscard]] bool isCoreTileFallback(TileType type) noexcept;

/// 片型是否属于核心 9 片 (基础套装): 目录中的 tier 标注优先,
/// 形状缺失时退回 isCoreTileFallback 的代码内白名单。
[[nodiscard]] bool isCoreTile(const TileCatalog& catalog, TileType type) noexcept;

}  // namespace magtile::core
