#pragma once

// =============================================================
// MagTile Studio - 详情页「预计用时」估算 (UI_UX_SPEC §5.4)
//
// 温和的儿童向用时估算: 经验公式 每步约 1.5 分钟 (看图 + 找片 +
// 摆放) + 每片约 0.1 分钟微调 (片多的步骤更费时), 再归整到
// 5/10/15/20/30/45 分钟六个档位 —— 界面上只说「大约 15 分钟」,
// 永不假精确到 1 分钟 (孩子搭建节奏差异很大, 精确数字只会带来
// "超时焦虑", §4.3 无压力原则)。平票取小档 (宁可少说不吓人),
// 超出最大档一律封顶 45 分钟。
//
// 纯函数、纯头文件、零框架依赖, 三端同一实现同一口径:
//   - 桌面 Qt: StudioBackend::modelDetail (经 apps/desktop_qt/src/
//     build_time_estimate.hpp 转发, 单测 ctest: qt_build_time_estimate);
//   - Android: JNI listModels 逐模型下发 estimated_minutes
//     (MainActivity 详情弹窗展示, Kotlin 侧零公式)。
// =============================================================

namespace magtile::core {

/// 用时档位表 (分钟, 升序): 详情界面展示的全部可能取值。
inline constexpr int kBuildTimeBuckets[] = {5, 10, 15, 20, 30, 45};
inline constexpr int kBuildTimeBucketCount =
    static_cast<int>(sizeof(kBuildTimeBuckets) / sizeof(kBuildTimeBuckets[0]));

/// 预计搭建用时 (分钟): 返回值必落在 kBuildTimeBuckets 档位内。
/// step_count <= 0 (步数未知/数据异常) 时返回 0, 界面据此隐藏该行
/// (不显示错误, P3 零挫败); 负的片数按 0 处理。
[[nodiscard]] constexpr int estimateBuildMinutes(int step_count, int total_pieces) noexcept {
    if (step_count <= 0) return 0;
    if (total_pieces < 0) total_pieces = 0;
    // 原始估算, 单位 0.1 分钟 (整数运算避免浮点平台差异):
    // 每步 1.5 分钟 = 15, 每片 0.1 分钟 = 1
    const int raw_tenths = step_count * 15 + total_pieces;
    // 取距离最近的档位; 平票取小档 (严格更近才换大档)
    int best = kBuildTimeBuckets[0];
    int best_diff = -1;
    for (int i = 0; i < kBuildTimeBucketCount; ++i) {
        const int bucket_tenths = kBuildTimeBuckets[i] * 10;
        const int diff = raw_tenths > bucket_tenths ? raw_tenths - bucket_tenths
                                                    : bucket_tenths - raw_tenths;
        if (best_diff < 0 || diff < best_diff) {
            best = kBuildTimeBuckets[i];
            best_diff = diff;
        }
    }
    return best;
}

}  // namespace magtile::core
