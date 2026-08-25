#include "magtile/physics/geometry.hpp"

#include <algorithm>
#include <cmath>
#include <limits>

namespace magtile::physics {
namespace {

/// 将共面多边形投影到该平面的二维正交基上。
struct PlaneBasis {
    Vec3 origin;
    Vec3 u;
    Vec3 v;

    [[nodiscard]] Vec2 project(const Vec3& p) const noexcept {
        const Vec3 d = p - origin;
        return {d.dot(u), d.dot(v)};
    }
};

PlaneBasis makeBasis(const TransformedTile& tile) {
    const Vec3 u = (tile.vertices[1] - tile.vertices[0]).normalized();
    const Vec3 v = tile.normal.cross(u).normalized();
    return {tile.vertices[0], u, v};
}

/// 一维投影区间
struct Interval {
    double min = std::numeric_limits<double>::max();
    double max = std::numeric_limits<double>::lowest();
};

Interval projectOntoAxis(const std::vector<Vec2>& points, const Vec2& axis) {
    Interval interval;
    for (const Vec2& p : points) {
        const double d = p.dot(axis);
        interval.min = std::min(interval.min, d);
        interval.max = std::max(interval.max, d);
    }
    return interval;
}

/// 分离轴检测: 任一轴上重叠深度 <= tolerance 即视为分离。
bool overlapsOnAllAxes(const std::vector<Vec2>& a, const std::vector<Vec2>& b, double tolerance) {
    const auto testEdges = [&](const std::vector<Vec2>& poly) {
        const std::size_t n = poly.size();
        for (std::size_t i = 0; i < n; ++i) {
            const Vec2 edge = poly[(i + 1) % n] - poly[i];
            const Vec2 axis = edge.perp().normalized();
            const Interval ia = projectOntoAxis(a, axis);
            const Interval ib = projectOntoAxis(b, axis);
            const double overlap = std::min(ia.max, ib.max) - std::max(ia.min, ib.min);
            if (overlap <= tolerance) return false;  // 找到分离轴
        }
        return true;
    };
    return testEdges(a) && testEdges(b);
}

double pointToSegmentDistance(const Vec2& p, const Vec2& a, const Vec2& b) {
    const Vec2 ab = b - a;
    const double len_sq = ab.dot(ab);
    if (len_sq <= 0.0) return (p - a).length();
    const double t = std::clamp((p - a).dot(ab) / len_sq, 0.0, 1.0);
    const Vec2 closest = a + ab * t;
    return (p - closest).length();
}

}  // namespace

std::pair<Vec3, Vec3> TransformedTile::edge(std::size_t i) const {
    return {vertices[i], vertices[(i + 1) % vertices.size()]};
}

bool TransformedTile::isMagnetEdge(std::size_t i) const noexcept {
    return shape != nullptr && shape->isMagnetEdge(static_cast<int>(i));
}

TransformedTile transformTile(const core::TileInstance& instance, const core::TileShape& shape) {
    TransformedTile result;
    result.instance = &instance;
    result.shape = &shape;

    const core::Mat3 rotation = core::eulerZYX(instance.rotation_deg);
    result.vertices.reserve(shape.vertices.size());
    result.min_z = std::numeric_limits<double>::max();
    for (const Vec2& local : shape.vertices) {
        const Vec3 world = rotation * Vec3{local.x, local.y, 0.0} + instance.position;
        result.min_z = std::min(result.min_z, world.z);
        result.vertices.push_back(world);
    }

    // 面法向: 本地 +Z 经旋转后的方向 (顶点逆时针绕序与其一致)
    result.normal = (rotation * Vec3{0.0, 0.0, 1.0}).normalized();

    // 面积与质心: 以顶点 0 为扇心做三角剖分 (目录中的形状均为凸多边形)
    double total_area = 0.0;
    Vec3 weighted_centroid{};
    for (std::size_t i = 1; i + 1 < result.vertices.size(); ++i) {
        const Vec3& a = result.vertices[0];
        const Vec3& b = result.vertices[i];
        const Vec3& c = result.vertices[i + 1];
        const double tri_area = (b - a).cross(c - a).length() * 0.5;
        const Vec3 tri_centroid = (a + b + c) * (1.0 / 3.0);
        total_area += tri_area;
        weighted_centroid += tri_centroid * tri_area;
    }
    result.area = total_area;
    result.centroid = total_area > 0.0 ? weighted_centroid * (1.0 / total_area) : instance.position;
    return result;
}

bool areCoplanar(const TransformedTile& a, const TransformedTile& b, double tolerance) {
    // 法向平行 (同向或反向均可)
    if (std::abs(std::abs(a.normal.dot(b.normal)) - 1.0) > 1e-6) return false;
    // 两平面间距
    return std::abs(a.normal.dot(b.centroid - a.centroid)) <= tolerance;
}

bool coplanarPolygonsOverlap(const TransformedTile& a, const TransformedTile& b,
                             double tolerance) {
    const PlaneBasis basis = makeBasis(a);
    std::vector<Vec2> pa;
    std::vector<Vec2> pb;
    pa.reserve(a.vertices.size());
    pb.reserve(b.vertices.size());
    for (const Vec3& v : a.vertices) pa.push_back(basis.project(v));
    for (const Vec3& v : b.vertices) pb.push_back(basis.project(v));
    return overlapsOnAllAxes(pa, pb, tolerance);
}

std::vector<Vec2> convexHull2D(std::vector<Vec2> points) {
    // Andrew 单调链, O(n log n)
    std::sort(points.begin(), points.end(), [](const Vec2& l, const Vec2& r) {
        return l.x < r.x || (l.x == r.x && l.y < r.y);
    });
    points.erase(std::unique(points.begin(), points.end(),
                             [](const Vec2& l, const Vec2& r) {
                                 return std::abs(l.x - r.x) < 1e-9 && std::abs(l.y - r.y) < 1e-9;
                             }),
                 points.end());
    const std::size_t n = points.size();
    if (n < 3) return points;

    std::vector<Vec2> hull(2 * n);
    std::size_t k = 0;
    for (std::size_t i = 0; i < n; ++i) {  // 下链
        while (k >= 2 && (hull[k - 1] - hull[k - 2]).cross(points[i] - hull[k - 2]) <= 0) --k;
        hull[k++] = points[i];
    }
    const std::size_t lower_size = k + 1;
    for (std::size_t i = n - 1; i-- > 0;) {  // 上链
        while (k >= lower_size &&
               (hull[k - 1] - hull[k - 2]).cross(points[i] - hull[k - 2]) <= 0)
            --k;
        hull[k++] = points[i];
    }
    hull.resize(k - 1);
    return hull;
}

double signedDistanceToHull(const Vec2& point, const std::vector<Vec2>& hull) {
    if (hull.empty()) return std::numeric_limits<double>::max();
    if (hull.size() == 1) return (point - hull[0]).length();
    if (hull.size() == 2) return pointToSegmentDistance(point, hull[0], hull[1]);

    // 凸包为逆时针: 点在所有边左侧 => 在内部, 返回负的最近边距
    bool inside = true;
    double min_edge_distance = std::numeric_limits<double>::max();
    const std::size_t n = hull.size();
    for (std::size_t i = 0; i < n; ++i) {
        const Vec2& a = hull[i];
        const Vec2& b = hull[(i + 1) % n];
        if ((b - a).cross(point - a) < 0.0) inside = false;
        min_edge_distance = std::min(min_edge_distance, pointToSegmentDistance(point, a, b));
    }
    return inside ? -min_edge_distance : min_edge_distance;
}

}  // namespace magtile::physics
