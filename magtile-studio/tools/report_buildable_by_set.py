#!/usr/bin/env python3
"""套装 → 模型可搭建率报告 (model match report)。

给定一个或多个实物套装 id, 合并 BOM 后对照全库 250 个模型 BOM,
输出能搭数量、按难度的分布, 以及缺片 blocker Top 10 (片型维度)。

退出码: 0 报告完成; 2 结构/参数错误。

用法:
  python3 tools/report_buildable_by_set.py standard_102
  python3 tools/report_buildable_by_set.py standard_102 deluxe_198
  python3 tools/report_buildable_by_set.py --json standard_102
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
MODELS = DATA / "models"
PHYSICAL = DATA / "physical_set_catalog.json"
CATALOG = DATA / "model_catalog.json"
TILE_CATALOG = DATA / "tile_catalog.json"


def fail(msg: str, code: int = 2) -> "sys.NoReturn":
    print(f"[错误] {msg}", file=sys.stderr)
    sys.exit(code)


def load_json(path: Path) -> dict:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except OSError as exc:
        fail(f"读取 {path} 失败: {exc}")
    except json.JSONDecodeError as exc:
        fail(f"JSON 非法 ({path}): {exc}")


def tile_names() -> dict[str, str]:
    catalog = load_json(TILE_CATALOG)
    names: dict[str, str] = {}
    for entry in catalog.get("tiles", []):
        if isinstance(entry, dict) and "type" in entry:
            names[entry["type"]] = entry.get("name_zh") or entry["type"]
    return names


def load_physical_sets() -> dict[str, dict]:
    physical = load_json(PHYSICAL)
    sets = physical.get("sets")
    if not isinstance(sets, list):
        fail(f"{PHYSICAL}: sets 必须为非空数组")
    by_id: dict[str, dict] = {}
    for entry in sets:
        if not isinstance(entry, dict) or "id" not in entry:
            fail(f"{PHYSICAL}: 套装条目缺少 id")
        by_id[entry["id"]] = entry
    return by_id


def merge_inventory(set_ids: list[str], by_id: dict[str, dict]) -> dict[str, int]:
    inventory: dict[str, int] = {}
    for set_id in set_ids:
        entry = by_id.get(set_id)
        if entry is None:
            fail(f"未知套装 id: {set_id}")
        pieces = entry.get("pieces") or entry.get("bom")
        if not isinstance(pieces, dict):
            fail(f"套装 {set_id} 缺少 pieces/bom")
        for tile_type, count in pieces.items():
            if not isinstance(count, int) or count < 0:
                fail(f"套装 {set_id} 片型 {tile_type} 数量非法")
            inventory[tile_type] = inventory.get(tile_type, 0) + count
    return inventory


def model_bom(model: dict) -> dict[str, int]:
    counts: dict[str, int] = {}
    for tile in model.get("final_assembly", []):
        if not isinstance(tile, dict):
            continue
        t = tile.get("type")
        if isinstance(t, str):
            counts[t] = counts.get(t, 0) + 1
    return counts


def missing_pieces(inventory: dict[str, int], bom: dict[str, int]) -> dict[str, int]:
    missing: dict[str, int] = {}
    for tile_type, needed in bom.items():
        owned = inventory.get(tile_type, 0)
        if owned < needed:
            missing[tile_type] = needed - owned
    return missing


def load_model_entries() -> list[dict]:
    catalog = load_json(CATALOG)
    models = catalog.get("models")
    if not isinstance(models, list):
        fail(f"{CATALOG}: models 必须为非空数组")
    return models


def analyze(set_ids: list[str]) -> dict:
    by_id = load_physical_sets()
    inventory = merge_inventory(set_ids, by_id)
    names = tile_names()

    entries = load_model_entries()
    buildable_by_diff: Counter[int] = Counter()
    short_by_diff: Counter[int] = Counter()
    blocker_models: Counter[str] = Counter()
    blocker_pieces: Counter[str] = Counter()
    buildable_ids: list[str] = []
    load_failures: list[str] = []

    for entry in entries:
        mid = entry.get("id", "")
        model_path = MODELS / f"{mid}.json"
        if not model_path.is_file():
            file_rel = entry.get("file", "")
            if file_rel:
                model_path = DATA / file_rel
        try:
            model = load_json(model_path)
        except SystemExit:
            load_failures.append(mid)
            continue

        diff = int(model.get("difficulty", entry.get("difficulty", 0)))
        bom = model_bom(model)
        missing = missing_pieces(inventory, bom)
        if not missing:
            buildable_by_diff[diff] += 1
            buildable_ids.append(mid)
        else:
            short_by_diff[diff] += 1
            for tile_type in missing:
                blocker_models[tile_type] += 1
                blocker_pieces[tile_type] += missing[tile_type]

    total = len(entries)
    buildable = len(buildable_ids)
    top_blockers = blocker_models.most_common(10)

    return {
        "set_ids": set_ids,
        "inventory_total_pieces": sum(inventory.values()),
        "inventory": inventory,
        "model_total": total,
        "buildable_count": buildable,
        "buildable_pct": round(100.0 * buildable / total, 1) if total else 0.0,
        "buildable_by_difficulty": {str(d): buildable_by_diff.get(d, 0)
                                    for d in range(1, 6)},
        "short_by_difficulty": {str(d): short_by_diff.get(d, 0)
                                for d in range(1, 6)},
        "top_missing_blockers": [
            {
                "tile_type": t,
                "name_zh": names.get(t, t),
                "models_blocked": n,
                "pieces_short_total": blocker_pieces[t],
            }
            for t, n in top_blockers
        ],
        "load_failures": load_failures,
    }


def print_report(report: dict) -> None:
    names = tile_names()
    print("=" * 62)
    print(" 套装 → 模型可搭建率报告 (report_buildable_by_set)")
    print("=" * 62)
    print(f"套装:         {', '.join(report['set_ids'])}")
    print(f"合并库存:     {report['inventory_total_pieces']} 片 "
          f"({len(report['inventory'])} 种片型)")
    print(f"模型总数:     {report['model_total']}")
    print(f"能搭:         {report['buildable_count']} "
          f"({report['buildable_pct']}%)")
    if report["load_failures"]:
        print(f"[警告] 跳过 {len(report['load_failures'])} 个模型加载失败")

    print("\n按难度 (能搭 / 还差):")
    for d in range(1, 6):
        ok = report["buildable_by_difficulty"].get(str(d), 0)
        short = report["short_by_difficulty"].get(str(d), 0)
        stars = "★" * d
        print(f"  D{d} {stars:5s}  能搭 {ok:3d}  /  还差 {short:3d}")

    print("\n缺片 blocker Top 10 (片型 → 阻断模型数 / 累计缺片):")
    if not report["top_missing_blockers"]:
        print("  (无 —— 全库可搭)")
    else:
        for i, row in enumerate(report["top_missing_blockers"], 1):
            print(f"  {i:2d}. {row['name_zh']} ({row['tile_type']})"
                  f"  阻断 {row['models_blocked']} 个模型"
                  f"  累计缺 {row['pieces_short_total']} 片")

    print("=" * 62)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="实物套装 BOM 对照全库模型的可搭建率报告")
    parser.add_argument("set_ids", nargs="+", help="套装 id (可多个, BOM 求和)")
    parser.add_argument("--json", action="store_true", help="机器可读 JSON 输出")
    args = parser.parse_args()

    report = analyze(args.set_ids)
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print_report(report)
    sys.exit(0)


if __name__ == "__main__":
    main()
