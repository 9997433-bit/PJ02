#!/usr/bin/env python3
"""重建模型库目录 data/model_catalog.json。

扫描 data/models/*.json, 把每个模型的展示元数据 (id/name/name_en/
description/difficulty/total_pieces/step_count/tags) 登记进目录,
条目按 难度 -> 片数 -> id 排序, 保证 library CLI 与 CTest 用例
library_catalog_check 校验的字段与模型文件逐项一致。

用法: python3 tools/update_model_catalog.py  (在 magtile-studio 目录下运行)
"""

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MODELS_DIR = ROOT / "data" / "models"
CATALOG = ROOT / "data" / "model_catalog.json"

COMMENT = (
    "模型库目录: 商业版模型库界面 (magtile_app library) 的数据源。每个条目描述"
    "一个模型的展示元数据, file 相对本文件所在目录解析; 元数据必须与模型 JSON "
    "一致 (由 library CLI 与 CTest 用例 library_catalog_check 把关)。本文件由 "
    "tools/update_model_catalog.py 自动生成, 请勿手工编辑。"
)


def main():
    entries = []
    for path in sorted(MODELS_DIR.glob("*.json")):
        model = json.loads(path.read_text(encoding="utf-8"))
        entries.append({
            "id": model["id"],
            "file": f"models/{path.name}",
            "name": model["name"],
            "name_en": model.get("name_en", ""),
            "description": model.get("description", ""),
            "difficulty": model["difficulty"],
            "total_pieces": model["total_pieces"],
            "step_count": len(model["steps"]),
            "tags": model.get("tags", []),
        })
    entries.sort(key=lambda e: (e["difficulty"], e["total_pieces"], e["id"]))

    catalog = {
        "schema_version": 1,
        "comment": COMMENT,
        "models": entries,
    }
    CATALOG.write_text(json.dumps(catalog, ensure_ascii=False, indent=2) + "\n",
                       encoding="utf-8")
    total = sum(e["total_pieces"] for e in entries)
    print(f"已登记 {len(entries)} 个模型到 {CATALOG}")
    print(f"全库合计 {total} 片, 难度分布: " + ", ".join(
        f"D{d} x {sum(1 for e in entries if e['difficulty'] == d)}"
        for d in sorted({e['difficulty'] for e in entries})))


if __name__ == "__main__":
    main()
