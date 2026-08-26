#!/usr/bin/env python3
"""难度配额检查 —— D3 冻结硬闸门 (批次评审机检项)。

内容缺口审计 (docs/reports/CONTENT_GAP_AUDIT.md 第 7.3 节) 的机制
建议第 2 条: D3 (熟练档) 已超 520 终态目标, 而 D1 (入门) / D5 (大师)
两端长期空转, 靠"建议"约束不了产线舒适区, 必须硬闸门化。
本工具扫描模型库, 输出 D1–D5 难度分布报告并执行三件事:

  1. 难度分布报告: 全库 D1–D5 计数与占比;
  2. D3 冻结判定: D1 < 20 或 D5 < 6 时冻结生效
     (解冻须两项同时达标 —— 审计 7.3 节维持上一版解冻条件);
  3. 批次硬闸门 (--batch): 冻结生效期间, 新增模型 difficulty=3
     直接 FAIL; 例外须策展人白名单签发 (--whitelist-file)。

--batch 接受两种输入 (对应批次评审的两个时点):
  * 新模型 JSON 目录 —— 入库前审查, 难度取自批次文件本身;
  * 模型 id 清单文件 (每行一个 id, # 开头为注释) —— 入库后复核,
    难度从主库按 id 查询 (id 优先按 <id>.json 文件名解析)。

冻结状态一律按主库 (data/models) 现状计算; id 清单模式下批次
模型已入库, 其难度已计入主库统计 (批次自带的 D1/D5 增量若足以
解冻, 闸门随之放行 —— 与审计"解冻条件"口径一致)。

退出码:
  0  检查通过 (默认报告模式恒为 0, 冻结与否只报告不拦截);
  1  闸门失败: --batch 存在未豁免的 D3 新模型 (冻结生效期间),
     或 --strict 模式下冻结生效 (CI 对主库状态的告警闸);
  2  结构错误 (文件不可读 / 难度值非法 / 批次 id 无法解析)。

用法:
  python3 tools/check_difficulty_quota.py [模型目录]
  python3 tools/check_difficulty_quota.py --batch 新模型目录或id清单 \\
      [--whitelist-file 白名单文件]
  python3 tools/check_difficulty_quota.py --strict
"""

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# 解冻线 (CONTENT_GAP_AUDIT.md 7.3 节: D1 >= 20 且 D5 >= 6)
D1_UNFREEZE_MIN = 20
D5_UNFREEZE_MIN = 6
FROZEN_DIFFICULTY = 3

DIFFICULTY_LABELS = {1: "入门", 2: "进阶", 3: "熟练", 4: "挑战", 5: "大师"}


def load_difficulty(path):
    """读取单个模型 JSON, 返回 (id, difficulty); 难度非法按结构错误退出。"""
    try:
        model = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"[错误] 读取 {path.name} 失败: {exc}", file=sys.stderr)
        sys.exit(2)

    mid = model.get("id", path.stem)
    diff = model.get("difficulty")
    if diff not in DIFFICULTY_LABELS:
        print(f"[错误] {mid} 的 difficulty 值非法: {diff!r} (须为 1–5)",
              file=sys.stderr)
        sys.exit(2)
    return mid, diff


def scan_library(models_dir):
    """扫描主库, 返回 (难度计数 {1..5: n}, id->难度映射)。"""
    model_files = sorted(models_dir.glob("*.json"))
    if not model_files:
        print(f"[错误] {models_dir} 下没有模型文件", file=sys.stderr)
        sys.exit(2)

    counts = {d: 0 for d in DIFFICULTY_LABELS}
    by_id = {}
    for path in model_files:
        mid, diff = load_difficulty(path)
        counts[diff] += 1
        by_id[mid] = diff
    return counts, by_id


def read_id_lines(path):
    """读取每行一个 id 的清单文件 (# 开头为注释, 空行忽略)。"""
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as exc:
        print(f"[错误] 读取 {path} 失败: {exc}", file=sys.stderr)
        sys.exit(2)
    ids = []
    for line in text.splitlines():
        line = line.strip()
        if line and not line.startswith("#"):
            ids.append(line)
    return ids


def load_batch(batch_path, models_dir, library_by_id):
    """解析批次输入, 返回 [(id, difficulty)] (保持输入顺序)。"""
    if batch_path.is_dir():
        batch_files = sorted(batch_path.glob("*.json"))
        if not batch_files:
            print(f"[错误] 批次目录 {batch_path} 下没有模型文件", file=sys.stderr)
            sys.exit(2)
        return [load_difficulty(p) for p in batch_files]

    if not batch_path.is_file():
        print(f"[错误] 批次路径不存在: {batch_path}", file=sys.stderr)
        sys.exit(2)

    entries = []
    for mid in read_id_lines(batch_path):
        json_path = models_dir / f"{mid}.json"
        if json_path.is_file():
            entries.append(load_difficulty(json_path))
        elif mid in library_by_id:
            entries.append((mid, library_by_id[mid]))
        else:
            print(f"[错误] 批次 id 无法解析: {mid} "
                  f"(主库 {models_dir} 中既无 {mid}.json 也无同 id 模型)",
                  file=sys.stderr)
            sys.exit(2)
    return entries


def main():
    parser = argparse.ArgumentParser(
        description="难度配额检查 —— D3 冻结硬闸门 (CONTENT_GAP_AUDIT.md 7.3 节)")
    parser.add_argument("models_dir", nargs="?", default=str(ROOT / "data" / "models"),
                        help="主库模型目录 (默认 data/models)")
    parser.add_argument("--batch", metavar="PATH",
                        help="批次输入: 新模型 JSON 目录, 或每行一个模型 id 的清单文件")
    parser.add_argument("--whitelist-file", metavar="PATH",
                        help="策展人白名单 (每行一个模型 id): 冻结期间豁免 D3 新模型")
    parser.add_argument("--strict", action="store_true",
                        help="冻结生效时以退出码 1 结束 (CI 对主库状态的告警闸)")
    args = parser.parse_args()

    models_dir = Path(args.models_dir)
    counts, library_by_id = scan_library(models_dir)
    total = sum(counts.values())

    d1, d5 = counts[1], counts[5]
    freeze_active = d1 < D1_UNFREEZE_MIN or d5 < D5_UNFREEZE_MIN

    print("=" * 62)
    print(" 难度配额检查 (D3 冻结硬闸门 —— CONTENT_GAP_AUDIT.md 7.3 节)")
    print("=" * 62)
    print(f"主库模型总数:      {total}  ({models_dir})")
    for d in sorted(DIFFICULTY_LABELS):
        n = counts[d]
        line = f"  D{d} ({DIFFICULTY_LABELS[d]}):        {n:>4}  ({n / total:.1%})"
        if d == 1:
            line += f"   解冻线 >= {D1_UNFREEZE_MIN}" + \
                (f", 缺 {D1_UNFREEZE_MIN - n}" if n < D1_UNFREEZE_MIN else ", 已达标")
        elif d == 5:
            line += f"   解冻线 >= {D5_UNFREEZE_MIN}" + \
                (f", 缺 {D5_UNFREEZE_MIN - n}" if n < D5_UNFREEZE_MIN else ", 已达标")
        print(line)

    if freeze_active:
        print(f"\nD3 冻结状态: 生效中 (D1 {d1}/{D1_UNFREEZE_MIN}, "
              f"D5 {d5}/{D5_UNFREEZE_MIN} —— 两项同时达标方可解冻)")
        print("  冻结期间新增 difficulty=3 模型将被批次评审拒绝 (--batch)")
    else:
        print(f"\nD3 冻结状态: 已解冻 (D1 {d1} >= {D1_UNFREEZE_MIN} 且 "
              f"D5 {d5} >= {D5_UNFREEZE_MIN})")

    gate_failed = False

    if args.batch:
        whitelist = set()
        if args.whitelist_file:
            whitelist = set(read_id_lines(Path(args.whitelist_file)))

        batch = load_batch(Path(args.batch), models_dir, library_by_id)
        print("\n" + "-" * 62)
        print(f"批次硬闸门审查: {args.batch}  ({len(batch)} 个新模型)")
        violations = []
        for mid, diff in batch:
            if diff == FROZEN_DIFFICULTY and freeze_active:
                if mid in whitelist:
                    print(f"  [PASS] D{diff}  {mid:<28} 策展人白名单豁免")
                else:
                    print(f"  [FAIL] D{diff}  {mid:<28} 冻结生效中, 未获白名单豁免")
                    violations.append(mid)
            else:
                print(f"  [PASS] D{diff}  {mid}")

        unused = sorted(whitelist - {mid for mid, _ in batch})
        if unused:
            print(f"  (提示: 白名单中 {len(unused)} 个 id 不在本批次: "
                  f"{', '.join(unused)})")

        if violations:
            gate_failed = True
            print(f"\n结果: FAIL —— {len(violations)}/{len(batch)} 个新模型违反 "
                  f"D3 冻结: {', '.join(violations)}")
            print("  处置: 改选 D1/D2/D4/D5 选题, 或由策展人签发白名单 "
                  "(--whitelist-file) 后重审。")
        else:
            print(f"\n结果: PASS —— 批次 {len(batch)} 个新模型全部通过 D3 冻结闸门")

    print("=" * 62)
    if gate_failed:
        sys.exit(1)
    if args.strict and freeze_active:
        print("strict 模式: D3 冻结生效中, 以退出码 1 结束")
        sys.exit(1)
    sys.exit(0)


if __name__ == "__main__":
    main()
