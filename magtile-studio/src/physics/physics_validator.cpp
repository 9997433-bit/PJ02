#include "magtile/physics/physics_validator.hpp"

#include <algorithm>
#include <cmath>
#include <iomanip>
#include <numbers>
#include <queue>
#include <random>
#include <set>
#include <sstream>

#include "magtile/physics/geometry.hpp"

namespace magtile::physics {
namespace {

using core::TileInstance;

std::string withContext(const std::string& context, const std::string& message) {
    return context.empty() ? message : context + ": " + message;
}

/// 点到线段的最短距离。
double pointToSegmentDistance(const Vec3& p, const Vec3& a, const Vec3& b) {
    const Vec3 ab = b - a;
    const double len_sq = ab.dot(ab);
    if (len_sq < 1e-12) return core::distance(p, a);
    const double t = std::clamp((p - a).dot(ab) / len_sq, 0.0, 1.0);
    return core::distance(p, a + ab * t);
}

/// 两条磁力边是否贴合 (R2 判定, docs/PHYSICS_RULES.md):
///   - 等长整边: 端点两两重合 (正反两种对应均可) —— 传统判定;
///   - 长短边搭配 (如大正方形边长 2 对小正方形边长 1, 或长方形长边对
///     小方边): 短边两个端点都落在长边线段上 (容差内) 即贴合 —— 短边
///     全程磁条对磁条接触, 与整边贴合同样稳固。由此一条长 2 的磁力边
///     可以同时吸住两片共线的边长 1 磁力片 (记为两条独立连接)。
///   - 错位半搭 (短边任一端点悬出长边之外) 仍判为未连接: 悬出部分
///     没有磁条对齐, 实物上是不稳定的。
/// 数学上以 "短边被长边线段完整包含" 统一表达: 等长时即退化为端点
/// 两两重合, 与旧判定完全一致。
bool edgesSnap(const std::pair<Vec3, Vec3>& ea, const std::pair<Vec3, Vec3>& eb,
               double tolerance) {
    const double len_a = core::distance(ea.first, ea.second);
    const double len_b = core::distance(eb.first, eb.second);
    const auto& shorter = len_a <= len_b ? ea : eb;
    const auto& longer = len_a <= len_b ? eb : ea;
    return pointToSegmentDistance(shorter.first, longer.first, longer.second) <= tolerance &&
           pointToSegmentDistance(shorter.second, longer.first, longer.second) <= tolerance;
}

/// 一条磁力连接的实际接触段: 两边中较短的那条 (containment 判定下
/// 短边即完整的磁条接触区间)。R5/R6 的铰链承重/力矩预算按接触段
/// 长度计算, 长短边搭配时不能按长边长度虚增预算。
std::pair<Vec3, Vec3> contactSegment(const std::pair<Vec3, Vec3>& ea,
                                     const std::pair<Vec3, Vec3>& eb) {
    const double len_a = core::distance(ea.first, ea.second);
    const double len_b = core::distance(eb.first, eb.second);
    return len_a <= len_b ? ea : eb;
}

/// 两片磁力片之间是否存在任意一对贴合的磁力边。
bool tilesSnap(const TransformedTile& a, const TransformedTile& b, double tolerance) {
    for (std::size_t ei = 0; ei < a.edgeCount(); ++ei) {
        if (!a.isMagnetEdge(ei)) continue;
        for (std::size_t ej = 0; ej < b.edgeCount(); ++ej) {
            if (!b.isMagnetEdge(ej)) continue;
            if (edgesSnap(a.edge(ei), b.edge(ej), tolerance)) return true;
        }
    }
    return false;
}

// ------------------------------------------------------------------
// R5/R6 静力学分析工具: 铰链线 (共线磁力边组)
//
// 磁力片的边连接是 "铰链" 而非刚性节点: 磁条只提供有限的拉脱力与
// 抗弯矩。位于同一条空间直线上的若干磁力连接共同构成一条铰链线,
// 假想剪断它后失去接地路径的子结构, 其重量与力矩全部压在这条线上。
// ------------------------------------------------------------------

/// 一条铰链线: 直线上一点 + 单位方向。
struct HingeLine {
    Vec3 point;
    Vec3 dir;
};

HingeLine makeHingeLine(const std::pair<Vec3, Vec3>& edge) {
    return {edge.first, (edge.second - edge.first).normalized()};
}

/// 两条铰链线是否共线 (方向平行且点在同一条直线上)。
bool sameLine(const HingeLine& a, const HingeLine& b, double tolerance) {
    if (std::abs(a.dir.dot(b.dir)) < 1.0 - 1e-6) return false;  // 方向不平行
    const Vec3 offset = b.point - a.point;
    const Vec3 perpendicular = offset - a.dir * offset.dot(a.dir);
    return perpendicular.length() <= tolerance;
}

/// 格式化克数 (保留 1 位小数)。
std::string formatGrams(double grams) {
    std::ostringstream oss;
    oss << std::fixed << std::setprecision(1) << grams;
    return oss.str();
}

// ------------------------------------------------------------------
// R7 装配可达性工具: 射线检测
// ------------------------------------------------------------------

/// 射线 (origin + t * dir) 是否命中磁力片所在的凸多边形。
/// 用于判断新片放置点是否被已完成结构包围。
bool rayHitsTile(const Vec3& origin, const Vec3& dir, const TransformedTile& tile) {
    const double denom = dir.dot(tile.normal);
    if (std::abs(denom) < 1e-9) return false;  // 射线与片平面平行
    const double t = (tile.vertices[0] - origin).dot(tile.normal) / denom;
    if (t < 0.05) return false;  // 忽略贴脸命中 (放置点附近的相邻片不算遮挡)
    const Vec3 hit = origin + dir * t;

    // 命中点是否在凸多边形内 (顶点绕法向逆时针; 容差取负让边界命中也算遮挡)
    const std::size_t n = tile.vertices.size();
    for (std::size_t i = 0; i < n; ++i) {
        const Vec3& a = tile.vertices[i];
        const Vec3& b = tile.vertices[(i + 1) % n];
        if ((b - a).cross(hit - a).dot(tile.normal) < -0.02) return false;
    }
    return true;
}

/// 新片是否被已放置结构完全包围 (从任何外部方向都伸不进手)。
/// 从放置点 (质心) 向上、四周与斜上共 13 个方向发射射线, 全部被
/// 已放置磁力片挡住即判定为封闭腔体内部; 不检测正下方 (桌面本来就挡)。
bool isEnclosed(const Vec3& origin, const std::vector<TransformedTile>& placed) {
    static const Vec3 kDirections[] = {
        {0, 0, 1},                                            // 正上
        {1, 0, 0},   {-1, 0, 0},  {0, 1, 0},   {0, -1, 0},    // 水平四向
        {1, 1, 0},   {1, -1, 0},  {-1, 1, 0},  {-1, -1, 0},   // 水平对角
        {1, 0, 1},   {-1, 0, 1},  {0, 1, 1},   {0, -1, 1},    // 斜上四向
    };
    for (const Vec3& raw : kDirections) {
        const Vec3 dir = raw.normalized();
        bool blocked = false;
        for (const TransformedTile& tile : placed) {
            if (rayHitsTile(origin, dir, tile)) {
                blocked = true;
                break;
            }
        }
        if (!blocked) return false;  // 存在一个可以伸手进入的方向
    }
    return true;
}

}  // namespace

PhysicsConfig PhysicsConfig::strictConsumer() {
    PhysicsConfig config;
    config.hanging_capacity_per_edge = 120.0;
    config.knock_safety_factor = 0.7;
    return config;
}

std::optional<PhysicsConfig> configForProfile(std::string_view name) {
    if (name.empty() || name == "default" || name == "standard") return PhysicsConfig{};
    if (name == "strict" || name == "strict_consumer") return PhysicsConfig::strictConsumer();
    return std::nullopt;
}

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
    double max_z = 0.0;
    for (const TileInstance* tile : tiles) {
        transformed.push_back(transformTile(*tile, catalog_->get(tile->type)));
        for (const Vec3& v : transformed.back().vertices) {
            max_z = std::max(max_z, v.z);
        }
    }

    // ---- R1 前置: 禁止穿入地面 (below_ground_tile) -----------------
    // 桌面是刚体: 任何顶点低于地面 (z < -ground_tolerance) 的磁力片
    // 实物上根本摆不出来。历史版本把 z <= ground_tolerance 一律视为
    // "接地", 穿地片反而被当作稳定接地片放行 (2026-08 负例回归加强时
    // 发现该漏洞, 由负例夹具 below_ground_tile.json 锁定回归)。
    for (std::size_t i = 0; i < transformed.size(); ++i) {
        if (transformed[i].min_z < -config_.ground_tolerance) {
            std::ostringstream oss;
            oss << "磁力片 " << tiles[i]->id << " 穿入地面: 最低顶点 z = "
                << transformed[i].min_z << ", 桌面是刚体, 实物无法这样放置";
            report.issues.push_back({IssueSeverity::Error, "below_ground_tile",
                                     withContext(context, oss.str()),
                                     {tiles[i]->id}});
        }
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

    // ---- R2 磁力连接图 (带连接索引, 供 R5/R6/R8 的切割分析复用) ----
    const std::vector<MagnetConnection> connections = findConnections(tiles);
    // adjacency[i] = { (相邻片下标, 连接下标), ... }
    std::vector<std::vector<std::pair<std::size_t, std::size_t>>> adjacency(tiles.size());
    for (std::size_t c = 0; c < connections.size(); ++c) {
        adjacency[connections[c].tile_a].push_back({connections[c].tile_b, c});
        adjacency[connections[c].tile_b].push_back({connections[c].tile_a, c});
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

    // 从接地片沿磁力连接做 BFS, 可跳过指定的被 "剪断" 连接集合;
    // R1 直接使用, R5/R6/R8 用它做假想切割分析。
    const auto reachableFromGround =
        [&](const std::vector<char>& removed_connections) -> std::vector<char> {
        std::vector<char> reachable(tiles.size(), 0);
        std::queue<std::size_t> frontier;
        for (std::size_t i = 0; i < transformed.size(); ++i) {
            if (transformed[i].min_z <= config_.ground_tolerance) {
                reachable[i] = 1;
                frontier.push(i);
            }
        }
        while (!frontier.empty()) {
            const std::size_t current = frontier.front();
            frontier.pop();
            for (const auto& [next, conn] : adjacency[current]) {
                if (!removed_connections.empty() && removed_connections[conn]) continue;
                if (!reachable[next]) {
                    reachable[next] = 1;
                    frontier.push(next);
                }
            }
        }
        return reachable;
    };

    // ---- R1 接地支撑 ----------------------------------------------
    const std::vector<char> supported = reachableFromGround({});
    bool has_floating = false;
    for (std::size_t i = 0; i < tiles.size(); ++i) {
        if (!supported[i]) {
            has_floating = true;
            report.issues.push_back(
                {IssueSeverity::Error, "floating_tile",
                 withContext(context, "磁力片 " + tiles[i]->id +
                                          " 悬空: 不存在通往地面的支撑路径"),
                 {tiles[i]->id}});
        }
    }

    // ---- 连通性: 统计连通分量 (多个各自接地的孤岛提示内容制作者) ----
    std::size_t num_components = 0;
    {
        std::vector<char> visited(tiles.size(), 0);
        for (std::size_t start = 0; start < tiles.size(); ++start) {
            if (visited[start]) continue;
            ++num_components;
            std::queue<std::size_t> bfs;
            bfs.push(start);
            visited[start] = 1;
            while (!bfs.empty()) {
                const std::size_t current = bfs.front();
                bfs.pop();
                for (const auto& [next, conn] : adjacency[current]) {
                    (void)conn;
                    if (!visited[next]) {
                        visited[next] = 1;
                        bfs.push(next);
                    }
                }
            }
        }
        if (num_components > 1) {
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
    const bool has_ground_contact = !ground_contacts.empty();

    if (!has_ground_contact) {
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

    // ================================================================
    // R5/R6 铰链切割静力分析
    //
    // 磁吸边连接在实物上是 "铰链": 抗压强 (下方有支撑时稳), 抗拉与
    // 抗弯都很弱。R1~R4 只回答 "结构是否连通且不倾倒", 却把每条磁
    // 力连接当成无限强 —— 这正是 "校验通过但实搭时掉下来" 的根源。
    //
    // 分析方法: 把所有共线的磁力连接归并为一条 "铰链线", 逐条假想
    // 剪断; 剪断后与地面失联的子结构, 其全部重量必须经由这条铰链
    // 传递:
    //   - 子结构重心低于铰链线 => 悬挂 (磁条受拉), 校验 R5 承重预算;
    //   - 重力绕铰链轴产生的力矩 => 悬臂 (磁条受弯), 校验 R6 力矩预算。
    // 被三角斜撑 / 环状结构加固的部分剪断单条铰链后仍有其他支撑路
    // 径, 自然不会进入分析 —— 桁架的加固效果由图论连通性隐式表达。
    //
    // 前置条件: R1 通过且存在接地片 (悬空结构做静力分析没有意义)。
    // ================================================================
    if (!has_floating && has_ground_contact && !connections.empty()) {
        // 每条连接的铰链线与磁力边长度: 取两侧边中较短者 (= 实际磁条
        // 接触段)。等长整边贴合时两侧在容差内重合, 与取 A 侧边等价;
        // 长短边搭配 (大正方形边吸小方边等) 时按接触段计, 承重/力矩
        // 预算不因长边名义长度而虚增。
        std::vector<HingeLine> lines;
        std::vector<double> edge_lengths;
        std::vector<std::pair<Vec3, Vec3>> contact_edges;
        lines.reserve(connections.size());
        edge_lengths.reserve(connections.size());
        contact_edges.reserve(connections.size());
        for (const MagnetConnection& c : connections) {
            const auto edge = contactSegment(transformed[c.tile_a].edge(c.edge_a),
                                             transformed[c.tile_b].edge(c.edge_b));
            lines.push_back(makeHingeLine(edge));
            edge_lengths.push_back((edge.second - edge.first).length());
            contact_edges.push_back(edge);
        }

        std::set<std::vector<std::size_t>> analyzed_cuts;  // 共线组去重
        for (std::size_t seed = 0; seed < connections.size(); ++seed) {
            // 与 seed 共线的全部连接构成一条铰链线 (一次性剪断)
            std::vector<std::size_t> cut;
            for (std::size_t j = 0; j < connections.size(); ++j) {
                if (sameLine(lines[seed], lines[j], config_.collinear_tolerance)) {
                    cut.push_back(j);
                }
            }
            if (!analyzed_cuts.insert(cut).second) continue;

            std::vector<char> removed(connections.size(), 0);
            for (const std::size_t j : cut) removed[j] = 1;
            const std::vector<char> still_grounded = reachableFromGround(removed);

            // 剪断后失联的磁力片, 按剩余连接划分为独立的悬挂/悬臂子结构
            std::vector<char> assigned(tiles.size(), 0);
            for (std::size_t i = 0; i < tiles.size(); ++i) {
                assigned[i] = still_grounded[i];
            }
            for (std::size_t start = 0; start < tiles.size(); ++start) {
                if (assigned[start]) continue;

                // 收集子结构 K
                std::vector<std::size_t> component;
                std::vector<char> in_component(tiles.size(), 0);
                std::queue<std::size_t> bfs;
                bfs.push(start);
                assigned[start] = 1;
                in_component[start] = 1;
                while (!bfs.empty()) {
                    const std::size_t current = bfs.front();
                    bfs.pop();
                    component.push_back(current);
                    for (const auto& [next, conn] : adjacency[current]) {
                        if (removed[conn] || assigned[next]) continue;
                        assigned[next] = 1;
                        in_component[next] = 1;
                        bfs.push(next);
                    }
                }

                // 跨越铰链线的连接 (子结构真正挂在哪些磁力边上)
                double hinge_length = 0.0;
                double hinge_z_sum = 0.0;
                int crossing_count = 0;
                for (const std::size_t j : cut) {
                    const MagnetConnection& c = connections[j];
                    if (in_component[c.tile_a] == in_component[c.tile_b]) continue;
                    ++crossing_count;
                    hinge_length += edge_lengths[j];
                    const auto& edge = contact_edges[j];
                    hinge_z_sum += (edge.first.z + edge.second.z) * 0.5;
                }
                if (crossing_count == 0) continue;  // 与本铰链线无直接联系
                const double hinge_z = hinge_z_sum / crossing_count;

                // 子结构质量与重心 (质量 = 面积 x 面密度)
                double component_mass = 0.0;
                Vec3 component_weighted{};
                for (const std::size_t idx : component) {
                    const double mass = transformed[idx].area * config_.tile_mass_per_area;
                    component_mass += mass;
                    component_weighted += transformed[idx].centroid * mass;
                }
                const Vec3 component_com = component_weighted * (1.0 / component_mass);

                std::vector<std::string> component_ids;
                component_ids.reserve(component.size());
                for (const std::size_t idx : component) {
                    component_ids.push_back(tiles[idx]->id);
                }

                // ---- R5 悬挂承重: 重心低于铰链线 => 磁条受拉 ------
                if (component_com.z < hinge_z - config_.hanging_z_tolerance) {
                    const double capacity = config_.hanging_capacity_per_edge * hinge_length *
                                            config_.knock_safety_factor;
                    if (component_mass > capacity + 1e-9) {
                        std::ostringstream oss;
                        // 安全系数随档位变化 (default 0.8 / strict 0.7),
                        // 文案必须跟随实际生效的参数, 不得硬编码。
                        oss << "悬挂链超重: " << component.size() << " 片约 "
                            << formatGrams(component_mass) << "g 全部悬挂在总长 "
                            << formatGrams(hinge_length) << " 的磁力边下方, 超过承重预算 "
                            << formatGrams(capacity) << "g (额定 "
                            << formatGrams(config_.hanging_capacity_per_edge)
                            << "g/单位边长 x "
                            << std::lround(config_.knock_safety_factor * 100.0)
                            << "% 抗碰撞裕量), 实搭时整串会脱落";
                        report.issues.push_back({IssueSeverity::Error, "hanging_chain_overload",
                                                 withContext(context, oss.str()),
                                                 component_ids});
                    } else if (static_cast<int>(component.size()) >
                               config_.max_hanging_tiles_per_edge * crossing_count) {
                        std::ostringstream oss;
                        oss << "悬挂链过长: " << component.size()
                            << " 片挂在 " << crossing_count
                            << " 条磁力边下方 (建议单边不超过 "
                            << config_.max_hanging_tiles_per_edge
                            << " 片), 铰链节点逐级累积晃动, 轻碰易整串脱落";
                        report.issues.push_back({IssueSeverity::Warning, "hanging_chain_long",
                                                 withContext(context, oss.str()),
                                                 component_ids});
                    }
                }

                // ---- R6 悬臂力矩: 重力绕铰链轴的力矩 => 磁条受弯 --
                // 力矩 = Σ mᵢ x ((质心ᵢ - 铰链点) x 重力方向) 在铰链轴上的分量。
                // 正上/正下方的子结构力矩为零 (纯压/纯拉), 水平外挑越远力矩越大。
                double torque = 0.0;
                for (const std::size_t idx : component) {
                    const double mass = transformed[idx].area * config_.tile_mass_per_area;
                    const Vec3 r = transformed[idx].centroid - lines[seed].point;
                    // r x g, g = (0,0,-1) => (-r.y, r.x, 0)
                    torque += mass * Vec3{-r.y, r.x, 0.0}.dot(lines[seed].dir);
                }
                torque = std::abs(torque);
                const double moment_capacity = config_.hinge_moment_capacity_per_edge *
                                               hinge_length * config_.knock_safety_factor;
                if (torque > moment_capacity + 1e-9) {
                    std::ostringstream oss;
                    oss << "悬臂力矩超限: " << component.size() << " 片外挑结构绕铰链线产生 "
                        << formatGrams(torque) << "g·单位 的重力力矩, 超过总长 "
                        << formatGrams(hinge_length) << " 磁力边的抗弯预算 "
                        << formatGrams(moment_capacity)
                        << "g·单位; 单边磁吸是铰链而非刚性节点, 请添加三角斜撑或在外挑远端增加支撑";
                    report.issues.push_back({IssueSeverity::Error, "cantilever_overload",
                                             withContext(context, oss.str()),
                                             component_ids});
                }
            }
        }
    }

    // ================================================================
    // R8 结构冗余 (高层结构, Warning 级)
    //
    // 结构越高, 碰撞与桌面震动的放大效应越强。仿真无法精确复现
    // "被小朋友撞一下", 因此只做拓扑级提示:
    //   1. 单点失效: 一条磁力连接独自撑起一大段结构 —— 掉一处塌一片;
    //   2. 无环拓扑: 连接图是纯树状 (没有任何环路/三角桁架), 每个
    //      节点都是自由铰链, 整体会像风铃一样晃。
    // ================================================================
    if (!has_floating && has_ground_contact && max_z >= config_.tall_structure_height &&
        tiles.size() > 1) {
        // 1. 单点失效: 逐条剪断单条连接, 统计失联片数
        for (std::size_t c = 0; c < connections.size(); ++c) {
            std::vector<char> removed(connections.size(), 0);
            removed[c] = 1;
            const std::vector<char> still_grounded = reachableFromGround(removed);
            std::size_t lost = 0;
            for (std::size_t i = 0; i < tiles.size(); ++i) {
                if (!still_grounded[i]) ++lost;
            }
            if (lost >= static_cast<std::size_t>(config_.spof_min_component_tiles)) {
                const std::string id_a = tiles[connections[c].tile_a]->id;
                const std::string id_b = tiles[connections[c].tile_b]->id;
                std::ostringstream oss;
                oss << "高层结构单点失效: " << id_a << " 与 " << id_b
                    << " 之间的单条磁力连接是 " << lost
                    << " 片子结构的唯一支撑路径, 碰撞时会整段脱落, "
                       "建议增加三角桁架或第二条连接路径";
                report.issues.push_back({IssueSeverity::Warning, "single_point_of_failure",
                                         withContext(context, oss.str()),
                                         {id_a, id_b}});
            }
        }

        // 2. 无环拓扑: 环路数 = E - (V - 连通分量数); 为零说明没有任何
        //    三角桁架 / 闭合环, 高层结构强烈建议至少一处环状加固。
        //    超过 unbraced_wall_max_height 的无环高墙升级为 Error:
        //    真实磁力片的高墙没有任何桁架时轻碰即整面倒塌, 不允许发布。
        const std::size_t cycles =
            connections.size() + num_components >= tiles.size()
                ? connections.size() + num_components - tiles.size()
                : 0;
        if (cycles == 0) {
            if (max_z >= config_.unbraced_wall_max_height) {
                std::ostringstream oss;
                oss << "无桁架高墙超限: 最高点 " << max_z << " 个单位已超过无加固结构上限 "
                    << config_.unbraced_wall_max_height
                    << ", 且磁力连接图是纯树状 (没有任何三角桁架或闭合环), "
                       "每个连接都是自由铰链, 实搭时轻碰即整面倒塌; "
                       "请增加三角斜撑、垂直翼墙或环状圈层加固";
                report.issues.push_back({IssueSeverity::Error, "unbraced_wall_too_tall",
                                         withContext(context, oss.str()),
                                         {}});
            } else {
                std::ostringstream oss;
                oss << "高层结构无环加固: 最高点 " << max_z
                    << " 个单位, 但磁力连接图是纯树状 (没有任何三角桁架或闭合环), "
                       "每个连接都是自由铰链, 整体抗晃动能力差, 建议增加三角形或环状加固";
                report.issues.push_back({IssueSeverity::Warning, "no_structural_redundancy",
                                         withContext(context, oss.str()),
                                         {}});
            }
        }
    }

    return report;
}

ValidationReport PhysicsValidator::validatePlacements(const core::ModelDefinition& model) const {
    ValidationReport report;

    // ================================================================
    // R7 装配可达性
    //
    // 静态规则 (R1~R6) 保证每个中间状态 "放好之后是稳的", 但没有回答
    // "这一片当时放得进去吗":
    //   a) 放下的那一刻必须有依托 —— 既不接地又吸不到任何已放置的片,
    //      松手即掉 (常见于步骤内 tiles_to_add 顺序写反);
    //   b) 放置点必须从外部可达 —— 已完成结构形成封闭腔体后, 手和
    //      磁力片都伸不进去 (常见于 "先封顶再补内部隔断" 的教程)。
    // 按教程步骤与步骤内列表顺序逐片模拟, 与真人搭建顺序完全一致。
    // ================================================================
    std::vector<TransformedTile> placed;
    placed.reserve(model.final_assembly.size());

    for (const core::BuildStep& step : model.steps) {
        std::ostringstream context;
        context << "第 " << step.step_number << " 步";

        for (const std::string& tile_id : step.tiles_to_add) {
            const TileInstance* tile = model.findTile(tile_id);
            if (tile == nullptr) continue;  // 引用错误由教程一致性检查负责报告

            TransformedTile geometry = transformTile(*tile, catalog_->get(tile->type));

            // ---- R7a 放置瞬间必须有依托 (接地或吸附) ---------------
            const bool grounded = geometry.min_z <= config_.ground_tolerance;
            bool attached = false;
            for (const TransformedTile& other : placed) {
                if (tilesSnap(geometry, other, config_.connect_tolerance)) {
                    attached = true;
                    break;
                }
            }
            if (!grounded && !attached) {
                report.issues.push_back(
                    {IssueSeverity::Error, "unplaceable_tile",
                     withContext(context.str(),
                                 "磁力片 " + tile->id +
                                     " 按教程顺序放下的那一刻既不接地、也吸不到任何已放置"
                                     "磁力片, 松手即掉; 请调整本步内 tiles_to_add 的先后"
                                     "顺序或拆分步骤"),
                     {tile->id}});
            } else if (!placed.empty() && isEnclosed(geometry.centroid, placed)) {
                // ---- R7b 放置点必须从外部伸手可达 ------------------
                report.issues.push_back(
                    {IssueSeverity::Error, "enclosed_placement",
                     withContext(context.str(),
                                 "磁力片 " + tile->id +
                                     " 的放置位置已被完成结构完全包围, 实搭时手无法从"
                                     "外部放入; 请把这一片移到封闭结构合拢之前放置"),
                     {tile->id}});
            }

            placed.push_back(std::move(geometry));
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

    // 每个步骤完成后的中间状态: 保证教程任意时刻都物理成立。
    // 用户搭到第 s 步就是一个真实存在过的实物结构, 它必须独立满足
    // 全部静态规则 —— 即使最终成品稳定, 中间状态失稳一样会塌。
    for (std::size_t s = 1; s <= model.steps.size(); ++s) {
        const auto partial = model.tilesUpToStep(static_cast<int>(s));
        std::ostringstream context;
        context << "第 " << model.steps[s - 1].step_number << " 步完成后";
        report.merge(validateAssembly(partial, context.str()));
    }

    // R7: 全程逐片放置可行性 (需要精确到步骤内的先后顺序)
    report.merge(validatePlacements(model));
    return report;
}

JitterReport PhysicsValidator::validateModelWithJitter(const core::ModelDefinition& model,
                                                       const JitterConfig& jitter) const {
    JitterReport result;
    result.iterations = std::max(jitter.iterations, 0);
    if (result.iterations == 0 || model.final_assembly.empty()) return result;

    // ---- 几何识别容差按注入误差的最坏情况放大 ----------------------
    // 注入的偏航绕每片自身局部原点的竖直轴旋转, 顶点位移上界为
    // 局部半径 x sin(偏航幅度); 平移每轴独立, 合位移上界为幅度 x √2。
    // 两片各自取最坏方向时相对错位再翻倍。贴合 (R2/R7a)、共面重叠
    // (R3) 与铰链共线分组 (R5/R6) 属于 "连接识别", 实物中毫米级错位
    // 会被磁吸自动拉回, 识别容差必须放大到能容纳注入误差, 否则每一
    // 轮都会把刻意注入的错位误报成 "没连上/穿插"。接地容差不放大
    // (平移只在水平面内、偏航不改变任何顶点的 z), 重心稳定裕量与
    // R5/R6 静力预算保持原档位 —— 它们才是抖动要考核的对象。
    double max_local_radius = 0.0;
    for (const TileInstance& tile : model.final_assembly) {
        for (const Vec2& v : catalog_->get(tile.type).vertices) {
            max_local_radius = std::max(max_local_radius, std::sqrt(v.x * v.x + v.y * v.y));
        }
    }
    const double yaw_rad = jitter.yaw_amplitude_deg * std::numbers::pi / 180.0;
    const double headroom = 2.0 * (jitter.translation_amplitude * std::numbers::sqrt2 +
                                   max_local_radius * std::sin(yaw_rad));
    PhysicsConfig jitter_config = config_;
    jitter_config.connect_tolerance += headroom;
    jitter_config.overlap_tolerance += headroom;
    jitter_config.collinear_tolerance += headroom;
    const PhysicsValidator jitter_validator(*catalog_, jitter_config);

    // 确定性均匀分布: 直接映射 mt19937 输出, 不用
    // std::uniform_real_distribution (标准未规定其算法, 跨标准库
    // 实现结果不同, 会破坏 CI 逐轮可复现)。
    std::mt19937 rng(jitter.seed);
    const auto uniform = [&rng](double amplitude) {
        constexpr double kRange = static_cast<double>(std::mt19937::max());
        return (static_cast<double>(rng()) / kRange * 2.0 - 1.0) * amplitude;
    };

    std::set<std::string> failing_codes;
    std::vector<std::string> sample_tile_ids;
    std::string sample_message;
    int first_failed_iteration = 0;

    for (int iteration = 1; iteration <= result.iterations; ++iteration) {
        // 逐字段构造扰动副本 (不整体拷贝: ModelDefinition 的惰性 id
        // 索引按尺寸判断新鲜度, 整体拷贝会带着指向原模型未扰动片的
        // 索引, 使 R7 逐片模拟悄悄校验回原始几何)。
        core::ModelDefinition perturbed;
        perturbed.id = model.id;
        perturbed.difficulty = model.difficulty;
        perturbed.total_pieces = model.total_pieces;
        perturbed.final_assembly = model.final_assembly;
        perturbed.steps = model.steps;

        // 每片一份独立误差, 整轮教程期间保持不变 —— 模拟 "这一次
        // 搭建中每片都放歪了一点且没有回调" 的误差累积场景 (每片在
        // 教程中恰好放置一次, 扰动成品即等价于扰动每步放置位置)。
        for (TileInstance& tile : perturbed.final_assembly) {
            tile.position.x += uniform(jitter.translation_amplitude);
            tile.position.y += uniform(jitter.translation_amplitude);
            tile.rotation_deg.z += uniform(jitter.yaw_amplitude_deg);
        }

        const ValidationReport iteration_report = jitter_validator.validateModel(perturbed);
        if (iteration_report.errorCount() == 0) continue;

        ++result.failed_iterations;
        for (const ValidationIssue& issue : iteration_report.issues) {
            if (issue.severity != IssueSeverity::Error) continue;
            failing_codes.insert(issue.code);
            if (first_failed_iteration == 0 && sample_message.empty()) {
                sample_message = issue.message;
                sample_tile_ids = issue.tile_ids;
            }
        }
        if (first_failed_iteration == 0) first_failed_iteration = iteration;
    }

    if (result.failed_iterations == 0) return result;

    std::string codes_text;
    for (const std::string& code : failing_codes) {
        if (!codes_text.empty()) codes_text += ", ";
        codes_text += code;
    }
    std::ostringstream oss;
    oss << std::fixed << std::setprecision(3);
    oss << "蒙特卡洛抖动仿真失败: 注入放置误差 (平移每轴 ±"
        << jitter.translation_amplitude << " 单位 ≈ ±"
        << formatGrams(jitter.translation_amplitude * 70.0) << "mm, 偏航 ±"
        << formatGrams(jitter.yaw_amplitude_deg) << "°) 后, " << result.iterations
        << " 轮中有 " << result.failed_iterations << " 轮违反物理规则 (涉及: " << codes_text
        << "); 首个失败样本 (第 " << first_failed_iteration << " 轮): " << sample_message
        << "。模型对毫米级放置误差没有足够裕量, 儿童实搭时误差累积可能倾倒或脱落 "
           "(BUILD_VERIFICATION.md F08), 请按 docs/PHYSICS_RULES.md R9 节加固";
    result.report.issues.push_back({IssueSeverity::Error, "placement_jitter_failure",
                                    oss.str(), std::move(sample_tile_ids)});
    return result;
}

}  // namespace magtile::physics
