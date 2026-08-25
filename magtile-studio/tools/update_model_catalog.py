#!/usr/bin/env python3
"""重建模型库目录 data/model_catalog.json。

扫描 data/models/*.json, 把每个模型的展示元数据 (id/name/name_en/
description/difficulty/total_pieces/step_count/theme/tags/thumbnail)
登记进目录, 条目按 难度 -> 片数 -> id 排序, 保证 library CLI 与
CTest 用例 library_catalog_check 校验的字段与模型文件逐项一致。

主题 (theme): 模型库卡片的主题角标与主题色依据。模型 JSON 自带
theme 字段时直接采用; 否则按 TAG_TO_THEME 关键词表从标签推导,
兜底取第一个标签 —— 保证目录中每个条目都有主题。

缩略图 (thumbnail): data/thumbnails/<id>.png 存在时登记相对路径
(相对 data 目录), 由 tools/generate_thumbnails.py 生成。

矩阵进度 (CONTENT_GAP_AUDIT §7.3 的机检化落地): 目录重建后, 若模型
带 content_meta.series (schema v2 的策略主题正字段, 13 主题词表见
MATRIX_THEMES), 追加输出 主题 × 难度 (D1–D5) 矩阵进度表, 对照
docs/CONTENT_STRATEGY.md §2.2 的 520 终态目标; series 尚未回填时
仅提示一句, 不影响目录重建。--matrix-report 可另存 markdown 快照
(默认落点 docs/reports/CONTENT_MATRIX_PROGRESS.md)。

用法: python3 tools/update_model_catalog.py [--matrix-report [FILE]]
(在 magtile-studio 目录下运行)
"""

import argparse
import datetime
import json
import unicodedata
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MODELS_DIR = ROOT / "data" / "models"
THUMBS_DIR = ROOT / "data" / "thumbnails"
CATALOG = ROOT / "data" / "model_catalog.json"

COMMENT = (
    "模型库目录: 商业版模型库界面 (magtile_app library) 的数据源。每个条目描述"
    "一个模型的展示元数据, file 与 thumbnail 相对本文件所在目录解析; 元数据必须"
    "与模型 JSON 一致 (由 library CLI 与 CTest 用例 library_catalog_check 把关)。"
    "theme 为卡片主题 (由标签推导), thumbnail 由 tools/generate_thumbnails.py "
    "生成。本文件由 tools/update_model_catalog.py 自动生成, 请勿手工编辑。"
)

# 标签关键词 -> 规范主题。按模型标签顺序取第一个命中的关键词,
# 全部未命中时退回第一个标签, 保证每个模型都有主题。
TAG_TO_THEME = {
    "城堡": "城堡王国",
    "吊桥": "城堡王国",
    "门楼": "城堡王国",
    "建筑地标": "建筑地标",
    "世界地标": "建筑地标",
    "金字塔": "建筑地标",
    "五重塔": "建筑地标",
    "宝塔": "建筑地标",
    "摩天大楼": "建筑地标",
    "未来建筑": "建筑地标",
    "穹顶": "建筑地标",
    "桥梁": "工程结构",
    "悬索桥": "工程结构",
    "古代工程": "工程结构",
    "工程": "工程结构",
    "自然": "自然世界",
    "昆虫": "自然世界",
    "恐龙": "自然世界",
    "动物世界": "自然世界",
    "航天": "航天探索",
    "火箭": "航天探索",
    "着陆器": "航天探索",
    "航天器": "航天探索",
    "发射台": "航天探索",
    "城市": "城市生活",
    "交通": "城市生活",
    "火车": "城市生活",
    "救援": "城市生活",
    "职业体验": "城市生活",
    "游乐园": "游乐园",
    "摩天轮": "游乐园",
    "滚珠": "滚珠乐园",
    "滚珠乐园": "滚珠乐园",
    "帆船": "海洋航行",
    "海洋": "海洋航行",
    "港口": "海洋航行",
    "海岸": "海洋航行",
    "灯塔": "海洋航行",
    "科学探索": "航天探索",
    "天文": "航天探索",
    "田园": "田园",
    "风车": "田园",
}


MATRIX_REPORT_DEFAULT = "docs/reports/CONTENT_MATRIX_PROGRESS.md"
SERIES_MAP = ROOT / "data" / "content_series_map.json"

# CONTENT_STRATEGY.md §2.2 主题 × 难度分布矩阵 (终态目标 520 个)。
# 每项: (series 词值, 中文主题名, (D1, D2, D3, D4, D5) 目标)。
# series 词值与 data/content_series_map.json 权威词表逐条一致 (该文件
# 是 content_meta.series 合法取值的唯一来源, 本表只补充 §2.2 的难度
# 目标); 词表文件在场时以其为准 (build_series_index), 兼收中文主题名。
MATRIX_THEMES = [
    ("castle_fortress", "城堡与要塞", (6, 10, 14, 8, 4)),
    ("land_transport", "陆地交通", (8, 12, 12, 8, 2)),
    ("sea_air_transport", "海空交通", (4, 8, 10, 8, 2)),
    ("spacecraft", "航天器", (4, 8, 10, 8, 4)),
    ("animal_world", "动物世界", (10, 14, 14, 8, 2)),
    ("architecture_landmark", "建筑地标", (4, 10, 14, 12, 10)),
    ("bridge_engineering", "桥梁工程", (2, 8, 12, 10, 8)),
    ("geometric_art", "几何艺术", (8, 12, 12, 8, 4)),
    ("marble_run", "滚珠乐园", (2, 8, 12, 10, 6)),
    ("plant_garden", "植物花园", (8, 10, 10, 4, 0)),
    ("festival_seasonal", "节日限定", (8, 10, 10, 6, 2)),
    ("utility_items", "实用功能", (10, 12, 10, 4, 0)),
    ("fantasy_machinery", "幻想与机械", (4, 8, 16, 10, 8)),
]


def build_series_index():
    """series 词值 -> 矩阵行下标, 及矩阵外合法桶的显示名。

    以 data/content_series_map.json 权威词表为准: matrix_bucket 为 null
    的条目按中文名对齐 §2.2 矩阵行, 非 null 的登记为矩阵外合法桶;
    词表缺失时退回 MATRIX_THEMES 内置词值。中文主题名恒可识别。
    """
    index = {}
    for i, (slug, cn, _targets) in enumerate(MATRIX_THEMES):
        index[slug] = i
        index[cn] = i
    bucket_names = {}
    if SERIES_MAP.is_file():
        name_to_row = {cn: i for i, (_s, cn, _t) in enumerate(MATRIX_THEMES)}
        series = json.loads(SERIES_MAP.read_text(encoding="utf-8"))["series"]
        for slug, info in series.items():
            name = info.get("display_name_zh", slug)
            if info.get("matrix_bucket") is None:
                row = name_to_row.get(name)
                if row is not None:
                    index[slug] = row
            else:
                bucket_names[slug] = name
    return index, bucket_names


def derive_theme(model):
    """模型 JSON -> 主题: 自带 theme 优先, 其次标签关键词, 兜底首个标签。"""
    explicit = model.get("theme", "")
    if explicit:
        return explicit
    tags = model.get("tags", [])
    for tag in tags:
        theme = TAG_TO_THEME.get(tag)
        if theme:
            return theme
    return tags[0] if tags else "未分类"


def collect_matrix(series_records):
    """(series, difficulty) 序列 -> 矩阵统计。

    返回 (counts, extra, missing): counts 为 13 主题 × D1–D5 计数,
    extra 为矩阵外 series 值计数 (词表登记的桶带中文显示名, 含难度
    越界的异常记录), missing 为未标注 series 的模型数。
    """
    index, bucket_names = build_series_index()
    counts = [[0] * 5 for _ in MATRIX_THEMES]
    extra = Counter()
    missing = 0
    for series, difficulty in series_records:
        if not series:
            missing += 1
            continue
        row = index.get(series)
        if row is None:
            name = bucket_names.get(series)
            extra[f"{name} ({series})" if name else series] += 1
        elif 1 <= difficulty <= 5:
            counts[row][difficulty - 1] += 1
        else:
            extra[f"{series} (难度越界 D{difficulty})"] += 1
    return counts, extra, missing


def matrix_rows(counts, markdown=False):
    """矩阵计数 -> 逐行单元格文本 (含合计行); markdown 模式给超编格加粗。"""
    rows = []
    col_cur = [0] * 5
    col_target = [0] * 5
    for (_slug, name, targets), cur in zip(MATRIX_THEMES, counts):
        cells = []
        for d in range(5):
            cell = f"{cur[d]}/{targets[d]}"
            if markdown and cur[d] > targets[d]:
                cell = f"**{cell}**"
            cells.append(cell)
            col_cur[d] += cur[d]
            col_target[d] += targets[d]
        row_cur, row_target = sum(cur), sum(targets)
        rows.append([name] + cells + [f"{row_cur}/{row_target}",
                                      f"{round(row_cur / row_target * 100)}%"])
    total_cur, total_target = sum(col_cur), sum(col_target)
    total_name = "**合计**" if markdown else "合计"
    rows.append([total_name]
                + [f"{col_cur[d]}/{col_target[d]}" for d in range(5)]
                + [f"{total_cur}/{total_target}",
                   f"{round(total_cur / total_target * 100)}%"])
    return rows


def _disp_width(text):
    """终端显示宽度 (东亚宽字符计 2 列), 用于矩阵表对齐。"""
    return sum(2 if unicodedata.east_asian_width(ch) in ("W", "F") else 1
               for ch in text)


def format_matrix_terminal(rows):
    """矩阵行 -> 终端对齐文本行 (首列左对齐, 数字列右对齐)。"""
    header = ["主题", "D1", "D2", "D3", "D4", "D5", "合计", "完成度"]
    widths = [max(_disp_width(r[i]) for r in [header] + rows)
              for i in range(len(header))]
    lines = []
    for row in [header] + rows:
        cells = []
        for i, cell in enumerate(row):
            pad = " " * (widths[i] - _disp_width(cell))
            cells.append(cell + pad if i == 0 else pad + cell)
        lines.append("  ".join(cells).rstrip())
    return lines


def matrix_note_lines(total, extra, missing):
    """series 覆盖情况 -> 提示行 (矩阵外 series 与未标注计数)。"""
    lines = []
    if extra:
        listed = ", ".join(f"{value} x {count}"
                           for value, count in sorted(extra.items(),
                                                      key=lambda kv: (-kv[1], kv[0])))
        lines.append(f"矩阵外 series (不计入 13 主题矩阵): {listed}")
    if missing:
        lines.append(f"未标注 content_meta.series: {missing}/{total} 个 "
                     f"(回填底稿见 docs/reports/CONTENT_GAP_AUDIT.md 附录 A)")
    return lines


def write_matrix_report(path, series_records, counts, extra, missing):
    """矩阵进度 markdown 快照 (CONTENT_GAP_AUDIT §7.3 的机检产物)。"""
    total = len(series_records)
    tagged = total - missing
    today = datetime.date.today().isoformat()
    lines = [
        "# 内容矩阵进度: 主题 × 难度 (自动生成)",
        "",
        f"- 生成时间: {today}",
        f"- 数据源: `data/models/` 全库 {total} 个模型的 "
        "`content_meta.series` × `difficulty`",
        "- 对照标尺: [CONTENT_STRATEGY.md](../CONTENT_STRATEGY.md) §2.2 "
        "主题 × 难度分布矩阵 (13 主题 × D1–D5, 终态目标 520)",
        f"- series 覆盖: {tagged}/{total} 个模型已标注 `content_meta.series`",
        "- 本文件由 `tools/update_model_catalog.py --matrix-report` 自动生成, "
        "请勿手工编辑",
        "",
    ]
    if tagged == 0:
        lines += [
            "## 矩阵进度暂不可用",
            "",
            f"全库 {total} 个模型的 `content_meta.series` 均未回填, 无法机检"
            "主题 × 难度矩阵进度。回填 (底稿见 "
            "[CONTENT_GAP_AUDIT.md](CONTENT_GAP_AUDIT.md) 附录 A, 权威词表见 "
            "`data/content_series_map.json`) 后重跑 "
            "`python3 tools/update_model_catalog.py --matrix-report` 即自动"
            "输出进度表。",
        ]
    else:
        header = "| 主题 | D1 | D2 | D3 | D4 | D5 | 合计 | 完成度 |"
        rule = "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |"
        lines += ["## 主题 × 难度矩阵: 现状 / 520 目标", "",
                  "每格为 `现状/目标`, 超编格 **加粗**。", "",
                  header, rule]
        lines += ["| " + " | ".join(row) + " |"
                  for row in matrix_rows(counts, markdown=True)]
        notes = matrix_note_lines(total, extra, missing)
        if notes:
            lines += [""] + [f"- {note}" for note in notes]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(
        description="重建 data/model_catalog.json 并输出主题 × 难度矩阵进度")
    parser.add_argument(
        "--matrix-report", nargs="?", const=MATRIX_REPORT_DEFAULT,
        metavar="FILE",
        help=f"另存矩阵进度 markdown 快照 (缺省落点 {MATRIX_REPORT_DEFAULT}, "
             "相对路径按仓库根目录解析)")
    args = parser.parse_args()

    entries = []
    series_records = []
    for path in sorted(MODELS_DIR.glob("*.json")):
        model = json.loads(path.read_text(encoding="utf-8"))
        content_meta = model.get("content_meta") or {}
        series_records.append((content_meta.get("series"), model["difficulty"]))
        entry = {
            "id": model["id"],
            "file": f"models/{path.name}",
            "name": model["name"],
            "name_en": model.get("name_en", ""),
            "description": model.get("description", ""),
            "difficulty": model["difficulty"],
            "total_pieces": model["total_pieces"],
            "step_count": len(model["steps"]),
            "theme": derive_theme(model),
            "tags": model.get("tags", []),
        }
        thumbnail = THUMBS_DIR / f"{model['id']}.png"
        if thumbnail.is_file():
            entry["thumbnail"] = f"thumbnails/{thumbnail.name}"
        entries.append(entry)
    entries.sort(key=lambda e: (e["difficulty"], e["total_pieces"], e["id"]))

    catalog = {
        "schema_version": 1,
        "comment": COMMENT,
        "models": entries,
    }
    CATALOG.write_text(json.dumps(catalog, ensure_ascii=False, indent=2) + "\n",
                       encoding="utf-8")
    total = sum(e["total_pieces"] for e in entries)
    with_thumbs = sum(1 for e in entries if "thumbnail" in e)
    print(f"已登记 {len(entries)} 个模型到 {CATALOG}")
    print(f"全库合计 {total} 片, 难度分布: " + ", ".join(
        f"D{d} x {sum(1 for e in entries if e['difficulty'] == d)}"
        for d in sorted({e['difficulty'] for e in entries})))
    print(f"主题分布: " + ", ".join(
        f"{t} x {sum(1 for e in entries if e['theme'] == t)}"
        for t in sorted({e['theme'] for e in entries})))
    print(f"缩略图: {with_thumbs}/{len(entries)} 个条目已登记 "
          f"(缺失的请运行 tools/generate_thumbnails.py)")

    counts, extra, missing = collect_matrix(series_records)
    tagged = len(series_records) - missing
    if tagged == 0:
        print(f"矩阵进度: 全库 {len(series_records)} 个模型均未标注 "
              "content_meta.series, 跳过主题 × 难度矩阵 "
              "(回填后自动输出; 底稿见 docs/reports/CONTENT_GAP_AUDIT.md 附录 A)")
    else:
        print(f"主题 × 难度矩阵进度 (现状/目标, 对照 CONTENT_STRATEGY §2.2 "
              f"终态 520; series 覆盖 {tagged}/{len(series_records)}):")
        for line in format_matrix_terminal(matrix_rows(counts)):
            print("  " + line)
        for note in matrix_note_lines(len(series_records), extra, missing):
            print("  " + note)

    if args.matrix_report:
        report_path = Path(args.matrix_report)
        if not report_path.is_absolute():
            report_path = ROOT / report_path
        write_matrix_report(report_path, series_records, counts, extra, missing)
        print(f"矩阵进度快照已写入 {report_path}")


if __name__ == "__main__":
    main()
