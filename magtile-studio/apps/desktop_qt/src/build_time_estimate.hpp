#pragma once

// =============================================================
// MagTile Studio (Qt) - 详情页「预计用时」转发头 (QT-1, UI_UX_SPEC §5.4)
//
// 实现已提升到核心层 include/magtile/core/build_time_estimate.hpp
// (纯函数、纯头文件、零框架依赖), 与 Android 详情弹窗共用同一份
// 算法 (JNI listModels 下发 estimated_minutes) —— 三端同一口径,
// 公式只此一处。本头保留 magtile::qtui 命名转发, StudioBackend::
// modelDetail 与单测 (ctest: qt_build_time_estimate) 无需改动。
// =============================================================

#include "magtile/core/build_time_estimate.hpp"

namespace magtile::qtui {

using magtile::core::estimateBuildMinutes;
using magtile::core::kBuildTimeBucketCount;
using magtile::core::kBuildTimeBuckets;

}  // namespace magtile::qtui
