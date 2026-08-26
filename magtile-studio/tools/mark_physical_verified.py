#!/usr/bin/env python3
"""实物复核通过后一键落盘 physical_verified 三字段 (路径 A 签核工具)。

背景: D4+ 模型按 docs/PHYSICAL_REBUILD_CHECKLIST.md 实搭复核通过后,
需要在模型 JSON 的 content_meta 下写入三字段 (PHYSICAL_REVIEW_USER_GUIDE.md
第 6 节口径):

    "physical_verified": true,
    "physical_verified_at": "YYYY-MM-DD",   # 实际复核日期 (ISO 8601)
    "physical_notes": "品牌/新旧片 + 耗时 + 敲击/提起/拆解重搭结论 一句话"

手工编辑 JSON 容易写错位置 (顶层 vs content_meta)、漏日期、或给没过
strict 预检的模型误标 —— 本工具把落盘动作收敛成一条命令, 并内置防线:

  1. 模型必须存在于模型目录 (默认 data/models/<model_id>.json);
  2. difficulty >= 4 (路径 A 实物复核只覆盖 D4+; 更低难度模型如需
     签核, 按用户指南第 6 节手工流程处理, 本工具拒绝代劳);
  3. strict 档软件校验必须通过 (magtile_app validate --profile strict
     退出码 0) —— 这是复核人开工前跑过的同一道预检, 落盘前再验一次,
     防止"实搭用的是旧结构、落盘时模型已被改动"的时间差事故;
  4. 已标记过的模型再次运行会打印旧值并覆盖 (改错日期/补笔记用),
     --notes 省略时保留已有 physical_notes。

红线不变 (用户指南第 1 节): 未实际搭过的模型严禁标记通过 ——
本工具只负责把"真实的复核结论"写对位置, 不制造结论。

用法:
    tools/mark_physical_verified.py <model_id> --date YYYY-MM-DD
                                    [--notes "一句话结论"] [--dry-run] [选项]
        model_id          模型 id (data/models/<model_id>.json 的文件名主干)
        --date DATE       实际复核日期 (ISO 8601, 如 2026-08-26; 不得晚于今天)
        --notes TEXT      复核笔记 (可选; 省略时保留模型中已有笔记)
        --dry-run         只跑全部检查并打印将写入的内容, 不落盘
        --models-dir DIR  模型目录 (默认: 仓库 data/models)
        --app PATH        校验器路径 (默认: 仓库 build/magtile_app)
        --data-dir DIR    validate 的 --data-dir (默认: 模型目录的上级)

退出码: 0 = 已落盘 (或 --dry-run 全部检查通过)
        1 = 拒绝 (难度 < 4 / strict 校验失败)
        2 = 用法或环境错误 (模型不存在 / 日期非法 / 校验器缺失 等)
"""

import argparse
import datetime
import json
import subprocess
import sys
from pathlib import Path

PHYSICAL_FIELDS = ("physical_verified", "physical_verified_at", "physical_notes")


def fail(message: str, code: int) -> int:
    print(f"错误: {message}", file=sys.stderr)
    return code


def parse_review_date(raw: str):
    """解析并校验复核日期: ISO 8601 且不晚于今天。返回 date 或 None。"""
    try:
        day = datetime.date.fromisoformat(raw)
    except ValueError:
        return None
    if day > datetime.date.today():
        return None
    return day


def resolve_app(app: Path) -> Path:
    """定位校验器: Windows 上默认路径无后缀时补 .exe。"""
    if app.is_file():
        return app
    exe = app.with_suffix(".exe")
    if exe.is_file():
        return exe
    return app


def validator_argv(app: Path):
    """组装校验器命令。Windows 不能 CreateProcess 一个 .py, 须经解释器。"""
    if app.suffix.lower() == ".py":
        return [sys.executable, str(app)]
    return [str(app)]


def run_strict_validate(app: Path, model_path: Path, data_dir: Path):
    """跑 strict 档校验, 返回 (退出码, 合并输出)。"""
    proc = subprocess.run(
        validator_argv(app) + [
            "validate", str(model_path),
            "--data-dir", str(data_dir), "--profile", "strict"],
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    return proc.returncode, proc.stdout


def rebuild_content_meta(content_meta: dict, date_str: str, notes):
    """重排 content_meta: 三字段紧跟 series 之后 (与已落盘示范一致)。

    notes 为 None 时保留已有 physical_notes (若有); 其余键保持原顺序。
    """
    trio = {
        "physical_verified": True,
        "physical_verified_at": date_str,
    }
    if notes is not None:
        trio["physical_notes"] = notes
    elif "physical_notes" in content_meta:
        trio["physical_notes"] = content_meta["physical_notes"]

    rebuilt = {}
    inserted = False
    for key, value in content_meta.items():
        if key in PHYSICAL_FIELDS:
            continue
        rebuilt[key] = value
        if key == "series":
            rebuilt.update(trio)
            inserted = True
    if not inserted:
        rebuilt.update(trio)
    return rebuilt


def main() -> int:
    root = Path(__file__).resolve().parent.parent
    parser = argparse.ArgumentParser(
        description="实物复核通过后落盘 content_meta.physical_verified 三字段 (D4+)")
    parser.add_argument("model_id", help="模型 id (data/models/<model_id>.json)")
    parser.add_argument("--date", required=True,
                        help="实际复核日期 (ISO 8601, 如 2026-08-26)")
    parser.add_argument("--notes", default=None,
                        help="复核笔记一句话 (省略时保留模型中已有笔记)")
    parser.add_argument("--dry-run", action="store_true",
                        help="只跑检查并预览写入内容, 不落盘")
    parser.add_argument("--models-dir", default=str(root / "data" / "models"))
    parser.add_argument("--app", default=str(root / "build" / "magtile_app"))
    parser.add_argument("--data-dir", default=None,
                        help="validate 的 --data-dir (默认: 模型目录的上级)")
    args = parser.parse_args()

    # -- 日期检查 (格式 + 不得晚于今天: 未来日期只能是笔误) --
    review_date = parse_review_date(args.date)
    if review_date is None:
        return fail(f"--date 非法: {args.date!r} (需要 ISO 8601 如 2026-08-26, "
                    "且不得晚于今天)", 2)

    # -- 模型存在性检查 --
    models_dir = Path(args.models_dir)
    if not models_dir.is_dir():
        return fail(f"模型目录不存在: {models_dir}", 2)
    model_path = models_dir / f"{args.model_id}.json"
    if not model_path.is_file():
        return fail(f"模型不存在: {model_path}\n"
                    f"  (待复核清单: python3 tools/list_physical_pending.py)", 2)
    try:
        model = json.loads(model_path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        return fail(f"模型 JSON 无法解析: {model_path}: {exc}", 2)
    if model.get("id") != args.model_id:
        return fail(f"模型文件 id 字段 ({model.get('id')!r}) 与文件名 "
                    f"({args.model_id!r}) 不一致, 请先修数据", 2)

    # -- 难度门槛: 路径 A 实物签核只覆盖 D4+ --
    difficulty = int(model.get("difficulty", 0))
    if difficulty < 4:
        print(f"拒绝: {args.model_id} 难度 D{difficulty} < D4 —— 路径 A 实物"
              "签核只覆盖 D4+ 模型。", file=sys.stderr)
        print("  更低难度模型如确需签核, 按 docs/reports/PHYSICAL_REVIEW_USER_GUIDE.md"
              " 第 6 节手工流程处理。", file=sys.stderr)
        return 1

    # -- strict 预检复验: 与复核人开工前跑的同一道安全检查 --
    app = resolve_app(Path(args.app))
    if not app.is_file():
        return fail(f"校验器不存在: {app}\n"
                    "  先构建: cmake -S . -B build && cmake --build build "
                    "--target magtile_app\n"
                    "  (或用 --app 指定 magtile_app 路径)", 2)
    data_dir = Path(args.data_dir) if args.data_dir else models_dir.parent
    print(f">> strict 预检复验: {app.name} validate {model_path.name} "
          f"--data-dir {data_dir} --profile strict")
    status, output = run_strict_validate(app, model_path, data_dir)
    if status != 0:
        print(output, file=sys.stderr)
        print(f"拒绝: {args.model_id} strict 档校验失败 (退出码 {status}) —— "
              "实搭结论不能落在没过软件预检的结构上。", file=sys.stderr)
        print("  模型若在实搭后被改过, 旧实物结论已作废, 须修复后重新实搭复核。",
              file=sys.stderr)
        return 1
    print("   [通过] strict 档零 Error")

    # -- 写入计划 (已标记过则打印旧值, 覆盖用于改错日期/补笔记) --
    content_meta = dict(model.get("content_meta") or {})
    if content_meta.get("physical_verified") is True:
        print(f"[注意] {args.model_id} 已标记过实物复核 "
              f"(physical_verified_at={content_meta.get('physical_verified_at')!r}), "
              "本次运行将覆盖为新值。")
    new_meta = rebuild_content_meta(content_meta, args.date, args.notes)
    print(f">> 将写入 {model_path} 的 content_meta:")
    for key in PHYSICAL_FIELDS:
        if key in new_meta:
            print(f"   {key} = {json.dumps(new_meta[key], ensure_ascii=False)}")
    if "physical_notes" not in new_meta:
        print("   physical_notes = (未提供, 不写入 —— 建议补一句话结论)")

    if args.dry_run:
        print("[dry-run] 全部检查通过, 未写入。去掉 --dry-run 正式落盘。")
        return 0

    model["content_meta"] = new_meta
    model_path.write_text(
        json.dumps(model, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"[完成] {args.model_id} 实物签核已落盘。")
    print("接下来 (用户指南第 6.2 节): 重新生成各报告并复查缺口计数, 如:")
    print("  python3 tools/list_physical_pending.py data/models")
    print("  python3 tools/export_physical_review_queue.py "
          "--csv docs/reports/PHYSICAL_REVIEW_QUEUE.csv "
          "--markdown docs/reports/PHYSICAL_REVIEW_QUEUE.md")
    return 0


if __name__ == "__main__":
    sys.exit(main())
