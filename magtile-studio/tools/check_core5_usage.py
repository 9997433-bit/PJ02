#!/usr/bin/env python3
"""核心五片型 (core-5) 覆盖率检查 —— 片型分层质检工具。

产品默认基础套装只含核心五片型 (docs/TILE_CATALOG.md):
正方形 / 等边三角形 / 直角三角形 / 等腰三角形 / 长方形。
本工具扫描模型库, 输出片型分层报告并核对内容策略 2.5 节的规则
(docs/CONTENT_STRATEGY.md):

  1. 全库 core-5 覆盖率: 只用核心五片型的模型占比 (主库以 core-5 为默认);
  2. 扩展片型清单: 每个用到扩展片型的模型, 列出具体片型;
  3. 标签一致性: 用了扩展片型的模型必须带 "需要扩展装" 标签,
     没用的不得带 (双向核对, 违反输出 WARN);
  4. 免费层红线: 带 "免费" 标签的模型中 >=80% 必须只用核心五片型,
     免费层用扩展片型的模型逐个输出 WARN。

目录一致性双重校验: data/tile_catalog.json 中 tier=core 的片型集合
必须与本工具内置的核心五片型白名单完全一致, 不一致按结构错误退出 —— 
tier 的事实来源是目录文件, 白名单只用来兜住目录被误改的情况。

退出码:
  0  检查完成 (可能有 WARN —— 现阶段警告不作为 CI 硬失败);
  1  --strict 模式下存在 WARN (免费 30 选品定稿后 CI 可切换);
  2  结构错误 (目录 tier 与白名单不一致 / 未知片型 / 文件不可读)。

用法:
  python3 tools/check_core5_usage.py [模型目录] [--catalog 目录文件] [--strict]
"""

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# 核心五片型白名单 (与 data/tile_catalog.json 的 tier=core 双重校验)
CORE5 = frozenset({
    "square", "equilateral_triangle", "right_triangle",
    "isosceles_triangle", "rectangle",
})

EXPANSION_TAG = "需要扩展装"   # 内容策略 2.5 节: 用扩展片型必打标
FREE_TAG = "免费"              # 免费层标记 (COMMERCIAL_PLAN.md 免费 30)
FREE_CORE5_MIN_RATIO = 0.80    # 免费层 core-5 占比红线


def load_tiers(catalog_path):
    """读取片型目录, 返回 {type: tier}; tier 集合与白名单双重校验。"""
    catalog = json.loads(catalog_path.read_text(encoding="utf-8"))
    tiers = {t["type"]: t.get("tier") for t in catalog["tiles"]}

    catalog_core = {t for t, tier in tiers.items() if tier == "core"}
    if catalog_core != CORE5:
        print("[错误] 目录 tier=core 集合与核心五片型白名单不一致:", file=sys.stderr)
        print(f"  目录 core:  {sorted(catalog_core)}", file=sys.stderr)
        print(f"  白名单:     {sorted(CORE5)}", file=sys.stderr)
        print("  请核对 data/tile_catalog.json 的 tier 字段或本工具白名单。",
              file=sys.stderr)
        sys.exit(2)

    bad_tier = {t: tier for t, tier in tiers.items() if tier not in ("core", "expansion")}
    if bad_tier:
        print(f"[错误] 目录中存在非法 tier 值: {bad_tier}", file=sys.stderr)
        sys.exit(2)
    return tiers


def main():
    parser = argparse.ArgumentParser(description="核心五片型 (core-5) 覆盖率检查")
    parser.add_argument("models_dir", nargs="?", default=str(ROOT / "data" / "models"),
                        help="模型目录 (默认 data/models)")
    parser.add_argument("--catalog", default=str(ROOT / "data" / "tile_catalog.json"),
                        help="片型目录文件 (默认 data/tile_catalog.json)")
    parser.add_argument("--strict", action="store_true",
                        help="有 WARN 时以退出码 1 结束 (未来 CI 硬闸门模式)")
    args = parser.parse_args()

    models_dir = Path(args.models_dir)
    tiers = load_tiers(Path(args.catalog))

    model_files = sorted(models_dir.glob("*.json"))
    if not model_files:
        print(f"[错误] {models_dir} 下没有模型文件", file=sys.stderr)
        sys.exit(2)

    warnings = []
    core5_only = []          # [(id, difficulty)]
    expansion_using = []     # [(id, difficulty, sorted(exp_types), tagged)]
    expansion_freq = {}      # 扩展片型 -> 使用它的模型数
    free_models = []         # [(id, uses_expansion)]

    for path in model_files:
        try:
            model = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            print(f"[错误] 读取 {path.name} 失败: {exc}", file=sys.stderr)
            sys.exit(2)

        mid = model.get("id", path.stem)
        tags = model.get("tags", [])
        used = {t["type"] for t in model["final_assembly"]}

        unknown = used - set(tiers)
        if unknown:
            print(f"[错误] {mid} 使用了目录之外的片型: {sorted(unknown)}", file=sys.stderr)
            sys.exit(2)

        exp_types = sorted(t for t in used if tiers[t] == "expansion")
        tagged = EXPANSION_TAG in tags

        if exp_types:
            expansion_using.append((mid, model.get("difficulty"), exp_types, tagged))
            for t in exp_types:
                expansion_freq[t] = expansion_freq.get(t, 0) + 1
            if not tagged:
                warnings.append(
                    f"{mid} 使用了扩展片型 {','.join(exp_types)} 但缺少 \"{EXPANSION_TAG}\" 标签")
        else:
            core5_only.append((mid, model.get("difficulty")))
            if tagged:
                warnings.append(
                    f"{mid} 只用核心五片型却带着 \"{EXPANSION_TAG}\" 标签 (应移除)")

        if FREE_TAG in tags:
            free_models.append((mid, bool(exp_types)))
            if exp_types:
                warnings.append(
                    f"免费层模型 {mid} 使用了扩展片型 {','.join(exp_types)} "
                    f"(免费层应以 core-5 为主, 橱窗模型须控制在 20% 以内)")

    total = len(model_files)
    n_core = len(core5_only)
    ratio = n_core / total

    print("=" * 62)
    print(" 核心五片型 (core-5) 覆盖率报告")
    print("=" * 62)
    print(f"模型总数:          {total}")
    print(f"只用核心五片型:    {n_core}  ({ratio:.1%})")
    print(f"用到扩展片型:      {len(expansion_using)}  ({1 - ratio:.1%})")

    if expansion_freq:
        print("\n扩展片型使用频次 (模型数):")
        for t, n in sorted(expansion_freq.items(), key=lambda kv: (-kv[1], kv[0])):
            print(f"  {t:<22} {n}")

    if expansion_using:
        print(f"\n使用扩展片型的模型 ({len(expansion_using)} 个):")
        for mid, diff, exp_types, tagged in expansion_using:
            mark = "" if tagged else "   <-- 缺标签"
            print(f"  D{diff}  {mid:<28} {','.join(exp_types)}{mark}")

    print("\n免费层检查 (标签 \"免费\", 红线: core-5 占比 >= 80%):")
    if free_models:
        free_core = sum(1 for _, uses_exp in free_models if not uses_exp)
        free_ratio = free_core / len(free_models)
        print(f"  免费层模型 {len(free_models)} 个, 其中只用 core-5 的 {free_core} 个"
              f" ({free_ratio:.1%})")
        if free_ratio < FREE_CORE5_MIN_RATIO:
            warnings.append(
                f"免费层 core-5 占比 {free_ratio:.1%} 低于红线 "
                f"{FREE_CORE5_MIN_RATIO:.0%} (CONTENT_STRATEGY.md 2.5 节)")
    else:
        print("  尚无模型带 \"免费\" 标签 —— 免费 30 选品定稿后本节自动生效")

    if warnings:
        print(f"\n[WARN] 共 {len(warnings)} 条 (现阶段不作为 CI 硬失败):")
        for w in warnings:
            print(f"  WARN: {w}")
    else:
        print("\n标签一致性与免费层红线: 全部通过, 无警告")

    print("=" * 62)
    if warnings and args.strict:
        print("strict 模式: 存在 WARN, 以退出码 1 结束")
        sys.exit(1)
    sys.exit(0)


if __name__ == "__main__":
    main()
