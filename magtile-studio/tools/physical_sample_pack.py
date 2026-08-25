#!/usr/bin/env python3
"""D4+ 实物复核 V1 上架优先抽样包 (Physical Sample Pack)。

背景: 全库 D4+ 模型实物复核是商用上架硬门槛 (软件 strict 全绿 != 真实
磁力片能搭, 见 docs/PHYSICAL_REBUILD_CHECKLIST.md)。全集清零由
tools/list_physical_pending.py --fail-on-pending 终防线把守; 本工具解决
"45 个从哪个先搭"的排产问题 —— 用确定性规则选出 V1 上架前必须优先
实搭的抽样包 (约 8~12 个), 并为真人桌边复核打印每个模型的备料 BOM
与逐步片型摘要。

抽样规则 (确定性, 重跑可复现; 依据见 docs/reports/PHYSICAL_SAMPLE_V1.md):
  S1  免费层 D4+ 全数 —— 免费层曝光最大, 一个不能漏
      (当前免费 30 个封顶 D3, S1 为空集; 规则常备, 免费层换血自动生效);
  S2  D5 全数 —— 片数与结构风险最高的旗舰;
  S3  付费 D4 按 总片数降序 补足名额 (上架前无真实下载量,
      片数是"旗舰热门 x 工程风险"的唯一可用代理指标),
      同主题最多 1 个 (与 S1/S2 已占主题合并计数, 保证结构原型覆盖),
      片数相同按 id 升序; 直至总数达到 --target (默认 10)。

"已复核"判定与 tools/list_physical_pending.py 完全同源 (直接 import 其
classify: content_meta.physical_verified == true, 或旁车验证文件哈希一致)。

用法:
    tools/physical_sample_pack.py [models_dir] [选项]
        models_dir              模型目录 (默认: 仓库 data/models)
        --catalog FILE          模型库目录 (主题来源, 默认 models_dir/../model_catalog.json)
        --verification-dir D    旁车验证记录目录 (默认 models_dir/../verification)
        --target N              抽样包目标规模 (默认 10, 建议 8~12)
        --no-bom                只输出抽样清单, 不打印逐模型 BOM 摘要
        --json                  机器可读 JSON 输出
        --markdown FILE         生成可签核 Markdown 报告
                                (docs/reports/PHYSICAL_SAMPLE_V1.md 即由此生成)
        --print-checklist [FILE]
                                输出逐步搭建签核工作单 Markdown (每模型逐步
                                勾选栏 + 问题记录栏 + 照片位; 省略 FILE 直出
                                stdout 并跳过常规报告, 便于重定向/打印;
                                docs/reports/PHYSICAL_SIGNOFF_WORKSHEET.md
                                即由此生成)
        --fail-on-missing-sample
                                抽样包内存在未实物复核模型时以退出码 1 结束
                                (release gate 将来挂接用; 默认仅报告不阻断)

退出码: 0 = 报告完成 / 1 = --fail-on-missing-sample 且抽样包有缺口 / 2 = 数据错误
"""

import argparse
import json
import sys
from collections import Counter
from datetime import date, datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from list_physical_pending import classify  # noqa: E402  (同一判定口径, 单一来源)

ROOT = Path(__file__).resolve().parent.parent
FREE_TAG = "免费"  # 与 tools/verify_free_tier.py 同一口径

# 分难度实搭耗时预算 (分钟), 与 PHYSICAL_REBUILD_CHECKLIST.md 第 2 节一致
TIME_BUDGET_MIN = {1: 10, 2: 20, 3: 40, 4: 70, 5: 120}

CHECKLIST_DOC = "PHYSICAL_REBUILD_CHECKLIST.md"
WORKSHEET_DOC = "PHYSICAL_SIGNOFF_WORKSHEET.md"


def load_json(path: Path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        print(f"错误: {path} 无法解析: {exc}", file=sys.stderr)
        sys.exit(2)


def load_tile_names(catalog_path: Path) -> dict:
    """片型 type -> 中文名 (备料 BOM 展示用); 目录缺失时退化为原始 type。"""
    if not catalog_path.is_file():
        return {}
    catalog = load_json(catalog_path)
    return {t["type"]: t.get("name_zh") or t["type"] for t in catalog.get("tiles", [])}


def select_sample(models: list, themes: dict, target: int):
    """按 S1/S2/S3 规则选抽样包; 返回 (sample, rule_hits)。"""
    eligible = [m for m in models if int(m.get("difficulty", 0)) >= 4]

    picked, used_themes = [], Counter()

    def take(model, layer):
        picked.append((model, layer))
        used_themes[themes.get(model["id"], "(未登记)")] += 1

    # S1: 免费层 D4+ 全数 (不受 target 与主题上限约束)
    for m in sorted(eligible, key=lambda m: (-int(m["difficulty"]), m["id"])):
        if FREE_TAG in m.get("tags", []):
            take(m, "S1")

    # S2: D5 全数
    for m in sorted(eligible, key=lambda m: m["id"]):
        if int(m["difficulty"]) >= 5 and all(p["id"] != m["id"] for p, _ in picked):
            take(m, "S2")

    # S3: 付费 D4 按片数降序补足, 同主题最多 1 个
    pool = sorted(
        (m for m in eligible
         if int(m["difficulty"]) == 4 and FREE_TAG not in m.get("tags", [])
         and all(p["id"] != m["id"] for p, _ in picked)),
        key=lambda m: (-int(m["total_pieces"]), m["id"]))
    for m in pool:
        if len(picked) >= target:
            break
        theme = themes.get(m["id"], "(未登记)")
        if used_themes[theme] >= 1:
            continue
        take(m, "S3")

    rule_hits = Counter(layer for _, layer in picked)
    order = lambda t: (-int(t[0]["difficulty"]), -int(t[0]["total_pieces"]), t[0]["id"])  # noqa: E731
    return sorted(picked, key=order), rule_hits


def step_bom(model: dict) -> list:
    """逐步片型摘要: [(step_no, [(type, color, count)], description)]。"""
    by_id = {t["id"]: t for t in model["final_assembly"]}
    rows = []
    for step in model.get("steps", []):
        counts = Counter()
        for tid in step.get("tiles_to_add", []):
            tile = by_id.get(tid)
            if tile is None:
                print(f"错误: {model['id']} 第 {step.get('step_number')} 步引用了"
                      f"不存在的片 id: {tid}", file=sys.stderr)
                sys.exit(2)
            counts[(tile["type"], tile.get("color", "?"))] += 1
        rows.append((
            step.get("step_number"),
            sorted(counts.items(), key=lambda kv: (-kv[1], kv[0])),
            step.get("description", ""),
        ))
    return rows


def total_bom(model: dict) -> list:
    """备料 BOM: [(type, total, [(color, count)])], 片数降序。"""
    by_type = {}
    for tile in model["final_assembly"]:
        by_type.setdefault(tile["type"], Counter())[tile.get("color", "?")] += 1
    return sorted(
        ((t, sum(c.values()), sorted(c.items(), key=lambda kv: (-kv[1], kv[0])))
         for t, c in by_type.items()),
        key=lambda row: (-row[1], row[0]))


def check_annotated(models: list, ver_dir: Path):
    """全库扫描已标注 physical_verified 的模型并核对一致性 (示范模型盘点)。"""
    annotated, warnings = [], []
    for m in models:
        cm = m.get("content_meta") or {}
        if not cm.get("physical_verified"):
            continue
        ok, via, w = classify(m, ver_dir)
        warnings += [f"{m['id']}: {x}" for x in w]
        at = cm.get("physical_verified_at", "")
        try:
            datetime.strptime(at, "%Y-%m-%d")
        except ValueError:
            warnings.append(f"{m['id']}: physical_verified_at 不是 ISO 日期: {at!r}")
        if not cm.get("physical_notes"):
            warnings.append(f"{m['id']}: 建议补 physical_notes (复核摘要, 见规程第 7 节)")
        annotated.append({"id": m["id"], "difficulty": int(m["difficulty"]),
                          "verified_at": at, "recognized": ok, "via": via})
    return annotated, warnings


def fmt_piece_counts(counts, tile_names) -> str:
    return " + ".join(
        f"{tile_names.get(t, t)}({color})x{n}" for (t, color), n in counts)


def build_entries(picked, themes, names, ver_dir):
    entries = []
    for m, layer in picked:
        ok, via, _ = classify(m, ver_dir)
        d = int(m["difficulty"])
        entries.append({
            "id": m["id"],
            "name": names.get(m["id"], m.get("name", m["id"])),
            "difficulty": d,
            "total_pieces": int(m["total_pieces"]),
            "steps": len(m.get("steps", [])),
            "theme": themes.get(m["id"], "(未登记)"),
            "free_tier": FREE_TAG in m.get("tags", []),
            "layer": layer,
            "est_minutes": TIME_BUDGET_MIN.get(d, 120),
            "verified": ok,
            "verified_via": via,
            "_model": m,
        })
    return entries


def render_markdown(entries, rule_hits, annotated, target, free_d4_count,
                    d4plus_total, pending_in_scope) -> str:
    missing = [e for e in entries if not e["verified"]]
    total_minutes = sum(e["est_minutes"] for e in entries)
    lines = []
    a = lines.append
    a("# V1 上架 D4+ 实物复核优先抽样包 (Physical Sample Pack V1)")
    a("")
    a(f"- 生成日期: {date.today().isoformat()}")
    a("- 生成工具: `tools/physical_sample_pack.py --markdown docs/reports/"
      "PHYSICAL_SAMPLE_V1.md` —— 模型库 / 免费层 / 复核状态变化后**重新生成**, "
      "勿手改; 签核进度以模型 `content_meta` 落盘为准 (重新生成后已复核模型的"
      "勾选表自动折叠为一行), 纸面勾选与工单链接归档到 QA 工单")
    a(f"- 复核规程: [`docs/{CHECKLIST_DOC}`](../{CHECKLIST_DOC}); "
      "已复核判定与 `tools/list_physical_pending.py` 同源 (同一 classify 函数)")
    a("")
    a("## 1. 定位")
    a("")
    a(f"全库 difficulty >= 4 共 **{d4plus_total} 个**, 其中 **{pending_in_scope} 个待"
      "实物复核** —— 软件 strict 全绿是入库必要条件, 不是充分条件, D4+ 逐个实搭"
      "复核是商用上架硬门槛。本抽样包把「先搭哪些」固化为确定性规则的工程产物: "
      "V1 上架前**优先**实搭并签核下表模型; 抽样包全绿**不豁免**全集清零 "
      "(`tools/run_release_gate.sh --fail-on-pending` 终防线仍以 D4+ 全集为准), "
      "只作为排产优先级与上架风险评估的可签核依据。")
    a("")
    a("## 2. 抽样规则 (确定性, 重跑可复现)")
    a("")
    a("| 层 | 规则 | 本次命中 |")
    a("| --- | --- | --- |")
    a(f"| S1 | 免费层 D4+ 全数 (曝光最大, 一个不能漏) | {rule_hits.get('S1', 0)} |")
    a(f"| S2 | D5 全数 (片数与结构风险最高的旗舰) | {rule_hits.get('S2', 0)} |")
    a("| S3 | 付费 D4 按总片数降序补足 (上架前无下载量, 片数为热门/风险代理指标), "
      f"同主题最多 1 个保证结构原型覆盖, 片数相同按 id 升序 | {rule_hits.get('S3', 0)} |")
    a("")
    a(f"目标规模 {target} 个 (8~12 区间)。**免费层说明**: 当前免费 30 个封顶 D3 "
      f"(免费层 D4+ = {free_d4_count} 个, S1 为空集); 免费层的实物风险由已复核的 "
      "D3 示范模型 (见第 5 节) 与 CONTENT_STRATEGY.md 4.3 节的 D3 抽检 30% 政策"
      "覆盖, 免费层选品换血引入 D4+ 时 S1 自动生效。")
    a("")
    a(f"## 3. 抽样清单 ({len(entries)} 个)")
    a("")
    a("| # | 模型 | 名称 | 难度 | 片数 | 步骤 | 主题 | 层 | 预计搭时 | 复核状态 |")
    a("| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |")
    for i, e in enumerate(entries, 1):
        status = f"已复核 ({e['verified_via']})" if e["verified"] else "**待复核**"
        a(f"| {i} | `{e['id']}` | {e['name']} | D{e['difficulty']} "
          f"| {e['total_pieces']} | {e['steps']} | {e['theme']} | {e['layer']} "
          f"| {e['est_minutes']} 分钟 | {status} |")
    a("")
    a(f"预计总耗时 (规程第 2 节难度预算): **{total_minutes} 分钟** "
      f"(约 {total_minutes / 60:.1f} 小时, 单人含敲击/提起/记录)。"
      "桌边核对时用一键命令打印每个模型的备料 BOM 与逐步片型摘要:")
    a("")
    a("```bash")
    a("python3 tools/physical_sample_pack.py                 # 抽样清单 + 逐模型 BOM 摘要")
    a("python3 tools/physical_sample_pack.py --json          # 机器可读 (含逐步 BOM)")
    a("```")
    a("")
    a("## 4. 逐模型签核勾选表")
    a("")
    a(f"检查项与判定标准以 [`docs/{CHECKLIST_DOC}`](../{CHECKLIST_DOC}) 对应章节为准; "
      "全部适用项 Pass 才可按第 5 节落盘 `physical_verified`。本节是**模型级**"
      f"签核摘要; 桌边随搭随填的**逐步级**原始记录 (逐步勾选/问题记录/照片位) 用"
      f"配套工作单 [`{WORKSHEET_DOC}`]({WORKSHEET_DOC}) "
      "(`tools/physical_sample_pack.py --print-checklist` 生成)。")
    a("")
    for e in entries:
        a(f"### {e['id']} — {e['name']} (D{e['difficulty']}, "
          f"{e['total_pieces']} 片, {e['steps']} 步)")
        a("")
        if e["verified"]:
            a(f"已复核 ({e['verified_via']}), 无需重复签核; 模型内容变更后三字段"
              "作废须重走。")
            a("")
            continue
        a("- [ ] §0 软件预检: default 与 strict 双档零 Error (strict 有豁免须注明)")
        a(f"- [ ] §2 逐步搭建: 只看教程完整搭完, 总耗时 ≤ {e['est_minutes']} 分钟预算, "
          "卡壳/掉片逐条记录")
        a("- [ ] §3 敲击测试: Pass (最高点 + 几何中部各 3 次)")
        a("- [ ] §4 提起测试: Pass / n-a (平铺类须教程注明不可移动)")
        a("- [ ] §5 拆解重搭 (D4+ 建议项): 第二次耗时 ≤ 第一次 80% 且零失效")
        a("- [ ] §6 复核记录归档: issue / QA 工单链接: ______")
        a("- [ ] §7 `content_meta.physical_verified` 三字段落盘 (操作见第 5 节)")
        a("")
        a("  复核人: ______  日期: ______  磁力片品牌/状态: ______")
        a("")
    a("## 5. 如何标记通过 (最短操作说明)")
    a("")
    a("**前提: 该模型全部适用项实搭 Pass。未实际搭过的模型严禁写 "
      "`physical_verified: true` —— 伪造复核结论比不复核更危险。**")
    a("")
    a("1. 编辑 `data/models/<model_id>.json`, 在 `content_meta` 下追加三个字段 "
      f"(schema 见 CONTENT_STRATEGY.md 5.1 节, 语义见规程第 7 节):")
    a("")
    a("```jsonc")
    a('"content_meta": {')
    a('  "physical_verified": true,')
    a('  "physical_verified_at": "' + date.today().isoformat() + '",   // 实际复核日期 (ISO 8601)')
    a('  "physical_notes": "品牌/新旧片 + 耗时 + 敲击/提起/拆解重搭结论 一句话"')
    a("}")
    a("```")
    a("")
    a("2. `python3 tools/list_physical_pending.py data/models` —— 确认该模型从"
      "「待复核」转入「已复核 (content_meta)」;")
    a("3. `python3 tools/physical_sample_pack.py` —— 确认抽样包缺口计数 -1。")
    a("")
    annotated_ok = [x for x in annotated if x["recognized"]]
    a("已标注示范 (工具一致性核对通过, 可对照其 `content_meta` 写法): "
      + "、".join(f"`{x['id']}` (D{x['difficulty']}, {x['verified_at']})"
                  for x in annotated_ok) + "。")
    a("")
    a("纪律 (规程第 7 节): 模型 `final_assembly` / `steps` 任何改动 (含生成器重跑) "
      "后三字段必须一并清除 —— 旧实物结论对新结构无效; 复核不通过不写字段, "
      "按失效编码反馈整改。")
    a("")
    a("## 6. 与发布门禁的挂钩")
    a("")
    a(f"当前抽样包缺口: **{len(missing)} / {len(entries)}**。"
      "`tools/physical_sample_pack.py --fail-on-missing-sample` 在抽样包存在未复核"
      "模型时退出码 1 (默认仅报告不阻断) —— release gate 可将其挂为「抽样包先行」"
      "中间闸门: 位于日常报告型缺口盘点之后、`--fail-on-pending` 全集终防线之前, "
      "V1 上架签核至少要求本闸门全绿 (挂接说明见 TESTING.md 第 5 节)。")
    a("")
    return "\n".join(lines) + "\n"


def md_cell(text: str, limit: int = 0) -> str:
    """Markdown 表格单元格安全化: 去换行/转义竖线; limit > 0 时截断。"""
    text = str(text).replace("\n", " ").replace("|", "\\|")
    if limit and len(text) > limit:
        text = text[: limit - 1] + "…"
    return text


def render_worksheet(entries, tile_names, target) -> str:
    """逐步搭建签核工作单: 每模型 逐步勾选栏 + 问题记录栏 + 照片位。

    与第 4 节模型级勾选表的分工: 那张表签"这个模型过没过", 本工作单是
    桌边随搭随填的原始记录载体 (打印或复制到 QA 工单后填写)。
    """
    pending = [e for e in entries if not e["verified"]]
    total_minutes = sum(e["est_minutes"] for e in pending)
    lines = []
    a = lines.append
    a("# V1 抽样包实物复核逐步签核工作单 (Physical Sign-off Worksheet)")
    a("")
    a(f"- 生成日期: {date.today().isoformat()}")
    a("- 生成工具: `tools/physical_sample_pack.py --print-checklist "
      f"docs/reports/{WORKSHEET_DOC}` —— 模型库 / 免费层 / 复核状态变化后"
      "**重新生成**, 勿手改; 仓库内只保存空白模板, 实际勾选与笔记**打印或"
      "复制到 QA 工单**后填写 (已复核模型重新生成时自动折叠为一行)")
    a("- 抽样口径: 与 [`PHYSICAL_SAMPLE_V1.md`](PHYSICAL_SAMPLE_V1.md) 同一"
      "确定性抽样规则 (S1/S2/S3), 判定标准以 "
      f"[`docs/{CHECKLIST_DOC}`](../{CHECKLIST_DOC}) 对应章节 (§0~§7) 为准; "
      "本工作单是其**逐步级**的原始记录载体, 模型级签核摘要仍看 "
      "PHYSICAL_SAMPLE_V1.md 第 4 节")
    a("- 照片归档约定: 每模型一个目录 `docs/reports/qa_photos/<model_id>/` "
      "(或 QA 工单附件, 「照片位」表填链接); 失效编码 F01~F12 见 "
      "BUILD_VERIFICATION.md 第 4 节")
    a("")
    a("## 0. 使用方法 (复核人开工前读一遍)")
    a("")
    a("1. **开始前**: 完成该模型「复核前置」三个勾选 (软件双档预检 + 环境), "
      "按「备料 BOM」逐行清点勾「备齐」—— 不多备, BOM 之外的片不上桌;")
    a("2. **搭建中**: 只看教程 (平板 tutorial GUI 或打印分步图, 不看模型 "
      "JSON), 每完成一步勾「完成」并记耗时; 卡壳 / 说明歧义 / 掉片**当场**"
      "写入「问题记录」, 非人为失误的掉片或坍塌记失效编码并拍照;")
    a("3. **成品后**: 静置 30 秒, 依次执行敲击 (§3) / 提起 (§4) / 拆解重搭 "
      "(§5), 在「固定动作测试」表圈选结果;")
    a("4. **收尾**: 补齐「照片位」与「结论与签核」; 通过 → 按 "
      "PHYSICAL_SAMPLE_V1.md 第 5 节把 `content_meta` 三字段落盘并重新生成"
      "两份报告; 不通过 → 失效编码 + 照片反馈设计师。**严禁未实搭勾选或"
      "事后补签** —— 伪造复核结论比不复核更危险。")
    a("")
    a(f"## 抽样总览 ({len(entries)} 个, 待复核 {len(pending)} 个, "
      f"待复核预算合计 {total_minutes} 分钟)")
    a("")
    a("| # | 模型 | 名称 | 难度 | 片数 | 步骤 | 耗时预算 | 复核状态 |")
    a("| --- | --- | --- | --- | --- | --- | --- | --- |")
    for i, e in enumerate(entries, 1):
        status = f"已复核 ({e['verified_via']})" if e["verified"] else "**待复核**"
        a(f"| {i} | `{e['id']}` | {e['name']} | D{e['difficulty']} "
          f"| {e['total_pieces']} | {e['steps']} | {e['est_minutes']} 分钟 "
          f"| {status} |")
    a("")
    for i, e in enumerate(entries, 1):
        m = e["_model"]
        a(f"## {i}. {e['id']} — {e['name']} (D{e['difficulty']}, "
          f"{e['total_pieces']} 片, {e['steps']} 步, "
          f"预算 {e['est_minutes']} 分钟)")
        a("")
        if e["verified"]:
            a(f"已复核 ({e['verified_via']}), 本轮无需填写; "
              "`final_assembly` / `steps` 变更后三字段作废, "
              "重新生成本工作单再走一遍。")
            a("")
            continue
        a("复核人: ______  日期: ______  磁力片品牌/状态: ______ "
          "(新片 / 旧片; 弱磁 strict 预检: 通过 / 豁免)")
        a("")
        a(f"### {i}.1 复核前置 (§0 软件预检 + §1 准备)")
        a("")
        a(f"- [ ] default 档零 Error: `./build/magtile_app validate "
          f"data/models/{e['id']}.json --data-dir data`")
        a("- [ ] strict 档零 Error (同命令加 `--profile strict`; "
          "有豁免须注明: ______)")
        a("- [ ] §1 环境合规: 平整硬质桌面 / 15~30°C / 秒表与录像机位就绪 / "
          "只看教程不看设计源文件")
        a("")
        a(f"### {i}.2 备料 BOM (共 {e['total_pieces']} 片, 逐行清点)")
        a("")
        a("| 片型 | 颜色分布 | 数量 | 备齐 |")
        a("| --- | --- | ---: | :---: |")
        for t, n, colors in total_bom(m):
            color_txt = ", ".join(f"{c} {k}" for c, k in colors)
            a(f"| {md_cell(tile_names.get(t, t))} | {md_cell(color_txt)} "
              f"| {n} | ☐ |")
        a("")
        a(f"### {i}.3 逐步搭建签核 ({e['steps']} 步, "
          f"总耗时预算 {e['est_minutes']} 分钟)")
        a("")
        a("| 步 | +片 | 本步片型 | 步骤摘要 | 完成 | 耗时(分) "
          "| 问题记录 (卡壳/歧义/掉片, 失效编码) |")
        a("| ---: | ---: | --- | --- | :---: | --- | --- |")
        for no, counts, desc in step_bom(m):
            added = sum(n for _, n in counts)
            a(f"| {no} | +{added} | {md_cell(fmt_piece_counts(counts, tile_names))} "
              f"| {md_cell(desc, 26)} | ☐ | | |")
        a(f"| 合计 | {e['total_pieces']} | — | — | — "
          f"| ____ / {e['est_minutes']} | 超时记 Warning 并反馈步骤拆分 |")
        a("")
        a(f"### {i}.4 固定动作测试 (§3 敲击 / §4 提起 / §5 拆解重搭)")
        a("")
        a("| 测试 | 结果 (圈选) | 细节 / 失效编码 |")
        a("| --- | --- | --- |")
        a("| §3 敲击 (静置 30 秒后, 最高点 + 几何中部侧面各 3 次) "
          "| Pass / Conditional / Fail | |")
        a("| §4 提起 (托底座两侧提 5cm, 悬停 10 秒) "
          "| Pass / Fail / n-a (平铺类须教程注明不可移动) | |")
        a("| §5 拆解重搭 (D4+ 建议项, 逆序拆解后二搭) "
          "| 第二次 ____ 分钟; ≤ 第一次 80%: 是 / 否; 零失效: 是 / 否 | |")
        a("")
        a(f"### {i}.5 照片位 (拍到后勾选并填路径 / 工单附件链接)")
        a("")
        a(f"| 照片 | 何时必拍 | 建议文件名 (`qa_photos/{e['id']}/`) "
          "| 已拍 | 路径 / 链接 |")
        a("| --- | --- | --- | :---: | --- |")
        a("| 成品全景 | 必拍 | `final_overview.jpg` | ☐ | |")
        a("| 敲击后状态 (最高点 + 中部敲击点) | 必拍 | `after_knock.jpg` "
          "| ☐ | |")
        a("| 提起悬停中 | 提起测试适用时 | `lift_hold.jpg` | ☐ | |")
        a("| 失效瞬间 (每次失效一张) | 有失效时 | `fail_step<NN>_F<XX>.jpg` "
          "| ☐ | |")
        a("")
        a(f"### {i}.6 结论与签核")
        a("")
        a("- [ ] 通过 —— 全部适用项 Pass, 已按 PHYSICAL_SAMPLE_V1.md 第 5 节"
          "写入 `content_meta` 三字段 (physical_verified / _at / _notes)")
        a("- [ ] 不通过 —— 失效编码: ______, 已反馈设计师 "
          "(issue / 工单: ______), 不写 verified 字段")
        a("- §6 复核记录归档: issue / QA 工单链接: ______")
        a("- 复核人签名: ______  完成日期: ______")
        a("")
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(
        description="D4+ 实物复核 V1 上架优先抽样包 (清单 + 逐模型 BOM 摘要)")
    parser.add_argument("models_dir", nargs="?", default=str(ROOT / "data" / "models"))
    parser.add_argument("--catalog", default=None,
                        help="模型库目录 model_catalog.json (主题来源)")
    parser.add_argument("--verification-dir", default=None)
    parser.add_argument("--target", type=int, default=10)
    parser.add_argument("--no-bom", action="store_true")
    parser.add_argument("--json", action="store_true", dest="as_json")
    parser.add_argument("--markdown", default=None, metavar="FILE")
    parser.add_argument("--print-checklist", nargs="?", const="-", default=None,
                        metavar="FILE",
                        help="输出逐步搭建签核工作单 Markdown (勾选栏/问题记录/"
                             "照片位); 省略 FILE 直出 stdout 并跳过常规报告")
    parser.add_argument("--fail-on-missing-sample", action="store_true")
    args = parser.parse_args()

    models_dir = Path(args.models_dir)
    if not models_dir.is_dir():
        print(f"错误: 模型目录不存在: {models_dir}", file=sys.stderr)
        return 2
    if args.target < 1:
        print(f"错误: --target 必须 >= 1 (给的是 {args.target})", file=sys.stderr)
        return 2
    ver_dir = Path(args.verification_dir) if args.verification_dir \
        else models_dir.parent / "verification"
    catalog_path = Path(args.catalog) if args.catalog \
        else models_dir.parent / "model_catalog.json"

    models = [load_json(p) for p in sorted(models_dir.glob("*.json"))]
    themes, names = {}, {}
    if catalog_path.is_file():
        for entry in load_json(catalog_path).get("models", []):
            themes[entry["id"]] = entry.get("theme", "(未登记)")
            names[entry["id"]] = entry.get("name", entry["id"])
    tile_names = load_tile_names(models_dir.parent / "tile_catalog.json")

    eligible = [m for m in models if int(m.get("difficulty", 0)) >= 4]
    pending_in_scope = sum(1 for m in eligible if not classify(m, ver_dir)[0])
    free_d4 = sum(1 for m in eligible if FREE_TAG in m.get("tags", []))

    picked, rule_hits = select_sample(models, themes, args.target)
    entries = build_entries(picked, themes, names, ver_dir)
    annotated, ann_warnings = check_annotated(models, ver_dir)
    missing = [e for e in entries if not e["verified"]]

    if args.markdown:
        md = render_markdown(entries, rule_hits, annotated, args.target,
                             free_d4, len(eligible), pending_in_scope)
        out = Path(args.markdown)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(md, encoding="utf-8")
        print(f"已生成: {out}")

    if args.print_checklist:
        ws = render_worksheet(entries, tile_names, args.target)
        if args.print_checklist == "-":
            if args.as_json:
                print("错误: --print-checklist 直出 stdout 时不能与 --json 混用 "
                      "(给 --print-checklist 一个 FILE 即可共存)", file=sys.stderr)
                return 2
            sys.stdout.write(ws)
            return 1 if (args.fail_on_missing_sample and missing) else 0
        out = Path(args.print_checklist)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(ws, encoding="utf-8")
        print(f"已生成: {out}")

    if args.as_json:
        payload = {
            "target": args.target,
            "d4plus_total": len(eligible),
            "d4plus_pending": pending_in_scope,
            "free_tier_d4plus": free_d4,
            "rule_hits": dict(rule_hits),
            "sample_size": len(entries),
            "missing_sample_count": len(missing),
            "annotated_models": annotated,
            "warnings": ann_warnings,
            "sample": [],
        }
        for e in entries:
            item = {k: v for k, v in e.items() if k != "_model"}
            item["bom"] = [
                {"type": t, "count": n,
                 "colors": [{"color": c, "count": k} for c, k in colors]}
                for t, n, colors in total_bom(e["_model"])]
            item["step_bom"] = [
                {"step": no,
                 "tiles": [{"type": t, "color": c, "count": n}
                           for (t, c), n in counts],
                 "description": desc}
                for no, counts, desc in step_bom(e["_model"])]
            payload["sample"].append(item)
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print("== V1 上架 D4+ 实物复核优先抽样包 "
              f"(规程: docs/{CHECKLIST_DOC}) ==")
        print(f"D4+ 共 {len(eligible)} 个 (待复核 {pending_in_scope}); "
              f"免费层 D4+ {free_d4} 个; 抽样目标 {args.target} 个, "
              f"命中 S1={rule_hits.get('S1', 0)} S2={rule_hits.get('S2', 0)} "
              f"S3={rule_hits.get('S3', 0)}")
        print()
        print(f"{'#':<3} {'模型':<24} {'难度':<3} {'片数':>4} {'步骤':>4} "
              f"{'主题':<6} {'层':<3} {'预计':>5} 状态")
        for i, e in enumerate(entries, 1):
            status = "已复核" if e["verified"] else "待复核"
            print(f"{i:<3} {e['id']:<24} D{e['difficulty']:<2} "
                  f"{e['total_pieces']:>4} {e['steps']:>4} "
                  f"{e['theme']:<6} {e['layer']:<3} "
                  f"{e['est_minutes']:>3}min {status}")
        total_minutes = sum(e["est_minutes"] for e in entries)
        print(f"\n预计总耗时: {total_minutes} 分钟 "
              f"(约 {total_minutes / 60:.1f} 小时, 难度预算口径见规程第 2 节)")

        if annotated:
            print(f"\n-- 已标注 physical_verified 的模型 ({len(annotated)}, "
                  "一致性核对) --")
            for x in annotated:
                flag = "OK " if x["recognized"] else "!!"
                print(f"  [{flag}] {x['id']:<24} D{x['difficulty']} "
                      f"{x['verified_at']} via {x['via']}")
        if ann_warnings:
            print(f"\n-- 警告 ({len(ann_warnings)}) --")
            for w in ann_warnings:
                print(f"  [WARN] {w}")

        if not args.no_bom:
            for i, e in enumerate(entries, 1):
                m = e["_model"]
                print("\n" + "-" * 66)
                print(f"[{i}/{len(entries)}] {e['id']} {e['name']} "
                      f"(D{e['difficulty']}, {e['total_pieces']} 片, "
                      f"{e['steps']} 步, 预计 {e['est_minutes']} 分钟, "
                      + ("已复核)" if e["verified"] else "待复核)"))
                print(f"  备料 BOM (共 {e['total_pieces']} 片):")
                for t, n, colors in total_bom(m):
                    color_txt = ", ".join(f"{c} {k}" for c, k in colors)
                    print(f"    {tile_names.get(t, t):<8} x{n:<3} ({color_txt})")
                print("  逐步核对:")
                for no, counts, desc in step_bom(m):
                    added = sum(n for _, n in counts)
                    short = desc if len(desc) <= 34 else desc[:33] + "…"
                    print(f"    第{no:>2}步 +{added:<2} "
                          f"{fmt_piece_counts(counts, tile_names)}")
                    print(f"          {short}")

        print(f"\n抽样包缺口: {len(missing)} / {len(entries)}"
              + (" (存在缺口, --fail-on-missing-sample 生效)"
                 if args.fail_on_missing_sample and missing else ""))

    if args.fail_on_missing_sample and missing:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
