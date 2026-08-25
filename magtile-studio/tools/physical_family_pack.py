#!/usr/bin/env python3
"""D4+ 实物复核结构族去重包 (Physical Family Pack)。

背景: 全库 D4+ 实物复核是商用上架硬门槛 (全集清零由
tools/list_physical_pending.py --fail-on-pending 终防线把守), 但 45 个 D4+
逐个实搭约 53 小时, 其中不少模型互为"同一结构原型的换皮" (同族箱形小楼 /
同族车轮底座载具 / 同族轨道坡道)。本工具用确定性规则把全库聚成**结构族**,
每族选 1 个代表: 代表实搭通过后, 同族其余成员的实搭可申请**缓建** (须策展
签核, 见第 5 节纪律), 从而给出可削减实搭人手的量化估算。

与 tools/physical_sample_pack.py 的分工 (互补, 不替代):
  sample = 上架抽样 —— V1 上架前哪些必须**先**搭 (免费层/D5/大片数旗舰);
  family = 结构去重 —— 哪些结构原型彼此重复, 全集清零阶段每族先搭代表,
           同族其余成员可缓建以削减重复劳动。
  抽样包成员始终必搭, 不参与缓建 (两工具取并集, 永不冲突)。

聚类口径 (确定性, 重跑可复现; 简单集合相似度, 不引入 ML):
  特征   content_meta.structural_signature.tile_histogram (片型直方图)
         + difficulty + 主题 tags (模型 tags 剔除层级标记
         免费/进阶/挑战/需要扩展装 后, 并入 model_catalog.json 的 theme)
  相似度 score = 0.60 x 片型直方图加权 Jaccard (逐片型 Σmin/Σmax)
               + 0.25 x 主题标签 Jaccard
               + 0.15 x 难度接近度 (1 - |Δd|/4)
  硬门   两模型至少共享 1 个主题标签 且 |Δdifficulty| <= 1, 否则不可同族
         (拦截"直方图巧合相同但题材毫不相干"的假同族)
  聚法   完全连接凝聚聚类 (complete linkage): 族内**任意两成员**相似度均
         >= --threshold (默认 0.67) —— 不用单连接, 避免传递链把不相似
         模型串进同族, "搭代表可覆盖同族"的断言才站得住

代表选取 (每族恰 1 个, 排序取首): D4+ 优先 > 未实物复核优先 (判定与
tools/list_physical_pending.py 同源 classify) > L2 标记命中数最多
(风险报告就位时) > 风险分最高 > id 升序。

风险来源 (依次探测, physical_risk_report 已存在则**复用**不重算; 字段
对齐 BUILD_VERIFICATION.md 2.1 节 L2 工具接口约定):
  1. --risk-report FILE 或默认路径 docs/reports/physical_risk_report.json
     (机器输出 JSON: models[] 逐模型 model_id/id + flags 检测编码数组;
      若工具额外给出数值分, 分值键兼容 risk_score / score / risk;
      也兼容 scores{} / 顶层映射 两种简化形态);
  2. tools/physical_risk_report.py 模块 (入口兼容 risk_score(model) /
     compute_risk_score(model) / score_model(model));
  3. 内置退化启发式 (0~100, 仅在前两者缺位时作垫底排序键):
     0.35x片数占比 + 0.20x步数占比 + 0.20x难度/5
     + 0.15x单步最大放片占比 + 0.10x physical_risk_notes 数占比。

用法:
    tools/physical_family_pack.py [models_dir] [选项]
        models_dir              模型目录 (默认: 仓库 data/models)
        --catalog FILE          模型库目录 (主题/名称来源,
                                默认 models_dir/../model_catalog.json)
        --verification-dir D    旁车验证记录目录 (默认 models_dir/../verification)
        --threshold X           同族相似度阈值, (0, 1] (默认 0.67)
        --risk-report FILE      显式指定风险报告 JSON (缺省走上述探测链)
        --json                  机器可读 JSON 输出 (含全部族与单模型族)
        --markdown FILE         生成可签核 Markdown 报告
                                (docs/reports/PHYSICAL_FAMILY_PACK.md 即由此生成)

退出码: 0 = 报告完成 / 2 = 数据错误
"""

import argparse
import json
import sys
from collections import Counter
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from list_physical_pending import classify  # noqa: E402  (复核判定单一来源)
from physical_sample_pack import TIME_BUDGET_MIN, select_sample  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent

# 层级/商务标记, 不是主题语义, 聚类前剔除 (与 verify_free_tier / 内容策略口径一致)
LEVEL_TAGS = {"免费", "进阶", "挑战", "需要扩展装", "入门", "基础"}

# 相似度权重与硬门 (改动即改变族划分, 须在报告里说明理由并重新签核)
W_HIST, W_TAG, W_DIFF = 0.60, 0.25, 0.15
MAX_DIFF_GAP = 1            # 硬门: 难度差超过 1 不可同族
DEFAULT_THRESHOLD = 0.67    # 完全连接阈值 (实测 209 库: 过高漏掉 treehouse
                            # 双子, 过低把跨题材直方图巧合串成假同族)

RISK_REPORT_CANDIDATES = ("docs/reports/physical_risk_report.json",
                          "docs/reports/PHYSICAL_RISK_REPORT.json")
RISK_MODULE_ENTRIES = ("risk_score", "compute_risk_score", "score_model")

REPORT_DOC = "PHYSICAL_FAMILY_PACK.md"
SAMPLE_DOC = "PHYSICAL_SAMPLE_V1.md"


def load_json(path: Path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        print(f"错误: {path} 无法解析: {exc}", file=sys.stderr)
        sys.exit(2)


# ---------------------------------------------------------------- 特征与相似度

def theme_tag_set(model: dict, theme: str) -> frozenset:
    tags = set(model.get("tags", [])) - LEVEL_TAGS
    if theme:
        tags.add(theme)
    return frozenset(tags)


def hist_similarity(a: dict, b: dict) -> float:
    """片型直方图加权 Jaccard: 逐片型 Σmin / Σmax, 值域 [0, 1]。"""
    keys = set(a) | set(b)
    hi = sum(max(a.get(k, 0), b.get(k, 0)) for k in keys)
    if hi <= 0:
        return 0.0
    return sum(min(a.get(k, 0), b.get(k, 0)) for k in keys) / hi


def pair_score(fa: dict, fb: dict) -> float:
    """两模型相似度; 未过硬门返回 -1 (任何阈值下都不可同族)。"""
    gap = abs(fa["difficulty"] - fb["difficulty"])
    if gap > MAX_DIFF_GAP or not (fa["tags"] & fb["tags"]):
        return -1.0
    tag_union = fa["tags"] | fb["tags"]
    tag_sim = len(fa["tags"] & fb["tags"]) / len(tag_union) if tag_union else 0.0
    return (W_HIST * hist_similarity(fa["hist"], fb["hist"])
            + W_TAG * tag_sim
            + W_DIFF * (1 - gap / 4))


def cluster_families(feats: list, threshold: float):
    """完全连接凝聚聚类; 返回 (族成员 id 列表的列表, 原始两两分数表)。

    feats 按 id 升序; 合并顺序确定 (每轮取族间最小相似度最大的一对,
    并列时取成员 id 最小者), 重跑可复现。
    """
    ids = [f["id"] for f in feats]
    scores = {}
    for i in range(len(feats)):
        for j in range(i + 1, len(feats)):
            scores[(ids[i], ids[j])] = pair_score(feats[i], feats[j])

    members = {mid: [mid] for mid in ids}    # 族键 = 族内最小成员 id
    link = dict(scores)                      # 族间完全连接距离 (min 两两分)

    def key(a, b):
        return (a, b) if a < b else (b, a)

    while True:
        best = None
        for (ka, kb), s in link.items():
            if s >= threshold and (best is None or s > best[0]
                                   or (s == best[0] and (ka, kb) < best[1:])):
                best = (s, ka, kb)
        if best is None:
            break
        _, ka, kb = best                     # ka < kb, 合并后族键仍为 ka
        members[ka] = sorted(members[ka] + members.pop(kb))
        del link[(ka, kb)]
        for kc in members:
            if kc == ka:
                continue
            link[key(ka, kc)] = min(link[key(ka, kc)], link.pop(key(kb, kc)))
    return sorted(members.values(), key=lambda c: (-len(c), c[0])), scores


# ---------------------------------------------------------------- 风险分来源

def extract_report(data):
    """从风险报告 JSON 提取 ({id: score}, {id: [flags]}); 不认识则双空。

    权威形态 (BUILD_VERIFICATION.md 2.1 节): models[] 逐模型至少含
    model_id + flags/flagged/l2_required; 数值分是工具的可选增值字段。
    """
    rows = None
    if isinstance(data, dict):
        if isinstance(data.get("models"), list):
            rows = data["models"]
        elif isinstance(data.get("scores"), dict):
            rows = [{"id": k, "risk_score": v} for k, v in data["scores"].items()]
        elif data and all(isinstance(v, (int, float)) and not isinstance(v, bool)
                          for v in data.values()):
            rows = [{"id": k, "risk_score": v} for k, v in data.items()]
    elif isinstance(data, list):
        rows = data
    scores, flags = {}, {}
    for row in rows or []:
        if not isinstance(row, dict):
            continue
        mid = row.get("model_id") or row.get("id")
        if not mid:
            continue
        if isinstance(row.get("flags"), list):
            flags[str(mid)] = [str(f) for f in row["flags"]]
        for field in ("risk_score", "score", "risk"):
            v = row.get(field)
            if isinstance(v, (int, float)) and not isinstance(v, bool):
                scores[str(mid)] = float(v)
                break
    return scores, flags


def builtin_scores(models: list) -> dict:
    """内置退化启发式 (0~100): 片数/步数/难度/单步放片峰值/风险注记数。"""
    def burst(m):
        return max((len(s.get("tiles_to_add", [])) for s in m.get("steps", [])),
                   default=0)
    max_pieces = max((int(m["total_pieces"]) for m in models), default=1) or 1
    max_steps = max((len(m.get("steps", [])) for m in models), default=1) or 1
    max_burst = max((burst(m) for m in models), default=1) or 1
    out = {}
    for m in models:
        notes = len((m.get("content_meta") or {}).get("physical_risk_notes") or [])
        out[m["id"]] = round(100 * (
            0.35 * int(m["total_pieces"]) / max_pieces
            + 0.20 * len(m.get("steps", [])) / max_steps
            + 0.20 * int(m["difficulty"]) / 5
            + 0.15 * burst(m) / max_burst
            + 0.10 * min(notes, 4) / 4), 1)
    return out


def load_risk_scores(models: list, explicit: str):
    """按探测链取风险; 返回 ({id: score}, {id: [L2 flags]}, 来源说明)。

    数值分缺位的模型垫内置启发式 (保证全序可排); L2 flags 仅在风险报告
    就位时非空, 在代表选取里优先于数值分。
    """
    candidates = ([Path(explicit)] if explicit
                  else [ROOT / c for c in RISK_REPORT_CANDIDATES])
    for path in candidates:
        if path.is_file():
            scores, flags = extract_report(load_json(path))
            if scores or flags:
                merged = builtin_scores(models)
                merged.update(scores)
                return merged, flags, (f"复用风险报告 {path.name} "
                                       "(physical_risk_report 产物, 接口约定见 "
                                       "BUILD_VERIFICATION.md 2.1 节)")
            if explicit:
                print(f"错误: --risk-report {path} 里没有可识别的风险字段 "
                      "(需要 models[] 逐模型 model_id/id + flags 或数值分, "
                      "或 scores{}/顶层映射 简化形态)", file=sys.stderr)
                sys.exit(2)
    if explicit:
        print(f"错误: --risk-report 文件不存在: {explicit}", file=sys.stderr)
        sys.exit(2)

    try:
        import physical_risk_report  # noqa: F401  (同目录探测, 就位即复用)
    except ImportError:
        physical_risk_report = None
    if physical_risk_report is not None:
        for entry in RISK_MODULE_ENTRIES:
            fn = getattr(physical_risk_report, entry, None)
            if callable(fn):
                return ({m["id"]: float(fn(m)) for m in models}, {},
                        f"复用 tools/physical_risk_report.py::{entry}()")

    return (builtin_scores(models), {},
            "内置退化启发式 (physical_risk_report 未就位)")


# ---------------------------------------------------------------- 族装配

def pick_representative(member_ids: list, by_id: dict, verified: dict,
                        risk: dict, flags: dict) -> str:
    """代表 = D4+ 优先 > 未复核优先 > L2 标记命中多者 > 风险分最高 > id 升序。"""
    return min(member_ids, key=lambda mid: (
        0 if int(by_id[mid]["difficulty"]) >= 4 else 1,
        0 if not verified[mid][0] else 1,
        -len(flags.get(mid, [])),
        -risk[mid],
        mid))


def build_families(clusters, scores, feats_by_id, by_id, names, verified,
                   risk, flags, sample_ids):
    families = []
    for n, member_ids in enumerate(clusters, 1):
        rep = pick_representative(member_ids, by_id, verified, risk, flags)
        shared = frozenset.intersection(*(feats_by_id[m]["tags"]
                                          for m in member_ids))
        min_sim = None
        if len(member_ids) > 1:
            min_sim = min(scores[(a, b)]
                          for i, a in enumerate(member_ids)
                          for b in member_ids[i + 1:])
        diffs = sorted({int(by_id[m]["difficulty"]) for m in member_ids})
        span = f"D{diffs[0]}" if len(diffs) == 1 else f"D{diffs[0]}~D{diffs[-1]}"
        members = []
        for mid in member_ids:
            m = by_id[mid]
            ok, via, _ = verified[mid]
            members.append({
                "id": mid,
                "name": names.get(mid, m.get("name", mid)),
                "difficulty": int(m["difficulty"]),
                "total_pieces": int(m["total_pieces"]),
                "steps": len(m.get("steps", [])),
                "risk_score": risk[mid],
                "l2_flags": flags.get(mid, []),
                "verified": ok,
                "verified_via": via,
                "is_representative": mid == rep,
                "in_sample_pack": mid in sample_ids,
            })
        families.append({
            "family_id": f"F{n:03d}",
            "size": len(member_ids),
            "difficulty_span": span,
            "shared_tags": sorted(shared),
            "min_similarity": round(min_sim, 3) if min_sim is not None else None,
            "representative": rep,
            "members": members,
        })
    return families


def compute_reduction(families, sample_ids):
    """D4+ 待复核口径的可削减人手估算。

    可缓建 = 同族里代表之外的 D4+ 待复核成员, 且不在上架抽样包内
    (抽样包成员始终必搭)。代表选取规则保证: 族内存在 D4+ 待复核成员时,
    代表必为其中之一, 故缓建成员总有一个同族 D4+ 代表兜底。
    """
    baseline, must, deferrable = [], [], []
    for fam in families:
        pend = [x for x in fam["members"]
                if x["difficulty"] >= 4 and not x["verified"]]
        baseline += pend
        for x in pend:
            if x["is_representative"] or x["id"] in sample_ids:
                must.append((fam, x))
            else:
                deferrable.append((fam, x))
    minutes = lambda rows: sum(  # noqa: E731
        TIME_BUDGET_MIN.get(x["difficulty"], 120) for _, x in rows)
    base_min = sum(TIME_BUDGET_MIN.get(x["difficulty"], 120) for x in baseline)
    return {
        "scope": "D4+ 待实物复核 (与 list_physical_pending 同一判定)",
        "pending_d4plus": len(baseline),
        "baseline_minutes": base_min,
        "must_build_count": len(must),
        "must_build_minutes": minutes(must),
        "deferrable_count": len(deferrable),
        "saved_minutes": minutes(deferrable),
        "saved_ratio": round(minutes(deferrable) / base_min, 3) if base_min else 0.0,
        "deferrable": [{
            "id": x["id"],
            "family_id": fam["family_id"],
            "representative": fam["representative"],
            "difficulty": x["difficulty"],
            "minutes": TIME_BUDGET_MIN.get(x["difficulty"], 120),
        } for fam, x in deferrable],
    }


# ---------------------------------------------------------------- 输出

def fmt_status(member: dict) -> str:
    return f"已复核 ({member['verified_via']})" if member["verified"] else "待复核"


def render_markdown(families, reduction, risk_source, threshold,
                    models_total, sample_ids) -> str:
    multi = [f for f in families if f["size"] > 1]
    singles = [f for f in families if f["size"] == 1]
    single_diffs = Counter(f["members"][0]["difficulty"] for f in singles)
    deduped = models_total - len(families)
    lines = []
    a = lines.append
    a("# D4+ 实物复核结构族去重包 (Physical Family Pack)")
    a("")
    a(f"- 生成日期: {date.today().isoformat()}")
    a("- 生成工具: `tools/physical_family_pack.py --markdown docs/reports/"
      f"{REPORT_DOC}` —— 模型库 / 复核状态 / 风险报告变化后**重新生成**, "
      "勿手改; 缓建签核以策展书面记录为准, 本报告只提供确定性族划分与估算")
    a(f"- 风险分来源: {risk_source}; 已复核判定与 "
      "`tools/list_physical_pending.py` 同源 (同一 classify 函数)")
    a("")
    a("## 1. 定位 (与上架抽样包互补)")
    a("")
    a(f"[`{SAMPLE_DOC}`]({SAMPLE_DOC}) 回答「上架前哪些必须**先**搭」"
      "(免费层/D5/大片数旗舰的**抽样**); 本报告回答「哪些结构原型彼此**重复**」"
      "(全集清零阶段的**去重**): 每族先实搭 1 个代表, 代表通过后同族其余 D4+ "
      "成员可向策展申请缓建, 削减重复实搭人手。两清单取并集, 抽样包成员"
      "始终必搭不参与缓建。**族去重不豁免全集清零** —— "
      "`tools/run_release_gate.sh --fail-on-pending` 终防线仍以 D4+ 全集为准, "
      "缓建只是排产顺序与人手预算的工程估算, 采纳与否是策展/QA 的政策决定。")
    a("")
    a("## 2. 聚类口径 (确定性, 重跑可复现)")
    a("")
    a("| 要素 | 取值 |")
    a("| --- | --- |")
    a("| 特征 | `content_meta.structural_signature.tile_histogram` + "
      "difficulty + 主题 tags (剔除层级标记 免费/进阶/挑战/需要扩展装, "
      "并入 catalog theme) |")
    a(f"| 相似度 | {W_HIST:.2f} x 片型直方图加权 Jaccard (逐片型 Σmin/Σmax) + "
      f"{W_TAG:.2f} x 主题标签 Jaccard + {W_DIFF:.2f} x 难度接近度 (1 - 难度差/4) |")
    a(f"| 硬门 | 至少共享 1 个主题标签 且 难度差 <= {MAX_DIFF_GAP} |")
    a(f"| 聚法 | 完全连接凝聚聚类, 族内任意两成员相似度 >= {threshold} "
      "(非单连接, 防传递链假同族) |")
    a("")
    a(f"全库 {models_total} 个模型聚成 **{len(families)} 族**: 多成员族 "
      f"{len(multi)} 个 (共 {sum(f['size'] for f in multi)} 模型, 折叠 "
      f"{deduped} 个重复原型), 单模型族 {len(singles)} 个 ("
      + ", ".join(f"D{d} x{c}" for d, c in sorted(single_diffs.items()))
      + ")。片型直方图是**备料构成**视角, 不含连接拓扑 —— 同族成员工序仍可能"
        "不同, 这是缓建须人工签核而非自动豁免的根本原因。")
    a("")
    a(f"## 3. 结构族表 (多成员族 {len(multi)} 个)")
    a("")
    a("| 族 | 规模 | 难度 | 共同标签 | 族内最低相似度 | 成员 (**粗体 = 代表**) |")
    a("| --- | --- | --- | --- | --- | --- |")
    for fam in multi:
        cells = []
        for x in fam["members"]:
            mark = f"**`{x['id']}`**" if x["is_representative"] else f"`{x['id']}`"
            if x["in_sample_pack"]:
                mark += "†"
            cells.append(mark)
        a(f"| {fam['family_id']} | {fam['size']} | {fam['difficulty_span']} "
          f"| {'、'.join(fam['shared_tags']) or '—'} | {fam['min_similarity']:.3f} "
          f"| {' '.join(cells)} |")
    a("")
    a("† = 同时入选上架抽样包 (必搭, 不参与缓建)。单模型族的代表即其自身, "
      "含单模型族的全量族表见 `tools/physical_family_pack.py --json`。")
    a("")
    reps = [(fam, x) for fam in multi for x in fam["members"]
            if x["is_representative"]]
    a(f"## 4. 代表清单 (多成员族, {len(reps)} 个)")
    a("")
    a("| 族 | 代表 | 名称 | 难度 | 片数 | 步数 | L2 标记 | 风险分 "
      "| 复核状态 | 上架抽样包 |")
    a("| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |")
    for fam, x in reps:
        l2 = "、".join(f"`{f}`" for f in x["l2_flags"]) if x["l2_flags"] else "—"
        a(f"| {fam['family_id']} | `{x['id']}` | {x['name']} | D{x['difficulty']} "
          f"| {x['total_pieces']} | {x['steps']} | {l2} | {x['risk_score']} "
          f"| {fmt_status(x)} | {'是' if x['in_sample_pack'] else '否'} |")
    a("")
    a("代表选取规则: D4+ 优先 > 未实物复核优先 > L2 标记命中多者 (风险报告"
      "就位时, 检测编码见 BUILD_VERIFICATION.md 第 2 节) > 风险分最高 > "
      "id 升序 —— 族内风险上界先过手, 代表通过对同族的覆盖论证才有分量。")
    a("")
    r = reduction
    a("## 5. 可削减人手估算 (D4+ 待复核口径)")
    a("")
    a("| 口径 | 模型数 | 实搭预算 |")
    a("| --- | ---: | ---: |")
    a(f"| 全集逐个实搭 (基线) | {r['pending_d4plus']} "
      f"| {r['baseline_minutes']} 分钟 ≈ {r['baseline_minutes'] / 60:.1f} 小时 |")
    a(f"| 族去重后必搭 (代表 + 单模型族 + 抽样包成员) | {r['must_build_count']} "
      f"| {r['must_build_minutes']} 分钟 ≈ {r['must_build_minutes'] / 60:.1f} 小时 |")
    a(f"| **可缓建 (须策展签核)** | **{r['deferrable_count']}** "
      f"| **{r['saved_minutes']} 分钟 ≈ {r['saved_minutes'] / 60:.1f} 小时 "
      f"(省 {r['saved_ratio']:.0%})** |")
    a("")
    if r["deferrable"]:
        a("| 可缓建模型 | 难度 | 所在族 | 兜底代表 | 单模型预算 |")
        a("| --- | --- | --- | --- | ---: |")
        for row in r["deferrable"]:
            a(f"| `{row['id']}` | D{row['difficulty']} | {row['family_id']} "
              f"| `{row['representative']}` | {row['minutes']} 分钟 |")
        a("")
    a("纪律 (缓建不是免检):")
    a("")
    a("1. 缓建只调整**排产顺序**, 不改变门禁 —— 终防线 `--fail-on-pending` "
      "清零口径不变, 缓建成员最终仍须实搭或由策展按族级抽检政策书面豁免;")
    a("2. 申请缓建的前提: 同族代表已实搭 **Pass** 且落盘 "
      "`content_meta.physical_verified` 三字段; 代表 Fail 则整族全员实搭;")
    a("3. 片型直方图不含连接拓扑, 同族成员若含独有高危工序 (悬臂/合壳/"
      "大跨度), 策展应将其移出缓建名单;")
    a("4. 模型内容变更 (`final_assembly` / `steps`) 后族划分可能失效, "
      "重新生成本报告再议。")
    a("")
    a("## 6. 建议排产顺序")
    a("")
    a(f"1. 上架抽样包 ([`{SAMPLE_DOC}`]({SAMPLE_DOC}), 上架前必须);")
    a("2. 本报告第 4 节族代表中尚未覆盖的部分 (按风险分降序);")
    a("3. 单模型族的 D4+ 待复核成员;")
    a("4. 缓建成员收尾 (或按策展签核的族级抽检政策处理)。")
    a("")
    return "\n".join(lines) + "\n"


def print_text(families, reduction, risk_source, threshold, models_total):
    multi = [f for f in families if f["size"] > 1]
    singles = models_total - sum(f["size"] for f in multi)
    print("== D4+ 实物复核结构族去重包 (与 physical_sample_pack 互补: "
          "sample=上架抽样, family=去重) ==")
    print(f"阈值 {threshold} (完全连接); 全库 {models_total} 个模型 -> "
          f"{len(families)} 族 (多成员族 {len(multi)} 个, 单模型族 {singles} 个); "
          f"风险分: {risk_source}")
    print()
    print(f"{'族':<5} {'规模':>3} {'难度':<7} {'最低相似':>7}  成员 (*=代表, †=抽样包)")
    for fam in multi:
        cells = []
        for x in fam["members"]:
            mark = "*" if x["is_representative"] else ""
            mark += "†" if x["in_sample_pack"] else ""
            cells.append(x["id"] + mark)
        print(f"{fam['family_id']:<5} {fam['size']:>3} {fam['difficulty_span']:<7} "
              f"{fam['min_similarity']:>7.3f}  {' '.join(cells)}")
    print()
    print("-- 代表清单 (多成员族) --")
    print(f"{'族':<5} {'代表':<26} {'难度':<3} {'片数':>4} {'风险分':>5} 状态")
    for fam in multi:
        x = next(m for m in fam["members"] if m["is_representative"])
        extra = " [抽样包]" if x["in_sample_pack"] else ""
        if x["l2_flags"]:
            extra += " L2:" + ",".join(x["l2_flags"])
        print(f"{fam['family_id']:<5} {x['id']:<26} D{x['difficulty']:<2} "
              f"{x['total_pieces']:>4} {x['risk_score']:>5} {fmt_status(x)}"
              + extra)
    r = reduction
    print()
    print("-- 可削减人手估算 (D4+ 待复核口径, 缓建须策展签核, 不豁免全集清零) --")
    print(f"基线全集实搭   : {r['pending_d4plus']:>3} 个, "
          f"{r['baseline_minutes']} 分钟 ≈ {r['baseline_minutes'] / 60:.1f} 小时")
    print(f"族去重后必搭   : {r['must_build_count']:>3} 个, "
          f"{r['must_build_minutes']} 分钟 ≈ {r['must_build_minutes'] / 60:.1f} 小时")
    print(f"可缓建 (估算)  : {r['deferrable_count']:>3} 个, "
          f"{r['saved_minutes']} 分钟 ≈ {r['saved_minutes'] / 60:.1f} 小时 "
          f"(省 {r['saved_ratio']:.0%})")
    for row in r["deferrable"]:
        print(f"    {row['id']:<26} D{row['difficulty']} {row['family_id']} "
              f"代表 {row['representative']} ({row['minutes']} 分钟)")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="结构族聚类 + 每族代表 + 可削减实搭人手估算 "
                    "(与 physical_sample_pack 互补: sample=上架抽样, family=去重)")
    parser.add_argument("models_dir", nargs="?", default=str(ROOT / "data" / "models"))
    parser.add_argument("--catalog", default=None,
                        help="模型库目录 model_catalog.json (主题/名称来源)")
    parser.add_argument("--verification-dir", default=None)
    parser.add_argument("--threshold", type=float, default=DEFAULT_THRESHOLD)
    parser.add_argument("--risk-report", default=None, metavar="FILE")
    parser.add_argument("--json", action="store_true", dest="as_json")
    parser.add_argument("--markdown", default=None, metavar="FILE")
    args = parser.parse_args()

    models_dir = Path(args.models_dir)
    if not models_dir.is_dir():
        print(f"错误: 模型目录不存在: {models_dir}", file=sys.stderr)
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
    risk, flags, risk_source = load_risk_scores(models, args.risk_report)

    # 上架抽样包成员 (physical_sample_pack 默认口径): 必搭, 不参与缓建
    sample_ids = {m["id"] for m, _ in select_sample(models, themes, target=10)[0]}

    clusters, scores = cluster_families(feats, args.threshold)
    families = build_families(clusters, scores, feats_by_id, by_id, names,
                              verified, risk, flags, sample_ids)
    reduction = compute_reduction(families, sample_ids)

    if args.markdown:
        md = render_markdown(families, reduction, risk_source, args.threshold,
                             len(models), sample_ids)
        out = Path(args.markdown)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(md, encoding="utf-8")
        print(f"已生成: {out}")

    if args.as_json:
        multi = [f for f in families if f["size"] > 1]
        print(json.dumps({
            "threshold": args.threshold,
            "weights": {"tile_histogram": W_HIST, "theme_tags": W_TAG,
                        "difficulty": W_DIFF},
            "gates": {"min_shared_theme_tags": 1,
                      "max_difficulty_gap": MAX_DIFF_GAP},
            "linkage": "complete",
            "models_total": len(models),
            "family_count": len(families),
            "multi_family_count": len(multi),
            "duplicate_prototypes_folded": len(models) - len(families),
            "risk_source": risk_source,
            "sample_pack_ids": sorted(sample_ids),
            "reduction": reduction,
            "families": families,
        }, ensure_ascii=False, indent=2))
    else:
        print_text(families, reduction, risk_source, args.threshold, len(models))
    return 0


if __name__ == "__main__":
    sys.exit(main())
