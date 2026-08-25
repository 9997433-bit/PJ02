#!/usr/bin/env python3
"""D4+ 实物待复核排产队列导出 (CSV / Markdown, 按风险分降序)。

背景: 实物复核排产要同时看三份产物 —— list_physical_pending (哪些还没搭) /
PHYSICAL_RISK_REPORT.json (哪些高危, 先验谁) / physical_family_pack (哪些是
结构重复, 可申请缓建)。排产人/QA 真正需要的是**一张合并单表**: D4+ 待复核
全集, 按风险分降序, 每行标注「必搭 / 可缓建」及依据, 可直接贴进工单或
表格软件。本工具只做合并与导出, **不重算任何口径** (单一来源纪律):

  待复核判定   import tools/list_physical_pending.classify
               (content_meta.physical_verified 或 旁车验证文件哈希一致);
  风险分/档    读 docs/reports/PHYSICAL_RISK_REPORT.json
  /L2 标记     (tools/physical_risk_report.py --json 存盘产物, 接口约定
               BUILD_VERIFICATION.md 2.1 节) —— 报告缺失即退出码 2,
               报告快照与当前模型库不一致时逐条告警提示重新生成;
  必搭/可缓建  import tools/physical_family_pack 同参数聚类:
               必搭 = 上架抽样包成员 ∪ 多成员族代表 ∪ 单模型族
               (与 PHYSICAL_FAMILY_PACK.md 第 5 节 compute_reduction 同口径),
               可缓建 = 其余成员 (同族代表兜底, 须策展签核);
  抽样包成员   import tools/physical_sample_pack.select_sample
               (S1/S2/S3 确定性规则), 耗时预算同 TIME_BUDGET_MIN。

纪律: 可缓建只是排产顺序与人手预算的工程估算 —— **不豁免**
`tools/list_physical_pending.py --fail-on-pending` 的 D4+ 全集清零终防线;
缓建成员最终仍须实搭或由策展按族级抽检政策书面豁免 (PHYSICAL_FAMILY_PACK.md
第 5 节纪律)。模型库 / 复核状态 / 风险报告变化后重新生成, 导出件勿手改。

用法:
    tools/export_physical_review_queue.py [models_dir] [选项]
        models_dir            模型目录 (默认: 仓库 data/models)
        --risk-report FILE    风险报告 JSON (默认
                              docs/reports/PHYSICAL_RISK_REPORT.json)
        --catalog FILE        模型库目录 (名称/主题来源,
                              默认 models_dir/../model_catalog.json)
        --verification-dir D  旁车验证记录目录 (默认 models_dir/../verification)
        --threshold X         结构族聚类阈值, 透传 physical_family_pack
                              (默认 0.67; 改动即改变必搭/缓建划分)
        --csv FILE            导出 CSV (docs/reports/PHYSICAL_REVIEW_QUEUE.csv
                              即由此生成; 表格软件/工单系统用)
        --markdown FILE       导出 Markdown (docs/reports/PHYSICAL_REVIEW_QUEUE.md
                              即由此生成; 评审/打印用)
        --json                机器可读 JSON 输出
        不带 --csv/--markdown/--json 时打印桌边速览文本表

退出码: 0 = 导出完成 / 2 = 数据错误 (模型目录或风险报告缺失/不可解析)
"""

import argparse
import csv
import json
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from list_physical_pending import classify  # noqa: E402  (复核判定单一来源)
from physical_family_pack import (  # noqa: E402  (族划分/风险探测单一来源)
    DEFAULT_THRESHOLD, build_families, cluster_families, load_json,
    load_risk_scores, theme_tag_set)
from physical_sample_pack import TIME_BUDGET_MIN, select_sample  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_RISK_REPORT = "docs/reports/PHYSICAL_RISK_REPORT.json"
MIN_DIFFICULTY = 4  # 队列口径固定 D4+ (与 compute_reduction / 终防线一致)

CSV_COLUMNS = ("rank", "model_id", "name", "difficulty", "risk_score",
               "risk_band", "l2_flags", "build_class", "build_reason",
               "family_id", "family_size", "family_representative",
               "in_sample_pack", "sample_pack_layer", "pieces", "steps",
               "est_minutes")


def load_report_rows(path: Path):
    """读风险报告 JSON, 返回 {model_id: 报告行}; 形态不认识即退出码 2。"""
    data = load_json(path)
    rows = data.get("models") if isinstance(data, dict) else None
    if not isinstance(rows, list):
        print(f"错误: {path} 不是 physical_risk_report --json 产物 "
              "(缺 models[] 逐模型数组, 接口约定见 BUILD_VERIFICATION.md 2.1 节)",
              file=sys.stderr)
        sys.exit(2)
    out = {}
    for row in rows:
        if isinstance(row, dict) and (row.get("model_id") or row.get("id")):
            out[str(row.get("model_id") or row.get("id"))] = row
    return out


def build_queue(models, names, verified, families, sample_layers, report_rows):
    """装配队列行 + 快照一致性告警; 返回 (rows, warnings)。"""
    fam_of = {m["id"]: (fam, m) for fam in families for m in fam["members"]}
    warnings = []

    lib_ids = {m["id"] for m in models}
    stale = sorted(lib_ids - set(report_rows))
    extra = sorted(set(report_rows) - lib_ids)
    if stale:
        warnings.append("风险报告缺 {} 个当前库模型 (如 {}), 报告已过期, "
                        "请先重新生成".format(len(stale), ", ".join(stale[:5])))
    if extra:
        warnings.append("风险报告含 {} 个库中不存在的模型 (如 {}), 报告已过期, "
                        "请先重新生成".format(len(extra), ", ".join(extra[:5])))

    rows = []
    for model in models:
        mid = model["id"]
        if int(model.get("difficulty", 0)) < MIN_DIFFICULTY:
            continue
        ok, _via, _w = verified[mid]
        rep_row = report_rows.get(mid, {})
        if rep_row and bool(rep_row.get("physical_verified")) != ok:
            warnings.append(f"{mid}: 风险报告快照的复核状态与当前模型库不一致, "
                            "请重新生成风险报告")
        if ok:
            continue

        fam, member = fam_of[mid]
        must = member["is_representative"] or member["in_sample_pack"]
        reason_parts = []
        if member["in_sample_pack"]:
            reason_parts.append("上架抽样包")
        if member["is_representative"]:
            reason_parts.append("族代表" if fam["size"] > 1 else "单模型族")
        difficulty = int(model["difficulty"])
        score = rep_row.get("risk_score")
        if not isinstance(score, (int, float)) or isinstance(score, bool):
            warnings.append(f"{mid}: 风险报告里没有该模型的 risk_score, "
                            "改用族划分用的垫底启发式分排序")
            score, band = member["risk_score"], "—"
        else:
            score, band = float(score), rep_row.get("risk_band") or "—"
        rows.append({
            "model_id": mid,
            "name": names.get(mid, rep_row.get("name", mid)),
            "difficulty": difficulty,
            "risk_score": score,
            "risk_band": band,
            "l2_flags": list(rep_row.get("flags") or []),
            "build_class": "must_build" if must else "deferrable",
            "build_reason": "+".join(reason_parts) if must
                            else f"同族代表 {fam['representative']} 兜底",
            "family_id": fam["family_id"],
            "family_size": fam["size"],
            "family_representative": fam["representative"],
            "in_sample_pack": member["in_sample_pack"],
            "sample_pack_layer": sample_layers.get(mid, ""),
            "pieces": member["total_pieces"],
            "steps": member["steps"],
            "est_minutes": TIME_BUDGET_MIN.get(difficulty, 120),
        })

    rows.sort(key=lambda r: (-r["risk_score"], -r["difficulty"], r["model_id"]))
    for rank, row in enumerate(rows, 1):
        row["rank"] = rank
    return rows, warnings


def summarize(rows):
    must = [r for r in rows if r["build_class"] == "must_build"]
    defer = [r for r in rows if r["build_class"] == "deferrable"]
    minutes = lambda rs: sum(r["est_minutes"] for r in rs)  # noqa: E731
    return {
        "scope": f"D{MIN_DIFFICULTY}+ 待实物复核 (与 list_physical_pending 同一判定)",
        "pending_total": len(rows),
        "must_build_count": len(must),
        "must_build_minutes": minutes(must),
        "deferrable_count": len(defer),
        "deferrable_minutes": minutes(defer),
        "total_minutes": minutes(rows),
    }


# ---------------------------------------------------------------- 三种导出

def write_csv(rows, path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=CSV_COLUMNS)
        writer.writeheader()
        for row in rows:
            flat = dict(row)
            flat["l2_flags"] = "|".join(row["l2_flags"])
            flat["in_sample_pack"] = "true" if row["in_sample_pack"] else "false"
            writer.writerow({k: flat[k] for k in CSV_COLUMNS})
    print(f"已生成: {path}")


def render_markdown(rows, summary, warnings, risk_source, threshold,
                    csv_target: str) -> str:
    s = summary
    lines = []
    a = lines.append
    a("# D4+ 实物待复核排产队列 (Physical Review Queue)")
    a("")
    a(f"- 生成日期: {date.today().isoformat()}")
    a("- 生成工具: `tools/export_physical_review_queue.py --markdown "
      "docs/reports/PHYSICAL_REVIEW_QUEUE.md` (CSV 版: `--csv "
      f"{csv_target}`) —— 模型库 / 复核状态 / 风险报告变化后**重新生成**, "
      "勿手改")
    a(f"- 数据来源 (单一来源, 本表不重算): 待复核判定与 "
      "`tools/list_physical_pending.py` 同源 (同一 classify 函数); "
      f"风险分/风险档/L2 标记 {risk_source}; 必搭/可缓建与 "
      f"`tools/physical_family_pack.py` 同参数聚类 (阈值 {threshold}); "
      "抽样包成员与 `tools/physical_sample_pack.py` 同源 (同一 select_sample)")
    a("- 排序: 风险分降序 (同分: 难度降序 > id 升序); **必搭 = 上架抽样包 ∪ "
      "多成员族代表 ∪ 单模型族**, 可缓建 = 其余同族成员 (须策展签核, "
      "**不豁免** `--fail-on-pending` D4+ 全集清零终防线)")
    a("")
    a("## 1. 摘要")
    a("")
    a("| 口径 | 模型数 | 实搭预算 |")
    a("| --- | ---: | ---: |")
    a(f"| 必搭 (先排产) | {s['must_build_count']} | {s['must_build_minutes']} "
      f"分钟 ≈ {s['must_build_minutes'] / 60:.1f} 小时 |")
    a(f"| 可缓建 (须策展签核) | {s['deferrable_count']} "
      f"| {s['deferrable_minutes']} 分钟 ≈ {s['deferrable_minutes'] / 60:.1f} 小时 |")
    a(f"| **合计 (D4+ 待复核全集)** | **{s['pending_total']}** "
      f"| **{s['total_minutes']} 分钟 ≈ {s['total_minutes'] / 60:.1f} 小时** |")
    a("")
    a(f"## 2. 队列 (按风险分降序, {len(rows)} 行)")
    a("")
    a("| # | 模型 | 名称 | 难度 | 风险分 | 风险档 | L2 标记 | 排产 | 依据 "
      "| 族 | 预算 (分) |")
    a("| ---: | --- | --- | --- | ---: | --- | --- | --- | --- | --- | ---: |")
    for r in rows:
        l2 = "、".join(f"`{f}`" for f in r["l2_flags"]) if r["l2_flags"] else "—"
        cls = "**必搭**" if r["build_class"] == "must_build" else "可缓建"
        reason = r["build_reason"]
        if r["build_class"] == "deferrable":
            reason = f"同族代表 `{r['family_representative']}` 兜底"
        layer = f" ({r['sample_pack_layer']})" if r["sample_pack_layer"] else ""
        a(f"| {r['rank']} | `{r['model_id']}` | {r['name']} | D{r['difficulty']} "
          f"| {r['risk_score']} | {r['risk_band']} | {l2} | {cls} "
          f"| {reason}{layer} | {r['family_id']} | {r['est_minutes']} |")
    a("")
    if warnings:
        a(f"## 3. 告警 ({len(warnings)})")
        a("")
        for w in warnings:
            a(f"- [WARN] {w}")
        a("")
    a(f"## {'4' if warnings else '3'}. 纪律 (缓建不是免检)")
    a("")
    a("1. 本表只合并三份既有产物的口径, 排产采纳与否是策展/QA 的政策决定; "
      "可缓建成员最终仍须实搭, 或由策展按族级抽检政策**书面**豁免 "
      "(依据与流程见 [PHYSICAL_FAMILY_PACK.md](PHYSICAL_FAMILY_PACK.md) 第 5 节);")
    a("2. 申请缓建的前提: 同族代表已实搭 **Pass** 且落盘 "
      "`content_meta.physical_verified` 三字段; 代表 Fail 则整族全员实搭;")
    a("3. 实搭动作与判定标准以 "
      "[PHYSICAL_REBUILD_CHECKLIST.md](../PHYSICAL_REBUILD_CHECKLIST.md) 为准, "
      "备料/打印/落盘见 [PHYSICAL_REVIEW_USER_GUIDE.md](PHYSICAL_REVIEW_USER_GUIDE.md);")
    a("4. 本表是快照 —— 模型内容 (`final_assembly` / `steps`) 或复核状态变化后, "
      "先重新生成风险报告再重新导出本队列。")
    a("")
    return "\n".join(lines) + "\n"


def print_text(rows, summary, warnings, risk_source, threshold):
    s = summary
    print("== D4+ 实物待复核排产队列 (风险分降序; 必搭 = 抽样包 ∪ 族代表 ∪ "
          "单模型族, 可缓建须策展签核) ==")
    print(f"风险分: {risk_source}; 族聚类阈值 {threshold}")
    print(f"待复核 {s['pending_total']} 个 = 必搭 {s['must_build_count']} 个 "
          f"({s['must_build_minutes']} 分钟 ≈ {s['must_build_minutes'] / 60:.1f} 小时) "
          f"+ 可缓建 {s['deferrable_count']} 个 ({s['deferrable_minutes']} 分钟 ≈ "
          f"{s['deferrable_minutes'] / 60:.1f} 小时)")
    print()
    print(f"{'#':>3} {'模型':<28} {'难度':<4} {'风险分':>5} {'档':<2} "
          f"{'排产':<4} 依据")
    for r in rows:
        cls = "必搭" if r["build_class"] == "must_build" else "缓建"
        print(f"{r['rank']:>3} {r['model_id']:<28} D{r['difficulty']:<3} "
              f"{r['risk_score']:>5} {r['risk_band']:<2} {cls:<4} "
              f"{r['build_reason']} [{r['family_id']}]")
    if warnings:
        print()
        for w in warnings:
            print(f"  [WARN] {w}")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="D4+ 实物待复核排产队列导出 (风险分降序 + 必搭/可缓建标注, "
                    "合并 list_physical_pending / 风险报告 / 结构族三口径)")
    parser.add_argument("models_dir", nargs="?", default=str(ROOT / "data" / "models"))
    parser.add_argument("--risk-report", default=str(ROOT / DEFAULT_RISK_REPORT),
                        metavar="FILE")
    parser.add_argument("--catalog", default=None,
                        help="模型库目录 model_catalog.json (名称/主题来源)")
    parser.add_argument("--verification-dir", default=None)
    parser.add_argument("--threshold", type=float, default=DEFAULT_THRESHOLD)
    parser.add_argument("--csv", default=None, metavar="FILE")
    parser.add_argument("--markdown", default=None, metavar="FILE")
    parser.add_argument("--json", action="store_true", dest="as_json")
    args = parser.parse_args()

    models_dir = Path(args.models_dir)
    if not models_dir.is_dir():
        print(f"错误: 模型目录不存在: {models_dir}", file=sys.stderr)
        return 2
    risk_path = Path(args.risk_report)
    if not risk_path.is_file():
        print(f"错误: 风险报告不存在: {risk_path}\n"
              "先生成: python3 tools/physical_risk_report.py --json > "
              f"{DEFAULT_RISK_REPORT}", file=sys.stderr)
        return 2
    if not 0 < args.threshold <= 1:
        print(f"错误: --threshold 必须在 (0, 1] (给的是 {args.threshold})",
              file=sys.stderr)
        return 2
    ver_dir = Path(args.verification_dir) if args.verification_dir \
        else models_dir.parent / "verification"
    catalog_path = Path(args.catalog) if args.catalog \
        else models_dir.parent / "model_catalog.json"

    models = [load_json(p) for p in sorted(models_dir.glob("*.json"))]
    if not models:
        print(f"错误: 模型目录为空: {models_dir}", file=sys.stderr)
        return 2
    themes, names = {}, {}
    if catalog_path.is_file():
        for entry in load_json(catalog_path).get("models", []):
            themes[entry["id"]] = entry.get("theme", "(未登记)")
            names[entry["id"]] = entry.get("name", entry["id"])

    # 族划分与 physical_family_pack 完全同参数 (特征/相似度/聚法/代表选取)
    feats = []
    for m in sorted(models, key=lambda m: m["id"]):
        hist = ((m.get("content_meta") or {})
                .get("structural_signature", {}).get("tile_histogram"))
        if not hist:
            print(f"错误: {m['id']} 缺 content_meta.structural_signature."
                  "tile_histogram (聚类特征必备, 见 CONTENT_STRATEGY.md 5.1 节)",
                  file=sys.stderr)
            return 2
        feats.append({"id": m["id"], "difficulty": int(m["difficulty"]),
                      "hist": hist,
                      "tags": theme_tag_set(m, themes.get(m["id"], ""))})
    by_id = {m["id"]: m for m in models}
    feats_by_id = {f["id"]: f for f in feats}
    verified = {m["id"]: classify(m, ver_dir) for m in models}
    risk, flags, risk_source = load_risk_scores(models, str(risk_path))
    sample_layers = {m["id"]: layer
                     for m, layer in select_sample(models, themes, target=10)[0]}
    clusters, scores = cluster_families(feats, args.threshold)
    families = build_families(clusters, scores, feats_by_id, by_id, names,
                              verified, risk, flags, set(sample_layers))

    report_rows = load_report_rows(risk_path)
    rows, warnings = build_queue(models, names, verified, families,
                                 sample_layers, report_rows)
    summary = summarize(rows)

    if args.csv:
        write_csv(rows, Path(args.csv))
    if args.markdown:
        csv_target = args.csv or "docs/reports/PHYSICAL_REVIEW_QUEUE.csv"
        md = render_markdown(rows, summary, warnings, risk_source,
                             args.threshold, csv_target)
        out = Path(args.markdown)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(md, encoding="utf-8")
        print(f"已生成: {out}")

    if args.as_json:
        print(json.dumps({
            "scope": summary["scope"],
            "sort": "risk_score desc, difficulty desc, model_id asc",
            "threshold": args.threshold,
            "risk_source": risk_source,
            "summary": summary,
            "queue": rows,
            "warnings": warnings,
        }, ensure_ascii=False, indent=2))
    elif not args.csv and not args.markdown:
        print_text(rows, summary, warnings, risk_source, args.threshold)
    return 0


if __name__ == "__main__":
    sys.exit(main())
