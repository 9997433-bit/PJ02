#!/usr/bin/env python3
"""技法标注守卫脚手架 —— content_meta.technique_tags.primary 缺失报告。

CONTENT_STRATEGY.md §1.2 规定每个模型声明恰好一个主技法
(content_meta.technique_tags.primary, §5.1 schema), 主技法是技法配额
(§4.3) 与唯一性检查主题/技法拥挤度统计 (tests/test_library_uniqueness.py)
的计量单位 —— 缺标注的模型不参与拥挤度统计, 批内技法节奏只能靠
策展人按多样性账本人工核对。

本工具是全库技法标注回填前的守卫脚手架: 只报告缺失, 不回填、不管
词值 (T01–T18 受控词表机检待回填落地后另行挂闸, 同 series 归类机检
"先回填后 strict 闸门"的推进次序, 见 TESTING.md 3.19)。检查口径:

  * primary 为非空字符串 -> 已标注;
  * technique_tags 整体缺失 / 不是对象 / primary 缺失、null、空串
    或非字符串 -> 计为缺失, 逐条报告 (区分两类: technique_tags
    整体缺席 vs 对象存在但 primary 缺失/非法)。

默认 warn-only (报告不阻断, 恒退出 0), 便于回填期间随时复跑看进度;
--strict 在存在缺失时退出 1, 供回填完成后接入批次评审/CI 硬闸门。

退出码:
  0  检查完成 (默认模式下缺失只 WARN 不失败);
  1  --strict 模式下存在缺失;
  2  结构错误 (模型目录为空 / 文件不可读)。

用法:
  python3 tools/check_technique_tags.py [模型目录] [--strict]
"""

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

MISSING_LIST_LIMIT = 20     # 缺失逐条列表上限 (回填前全库缺失, 防刷屏)


def classify(model):
    """返回 (状态, 说明)。状态: "ok" | "no_tags" | "no_primary"。"""
    meta = model.get("content_meta") or {}
    tags = meta.get("technique_tags")
    if tags is None:
        return "no_tags", "缺失 content_meta.technique_tags"
    if not isinstance(tags, dict):
        return "no_tags", (f"content_meta.technique_tags 应为对象, "
                           f"实为 {type(tags).__name__}")
    primary = tags.get("primary")
    if isinstance(primary, str) and primary.strip():
        return "ok", ""
    return "no_primary", (f"technique_tags 存在但 primary 缺失/非法 "
                          f"(primary={primary!r}, 应为非空字符串)")


def main():
    parser = argparse.ArgumentParser(
        description="技法标注守卫 (content_meta.technique_tags.primary 缺失报告)")
    parser.add_argument("models_dir", nargs="?",
                        default=str(ROOT / "data" / "models"),
                        help="模型目录 (默认 data/models)")
    parser.add_argument("--strict", action="store_true",
                        help="有缺失时以退出码 1 结束 (回填完成后的 CI 硬闸门档)")
    args = parser.parse_args()

    models_dir = Path(args.models_dir)
    model_files = sorted(models_dir.glob("*.json"))
    if not model_files:
        print(f"[错误] {models_dir} 下没有模型文件", file=sys.stderr)
        sys.exit(2)

    tagged = 0
    missing = []      # [(模型 id, 状态, 说明)], 保持文件名序
    for path in model_files:
        try:
            model = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            print(f"[错误] 读取 {path.name} 失败: {exc}", file=sys.stderr)
            sys.exit(2)

        mid = model.get("id", path.stem)
        status, note = classify(model)
        if status == "ok":
            tagged += 1
        else:
            missing.append((mid, status, note))

    total = len(model_files)
    no_tags = sum(1 for _, status, _ in missing if status == "no_tags")

    print("=" * 62)
    print(" 技法标注守卫 (content_meta.technique_tags.primary)")
    print("=" * 62)
    print(f"模型总数:          {total}  ({models_dir})")
    print(f"已标注主技法:      {tagged}  ({tagged / total:.1%})")
    print(f"缺失主技法:        {len(missing)}  ({len(missing) / total:.1%})")
    if missing:
        print(f"  其中 technique_tags 缺席/非对象 {no_tags} 个, "
              f"对象存在但 primary 缺失/非法 {len(missing) - no_tags} 个")

    if missing:
        shown = missing[:MISSING_LIST_LIMIT]
        print(f"\n[WARN] 缺失主技法 {len(missing)} 个 "
              f"(主技法词表与组合规则见 CONTENT_STRATEGY.md §1):")
        for mid, _, note in shown:
            print(f"  WARN: {mid} —— {note}")
        if len(missing) > len(shown):
            print(f"  ... 其余 {len(missing) - len(shown)} 个从略")
    else:
        print("\n全库主技法标注齐全, 无警告")

    print("=" * 62)
    if missing and args.strict:
        print(f"strict 模式: 缺失 {len(missing)}, 以退出码 1 结束")
        sys.exit(1)
    sys.exit(0)


if __name__ == "__main__":
    main()
