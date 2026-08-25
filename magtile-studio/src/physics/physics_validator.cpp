#include "magtile/physics/physics_validator.hpp"

#include <algorithm>
#include <queue>
#include <sstream>

#include "magtile/physics/geometry.hpp"

namespace magtile::physics {
namespace {

using core::TileInstance;

std::string withContext(const std::string& context, const std::string& message) {
    return context.empty() ? message : context + ": " + message;
}

/// 两条磁力边是否贴合: 端点两两重合 (允许正反两种对应)。
bool edgesSnap(const std::pair<Vec3, Vec3>& ea, const std::pair<Vec3, Vec3>& eb,
               double tolerance) {
    const bool forward = core::distance(ea.first, eb.first) <= tolerance &&
                         core::distance(ea.second, eb.second) <= tolerance;
    const bool reverse = core::distance(ea.first, eb.second) <= tolerance &&
                         core::distance(ea.second, eb.first) <= tolerance;
    return forward || reverse;
}

}  // namespace

std::size_t ValidationReport::errorCount() const noexcept {
    return static_cast<std::size_t>(std::count_if(
        issues.begin(), issues.end(),
        [](const ValidationIssue& i) { return i.severity == IssueSeverity::Error; }));
}

std::size_t ValidationReport::warningCount() const noexcept {
    return issues.size() - errorCount();
}

void ValidationReport::merge(const ValidationReport& other) {
    issues.insert(issues.end(), other.issues.begin(), other.issues.end());
}

PhysicsValidator::PhysicsValidator(const core::TileCatalog& catalog, PhysicsConfig config)
    : catalog_(&catalog), config_(config) {}

std::vector<MagnetConnection> PhysicsValidator::findConnections(
    const std::vector<const TileInstance*>& tiles) const {
    std::vector<TransformedTile> transformed;
    transformed.reserve(tiles.size());
    for (const TileInstance* tile : tiles) {
        transformed.push_back(transformTile(*tile, catalog_->get(tile->type)));
    }

    std::vector<MagnetConnection> connections;
    for (std::size_t i = 0; i < transformed.size(); ++i) {
        for (std::size_t j = i + 1; j < transformed.size(); ++j) {
            for (std::size_t ei = 0; ei < transformed[i].edgeCount(); ++ei) {
                if (!transformed[i].isMagnetEdge(ei)) continue;
                for (std::size_t ej = 0; ej < transformed[j].edgeCount(); ++ej) {
                    if (!transformed[j].isMagnetEdge(ej)) continue;
                    if (edgesSnap(transformed[i].edge(ei), transformed[j].edge(ej),
                                  config_.connect_tolerance)) {
                        connections.push_back({i, j, ei, ej});
                    }
                }
            }
        }
    }
    return connections;
}

ValidationReport PhysicsValidator::validateAssembly(
    const std::vector<const TileInstance*>& tiles, const std::string& context) const {
    ValidationReport report;
    if (tiles.empty()) return report;

    // ---- 预计算世界坐标几何 ---------------------------------------
    std::vector<TransformedTile> transformed;
    transformed.reserve(tiles.size());
    for (const TileInstance* tile : tiles) {
        transformed.push_back(transformTile(*tile, catalog_->get(tile->type)));
    }

    // ---- R3 无重叠: 共面片做分离轴检测 ----------------------------
    for (std::size_t i = 0; i < transformed.size(); ++i) {
        for (std::size_t j = i + 1; j < transformed.size(); ++j) {
            if (!areCoplanar(transformed[i], transformed[j], config_.coplanar_tolerance)) {
                continue;
            }
            if (coplanarPolygonsOverlap(transformed[i], transformed[j],
                                        config_.overlap_tolerance)) {
                report.issues.push_back(
                    {IssueSeverity::Error, "tile_overlap",
                     withContext(context, "磁力片 " + tiles[i]->id + " 与 " + tiles[j]->id +
                                              " 在同一平面上互相重叠"),
                     {tiles[i]->id, tiles[j]->id}});
            }
        }
    }

    // ---- R2 磁力连接图 --------------------------------------------
    const std::vector<MagnetConnection> connections = findConnections(tiles);
    std::vector<std::vector<std::size_t>> adjacency(tiles.size());
    for (const MagnetConnection& c : connections) {
        adjacency[c.tile_a].push_back(c.tile_b);
        adjacency[c.tile_b].push_back(c.tile_a);
    }

    if (tiles.size() > 1) {
        for (std::size_t i = 0; i < tiles.size(); ++i) {
            if (adjacency[i].empty()) {
                report.issues.push_back(
                    {IssueSeverity::Error, "isolated_tile",
                     withContext(context, "磁力片 " + tiles[i]->id +
                                              " 没有与任何其他磁力片形成磁力连接"),
                     {tiles[i]->id}});
            }
        }
    }

    // ---- R1 接地支撑: 从接地片沿磁力连接做 BFS --------------------
    std::vector<bool> supported(tiles.size(), false);
    std::queue<std::size_t> frontier;
    for (std::size_t i = 0; i < transformed.size(); ++i) {
        if (transformed[i].min_z <= config_.ground_tolerance) {
            supported[i] = true;
            frontier.push(i);
        }
    }
    while (!frontier.empty()) {
        const std::size_t current = frontier.front();
        frontier.pop();
        for (const std::size_t next : adjacency[current]) {
            if (!supported[next]) {
                supported[next] = true;
                frontier.push(next);
            }
        }
    }
    for (std::size_t i = 0; i < tiles.size(); ++i) {
        if (!supported[i]) {
            report.issues.push_back(
                {IssueSeverity::Error, "floating_tile",
                 withContext(context, "磁力片 " + tiles[i]->id +
                                          " 悬空: 不存在通往地面的支撑路径"),
                 {tiles[i]->id}});
        }
    }

    // ---- 连通性: 多个各自接地的孤岛不算错误, 但提示内容制作者 ------
    if (!tiles.empty()) {
        std::vector<bool> visited(tiles.size(), false);
        std::queue<std::size_t> bfs;
        bfs.push(0);
        visited[0] = true;
        std::size_t reached = 1;
        while (!bfs.empty()) {
            const std::size_t current = bfs.front();
            bfs.pop();
            for (const std::size_t next : adjacency[current]) {
                if (!visited[next]) {
                    visited[next] = true;
                    ++reached;
                    bfs.push(next);
                }
            }
        }
        if (reached != tiles.size()) {
            report.issues.push_back({IssueSeverity::Warning, "disconnected_assembly",
                                     withContext(context,
                                                 "模型由多个互不相连的部分组成, "
                                                 "建议在教程中明确分组说明"),
                                     {}});
        }
    }

    // ---- R4 重心稳定 (基础版): 重心水平投影须落在接地凸包内 --------
    double total_area = 0.0;
    Vec3 weighted_com{};
    std::vector<Vec2> ground_contacts;
    for (const TransformedTile& tile : transformed) {
        weighted_com += tile.centroid * tile.area;
        total_area += tile.area;
        for (const Vec3& v : tile.vertices) {
            if (v.z <= config_.ground_tolerance) {
                ground_contacts.push_back(v.xy());
            }
        }
    }

    if (ground_contacts.empty()) {
        report.issues.push_back({IssueSeverity::Error, "no_ground_contact",
                                 withContext(context, "模型没有任何接触地面的磁力片"),
                                 {}});
    } else if (total_area > 0.0) {
        const Vec3 com = weighted_com * (1.0 / total_area);
        const std::vector<Vec2> hull = convexHull2D(std::move(ground_contacts));
        const double dist = signedDistanceToHull(com.xy(), hull);
        if (dist > config_.stability_margin) {
            std::ostringstream oss;
            oss << "整体重心 (" << com.x << ", " << com.y << ") 的水平投影超出接地区域 "
                << dist << " 个单位, 模型可能倾倒";
            report.issues.push_back({IssueSeverity::Error, "unstable_center_of_mass",
                                     withContext(context, oss.str()),
                                     {}});
        }
    }

    return report;
}

ValidationReport PhysicsValidator::validateModel(const core::ModelDefinition& model) const {
    ValidationReport report;

    // 最终成品
    std::vector<const TileInstance*> all_tiles;
    all_tiles.reserve(model.final_assembly.size());
    for (const TileInstance& tile : model.final_assembly) {
        all_tiles.push_back(&tile);
    }
    report.merge(validateAssembly(all_tiles, "最终成品"));

    // 每个步骤完成后的中间状态: 保证教程任意时刻都物理成立
    for (std::size_t s = 1; s <= model.steps.size(); ++s) {
        const auto partial = model.tilesUpToStep(static_cast<int>(s));
        std::ostringstream context;
        context << "第 " << model.steps[s - 1].step_number << " 步完成后";
        report.merge(validateAssembly(partial, context.str()));
    }
    return report;
}

}  // namespace magtile::physics
