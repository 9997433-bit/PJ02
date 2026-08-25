#!/usr/bin/env python3
# =============================================================
# MagTile Studio - 反平凡模型检查
#
# 商业教程内容不能是"几片拼个平面"的敷衍货。本脚本对 data/models/
# 下的每个模型执行结构复杂度检查, 不达标即拒绝入库:
#
#   [FAIL] 总片数 < 40                    -> 规模太小, 没有搭建价值
#   [FAIL] 使用的磁力片形状 < 3 种        -> 形状单一, 教学价值不足
#   [FAIL] 结构 Z 层数 < 2                -> 纯平面模型, 不是立体建筑
#   [FAIL] 所有磁力片都是平铺的           -> 没有立起来的片, 不构成结构
#   [WARN] 超过 50% 的步骤只放 1~2 片     -> 步骤切分过碎, 教程体验差
#
# 用法: test_anti_trivial.py <models_dir 或 model.json ...>
# 退出码: 0 = 全部通过 (WARN 不算失败), 1 = 存在 FAIL, 2 = 用法错误
# =============================================================

import json
import math
import sys
from pathlib import Path

MIN_PIECES = 40
MIN_TILE_TYPES = 3
MIN_Z_LAYERS = 2
Z_LAYER_TOLERANCE = 0.1     # 相距小于该值的 z 视为同一层
FLAT_NORMAL_Z = 0.999       # 面法向 z 分量绝对值超过该值视为平铺
SMALL_STEP_MAX_TILES = 2    # "小步骤"判定: 本步只放 1~2 片
SMALL_STEP_WARN_RATIO = 0.5


def tile_is_flat(rotation_deg):
    """旋转约定与 C++ 端一致: R = Rz * Ry * Rx, 本地法向为 +Z。

    R * (0,0,1) 的 z 分量 = cos(rx) * cos(ry), 与 rz 无关
    (绕 Z 轴旋转不改变平铺状态)。
    """
    rx, ry = math.radians(rotation_deg[0]), math.radians(rotation_deg[1])
    normal_z = math.cos(rx) * math.cos(ry)
    return abs(normal_z) >= FLAT_NORMAL_Z


def count_z_layers(z_values):
    """把 z 坐标聚成层: 排序后相邻差超过容差即认为进入新的一层。"""
    if not z_values:
        return 0
    layers = 1
    ordered = sorted(z_values)
    for prev, cur in zip(ordered, ordered[1:]):
        if cur - prev > Z_LAYER_TOLERANCE:
            layers += 1
    return layers


def check_model(path):
    """返回 (fail 列表, warn 列表, 统计信息字符串)。"""
    fails, warns = [], []
    model = json.loads(path.read_text(encoding="utf-8"))

    tiles = model["final_assembly"]
    steps = model["steps"]

    # 规则 1: 总片数
    if len(tiles) < MIN_PIECES:
        fails.append(f"总片数 {len(tiles)} < {MIN_PIECES}, 规模太小")

    # 规则 2: 形状多样性
    types_used = sorted({t["type"] for t in tiles})
    if len(types_used) < MIN_TILE_TYPES:
        fails.append(
            f"只使用了 {len(types_used)} 种形状 ({', '.join(types_used)}), "
            f"至少需要 {MIN_TILE_TYPES} 种")

    # 规则 3: 结构高度
    z_layers = count_z_layers([t["position"][2] for t in tiles])
    if z_layers < MIN_Z_LAYERS:
        fails.append(f"结构 Z 层数 {z_layers} < {MIN_Z_LAYERS}, 属于纯平面模型")

    # 规则 4: 必须有立起来的片
    flat_count = sum(1 for t in tiles if tile_is_flat(t["rotation"]))
    if flat_count == len(tiles):
        fails.append("所有磁力片都是平铺的 (旋转均接近 0,0,0), 不构成立体结构")

    # 规则 5: 步骤切分质量 (仅警告)
    small_steps = sum(1 for s in steps if len(s["tiles_to_add"]) <= SMALL_STEP_MAX_TILES)
    if steps and small_steps / len(steps) > SMALL_STEP_WARN_RATIO:
        warns.append(
            f"{small_steps}/{len(steps)} 个步骤只放 1~2 片, "
            f"超过 {SMALL_STEP_WARN_RATIO:.0%}, 建议合并零碎步骤")

    stats = (f"{len(tiles)} 片, {len(types_used)} 种形状, {z_layers} 个 Z 层, "
             f"{len(tiles) - flat_count} 片立置, {len(steps)} 步")
    return fails, warns, stats


def main(argv):
    if len(argv) < 2:
        print("用法: test_anti_trivial.py <models_dir 或 model.json ...>", file=sys.stderr)
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
    print(f" 反平凡模型检查: 共 {len(model_files)} 个模型")
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
        print(f" 结果: {len(model_files)} 个模型中有 {failed_models} 个过于简单, 拒绝入库")
        return 1
    print(f" 结果: 全部 {len(model_files)} 个模型达到复杂度要求")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
