#!/usr/bin/env python3
# =============================================================
# MagTile Studio - content_meta.series 全库回填
#
# 依据 data/content_series_map.json (底稿: docs/reports/CONTENT_GAP_AUDIT.md
# 附录 A 的 250 模型逐一归类) 把策略主题写回每个模型 JSON:
#
#   矩阵内 (13 主题):  content_meta.series = <snake_case slug>
#   矩阵外 (74 个):    content_meta.series = null
#                      content_meta.matrix_bucket = <子类桶 slug>
#
# 只增改 content_meta.series 与 content_meta.matrix_bucket 两个键,
# 其余 content_meta 字段 (structural_signature / physical_verified 等)
# 与模型其他部分一律原样保留; 序列化格式与库内一致 (indent=2, 非 ASCII
# 原样输出, 结尾换行), 重复执行幂等。
#
# 写入后自检: 全库每个模型必须 series 非空 或 matrix_bucket 非空,
# 且映射表与 data/models/ 的 id 集合严格一致 (无缺漏、无多余)。
#
# 用法: tools/backfill_content_series.py [--root <repo_root>] [--dry-run]
# 退出码: 0 = 回填并自检通过, 1 = 映射缺漏/自检失败, 2 = 用法/环境错误
# =============================================================

import argparse
import json
import sys
from collections import Counter
from pathlib import Path

MAP_RELPATH = Path("data/content_series_map.json")
MODELS_RELPATH = Path("data/models")


def load_map(root):
    map_path = root / MAP_RELPATH
    if not map_path.is_file():
        print(f"错误: 找不到映射表 {map_path}", file=sys.stderr)
        return None
    mapping = json.loads(map_path.read_text(encoding="utf-8"))
    valid_series = set(mapping["series"])
    valid_buckets = set(mapping["off_matrix_buckets"])
    for mid, entry in mapping["models"].items():
        series = entry.get("series")
        bucket = entry.get("matrix_bucket")
        if series is not None and series not in valid_series:
            print(f"错误: {mid} 的 series 值 {series!r} 不在 13 主题词表内",
                  file=sys.stderr)
            return None
        if series is None and bucket not in valid_buckets:
            print(f"错误: 矩阵外模型 {mid} 的 matrix_bucket 值 {bucket!r} "
                  f"不在子类桶词表内", file=sys.stderr)
            return None
        if series is not None and bucket is not None:
            print(f"错误: {mid} 同时声明 series 与 matrix_bucket", file=sys.stderr)
            return None
    return mapping


def rebuilt_content_meta(old_meta, entry):
    """series / matrix_bucket 置于 content_meta 首位 (与 CONTENT_STRATEGY.md
    5.1 节 schema v2 字段顺序一致), 其余字段按原顺序保留。"""
    meta = {"series": entry.get("series")}
    if entry.get("series") is None:
        meta["matrix_bucket"] = entry["matrix_bucket"]
    for key, value in old_meta.items():
        if key not in ("series", "matrix_bucket"):
            meta[key] = value
    return meta


def main(argv):
    parser = argparse.ArgumentParser(description="content_meta.series 全库回填")
    parser.add_argument("--root", default=None,
                        help="仓库根目录 (默认: 本脚本上一级)")
    parser.add_argument("--dry-run", action="store_true",
                        help="只报告将发生的改动, 不写文件")
    args = parser.parse_args(argv[1:])

    root = Path(args.root) if args.root else Path(__file__).resolve().parent.parent
    mapping = load_map(root)
    if mapping is None:
        return 2
    assignments = mapping["models"]

    model_files = sorted((root / MODELS_RELPATH).glob("*.json"))
    if not model_files:
        print(f"错误: {root / MODELS_RELPATH} 下没有模型 JSON", file=sys.stderr)
        return 2

    disk_ids = {p.stem for p in model_files}
    missing = disk_ids - set(assignments)
    orphaned = set(assignments) - disk_ids
    if missing or orphaned:
        for mid in sorted(missing):
            print(f"[FAIL] 模型 {mid} 不在映射表内, 无法回填")
        for mid in sorted(orphaned):
            print(f"[FAIL] 映射表条目 {mid} 在 data/models/ 中不存在")
        return 1

    changed, unchanged = 0, 0
    series_counts = Counter()
    bucket_counts = Counter()
    for path in model_files:
        raw = path.read_text(encoding="utf-8")
        model = json.loads(raw)
        entry = assignments[path.stem]
        model["content_meta"] = rebuilt_content_meta(
            model.get("content_meta", {}), entry)
        if entry.get("series") is not None:
            series_counts[entry["series"]] += 1
        else:
            bucket_counts[entry["matrix_bucket"]] += 1
        rendered = json.dumps(model, ensure_ascii=False, indent=2) + "\n"
        if rendered == raw:
            unchanged += 1
            continue
        changed += 1
        if args.dry_run:
            print(f"  [dry-run] 将回填 {path.name}")
        else:
            path.write_text(rendered, encoding="utf-8")

    print("==============================================================")
    print(f" content_meta.series 回填: 共 {len(model_files)} 个模型, "
          f"写入 {changed} 个, 已是目标状态 {unchanged} 个"
          f"{' (dry-run 未落盘)' if args.dry_run else ''}")
    print(" 矩阵内 (13 主题):")
    for slug, count in sorted(series_counts.items(), key=lambda kv: (-kv[1], kv[0])):
        print(f"   {slug}: {count}")
    print(f" 矩阵外 (series=null, 共 {sum(bucket_counts.values())}):")
    for slug, count in sorted(bucket_counts.items(), key=lambda kv: (-kv[1], kv[0])):
        print(f"   {slug}: {count}")

    # ---- 自检: 全库覆盖率必须 100% --------------------------------------
    if args.dry_run:
        print(" 自检跳过 (dry-run)")
        return 0
    uncovered = []
    for path in model_files:
        meta = json.loads(path.read_text(encoding="utf-8")).get("content_meta", {})
        if meta.get("series") is None and meta.get("matrix_bucket") is None:
            uncovered.append(path.stem)
    if uncovered:
        print(f"[FAIL] {len(uncovered)} 个模型回填后仍无 series/matrix_bucket: "
              f"{', '.join(uncovered[:10])}")
        return 1
    print(f" 自检: {len(model_files)}/{len(model_files)} 全部具备 "
          f"series 或 matrix_bucket")
    print("==============================================================")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
