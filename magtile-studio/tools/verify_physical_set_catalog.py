#!/usr/bin/env python3
"""实物磁力片套装目录校验 —— data/physical_set_catalog.json 结构守卫。

背景 (docs/PHYSICAL_SET_CATALOG.md): 用户勾选盒装套装 → 按片型求和
得到 tile_inventory → canBuild / inventory match 直接可用。本工具在
合入前断言目录 JSON 与片型目录一致、计数合法、套装 id 唯一、tier_scope
与片型分层不冲突。

退出码:
  0  全部断言通过;
  1  存在断言失败 (未知片型 / 负计数 / id 重复 / 合计不符 / tier 冲突);
  2  结构错误 (文件不可读 / JSON 非法 / 缺少必填字段)。

用法:
  python3 tools/verify_physical_set_catalog.py [--catalog 片型目录]
                                              [--physical 套装目录]
随 QA 流水线运行见 tests/run_full_qa.sh 与 tests/test_physical_set_catalog.sh。
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

VALID_TIER_SCOPES = frozenset({"core", "core+expansion"})


def fail_structural(message: str) -> "sys.NoReturn":
    print(f"[错误] {message}", file=sys.stderr)
    sys.exit(2)


def load_json(path: Path, label: str) -> dict:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except OSError as exc:
        fail_structural(f"读取{label} {path} 失败: {exc}")
    except json.JSONDecodeError as exc:
        fail_structural(f"{label} JSON 非法 ({path}): {exc}")


def load_tile_tiers(catalog_path: Path) -> dict[str, str]:
    catalog = load_json(catalog_path, "片型目录")
    tiles = catalog.get("tiles")
    if not isinstance(tiles, list):
        fail_structural(f"{catalog_path}: 缺少 tiles 数组")
    tiers: dict[str, str] = {}
    for entry in tiles:
        if not isinstance(entry, dict) or "type" not in entry:
            fail_structural(f"{catalog_path}: tiles 条目缺少 type")
        tiers[entry["type"]] = entry.get("tier", "")
    return tiers


def main() -> None:
    parser = argparse.ArgumentParser(
        description="实物磁力片套装目录校验 (physical_set_catalog x tile_catalog)")
    parser.add_argument("--catalog", type=Path,
                        default=ROOT / "data" / "tile_catalog.json",
                        help="片型目录 (默认 data/tile_catalog.json)")
    parser.add_argument("--physical", type=Path,
                        default=ROOT / "data" / "physical_set_catalog.json",
                        help="套装目录 (默认 data/physical_set_catalog.json)")
    args = parser.parse_args()

    tiers = load_tile_tiers(args.catalog)
    known_types = set(tiers)

    physical = load_json(args.physical, "套装目录")
    if "schema_version" not in physical:
        fail_structural(f"{args.physical}: 缺少 schema_version")
    sets = physical.get("sets")
    if not isinstance(sets, list) or not sets:
        fail_structural(f"{args.physical}: sets 必须为非空数组")

    failures: list[str] = []
    seen_ids: set[str] = set()

    for idx, entry in enumerate(sets):
        prefix = f"sets[{idx}]"
        if not isinstance(entry, dict):
            failures.append(f"{prefix}: 条目必须是对象")
            continue

        set_id = entry.get("id")
        if not isinstance(set_id, str) or not set_id.strip():
            failures.append(f"{prefix}: 缺少非空 id")
            continue
        if set_id in seen_ids:
            failures.append(f"套装 id 重复: {set_id}")
        seen_ids.add(set_id)
        prefix = f"sets[{set_id}]"

        for field in ("brand", "name_zh", "name_en", "piece_count_label",
                      "tier_scope", "pieces"):
            if field not in entry:
                failures.append(f"{prefix}: 缺少必填字段 {field}")

        tier_scope = entry.get("tier_scope")
        if tier_scope not in VALID_TIER_SCOPES:
            failures.append(
                f"{prefix}: tier_scope 非法 {tier_scope!r} "
                f"(允许 {sorted(VALID_TIER_SCOPES)})")

        pieces = entry.get("pieces")
        if not isinstance(pieces, dict) or not pieces:
            failures.append(f"{prefix}: pieces 必须为非空对象")
            continue

        label = entry.get("piece_count_label")
        if not isinstance(label, int) or label < 0:
            failures.append(f"{prefix}: piece_count_label 必须为非负整数")
            label = None

        total = 0
        for tile_type, count in pieces.items():
            if tile_type not in known_types:
                failures.append(
                    f"{prefix}: 未知片型 {tile_type!r} (不在 tile_catalog.json)")
                continue
            if not isinstance(count, int) or count < 0:
                failures.append(
                    f"{prefix}: {tile_type} 数量必须为非负整数, 实际 {count!r}")
                continue
            total += count
            piece_tier = tiers[tile_type]
            if tier_scope == "core" and piece_tier == "expansion":
                failures.append(
                    f"{prefix}: tier_scope=core 但含扩展片型 {tile_type}")
            if tier_scope == "core+expansion" and piece_tier not in (
                    "core", "expansion"):
                failures.append(
                    f"{prefix}: 片型 {tile_type} tier={piece_tier!r} 无法识别")

        if label is not None and total != label:
            failures.append(
                f"{prefix}: pieces 合计 {total} != piece_count_label {label}")

    print("=" * 62)
    print(" 实物套装目录校验 (docs/PHYSICAL_SET_CATALOG.md)")
    print("=" * 62)
    print(f"片型目录:     {args.catalog} ({len(known_types)} 种)")
    print(f"套装目录:     {args.physical} (schema_version={physical.get('schema_version')})")
    print(f"套装条目:     {len(sets)}  (要求 id 唯一)")

    if failures:
        print(f"\n[失败] 共 {len(failures)} 条:")
        for msg in failures:
            print(f"  FAIL: {msg}")
        print("=" * 62)
        sys.exit(1)

    print("\n全部断言通过: 片型存在 / 计数合法 / id 唯一 / 合计一致 / tier 一致。")
    print("=" * 62)
    sys.exit(0)


if __name__ == "__main__":
    main()
