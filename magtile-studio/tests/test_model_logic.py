#!/usr/bin/env python3
# =============================================================
# MagTile Studio - 模型逻辑质检 (教程合理性 + 元数据一致性)
#
# 物理校验器保证"搭得起来", 本脚本保证"教程讲得通、元数据不骗人"。
# 对 data/models/ 下的每个模型执行以下检查:
#
#   [FAIL] 某步骤放置 0 片                  -> 空步骤, 教程逻辑错误
#   [FAIL] 某步骤放置 > 15 片               -> 单步信息量爆炸, 用户必然跟丢
#   [WARN] 某步骤放置 13~15 片              -> 超出推荐粒度 (1~12), 建议拆分
#   [FAIL] 步骤说明为空或不含中文           -> 面向中文用户的教程必须有中文说明
#   [FAIL] final_assembly 片数 != 各步骤 tiles_to_add 之和 (或存在重复 id)
#                                           -> 教程与成品对不上账
#   [FAIL] difficulty 与片数区间不匹配      -> 难度定级违反 CONTENT_STRATEGY.md 2.1 节
#   [WARN] 步骤数超出该难度的参考区间       -> 步骤节奏与难度定位不符
#   [FAIL] BOM (备料清单) 与实际用片不一致  -> 用户按清单备料会缺片/多片
#   [FAIL] 缺少 BOM                         -> 入库模型必须携带备料清单
#
# BOM 读取位置 (二选一, 前者优先):
#   content_meta.structural_signature.tile_histogram   (schema v2, 见 CONTENT_STRATEGY.md 5.1)
#   metadata.bom                                       (旧式兼容)
#
# 用法: test_model_logic.py <models_dir 或 model.json ...>
# 退出码: 0 = 全部通过 (WARN 不算失败), 1 = 存在 FAIL, 2 = 用法错误
# =============================================================

import json
import sys
from collections import Counter
from pathlib import Path

# ---- 步骤粒度 (片/步) --------------------------------------------
STEP_MIN_TILES = 1          # 少于此数 (即 0 片) 为空步骤, FAIL
STEP_RECOMMENDED_MAX = 12   # 推荐单步上限, 超出即 WARN
STEP_HARD_MAX = 15          # 硬性单步上限, 超出即 FAIL

# ---- 难度 <-> 片数区间 (CONTENT_STRATEGY.md 2.1 节, 边界值归属两侧均可) ----
# D1 下限 20 片: 反幼稚规则 (CONTENT_STRATEGY.md 2.4 节), 入门档降低的是
# 操作难度, 不是作品的成品感。
DIFFICULTY_PIECE_BANDS = {
    1: (20, 28),
    2: (28, 48),
    3: (48, 75),
    4: (75, 110),
    5: (110, 180),
}

# ---- 难度 <-> 步骤数参考区间 (同表, 仅 WARN) ----------------------
DIFFICULTY_STEP_BANDS = {
    1: (4, 8),
    2: (8, 14),
    3: (12, 20),
    4: (18, 30),
    5: (25, 40),
}


def has_chinese(text):
    """至少包含一个 CJK 统一表意文字。"""
    return any("\u4e00" <= ch <= "\u9fff" for ch in text)


def find_bom(model):
    """返回 (BOM 字典或 None, 来源描述)。"""
    histogram = (model.get("content_meta", {})
                      .get("structural_signature", {})
                      .get("tile_histogram"))
    if isinstance(histogram, dict) and histogram:
        return histogram, "content_meta.structural_signature.tile_histogram"
    legacy = model.get("metadata", {}).get("bom")
    if isinstance(legacy, dict) and legacy:
        return legacy, "metadata.bom"
    return None, None


def check_model(path):
    """返回 (fail 列表, warn 列表, 统计信息字符串)。"""
    fails, warns = [], []
    model = json.loads(path.read_text(encoding="utf-8"))

    tiles = model["final_assembly"]
    steps = model["steps"]

    # ---- 1. 步骤粒度: 每步 1~12 片 (硬上限 15) ---------------------
    for i, step_def in enumerate(steps, start=1):
        n = len(step_def["tiles_to_add"])
        if n < STEP_MIN_TILES:
            fails.append(f"第 {i} 步放置 {n} 片: 空步骤没有教学内容, 必须删除或合并")
        elif n > STEP_HARD_MAX:
            fails.append(
                f"第 {i} 步一次放置 {n} 片 > 硬上限 {STEP_HARD_MAX}, "
                f"用户无法跟随, 必须拆分")
        elif n > STEP_RECOMMENDED_MAX:
            warns.append(
                f"第 {i} 步放置 {n} 片, 超出推荐粒度 {STEP_RECOMMENDED_MAX} 片/步, 建议拆分")

    # ---- 2. 步骤说明: 非空中文 -----------------------------------
    for i, step_def in enumerate(steps, start=1):
        description = step_def.get("description", "").strip()
        if not description:
            fails.append(f"第 {i} 步说明为空")
        elif not has_chinese(description):
            fails.append(f"第 {i} 步说明不含中文: {description[:30]!r}")

    # ---- 3. 教程与成品对账: 总数一致且无重复 -----------------------
    final_ids = [t["id"] for t in tiles]
    if len(set(final_ids)) != len(final_ids):
        duplicated = sorted(k for k, v in Counter(final_ids).items() if v > 1)
        fails.append(f"final_assembly 存在重复 id: {duplicated[:5]}")

    placed_ids = [tile_id for s in steps for tile_id in s["tiles_to_add"]]
    placed_counter = Counter(placed_ids)
    duplicated_placed = sorted(k for k, v in placed_counter.items() if v > 1)
    if duplicated_placed:
        fails.append(f"以下磁力片被多个步骤重复放置: {duplicated_placed[:5]}")
    if len(placed_ids) != len(tiles):
        fails.append(
            f"各步骤 tiles_to_add 之和 ({len(placed_ids)}) != "
            f"final_assembly 片数 ({len(tiles)})")
    unknown = sorted(set(placed_ids) - set(final_ids))
    if unknown:
        fails.append(f"步骤引用了 final_assembly 中不存在的磁力片: {unknown[:5]}")
    never_placed = sorted(set(final_ids) - set(placed_ids))
    if never_placed:
        fails.append(f"以下磁力片不属于任何步骤: {never_placed[:5]}")

    # ---- 4. 难度定级 <-> 片数区间 ---------------------------------
    difficulty = model.get("difficulty")
    if difficulty not in DIFFICULTY_PIECE_BANDS:
        fails.append(f"difficulty = {difficulty!r} 非法, 必须为 1~5 的整数")
    else:
        low, high = DIFFICULTY_PIECE_BANDS[difficulty]
        if not (low <= len(tiles) <= high):
            fails.append(
                f"难度 D{difficulty} 要求片数在 [{low}, {high}] 区间 "
                f"(CONTENT_STRATEGY.md 2.1 节), 实际 {len(tiles)} 片, 请修正难度或规模")
        step_low, step_high = DIFFICULTY_STEP_BANDS[difficulty]
        if steps and not (step_low <= len(steps) <= step_high):
            warns.append(
                f"难度 D{difficulty} 的步骤数参考区间为 [{step_low}, {step_high}], "
                f"实际 {len(steps)} 步, 建议核对步骤节奏")

    # ---- 5. BOM (备料清单) <-> 实际用片 ----------------------------
    actual_bom = dict(Counter(t["type"] for t in tiles))
    declared_bom, bom_source = find_bom(model)
    if declared_bom is None:
        fails.append(
            "缺少 BOM 备料清单: 请在 content_meta.structural_signature.tile_histogram "
            "声明各片形用量 (工具生成, 勿手写)")
    elif {k: int(v) for k, v in declared_bom.items()} != actual_bom:
        fails.append(
            f"BOM ({bom_source}) 与实际用片不一致: "
            f"声明 {json.dumps(declared_bom, ensure_ascii=False, sort_keys=True)}, "
            f"实际 {json.dumps(actual_bom, ensure_ascii=False, sort_keys=True)}")

    step_sizes = [len(s["tiles_to_add"]) for s in steps]
    stats = (f"{len(tiles)} 片 / {len(steps)} 步 / 难度 D{difficulty} / "
             f"单步片数 {min(step_sizes) if step_sizes else 0}"
             f"~{max(step_sizes) if step_sizes else 0} / "
             f"BOM {'√' if declared_bom is not None else '缺失'}")
    return fails, warns, stats


def main(argv):
    if len(argv) < 2:
        print("用法: test_model_logic.py <models_dir 或 model.json ...>", file=sys.stderr)
        return 2

    model_files = []
    for arg in argv[1:]:
        path = Path(arg)
        if path.is_dir():
            model_files.extend(sorted(path.glob("*.json")))
        else:
            model_files.append(path)

    if not model_files:
        print("错误: 没有找到任何模型 JSON", file=sys.stderr)
        return 1

    print("==============================================================")
    print(f" 模型逻辑质检: 共 {len(model_files)} 个模型")
    print("==============================================================")

    failed_models = 0
    for path in model_files:
        try:
            fails, warns, stats = check_model(path)
        except Exception as exc:  # JSON 损坏或缺字段同样视为失败
            print(f"\n[FAIL] {path.name}: 无法解析 ({exc})")
            failed_models += 1
            continue

        verdict = "FAIL" if fails else "PASS"
        print(f"\n[{verdict}] {path.name}: {stats}")
        for message in fails:
            print(f"    [FAIL] {message}")
        for message in warns:
            print(f"    [WARN] {message}")
        if fails:
            failed_models += 1

    print("\n==============================================================")
    if failed_models:
        print(f" 结果: {len(model_files)} 个模型中有 {failed_models} 个逻辑质检未通过")
        return 1
    print(f" 结果: 全部 {len(model_files)} 个模型逻辑质检通过")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
