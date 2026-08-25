#include "magtile/core/types.hpp"

#include <array>
#include <utility>

namespace magtile::core {
namespace {

struct TileTypeInfo {
    TileType type;
    std::string_view key;      // JSON 中使用的稳定标识
    std::string_view name_zh;
};

constexpr std::array<TileTypeInfo, kTileTypeCount> kTileTypes{{
    {TileType::Square, "square", "正方形"},
    {TileType::EquilateralTriangle, "equilateral_triangle", "等边三角形"},
    {TileType::RightTriangle, "right_triangle", "直角三角形"},
    {TileType::IsoscelesTriangle, "isosceles_triangle", "等腰三角形"},
    {TileType::Rectangle, "rectangle", "长方形"},
    {TileType::Rhombus, "rhombus", "菱形"},
    {TileType::Trapezoid, "trapezoid", "梯形"},
    {TileType::Hexagon, "hexagon", "六边形"},
    {TileType::Sector, "sector", "扇形"},
}};

struct TileColorInfo {
    TileColor color;
    std::string_view key;
    std::string_view name_zh;
};

constexpr std::array<TileColorInfo, 10> kTileColors{{
    {TileColor::Red, "red", "红色"},
    {TileColor::Orange, "orange", "橙色"},
    {TileColor::Yellow, "yellow", "黄色"},
    {TileColor::Green, "green", "绿色"},
    {TileColor::Cyan, "cyan", "青色"},
    {TileColor::Blue, "blue", "蓝色"},
    {TileColor::Purple, "purple", "紫色"},
    {TileColor::Pink, "pink", "粉色"},
    {TileColor::Clear, "clear", "透明"},
    {TileColor::Gray, "gray", "灰色"},
}};

}  // namespace

std::string_view toString(TileType type) noexcept {
    for (const auto& info : kTileTypes) {
        if (info.type == type) return info.key;
    }
    return "unknown";
}

std::string_view displayNameZh(TileType type) noexcept {
    for (const auto& info : kTileTypes) {
        if (info.type == type) return info.name_zh;
    }
    return "未知形状";
}

std::optional<TileType> tileTypeFromString(std::string_view name) noexcept {
    for (const auto& info : kTileTypes) {
        if (info.key == name) return info.type;
    }
    return std::nullopt;
}

std::string_view toString(TileColor color) noexcept {
    for (const auto& info : kTileColors) {
        if (info.color == color) return info.key;
    }
    return "unknown";
}

std::string_view displayNameZh(TileColor color) noexcept {
    for (const auto& info : kTileColors) {
        if (info.color == color) return info.name_zh;
    }
    return "未知颜色";
}

std::optional<TileColor> tileColorFromString(std::string_view name) noexcept {
    for (const auto& info : kTileColors) {
        if (info.key == name) return info.color;
    }
    return std::nullopt;
}

}  // namespace magtile::core
