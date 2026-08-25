#pragma once

// =============================================================
// MagTile Studio - 轨道相机
// 围绕目标点旋转 / 缩放 / 平移的观察相机, 是磁力片教程的标准
// 交互方式。仅做纯数学计算, 不依赖任何窗口或图形库, 由渲染后端
// 将鼠标输入换算为下列操作。
// =============================================================

#include "magtile/core/vec3.hpp"
#include "magtile/render/renderer.hpp"

namespace magtile::render {

class OrbitCamera {
public:
    // 缺省视角: 从西南上方 45 度俯视原点附近的地面。
    OrbitCamera() = default;

    /// 水平/垂直旋转 (度)。俯仰角被限制在 (-89, 89) 度, 避免万向锁。
    void rotate(double delta_yaw_deg, double delta_pitch_deg) noexcept;

    /// 在视平面内平移目标点。dx/dy 为屏幕像素位移, viewport_height
    /// 用于把像素换算为世界距离, 保证不同缩放级别下手感一致。
    void pan(double dx_pixels, double dy_pixels, int viewport_height) noexcept;

    /// 缩放: steps 为滚轮格数, 正值拉近。距离按指数缩放并夹在合法区间。
    void zoom(double scroll_steps) noexcept;

    /// 每格滚轮的距离缩放系数 (12%/格)。触屏捏合等连续手势可据此把
    /// 比例变化换算成等效滚轮格数, 与滚轮共用同一缩放口径。
    static constexpr double kZoomStepFactor = 0.88;

    /// 取景: 移动目标点到包围盒中心并调整距离, 使整个模型进入视野。
    void frameBounds(const core::Vec3& min_corner, const core::Vec3& max_corner) noexcept;

    /// 恢复到最近一次 frameBounds 的取景 (未取景过则回到缺省视角)。
    void resetView() noexcept;

    /// 导出渲染所需的相机参数。
    [[nodiscard]] Camera toCamera() const noexcept;

    [[nodiscard]] const core::Vec3& target() const noexcept { return target_; }
    [[nodiscard]] double distance() const noexcept { return distance_; }
    [[nodiscard]] core::Vec3 eye() const noexcept;

private:
    static constexpr double kMinDistance = 1.5;
    static constexpr double kMaxDistance = 80.0;
    static constexpr double kMaxPitchDeg = 89.0;
    static constexpr double kFovDeg = 45.0;

    core::Vec3 target_{0.0, 0.0, 1.0};
    double yaw_deg_ = -125.0;  ///< 绕 Z 轴, 0 = +X 方向
    double pitch_deg_ = 32.0;  ///< 相对地平面仰角
    double distance_ = 14.0;

    // frameBounds 记录的"主场景"取景, 供 resetView 恢复
    core::Vec3 home_target_{0.0, 0.0, 1.0};
    double home_distance_ = 14.0;
};

}  // namespace magtile::render
