#pragma once

// =============================================================
// MagTile Studio - 基础数学类型
// 约定: 1.0 个世界单位 = 标准正方形磁力片的边长 (约 70mm 实物)。
// 坐标系: 右手系, Z 轴竖直向上, 地面为 z = 0 平面。
// =============================================================

#include <array>
#include <cmath>

namespace magtile::core {

struct Vec2 {
    double x = 0.0;
    double y = 0.0;

    constexpr Vec2 operator+(const Vec2& o) const noexcept { return {x + o.x, y + o.y}; }
    constexpr Vec2 operator-(const Vec2& o) const noexcept { return {x - o.x, y - o.y}; }
    constexpr Vec2 operator*(double s) const noexcept { return {x * s, y * s}; }

    [[nodiscard]] constexpr double dot(const Vec2& o) const noexcept { return x * o.x + y * o.y; }
    /// 二维叉积 (z 分量), 用于凸包与朝向判断
    [[nodiscard]] constexpr double cross(const Vec2& o) const noexcept { return x * o.y - y * o.x; }
    [[nodiscard]] double length() const noexcept { return std::sqrt(x * x + y * y); }

    [[nodiscard]] Vec2 normalized() const noexcept {
        const double len = length();
        return len > 0.0 ? Vec2{x / len, y / len} : Vec2{};
    }
    /// 逆时针旋转 90 度, 即左法线
    [[nodiscard]] constexpr Vec2 perp() const noexcept { return {-y, x}; }
};

struct Vec3 {
    double x = 0.0;
    double y = 0.0;
    double z = 0.0;

    constexpr Vec3 operator+(const Vec3& o) const noexcept { return {x + o.x, y + o.y, z + o.z}; }
    constexpr Vec3 operator-(const Vec3& o) const noexcept { return {x - o.x, y - o.y, z - o.z}; }
    constexpr Vec3 operator*(double s) const noexcept { return {x * s, y * s, z * s}; }
    Vec3& operator+=(const Vec3& o) noexcept {
        x += o.x;
        y += o.y;
        z += o.z;
        return *this;
    }

    [[nodiscard]] constexpr double dot(const Vec3& o) const noexcept {
        return x * o.x + y * o.y + z * o.z;
    }
    [[nodiscard]] constexpr Vec3 cross(const Vec3& o) const noexcept {
        return {y * o.z - z * o.y, z * o.x - x * o.z, x * o.y - y * o.x};
    }
    [[nodiscard]] double length() const noexcept { return std::sqrt(dot(*this)); }

    [[nodiscard]] Vec3 normalized() const noexcept {
        const double len = length();
        return len > 0.0 ? Vec3{x / len, y / len, z / len} : Vec3{};
    }
    [[nodiscard]] constexpr Vec2 xy() const noexcept { return {x, y}; }
};

inline double distance(const Vec3& a, const Vec3& b) noexcept { return (a - b).length(); }

/// 行主序 3x3 矩阵, 仅用于旋转变换
struct Mat3 {
    // m[row][col]
    std::array<std::array<double, 3>, 3> m{{{1, 0, 0}, {0, 1, 0}, {0, 0, 1}}};

    [[nodiscard]] Vec3 operator*(const Vec3& v) const noexcept {
        return {
            m[0][0] * v.x + m[0][1] * v.y + m[0][2] * v.z,
            m[1][0] * v.x + m[1][1] * v.y + m[1][2] * v.z,
            m[2][0] * v.x + m[2][1] * v.y + m[2][2] * v.z,
        };
    }

    [[nodiscard]] Mat3 operator*(const Mat3& o) const noexcept {
        Mat3 r;
        for (int i = 0; i < 3; ++i) {
            for (int j = 0; j < 3; ++j) {
                r.m[i][j] = m[i][0] * o.m[0][j] + m[i][1] * o.m[1][j] + m[i][2] * o.m[2][j];
            }
        }
        return r;
    }

    static Mat3 rotationX(double degrees) noexcept;
    static Mat3 rotationY(double degrees) noexcept;
    static Mat3 rotationZ(double degrees) noexcept;
};

constexpr double kDegToRad = 3.14159265358979323846 / 180.0;

inline Mat3 Mat3::rotationX(double degrees) noexcept {
    const double c = std::cos(degrees * kDegToRad);
    const double s = std::sin(degrees * kDegToRad);
    Mat3 r;
    r.m = {{{1, 0, 0}, {0, c, -s}, {0, s, c}}};
    return r;
}

inline Mat3 Mat3::rotationY(double degrees) noexcept {
    const double c = std::cos(degrees * kDegToRad);
    const double s = std::sin(degrees * kDegToRad);
    Mat3 r;
    r.m = {{{c, 0, s}, {0, 1, 0}, {-s, 0, c}}};
    return r;
}

inline Mat3 Mat3::rotationZ(double degrees) noexcept {
    const double c = std::cos(degrees * kDegToRad);
    const double s = std::sin(degrees * kDegToRad);
    Mat3 r;
    r.m = {{{c, -s, 0}, {s, c, 0}, {0, 0, 1}}};
    return r;
}

/// 欧拉角 (度) 转旋转矩阵。
/// 施加顺序: 先绕 X, 再绕 Y, 最后绕 Z, 即 R = Rz * Ry * Rx。
/// 典型用法: 平铺磁力片无旋转; 竖立磁力片先 rotX=90 立起, 再用 rotZ 调整朝向。
inline Mat3 eulerZYX(const Vec3& degrees) noexcept {
    return Mat3::rotationZ(degrees.z) * Mat3::rotationY(degrees.y) * Mat3::rotationX(degrees.x);
}

}  // namespace magtile::core
