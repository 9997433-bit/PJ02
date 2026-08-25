#!/usr/bin/env python3
# =============================================================
# MagTile Studio - 教程步进性能基准入口 (包装 magtile_bench_tutorial)
#
# 商用承诺: 大模型 (100+ 片) 教程步进不能卡死。本脚本以固定口径
# (小/中/大三个代表模型) 调用 C++ 微基准 tests/bench_tutorial_step.cpp
# 编译出的 magtile_bench_tutorial, 逐步计时 nextStep / goToStep +
# 渲染层每步查询, 输出每步 ms 与 P95, 超预算退出码 1。
#
# 代表模型 (按 total_pieces 覆盖全库规模区间, 全库 44 ~ 122 片):
#   小: beach_hut_01          44 片 / 12 步 (全库最小)
#   中: castle_foundation_01  72 片 / 16 步 (中位规模, 旗舰)
#   大: skyscraper_01        122 片 / 26 步 (全库最大)
#
# 用法:
#   python3 tools/bench_tutorial_step.py [--build-dir build]
#       [--budget-ms 500] [--iterations 25] [--models a.json b.json ...]
# 环境变量 (由 C++ 基准解释):
#   MAGTILE_BENCH_BUDGET_MS  预算覆盖 (未显式给 --budget-ms 时生效)
#   MAGTILE_BENCH_SKIP=1     跳过 (退出码 77 = SKIP)
# 退出码: 0 通过; 1 超预算 (性能回归); 2 环境/用法错误; 77 跳过
# =============================================================
"""教程步进性能基准入口: 定位构建产物并按固定口径执行 C++ 微基准。"""

import argparse
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

DEFAULT_MODELS = [
    "beach_hut_01.json",          # 小: 44 片 / 12 步
    "castle_foundation_01.json",  # 中: 72 片 / 16 步
    "skyscraper_01.json",         # 大: 122 片 / 26 步
]


def find_bench_binary(build_dir: str) -> str:
    """在构建目录中定位基准可执行文件, 找不到返回空串。"""
    for name in ("magtile_bench_tutorial", "magtile_bench_tutorial.exe"):
        for sub in ("", "Release", "Debug"):  # 多配置生成器 (MSVC) 的子目录
            candidate = os.path.join(build_dir, sub, name)
            if os.path.isfile(candidate) and os.access(candidate, os.X_OK):
                return candidate
    return ""


def main() -> int:
    parser = argparse.ArgumentParser(description="教程步进性能基准 (小/中/大代表模型)")
    parser.add_argument("--build-dir", default=os.path.join(ROOT, "build"),
                        help="CMake 构建目录 (默认 build)")
    parser.add_argument("--budget-ms", type=float, default=None,
                        help="单步预算 ms (默认 500, 亦可用 MAGTILE_BENCH_BUDGET_MS)")
    parser.add_argument("--iterations", type=int, default=None,
                        help="每模型计时轮数 (默认由基准决定, 25)")
    parser.add_argument("--models", nargs="+", default=None,
                        help="模型 JSON 路径列表 (默认小/中/大三个代表模型)")
    args = parser.parse_args()

    build_dir = args.build_dir if os.path.isabs(args.build_dir) \
        else os.path.join(ROOT, args.build_dir)
    binary = find_bench_binary(build_dir)
    if not binary:
        print(f"错误: 在 {build_dir} 未找到 magtile_bench_tutorial, "
              "请先构建: cmake --build <build-dir> --target magtile_bench_tutorial",
              file=sys.stderr)
        return 2

    if args.models is not None:
        models = [m if os.path.isabs(m) else os.path.join(ROOT, m) for m in args.models]
    else:
        models = [os.path.join(ROOT, "data", "models", m) for m in DEFAULT_MODELS]
    missing = [m for m in models if not os.path.isfile(m)]
    if missing:
        print("错误: 模型文件不存在: " + ", ".join(missing), file=sys.stderr)
        return 2

    cmd = [binary] + models
    if args.budget_ms is not None:
        cmd += ["--budget-ms", str(args.budget_ms)]
    if args.iterations is not None:
        cmd += ["--iterations", str(args.iterations)]
    return subprocess.run(cmd, check=False).returncode


if __name__ == "__main__":
    sys.exit(main())
