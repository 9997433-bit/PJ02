#!/usr/bin/env python3
"""难度配额置换规划 —— 路径 B1 (250 上限内换题解冻) 退役候选生成器。

解冻线 (check_difficulty_quota.py): D1 >= 20 且 D5 >= 6 同时达标。
在 250 上限内, 每新增 1 个 D1/D5 须退役 1 个存量 D3 (净换题, 不扩库)。

本工具扫描主库, 按策展规则排出可退役 D3 候选序, 并对照
CONTENT_GAP_AUDIT.md 批 J–M 选题池估算分阶段解冻路径。

退出码: 0 报告; 2 结构错误。

用法:
  python3 tools/plan_quota_substitution.py
  python3 tools/plan_quota_substitution.py --markdown docs/reports/QUOTA_SUBSTITUTION_PLAN.md
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MODELS = ROOT / "data" / "models"
STARTER = ROOT / "platforms" / "windows" / "packaging" / "starter_models.txt"

D1_MIN = 20
D5_MIN = 6

# 批 J–M 净增量 (置换模式, 零 D3)
BATCH_JM = {"D1": 8, "D2": 4, "D4": 1, "D5": 3, "total": 16}

# 矩阵内超编主题 (D3 优先从这类格子退役)
MATRIX_D3_EXCESS = frozenset({
    "land_transport", "spacecraft", "animal_world", "sea_air_transport",
    "fantasy_machinery", "holiday_seasonal",
})


def load_starter_ids() -> set[str]:
    if not STARTER.is_file():
        return set()
    return {line.strip() for line in STARTER.read_text().splitlines() if line.strip()}


def load_models():
    files = sorted(MODELS.glob("*.json"))
    if not files:
        print(f"[错误] {MODELS} 下没有模型文件", file=sys.stderr)
        sys.exit(2)
    rows = []
    for path in files:
        m = json.loads(path.read_text(encoding="utf-8"))
        mid = m.get("id", path.stem)
        diff = m.get("difficulty")
        if diff not in (1, 2, 3, 4, 5):
            print(f"[错误] {mid} difficulty 非法: {diff!r}", file=sys.stderr)
            sys.exit(2)
        meta = m.get("content_meta") or {}
        tags = m.get("tags") or []
        starter = load_starter_ids()
        is_free = mid in starter or "免费" in tags
        series = meta.get("series")
        bucket = meta.get("matrix_bucket")
        rows.append({
            "id": mid,
            "difficulty": diff,
            "pieces": m.get("total_pieces", 0),
            "series": series,
            "bucket": bucket,
            "in_matrix": bool(series),
            "is_free": is_free,
            "label": series or bucket or "(none)",
        })
    return rows


def retire_score(row: dict) -> tuple:
    """分数越低越优先退役 (matrix_bucket > matrix 超编 > 其他)。"""
    if row["is_free"]:
        return (9, 0, row["id"])  # 不可退役
    if row["difficulty"] != 3:
        return (9, 0, row["id"])
    tier = 0
    if not row["in_matrix"]:
        tier = 0  # 矩阵外优先
    elif row["series"] in MATRIX_D3_EXCESS:
        tier = 1
    else:
        tier = 2
    return (tier, -row["pieces"], row["id"])


def count_by_diff(rows):
    c = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
    for r in rows:
        c[r["difficulty"]] += 1
    return c


def project_counts(base: dict, d1_add: int = 0, d3_sub: int = 0, d5_add: int = 0):
    return {
        1: base[1] + d1_add,
        2: base[2],
        3: base[3] - d3_sub,
        4: base[4],
        5: base[5] + d5_add,
    }


def frozen(counts: dict) -> bool:
    return counts[1] < D1_MIN or counts[5] < D5_MIN


def min_swaps_to_unfreeze(counts: dict) -> tuple[int, int, int]:
    """返回 (总置换数, 需 D1 增量, 需 D5 增量)。"""
    d1_need = max(0, D1_MIN - counts[1])
    d5_need = max(0, D5_MIN - counts[5])
    return d1_need + d5_need, d1_need, d5_need


def build_report(rows) -> str:
    counts = count_by_diff(rows)
    total_swaps, d1_need, d5_need = min_swaps_to_unfreeze(counts)
    candidates = sorted(
        [r for r in rows if r["difficulty"] == 3 and not r["is_free"]],
        key=retire_score,
    )
    lines = [
        "# 难度配额置换规划 (路径 B1)",
        "",
        f"- 基线: 主库 {len(rows)} 模型",
        f"- 解冻线: D1 >= {D1_MIN} 且 D5 >= {D5_MIN}",
        f"- 现状: D1={counts[1]} D2={counts[2]} D3={counts[3]} "
        f"D4={counts[4]} D5={counts[5]}",
        f"- 冻结: **{'是' if frozen(counts) else '否'}**",
        f"- 净换题需求: **至少 {total_swaps} 次** (D1 +{d1_need}, D5 +{d5_need})",
        "",
        "## 1. 分阶段演算",
        "",
        "| 阶段 | 动作 | D1 | D5 | 冻结 |",
        "| --- | --- | ---: | ---: | --- |",
    ]
    c0 = counts.copy()
    lines.append(
        f"| 现状 | — | {c0[1]} | {c0[5]} | {'是' if frozen(c0) else '否'} |"
    )
    # 批 J-M
    c1 = project_counts(c0, d1_add=BATCH_JM["D1"], d3_sub=BATCH_JM["total"],
                        d5_add=BATCH_JM["D5"])
    lines.append(
        f"| 批 J–M (16 置换) | 退役 16×D3 → 8×D1+4×D2+1×D4+3×D5 | "
        f"{c1[1]} | {c1[5]} | {'是' if frozen(c1) else '否'} |"
    )
    remain_d1 = max(0, D1_MIN - c1[1])
    remain_d5 = max(0, D5_MIN - c1[5])
    remain_swaps = remain_d1 + remain_d5
    if remain_swaps:
        c2 = project_counts(c1, d1_add=remain_d1, d3_sub=remain_swaps, d5_add=remain_d5)
        lines.append(
            f"| 批 N+ (建议) | 再置换 {remain_swaps} 次 (D1 +{remain_d1}, D5 +{remain_d5}) | "
            f"{c2[1]} | {c2[5]} | {'是' if frozen(c2) else '否'} |"
        )
    lines += [
        "",
        "批 J–M 选题见 [CONTENT_GAP_AUDIT.md](../CONTENT_GAP_AUDIT.md) §8。",
        "",
        "## 2. 退役候选序 (前 30, 非免费 D3)",
        "",
        "排序规则: 矩阵外桶 > 矩阵内超编主题 > 其他; 同档按片数降序。",
        "**不可退役**: 免费层 26 个 D3 (`FREE_TIER_MANIFEST.md`)。",
        "",
        "| # | 模型 id | 归类 | 片数 | 备注 |",
        "| ---: | --- | --- | ---: | --- |",
    ]
    for i, r in enumerate(candidates[:30], 1):
        note = "矩阵外" if not r["in_matrix"] else (
            "超编主题" if r["series"] in MATRIX_D3_EXCESS else "矩阵内"
        )
        lines.append(
            f"| {i} | `{r['id']}` | {r['label']} | {r['pieces']} | {note} |"
        )
    lines += [
        "",
        "## 3. 执行纪律 (置换模式)",
        "",
        "1. 用户书面批准路径 B1 后启动;",
        "2. 每批: 先退役候选序顶部 N 个 D3 (删 JSON + 目录 + 缩略图), 再入库新批;",
        "3. 入库前跑 `tools/review_content_batch.sh` 五关机检;",
        "4. 全库保持 250 模型; `check_difficulty_quota.py --strict` 达标后 G2 红灯②自动转绿。",
        "",
        "生成: `python3 tools/plan_quota_substitution.py --markdown 本文件`",
    ]
    return "\n".join(lines) + "\n"


def main():
    ap = argparse.ArgumentParser(description="难度配额置换规划 (路径 B1)")
    ap.add_argument("--markdown", metavar="FILE", help="写入 Markdown 报告")
    args = ap.parse_args()
    rows = load_models()
    text = build_report(rows)
    if args.markdown:
        out = Path(args.markdown)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(text, encoding="utf-8")
        print(f"已写入 {out}")
    else:
        print(text)


if __name__ == "__main__":
    main()
