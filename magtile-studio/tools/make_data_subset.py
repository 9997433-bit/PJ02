#!/usr/bin/env python3
"""打包用数据子集装配器: 按清单把 data/ 裁剪成安装包内容。

用途
----
Windows 安装包 (scripts/package_windows.md) 支持只随包分发模型库的一个
子集 (如免费层 30 模型, 见 docs/COMMERCIAL_PLAN.md §2.1 与
docs/FREE_TIER_MANIFEST.md)。本脚本把
完整 data/ 目录裁剪成一个自洽的安装布局:

    <out-dir>/
    ├── tile_catalog.json        磁力片形状目录 (整份复制, 运行必需)
    ├── model_catalog.json       模型库目录 (按清单过滤重写)
    ├── models/<id>.json         清单列出的模型
    └── thumbnails/<id>.png      对应缩略图 (缺失仅警告, 界面显示占位色)

model_catalog.json 必须与实际存在的模型文件一致 —— 运行时加载器
(src/core/model_catalog.cpp) 对目录里登记但文件缺失的条目直接抛错,
因此绝不能只删模型文件而不过滤目录; 本脚本保证两者同步。

清单格式: 每行一个模型 id (不带 .json 后缀), 支持空行与 # 注释。
示例见 platforms/windows/packaging/starter_models.txt。

调用方 (均不需要手工执行本脚本):
  - CPack 子集模式: platforms/windows/packaging/CPackWindows.cmake 在
    -DMAGTILE_PACKAGE_MODEL_SET=starter/清单路径 时于安装阶段调用;
  - WiX/MSI 路径: 先手工运行本脚本 staging, 再把 -d DataDir= 指向输出目录。

退出码: 0 成功; 1 参数/清单/数据错误 (错误信息一律打到 stderr)。
"""

from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path


def fail(message: str) -> "sys.NoReturn":
    print(f"make_data_subset: 错误: {message}", file=sys.stderr)
    raise SystemExit(1)


def read_manifest(manifest_path: Path) -> list[str]:
    """读取清单: 每行一个模型 id, 忽略空行与 # 注释, 拒绝重复。"""
    if not manifest_path.is_file():
        fail(f"清单文件不存在: {manifest_path}")
    ids: list[str] = []
    seen: set[str] = set()
    for line_no, raw in enumerate(
        manifest_path.read_text(encoding="utf-8").splitlines(), start=1
    ):
        entry = raw.split("#", 1)[0].strip()
        if not entry:
            continue
        if entry.endswith(".json"):
            fail(
                f"{manifest_path}:{line_no}: 清单只写模型 id (不带 .json 后缀): {entry}"
            )
        if entry in seen:
            fail(f"{manifest_path}:{line_no}: 模型 id 重复: {entry}")
        seen.add(entry)
        ids.append(entry)
    if not ids:
        fail(f"清单为空 (没有任何模型 id): {manifest_path}")
    return ids


def filter_catalog(catalog_file: Path, wanted: list[str], manifest_name: str) -> dict:
    """按清单过滤 model_catalog.json, 保持目录自身的条目顺序。

    清单里的 id 必须全部在目录中登记 —— 目录由 tools/update_model_catalog.py
    对全库自动生成, 未登记通常意味着 id 拼写错误或目录忘了重新生成。
    """
    with catalog_file.open(encoding="utf-8") as stream:
        catalog = json.load(stream)
    entries = catalog.get("models")
    if not isinstance(entries, list):
        fail(f"{catalog_file}: 缺少 models 数组, 目录文件损坏?")
    registered = {entry.get("id") for entry in entries}
    missing = [model_id for model_id in wanted if model_id not in registered]
    if missing:
        fail(
            f"以下清单模型未在 {catalog_file.name} 登记 (id 拼写错误? "
            f"或需重跑 tools/update_model_catalog.py): {', '.join(missing)}"
        )
    wanted_set = set(wanted)
    filtered = dict(catalog)
    filtered["models"] = [e for e in entries if e.get("id") in wanted_set]
    filtered["comment"] = (
        f"模型库目录 (打包子集): 由 tools/make_data_subset.py 按清单 "
        f"{manifest_name} 从完整 model_catalog.json 过滤生成, 只登记随包分发的 "
        f"{len(wanted)} 个模型。请勿手工编辑; 完整目录见源码仓库 data/。"
    )
    return filtered


def stage(data_dir: Path, manifest_path: Path, out_dir: Path) -> None:
    models_dir = data_dir / "models"
    thumbs_dir = data_dir / "thumbnails"
    tile_catalog = data_dir / "tile_catalog.json"
    model_catalog = data_dir / "model_catalog.json"
    for required in (models_dir, tile_catalog, model_catalog):
        if not required.exists():
            fail(f"data 目录不完整, 缺少 {required}")

    wanted = read_manifest(manifest_path)

    missing_models = [m for m in wanted if not (models_dir / f"{m}.json").is_file()]
    if missing_models:
        fail(
            "以下清单模型在 data/models/ 中不存在: " + ", ".join(missing_models)
        )

    filtered_catalog = filter_catalog(model_catalog, wanted, manifest_path.name)

    # 输出目录整体重建, 防止上一次更大的子集留下多余模型文件
    out_dir = out_dir.resolve()
    if out_dir == data_dir.resolve() or out_dir in data_dir.resolve().parents:
        fail(f"输出目录不能是源 data 目录或其父目录: {out_dir}")
    if out_dir.exists():
        shutil.rmtree(out_dir)
    (out_dir / "models").mkdir(parents=True)
    (out_dir / "thumbnails").mkdir()

    shutil.copy2(tile_catalog, out_dir / "tile_catalog.json")
    with (out_dir / "model_catalog.json").open("w", encoding="utf-8") as stream:
        json.dump(filtered_catalog, stream, ensure_ascii=False, indent=2)
        stream.write("\n")

    thumbs_copied = 0
    for model_id in wanted:
        shutil.copy2(models_dir / f"{model_id}.json", out_dir / "models")
        thumb = thumbs_dir / f"{model_id}.png"
        if thumb.is_file():
            shutil.copy2(thumb, out_dir / "thumbnails")
            thumbs_copied += 1
        else:
            # 非致命: 界面对缺失缩略图显示主题色占位 (model_catalog.cpp)
            print(
                f"make_data_subset: 警告: 缺少缩略图 {thumb.name}, 卡片将显示占位色",
                file=sys.stderr,
            )

    total_bytes = sum(f.stat().st_size for f in out_dir.rglob("*") if f.is_file())
    print(
        f"make_data_subset: 已装配 {len(wanted)} 个模型 / {thumbs_copied} 张缩略图 "
        f"→ {out_dir} (共 {total_bytes / 1024 / 1024:.1f} MiB)"
    )


def main() -> None:
    parser = argparse.ArgumentParser(
        description="按清单把完整 data/ 裁剪成安装包用的自洽数据子集"
    )
    parser.add_argument(
        "--data-dir", required=True, type=Path, help="完整数据目录 (仓库 data/)"
    )
    parser.add_argument(
        "--manifest",
        required=True,
        type=Path,
        help="模型 id 清单文件 (每行一个 id, 支持 # 注释)",
    )
    parser.add_argument(
        "--out-dir",
        required=True,
        type=Path,
        help="输出目录 (已存在时整体重建)",
    )
    args = parser.parse_args()
    stage(args.data_dir, args.manifest, args.out_dir)


if __name__ == "__main__":
    main()
