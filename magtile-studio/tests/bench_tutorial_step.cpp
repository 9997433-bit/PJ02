// =============================================================
// MagTile Studio - 教程步进性能基准 (microbench)
//
// 商用软件承诺: 大模型 (100+ 片) 的教程步进不能卡死。本基准对代表
// 模型逐步计时 TutorialEngine 的完整"每步工作量" —— 步骤导航
// (nextStep / goToStep) 加上渲染层每步都会调用的场景查询
// (currentStep / visibleTiles / tilesAddedThisStep / highlightTiles /
// progress), 与 Qt TutorialViewport::rebuildSceneTiles 及 Android JNI
// 每步实际执行的引擎调用一致 (进度落盘 SQLite 与 GPU 上传不在
// 本基准范围内, 分别由 progress_roundtrip 与 GL 冒烟覆盖)。
//
// 两种导航模式都测:
//   - 顺序走查: reset 后 nextStep 逐步推到底 (日常搭建路径);
//   - 钟摆跳转: goToStep 在 0 与最后一步之间来回远跳 (进度页
//     "继续搭建" / 用户拖动步骤条的最坏情况, 每次都重建完整可见集)。
//
// 用法:
//   magtile_bench_tutorial <model.json> [<model.json> ...]
//       [--iterations N] [--budget-ms X]
// 环境变量:
//   MAGTILE_BENCH_BUDGET_MS  预算覆盖 (未显式给 --budget-ms 时生效;
//                            负载不稳的共享 CI 可临时放宽)
//   MAGTILE_BENCH_SKIP=1     跳过基准 (退出码 77 = ctest SKIP)
// 退出码: 0 全部通过; 1 存在超预算模型; 2 用法/数据错误; 77 跳过
// =============================================================

#include <algorithm>
#include <chrono>
#include <cmath>
#include <cstdio>
#include <cstdlib>
#include <string>
#include <vector>

#include "magtile/core/json_io.hpp"
#include "magtile/tutorial/tutorial_engine.hpp"

namespace {

using Clock = std::chrono::steady_clock;

// 防止编译器把无副作用的查询整体优化掉。
volatile std::size_t g_sink = 0;

constexpr double kDefaultBudgetMs = 500.0;
constexpr int kDefaultIterations = 25;
constexpr int kExitSkip = 77;  // ctest SKIP_RETURN_CODE

/// 执行渲染层每步都要做的全部引擎查询, 返回吞入 sink 的规模。
std::size_t runStepQueries(const magtile::tutorial::TutorialEngine& engine) {
    std::size_t total = 0;
    if (const auto* step = engine.currentStep()) total += step->tiles_to_add.size();
    total += engine.visibleTiles().size();
    total += engine.tilesAddedThisStep().size();
    total += engine.highlightTiles().size();
    total += static_cast<std::size_t>(engine.progress() * 1000.0);
    return total;
}

double median(std::vector<double> samples) {
    std::sort(samples.begin(), samples.end());
    const std::size_t n = samples.size();
    return n % 2 == 1 ? samples[n / 2] : (samples[n / 2 - 1] + samples[n / 2]) / 2.0;
}

double percentile(std::vector<double> samples, double p) {
    std::sort(samples.begin(), samples.end());
    const auto n = static_cast<double>(samples.size());
    auto idx = static_cast<std::size_t>(std::ceil(p * n));
    if (idx > 0) --idx;
    return samples[std::min(idx, samples.size() - 1)];
}

struct ModelResult {
    std::string id;
    double load_ms = 0.0;
    double slowest_step_median_ms = 0.0;  ///< 全部步骤中位数的最大值
    double p95_ms = 0.0;                  ///< 全部样本 (两种模式合并) P95
    double max_ms = 0.0;
    bool passed = false;
};

/// 对单个模型跑基准; 计时失败 (数据加载异常) 时抛出。
ModelResult benchModel(const std::string& file, int iterations, double budget_ms) {
    const auto load_start = Clock::now();
    auto model = magtile::core::loadModelDefinition(file);
    const double load_ms =
        std::chrono::duration<double, std::milli>(Clock::now() - load_start).count();

    const std::size_t piece_count = model.final_assembly.size();
    magtile::tutorial::TutorialEngine engine(std::move(model));
    const int step_count = engine.stepCount();
    if (step_count <= 0) throw std::runtime_error("模型没有教程步骤: " + file);

    std::printf("==== 模型 %s (%zu 片 / %d 步) ====\n", engine.model().id.c_str(),
                piece_count, step_count);
    std::printf("  加载: %.3f ms\n", load_ms);

    // 预热一轮: 触发惰性 tile 索引构建等一次性成本, 不计入样本。
    engine.reset();
    while (engine.nextStep()) g_sink = g_sink + runStepQueries(engine);

    // samples[step - 1] = 该步骤的全部计时样本 (ms)
    std::vector<std::vector<double>> next_samples(static_cast<std::size_t>(step_count));
    std::vector<std::vector<double>> goto_samples(static_cast<std::size_t>(step_count));

    // 钟摆访问序: 0, N, 1, N-1, 2, N-2 ... 每次跳转跨度都接近全程。
    std::vector<int> pendulum;
    for (int lo = 0, hi = step_count; lo <= hi;) {
        pendulum.push_back(lo++);
        if (lo > hi) break;
        pendulum.push_back(hi--);
    }

    for (int iter = 0; iter < iterations; ++iter) {
        engine.reset();
        for (int s = 1; s <= step_count; ++s) {
            const auto t0 = Clock::now();
            const bool ok = engine.nextStep();
            const std::size_t sink = runStepQueries(engine);
            const auto t1 = Clock::now();
            g_sink = g_sink + sink;
            if (!ok) throw std::runtime_error("nextStep 意外失败");
            next_samples[static_cast<std::size_t>(s - 1)].push_back(
                std::chrono::duration<double, std::milli>(t1 - t0).count());
        }
        for (const int target : pendulum) {
            const auto t0 = Clock::now();
            const bool ok = engine.goToStep(target);
            const std::size_t sink = runStepQueries(engine);
            const auto t1 = Clock::now();
            g_sink = g_sink + sink;
            if (!ok) throw std::runtime_error("goToStep 意外失败");
            if (target == 0) continue;  // 第 0 步 = 空场景, 不设预算
            goto_samples[static_cast<std::size_t>(target - 1)].push_back(
                std::chrono::duration<double, std::milli>(t1 - t0).count());
        }
    }

    ModelResult result;
    result.id = engine.model().id;
    result.load_ms = load_ms;
    std::vector<double> all;
    for (int s = 1; s <= step_count; ++s) {
        const auto& next = next_samples[static_cast<std::size_t>(s - 1)];
        const auto& jump = goto_samples[static_cast<std::size_t>(s - 1)];
        const double next_med = median(next);
        const double goto_med = median(jump);
        std::printf("  步 %2d/%d: next %.4f ms | goToStep %.4f ms\n", s, step_count,
                    next_med, goto_med);
        result.slowest_step_median_ms =
            std::max({result.slowest_step_median_ms, next_med, goto_med});
        all.insert(all.end(), next.begin(), next.end());
        all.insert(all.end(), jump.begin(), jump.end());
    }
    result.p95_ms = percentile(all, 0.95);
    result.max_ms = *std::max_element(all.begin(), all.end());
    result.passed = result.slowest_step_median_ms <= budget_ms && result.p95_ms <= budget_ms;

    double sum = 0.0;
    for (const double v : all) sum += v;
    std::printf("  样本 %zu 个: 均值 %.4f ms | P95 %.4f ms | 最大 %.4f ms | 最慢步中位 %.4f ms\n",
                all.size(), sum / static_cast<double>(all.size()), result.p95_ms,
                result.max_ms, result.slowest_step_median_ms);
    std::printf("  预算 %.1f ms/步 -> %s\n\n", budget_ms, result.passed ? "通过" : "超预算");
    return result;
}

}  // namespace

int main(int argc, char** argv) {
    if (const char* skip = std::getenv("MAGTILE_BENCH_SKIP");
        skip != nullptr && std::string(skip) == "1") {
        std::printf("[跳过] MAGTILE_BENCH_SKIP=1, 教程步进基准不执行 (退出码 77)\n");
        return kExitSkip;
    }

    std::vector<std::string> model_files;
    int iterations = kDefaultIterations;
    double budget_ms = kDefaultBudgetMs;
    bool budget_from_cli = false;

    for (int i = 1; i < argc; ++i) {
        const std::string arg = argv[i];
        if (arg == "--iterations" && i + 1 < argc) {
            iterations = std::atoi(argv[++i]);
        } else if (arg == "--budget-ms" && i + 1 < argc) {
            budget_ms = std::atof(argv[++i]);
            budget_from_cli = true;
        } else if (!arg.empty() && arg[0] == '-') {
            std::fprintf(stderr, "未知参数: %s\n", arg.c_str());
            return 2;
        } else {
            model_files.push_back(arg);
        }
    }
    if (!budget_from_cli) {
        if (const char* env = std::getenv("MAGTILE_BENCH_BUDGET_MS"); env != nullptr) {
            budget_ms = std::atof(env);
        }
    }
    if (model_files.empty() || iterations <= 0 || budget_ms <= 0.0) {
        std::fprintf(stderr,
                     "用法: magtile_bench_tutorial <model.json> [<model.json> ...]\n"
                     "          [--iterations N] [--budget-ms X]\n");
        return 2;
    }

    std::printf("教程步进性能基准: %zu 个模型, 每模型 %d 轮, 预算 %.1f ms/步\n\n",
                model_files.size(), iterations, budget_ms);

    std::vector<ModelResult> results;
    for (const auto& file : model_files) {
        try {
            results.push_back(benchModel(file, iterations, budget_ms));
        } catch (const std::exception& ex) {
            std::fprintf(stderr, "基准执行失败 (%s): %s\n", file.c_str(), ex.what());
            return 2;
        }
    }

    std::printf("---- 基准总结 (预算 %.1f ms/步) ----\n", budget_ms);
    bool all_passed = true;
    for (const auto& r : results) {
        std::printf("  %-8s %-24s 最慢步中位 %.4f ms | P95 %.4f ms | 最大 %.4f ms\n",
                    r.passed ? "[通过]" : "[超预算]", r.id.c_str(),
                    r.slowest_step_median_ms, r.p95_ms, r.max_ms);
        all_passed = all_passed && r.passed;
    }
    if (!all_passed) {
        std::printf("结论: 存在超预算模型, 教程步进性能回归 (退出码 1)\n");
        return 1;
    }
    std::printf("结论: 全部模型步进耗时在预算之内\n");
    return 0;
}
