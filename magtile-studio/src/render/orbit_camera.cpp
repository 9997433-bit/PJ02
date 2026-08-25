#include "magtile/render/orbit_camera.hpp"

#include <algorithm>
#include <cmath>

namespace magtile::render {

using core::Vec3;

namespace {

/// 由偏航/俯仰角计算从目标指向相机的单位方向 (Z 轴向上的右手系)。
Vec3 orbitDirection(double yaw_deg, double pitch_deg) noexcept {
    const double yaw = yaw_deg * core::kDegToRad;
    const double pitch = pitch_deg * core::kDegToRad;
    const double cp = std::cos(pitch);
    return {cp * std::cos(yaw), cp * std::sin(yaw), std::sin(pitch)};
}

}  // namespace

void OrbitCamera::rotate(double delta_yaw_deg, double delta_pitch_deg) noexcept {
    yaw_deg_ += delta_yaw_deg;
    // 保持角度在 [-180, 180) 区间, 避免长时间拖拽后精度下降
    yaw_deg_ = std::fmod(yaw_deg_ + 540.0, 360.0) - 180.0;
    pitch_deg_ = std::clamp(pitch_deg_ + delta_pitch_deg, -kMaxPitchDeg, kMaxPitchDeg);
}

void OrbitCamera::pan(double dx_pixels, double dy_pixels, int viewport_height) noexcept {
    if (viewport_height <= 0) return;
    // 目标点深度处每像素对应的世界距离
    const double world_per_pixel =
        2.0 * distance_ * std::tan(kFovDeg * 0.5 * core::kDegToRad) / viewport_height;

    const Vec3 view_dir = orbitDirection(yaw_deg_, pitch_deg_) * -1.0;  // 相机 -> 目标
    const Vec3 world_up{0.0, 0.0, 1.0};
    const Vec3 right = view_dir.cross(world_up).normalized();
    const Vec3 up = right.cross(view_dir).normalized();

    target_ += right * (-dx_pixels * world_per_pixel) + up * (dy_pixels * world_per_pixel);
}

void OrbitCamera::zoom(double scroll_steps) noexcept {
    // 每格滚轮缩放 12%, 指数级手感在远近两端都平滑
    distance_ = std::clamp(distance_ * std::pow(kZoomStepFactor, scroll_steps), kMinDistance,
                           kMaxDistance);
}

void OrbitCamera::frameBounds(const Vec3& min_corner, const Vec3& max_corner) noexcept {
    const Vec3 center = (min_corner + max_corner) * 0.5;
    const double radius = std::max(0.5, (max_corner - min_corner).length() * 0.5);

    target_ = center;
    // 令包围球恰好落入垂直视场, 再放大 1.25 倍留出边距
    distance_ = std::clamp(radius / std::sin(kFovDeg * 0.5 * core::kDegToRad) * 1.25,
                           kMinDistance, kMaxDistance);
    home_target_ = target_;
    home_distance_ = distance_;
}

void OrbitCamera::resetView() noexcept {
    target_ = home_target_;
    distance_ = home_distance_;
    yaw_deg_ = -125.0;
    pitch_deg_ = 32.0;
}

Vec3 OrbitCamera::eye() const noexcept {
    return target_ + orbitDirection(yaw_deg_, pitch_deg_) * distance_;
}

Camera OrbitCamera::toCamera() const noexcept {
    Camera camera;
    camera.eye = eye();
    camera.target = target_;
    camera.up = {0.0, 0.0, 1.0};
    camera.fov_deg = kFovDeg;
    return camera;
}

}  // namespace magtile::render
