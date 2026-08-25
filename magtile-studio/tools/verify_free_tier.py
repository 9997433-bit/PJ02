#!/usr/bin/env python3
"""免费层三端清单对齐核验 —— 防止免费标签与 starter 打包清单再度漂移。

背景 (docs/FREE_TIER_MANIFEST.md): 免费层曾出现两份各自为政的 30 模型
清单 —— 模型 JSON 的 "免费" 标签 (运行时解锁的事实来源) 与 Windows
打包子集清单 starter_models.txt (随包分发的投影), 30 个里只有 10 个
重合。裁决以 COMMERCIAL_PLAN.md §2.1 为准对齐后, 本工具把对齐结果
固化为三条断言:

  1. 数量: 带 "免费" 标签的模型恰好 FREE_COUNT (=30) 个;
  2. 片型: 免费层全部只用核心 9 片型 (core-9) —— 这是橱窗名额补选前
     的落地口径 (COMMERCIAL_PLAN §2.1 "选品状态: 已落地"), 严于
     CONTENT_STRATEGY §2.5 的 >=80% 红线; 付费墙上线后若补选橱窗
     模型, 本断言应放宽为红线口径 (见 FREE_TIER_MANIFEST.md 第 3 节);
  3. 对齐: starter_models.txt 与 "免费" 标签集合相等 (设计如此 ——
     清单是标签的打包投影), 不等时逐条列出两侧差异。

目录一致性双重校验与 check_core5_usage.py 相同: tile_catalog.json 中
tier=core 的集合必须与内置 core-9 白名单一致, 不一致按结构错误退出。

退出码:
  0  三条断言全部通过;
  1  存在断言失败 (清单漂移 / 数量不符 / 片型违规);
  2  结构错误 (目录 tier 与白名单不一致 / 清单文件非法 / 文件不可读)。

用法:
  python3 tools/verify_free_tier.py [--models-dir 目录] [--catalog 文件]
                                    [--manifest 清单]
所有参数默认取仓库内路径, 日常直接裸跑; 随 QA 流水线运行见
tests/run_full_qa.sh (可选关卡, MAGTILE_FREE_TIER_CHECK=1 开启)。
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

FREE_TAG = "免费"          # 运行时免费层标记 (COMMERCIAL_PLAN.md §2.1)
FREE_COUNT = 30            # 免费层定稿规模 (免费 30)

# 核心九片型白名单 (与 data/tile_catalog.json 的 tier=core 双重校验,
# 与 tools/check_core5_usage.py 保持同一份口径)
CORE9 = frozenset({
    "square", "equilateral_triangle", "right_triangle",
    "isosceles_triangle", "rectangle",
    "large_square", "window_square", "door_frame", "wheel_base",
})


def fail_structural(message: str) -> "sys.NoReturn":
    print(f"[错误] {message}", file=sys.stderr)
    sys.exit(2)


def load_tiers(catalog_path: Path) -> dict[str, str]:
    """读取片型目录 {type: tier}; tier=core 集合与白名单双重校验。"""
    try:
        catalog = json.loads(catalog_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        fail_structural(f"读取片型目录 {catalog_path} 失败: {exc}")
    tiers = {t["type"]: t.get("tier") for t in catalog["tiles"]}
    catalog_core = {t for t, tier in tiers.items() if tier == "core"}
    if catalog_core != CORE9:
        fail_structural(
            "目录 tier=core 集合与核心九片型白名单不一致:\n"
            f"  目录 core: {sorted(catalog_core)}\n"
            f"  白名单:    {sorted(CORE9)}\n"
            "  请核对 data/tile_catalog.json 的 tier 字段或本工具白名单。"
        )
    return tiers


def read_manifest(manifest_path: Path) -> list[str]:
    """读取 starter 清单 (与 tools/make_data_subset.py 同一套解析规则)。"""
    if not manifest_path.is_file():
        fail_structural(f"starter 清单不存在: {manifest_path}")
    ids: list[str] = []
    seen: set[str] = set()
    for line_no, raw in enumerate(
        manifest_path.read_text(encoding="utf-8").splitlines(), start=1
    ):
        entry = raw.split("#", 1)[0].strip()
        if not entry:
            continue
        if entry.endswith(".json"):
            fail_structural(
                f"{manifest_path}:{line_no}: 清单只写模型 id (不带 .json): {entry}")
        if entry in seen:
            fail_structural(f"{manifest_path}:{line_no}: 模型 id 重复: {entry}")
        seen.add(entry)
        ids.append(entry)
    return ids


def main() -> None:
    parser = argparse.ArgumentParser(
        description="免费层三端清单对齐核验 (免费标签 x starter 清单 x core-9)")
    parser.add_argument("--models-dir", type=Path,
                        default=ROOT / "data" / "models",
                        help="模型目录 (默认 data/models)")
    parser.add_argument("--catalog", type=Path,
                        default=ROOT / "data" / "tile_catalog.json",
                        help="片型目录文件 (默认 data/tile_catalog.json)")
    parser.add_argument("--manifest", type=Path,
                        default=ROOT / "platforms" / "windows" / "packaging"
                        / "starter_models.txt",
                        help="starter 打包清单 (默认 platforms/windows/"
                             "packaging/starter_models.txt)")
    args = parser.parse_args()

    tiers = load_tiers(args.catalog)

    model_files = sorted(args.models_dir.glob("*.json"))
    if not model_files:
        fail_structural(f"{args.models_dir} 下没有模型文件")

    free_ids: set[str] = set()
    free_expansion: dict[str, list[str]] = {}   # 免费模型 -> 使用的扩展片型
    for path in model_files:
        try:
            model = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            fail_structural(f"读取 {path.name} 失败: {exc}")
        if FREE_TAG not in model.get("tags", []):
            continue
        mid = model.get("id", path.stem)
        free_ids.add(mid)
        used = {t["type"] for t in model["final_assembly"]}
        unknown = used - set(tiers)
        if unknown:
            fail_structural(f"{mid} 使用了目录之外的片型: {sorted(unknown)}")
        exp = sorted(t for t in used if tiers[t] == "expansion")
        if exp:
            free_expansion[mid] = exp

    starter_ids = set(read_manifest(args.manifest))

    failures: list[str] = []

    # 断言 1: 免费标签数
    if len(free_ids) != FREE_COUNT:
        failures.append(
            f"免费标签数 {len(free_ids)} != {FREE_COUNT} "
            f"(COMMERCIAL_PLAN §2.1 免费 30 已定稿)")

    # 断言 2: 全 core-9 (橱窗补选前口径)
    for mid in sorted(free_expansion):
        failures.append(
            f"免费模型 {mid} 使用扩展片型 {','.join(free_expansion[mid])} "
            f"(现口径免费层 100% core-9; 补选橱窗模型时先改 "
            f"FREE_TIER_MANIFEST.md 决议再放宽本断言)")

    # 断言 3: starter 清单与免费标签集合相等
    only_starter = sorted(starter_ids - free_ids)
    only_tags = sorted(free_ids - starter_ids)
    for mid in only_starter:
        failures.append(f"仅在 starter 清单, 模型无 \"{FREE_TAG}\" 标签: {mid}")
    for mid in only_tags:
        failures.append(f"仅带 \"{FREE_TAG}\" 标签, 不在 starter 清单: {mid}")

    print("=" * 62)
    print(" 免费层三端清单对齐核验 (docs/FREE_TIER_MANIFEST.md)")
    print("=" * 62)
    print(f"扫描模型:            {len(model_files)}")
    print(f"带 \"{FREE_TAG}\" 标签:      {len(free_ids)}  (要求恰好 {FREE_COUNT})")
    print(f"免费层用扩展片型:    {len(free_expansion)}  (要求 0, 全 core-9)")
    print(f"starter 清单条目:    {len(starter_ids)}")
    print(f"两侧清单差异:        {len(only_starter) + len(only_tags)}  (要求 0)")

    if failures:
        print(f"\n[失败] 共 {len(failures)} 条:")
        for f in failures:
            print(f"  FAIL: {f}")
        print("=" * 62)
        print("清单已漂移 —— 换血流程见 CONTENT_STRATEGY §2.5.1 "
              "(改 tags 与 starter_models.txt 必须同步)。")
        sys.exit(1)

    print("\n三条断言全部通过: 免费标签 x starter 清单 x core-9 对齐。")
    print("=" * 62)
    sys.exit(0)


if __name__ == "__main__":
    main()
