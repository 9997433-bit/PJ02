#pragma once

// =============================================================
// MagTile Studio - 磁力片基础类型定义
// =============================================================

#include <optional>
#include <string_view>

namespace magtile::core {

/// 标准磁力片形状 (与市售主流磁力片套装一致)。
/// 序列化一律使用 toString 的稳定字符串标识, 枚举序号只决定展示顺序。
enum class TileType {
    Square,               ///< 正方形 (边长 1)
    LargeSquare,          ///< 大正方形 (边长 2)
    WindowSquare,         ///< 窗格方 (外框同正方形, 面内窗格造型)
    DoorFrame,            ///< 门框方 (外框同正方形, 中心镂空作门洞)
    EquilateralTriangle,  ///< 等边三角形 (边长 1)
    RightTriangle,        ///< 直角三角形 (两直角边长 1, 等腰直角)
    IsoscelesTriangle,    ///< 等腰三角形 (底 1, 高 1)
    Rectangle,            ///< 长方形 (2 x 1)
    WheelBase,            ///< 车轮底座 (外框同长方形 2 x 1, 底面带滚动车轮)
    Rhombus,              ///< 菱形 (边长 1, 锐角 60 度)
    Trapezoid,            ///< 等腰梯形 (下底 2, 上底 1, 腰 1)
    Hexagon,              ///< 正六边形 (边长 1)
    Sector,               ///< 扇形 (四分之一圆, 半径 1, 弧边无磁力)
};

inline constexpr int kTileTypeCount = 13;

/// 磁力片常见颜色 (半透明彩色 ABS)
enum class TileColor {
    Red,     ///< 红
    Orange,  ///< 橙
    Yellow,  ///< 黄
    Green,   ///< 绿
    Cyan,    ///< 青
    Blue,    ///< 蓝
    Purple,  ///< 紫
    Pink,    ///< 粉
    Clear,   ///< 透明
    Gray,    ///< 灰
};

[[nodiscard]] std::string_view toString(TileType type) noexcept;
[[nodiscard]] std::string_view displayNameZh(TileType type) noexcept;
[[nodiscard]] std::optional<TileType> tileTypeFromString(std::string_view name) noexcept;

[[nodiscard]] std::string_view toString(TileColor color) noexcept;
[[nodiscard]] std::string_view displayNameZh(TileColor color) noexcept;
[[nodiscard]] std::optional<TileColor> tileColorFromString(std::string_view name) noexcept;

}  // namespace magtile::core
