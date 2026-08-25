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

用法: python3 tools/update_model_catalog.py  (在 magtile-studio 目录下运行)
"""

import json
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
}


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


def main():
    entries = []
    for path in sorted(MODELS_DIR.glob("*.json")):
        model = json.loads(path.read_text(encoding="utf-8"))
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


if __name__ == "__main__":
    main()
