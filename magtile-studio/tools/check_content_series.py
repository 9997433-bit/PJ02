#!/usr/bin/env python3
"""内容系列归类机检 —— content_meta.series / matrix_bucket 全库核验。

CONTENT_GAP_AUDIT.md §7.3 「series 回填 + 矩阵进度机检化」的机检落地:
缺口审计从人工逐模型归类 (附录 A) 升级为可复跑的常规指标, 前提是
全库归类字段回填且词值受控。本工具核对三条规则:

  1. 归类齐全: 每个模型必须带 content_meta.series (13 策略主题之一,
     CONTENT_STRATEGY.md §2.2) 或 content_meta.matrix_bucket (矩阵外桶,
     审计第 6 节的治理口径), 二者恰好其一 —— 同时缺失或同时携带都算
     归类问题 (显式写 null 视同缺席, 回填工具对矩阵外模型即写
     series=null + matrix_bucket);
  2. 词值受控: series / matrix_bucket 取值必须落在
     data/content_series_map.json 词表内 (series 取 series 节的
     13 个主题词值, matrix_bucket 取 off_matrix_buckets 节的桶词值);
     中文主题名 / 词值写错字段等常见回填笔误会给出定向修复提示;
  3. 矩阵计数: 输出 13 主题 × D1–D5 现状计数与矩阵外桶计数, 供对照
     CONTENT_GAP_AUDIT.md 第 3 节复核 (520 目标对照表由
     tools/update_model_catalog.py --matrix-report 负责, 不在此重复)。

series 回填 (tools/backfill_content_series.py, 底稿见
CONTENT_GAP_AUDIT.md 附录 A) 已全库落地 —— 本工具以 --strict 作为
后续内容批次的硬闸门 (tests/run_full_qa.sh 可选关卡,
MAGTILE_SERIES_CHECK=1 开启), 新增模型漏归类 / 词值走样即失败;
非 strict 模式只报告不阻断。

退出码:
  0  检查完成 (可能有 WARN —— 非 strict 模式下缺失/非法不作为硬失败);
  1  --strict 模式下存在缺失/非法归类;
  2  结构错误 (词表/模型文件不可读, 词表矩阵主题数 != 13)。

用法:
  python3 tools/check_content_series.py [模型目录] [--map 词表文件] [--strict]
"""

import argparse
import json
import sys
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

MATRIX_THEME_COUNT = 13     # CONTENT_STRATEGY.md §2.2 的策略主题数
MISSING_LIST_LIMIT = 20     # 缺失归类的逐条列表上限 (回填前全库缺失, 防刷屏)


def _disp_width(text):
    """终端显示宽度 (东亚宽字符计 2 列), 用于矩阵表对齐。"""
    return sum(2 if unicodedata.east_asian_width(ch) in ("W", "F") else 1
               for ch in text)


def _pad(text, width):
    return text + " " * (width - _disp_width(text))


def load_allowlists(map_path):
    """读取词表, 返回 (series 词值表, 矩阵外桶词值表, 修复提示索引)。

    词表的 series 节 (词值 -> {display_name_zh, matrix_bucket: null}) 定义
    content_meta.series 的 13 个合法取值, off_matrix_buckets 节 (词值 ->
    {display_name_zh}) 定义 content_meta.matrix_bucket 的合法桶词值
    (权威 schema 见 data/content_series_map.README.md)。
    修复提示索引把中文名映射到应写的字段与词值, 用于定位常见回填笔误。
    """
    try:
        data = json.loads(map_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"[错误] 读取词表 {map_path} 失败: {exc}", file=sys.stderr)
        sys.exit(2)

    series_table = data.get("series")
    bucket_table = data.get("off_matrix_buckets")
    if not isinstance(series_table, dict) or not series_table:
        print(f"[错误] 词表 {map_path} 缺少非空的 series 对象",
              file=sys.stderr)
        sys.exit(2)
    if not isinstance(bucket_table, dict) or not bucket_table:
        print(f"[错误] 词表 {map_path} 缺少非空的 off_matrix_buckets 对象",
              file=sys.stderr)
        sys.exit(2)

    series_allow = {slug: entry["display_name_zh"]
                    for slug, entry in series_table.items()}
    bucket_allow = {slug: entry["display_name_zh"]
                    for slug, entry in bucket_table.items()}
    if len(set(series_allow.values())) != len(series_allow) \
            or len(set(bucket_allow.values())) != len(bucket_allow):
        print("[错误] 词表存在重复中文名 (series / off_matrix_buckets "
              "的 display_name_zh 必须各自唯一)", file=sys.stderr)
        sys.exit(2)
    overlap = set(series_allow) & set(bucket_allow)
    if overlap:
        print(f"[错误] 词值同时出现在 series 与 off_matrix_buckets: "
              f"{sorted(overlap)}", file=sys.stderr)
        sys.exit(2)
    if len(series_allow) != MATRIX_THEME_COUNT:
        print(f"[错误] 词表矩阵主题数 {len(series_allow)} != "
              f"{MATRIX_THEME_COUNT} (series 节应恰好覆盖"
              f" CONTENT_STRATEGY.md §2.2 的 13 主题): "
              f"{sorted(series_allow)}", file=sys.stderr)
        sys.exit(2)

    zh_hint = {name: ("series", slug) for slug, name in series_allow.items()}
    zh_hint.update((name, ("matrix_bucket", slug))
                   for slug, name in bucket_allow.items())
    return series_allow, bucket_allow, zh_hint


def diagnose(field, value, series_allow, bucket_allow, zh_hint):
    """非法词值 -> 定向修复提示 (笔误多为字段写反或误用中文主题名)。"""
    if field == "series" and value in bucket_allow:
        return f"\"{value}\" 是矩阵外桶词值, 应写入 content_meta.matrix_bucket"
    if field == "matrix_bucket" and value in series_allow:
        return f"\"{value}\" 是 13 主题词值, 应写入 content_meta.series"
    if value in zh_hint:
        target_field, slug = zh_hint[value]
        return f"中文名应替换为词值: {target_field} = \"{slug}\""
    return "词表中不存在该词值"


def main():
    parser = argparse.ArgumentParser(
        description="内容系列归类机检 (content_meta.series / matrix_bucket)")
    parser.add_argument("models_dir", nargs="?",
                        default=str(ROOT / "data" / "models"),
                        help="模型目录 (默认 data/models)")
    parser.add_argument("--map",
                        default=str(ROOT / "data" / "content_series_map.json"),
                        help="系列词表文件 (默认 data/content_series_map.json)")
    parser.add_argument("--strict", action="store_true",
                        help="有缺失/非法归类时以退出码 1 结束 (回填后的 CI 硬闸门)")
    args = parser.parse_args()

    series_allow, bucket_allow, zh_hint = load_allowlists(Path(args.map))

    models_dir = Path(args.models_dir)
    model_files = sorted(models_dir.glob("*.json"))
    if not model_files:
        print(f"[错误] {models_dir} 下没有模型文件", file=sys.stderr)
        sys.exit(2)

    matrix = {slug: [0] * 5 for slug in series_allow}   # slug -> D1..D5 计数
    bucket_counts = {b: 0 for b in bucket_allow}
    missing = []      # 未归类模型 id
    problems = []     # 非法归类 (含同时携带/难度越界), 逐条打印

    for path in model_files:
        try:
            model = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            print(f"[错误] 读取 {path.name} 失败: {exc}", file=sys.stderr)
            sys.exit(2)

        mid = model.get("id", path.stem)
        meta = model.get("content_meta") or {}
        series = meta.get("series")
        bucket = meta.get("matrix_bucket")

        if series is None and bucket is None:
            missing.append(mid)
            continue
        if series is not None and bucket is not None:
            problems.append(f"{mid} 同时携带 series=\"{series}\" 与 "
                            f"matrix_bucket=\"{bucket}\" (二者应恰好其一)")
            continue

        if series is not None:
            if series not in series_allow:
                problems.append(f"{mid} series=\"{series}\" 非法: "
                                + diagnose("series", series,
                                           series_allow, bucket_allow, zh_hint))
                continue
            diff = model.get("difficulty")
            if isinstance(diff, int) and 1 <= diff <= 5:
                matrix[series][diff - 1] += 1
            else:
                problems.append(f"{mid} series=\"{series}\" 但难度越界 "
                                f"(difficulty={diff!r}, 应为 1–5), 不计入矩阵")
        else:
            if bucket not in bucket_allow:
                problems.append(f"{mid} matrix_bucket=\"{bucket}\" 非法: "
                                + diagnose("matrix_bucket", bucket,
                                           series_allow, bucket_allow, zh_hint))
                continue
            bucket_counts[bucket] += 1

    total = len(model_files)
    in_matrix = sum(sum(row) for row in matrix.values())
    off_matrix = sum(bucket_counts.values())

    print("=" * 62)
    print(" 内容系列归类机检 (content_meta.series / matrix_bucket)")
    print("=" * 62)
    print(f"词表:              {args.map}")
    print(f"                   ({len(series_allow)} 个矩阵主题 + "
          f"{len(bucket_allow)} 个矩阵外桶)")
    print(f"模型总数:          {total}")
    print(f"矩阵内 (series):   {in_matrix}")
    print(f"矩阵外 (bucket):   {off_matrix}")
    print(f"缺失归类:          {len(missing)}")
    print(f"词值非法:          {len(problems)}")

    print("\n主题 × 难度矩阵计数 (现状; 520 目标对照见 CONTENT_GAP_AUDIT.md 第 3 节):")
    name_width = max(_disp_width(f"{name} {slug}")
                     for slug, name in series_allow.items())
    header = _pad("  主题", name_width + 2) + "   D1   D2   D3   D4   D5  合计"
    print(header)
    for slug, name in series_allow.items():
        row = matrix[slug]
        cells = "".join(f"{n:>5}" for n in row)
        print(_pad(f"  {name} {slug}", name_width + 2) + cells
              + f"{sum(row):>6}")
    col_sums = [sum(matrix[slug][d] for slug in series_allow) for d in range(5)]
    print(_pad("  矩阵内小计", name_width + 2)
          + "".join(f"{n:>5}" for n in col_sums) + f"{in_matrix:>6}")

    print("\n矩阵外桶计数:")
    for bucket, name in bucket_allow.items():
        print(_pad(f"  {name} {bucket}", name_width + 2)
              + f"{bucket_counts[bucket]:>5}")
    print(_pad("  矩阵外小计", name_width + 2) + f"{off_matrix:>5}")

    warn_total = len(missing) + len(problems)
    if missing:
        shown = missing[:MISSING_LIST_LIMIT]
        print(f"\n[WARN] 缺失归类 {len(missing)} 个 (未带 content_meta.series "
              f"/ matrix_bucket, 回填底稿见 CONTENT_GAP_AUDIT.md 附录 A):")
        for mid in shown:
            print(f"  WARN: {mid} 缺失归类")
        if len(missing) > len(shown):
            print(f"  ... 其余 {len(missing) - len(shown)} 个从略")
    if problems:
        print(f"\n[WARN] 词值非法 {len(problems)} 条:")
        for p in problems:
            print(f"  WARN: {p}")
    if not warn_total:
        print("\n归类齐全且词值全部合法, 无警告")

    print("=" * 62)
    if warn_total and args.strict:
        print(f"strict 模式: 缺失 {len(missing)} + 非法 {len(problems)}, "
              f"以退出码 1 结束")
        sys.exit(1)
    sys.exit(0)


if __name__ == "__main__":
    main()
