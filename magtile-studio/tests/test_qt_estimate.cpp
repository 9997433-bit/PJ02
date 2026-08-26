// =============================================================
// MagTile Studio - 详情页「预计用时」纯函数单测
// (ctest: qt_build_time_estimate, 仅 MAGTILE_BUILD_QT=ON 时注册)
//
// 覆盖 build_time_estimate.hpp (QT-1, UI_UX_SPEC §5.4):
//   1. 返回值必落在 5/10/15/20/30/45 分钟档位 (不假精确到 1 分钟);
//   2. 档位归整: 取最近档, 平票取小档 (温和, 宁可少说不吓人);
//   3. 上限封顶 45 分钟 / 极小模型落 5 分钟档;
//   4. 步数未知 (<= 0) 返回 0 (界面隐藏, 不显示错误), 负片数按 0;
//   5. 全库代表值回归 (中位 16 步 69 片 -> 30 分钟等);
//   6. 单调性: 步数/片数增加, 估算档位不下降。
// 纯函数无 Qt 依赖, 关键值另以 static_assert 编译期锁定。
// =============================================================

#include <cstdio>

#include "build_time_estimate.hpp"

namespace {

int g_failures = 0;

void expect(bool condition, const char* message) {
    if (condition) {
        std::printf("[通过] %s\n", message);
    } else {
        std::printf("[失败] %s\n", message);
        ++g_failures;
    }
}

}  // namespace

using magtile::qtui::estimateBuildMinutes;
using magtile::qtui::kBuildTimeBucketCount;
using magtile::qtui::kBuildTimeBuckets;

// ---- 编译期锁定关键值 (constexpr 纯函数) -------------------------------
static_assert(estimateBuildMinutes(0, 50) == 0, "步数未知返回 0");
static_assert(estimateBuildMinutes(16, 69) == 30, "全库中位模型落 30 分钟档");
static_assert(estimateBuildMinutes(26, 122) == 45, "最大模型封顶 45 分钟档");

int main() {
    // ---- 1. 返回值必落在档位表内 (扫全输入面) --------------------------
    {
        bool all_in_buckets = true;
        for (int steps = 1; steps <= 40 && all_in_buckets; ++steps) {
            for (int pieces = 0; pieces <= 200; ++pieces) {
                const int minutes = estimateBuildMinutes(steps, pieces);
                bool in_bucket = false;
                for (int i = 0; i < kBuildTimeBucketCount; ++i) {
                    if (minutes == kBuildTimeBuckets[i]) in_bucket = true;
                }
                if (!in_bucket) {
                    std::printf("[失败] 越档: %d 步 %d 片 -> %d 分钟\n", steps, pieces,
                                minutes);
                    all_in_buckets = false;
                    break;
                }
            }
        }
        expect(all_in_buckets, "任意输入估算必落 5/10/15/20/30/45 分钟档 (不假精确)");
    }

    // ---- 2. 档位归整: 最近档, 平票取小档 -------------------------------
    // 2 步 8 片 = 3.8 分钟 -> 最近 5 分钟档
    expect(estimateBuildMinutes(2, 8) == 5, "极小模型落最小 5 分钟档");
    // 5 步 20 片 = 9.5 分钟 -> 最近 10 分钟档
    expect(estimateBuildMinutes(5, 20) == 10, "9.5 分钟归整到 10 分钟档");
    // 3 步 30 片 = 7.5 分钟, 距 5 与 10 等距 -> 取小档 5 (温和不吓人)
    expect(estimateBuildMinutes(3, 30) == 5, "档位平票取小档 (7.5 -> 5)");
    // 10 步 100 片 = 25.0 分钟, 距 20 与 30 等距 -> 取小档 20
    expect(estimateBuildMinutes(10, 100) == 20, "档位平票取小档 (25.0 -> 20)");

    // ---- 3. 上限封顶: 再大的模型也只说 45 分钟 -------------------------
    expect(estimateBuildMinutes(40, 200) == 45, "超大模型封顶 45 分钟档");
    expect(estimateBuildMinutes(100, 500) == 45, "极端输入同样封顶 45 分钟档");

    // ---- 4. 数据异常时温和降级 (0 = 界面隐藏, 不报错) ------------------
    expect(estimateBuildMinutes(0, 60) == 0, "步数 0 (未知) 返回 0 供界面隐藏");
    expect(estimateBuildMinutes(-1, 60) == 0, "负步数返回 0 供界面隐藏");
    expect(estimateBuildMinutes(12, -5) == estimateBuildMinutes(12, 0),
           "负片数按 0 处理 (不影响估算)");

    // ---- 5. 全库代表值回归 (docs 口径: 每步 1.5 分钟 + 每片 0.1 分钟) --
    expect(estimateBuildMinutes(10, 46) == 20, "最小在库模型 (10 步 46 片) -> 20 分钟");
    expect(estimateBuildMinutes(12, 69) == 20, "收费站 (12 步 69 片) -> 20 分钟");
    expect(estimateBuildMinutes(16, 69) == 30, "中位模型 (16 步 69 片) -> 30 分钟");
    expect(estimateBuildMinutes(26, 122) == 45, "摩天楼 (26 步 122 片) -> 45 分钟");

    // ---- 6. 单调性: 工作量增加, 档位不下降 -----------------------------
    {
        bool monotonic = true;
        for (int steps = 1; steps <= 40 && monotonic; ++steps) {
            for (int pieces = 0; pieces <= 200; ++pieces) {
                if (estimateBuildMinutes(steps + 1, pieces) <
                        estimateBuildMinutes(steps, pieces) ||
                    estimateBuildMinutes(steps, pieces + 1) <
                        estimateBuildMinutes(steps, pieces)) {
                    std::printf("[失败] 单调性破坏于 %d 步 %d 片\n", steps, pieces);
                    monotonic = false;
                    break;
                }
            }
        }
        expect(monotonic, "步数/片数增加时估算档位不下降");
    }

    if (g_failures == 0) {
        std::printf("预计用时纯函数单测全部通过\n");
        return 0;
    }
    std::printf("共 %d 项失败\n", g_failures);
    return 1;
}
