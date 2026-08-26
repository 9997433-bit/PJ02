#pragma once

// =============================================================
// MagTile Studio - 磁力片实例
// =============================================================

#include <string>

#include "magtile/core/types.hpp"
#include "magtile/core/vec3.hpp"

namespace magtile::core {

/// 模型中一片具体摆放的磁力片。
///
/// 位置/旋转约定:
/// - 形状的本地顶点定义在 XY 平面内 (z = 0), 见 TileCatalog;
/// - position 为形状本地原点在世界坐标中的位置;
/// - rotation_deg 为欧拉角 (度), 施加顺序 R = Rz * Ry * Rx (见 eulerZYX);
/// - 平铺: rotation = (0, 0, yaw); 竖立: rotation = (90, 0, yaw)。
struct TileInstance {
    std::string id;              ///< 模型内唯一标识, 例如 "wall_s_02"
    TileType type = TileType::Square;
    Vec3 position;               ///< 世界坐标 (单位 = 正方形边长)
    Vec3 rotation_deg;           ///< 欧拉角 (度)
    TileColor color = TileColor::Blue;
};

}  // namespace magtile::core
