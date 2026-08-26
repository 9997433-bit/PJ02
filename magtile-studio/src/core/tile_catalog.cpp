#include "magtile/core/tile_catalog.hpp"

#include <algorithm>
#include <cmath>
#include <stdexcept>
#include <string>

namespace magtile::core {

bool TileShape::isMagnetEdge(int edge_index) const noexcept {
    return std::find(magnet_edge_indices.begin(), magnet_edge_indices.end(), edge_index) !=
           magnet_edge_indices.end();
}

double TileShape::area() const noexcept {
    // 鞋带公式
    double twice_area = 0.0;
    const std::size_t n = vertices.size();
    for (std::size_t i = 0; i < n; ++i) {
        const Vec2& a = vertices[i];
        const Vec2& b = vertices[(i + 1) % n];
        twice_area += a.cross(b);
    }
    return std::abs(twice_area) * 0.5;
}

void TileCatalog::addShape(TileShape shape) {
    shapes_[shape.type] = std::move(shape);
}

const TileShape* TileCatalog::find(TileType type) const noexcept {
    const auto it = shapes_.find(type);
    return it != shapes_.end() ? &it->second : nullptr;
}

const TileShape& TileCatalog::get(TileType type) const {
    const TileShape* shape = find(type);
    if (shape == nullptr) {
        throw std::out_of_range("形状目录中缺少形状: " + std::string(toString(type)));
    }
    return *shape;
}

bool isCoreTileFallback(TileType type) noexcept {
    switch (type) {
        case TileType::Square:
        case TileType::LargeSquare:
        case TileType::WindowSquare:
        case TileType::DoorFrame:
        case TileType::EquilateralTriangle:
        case TileType::RightTriangle:
        case TileType::IsoscelesTriangle:
        case TileType::Rectangle:
        case TileType::WheelBase:
            return true;
        case TileType::Rhombus:
        case TileType::Trapezoid:
        case TileType::Hexagon:
        case TileType::Sector:
            return false;
    }
    return false;
}

bool isCoreTile(const TileCatalog& catalog, TileType type) noexcept {
    if (const TileShape* shape = catalog.find(type)) {
        return shape->tier == "core";
    }
    return isCoreTileFallback(type);
}

}  // namespace magtile::core
