#!/usr/bin/env python3
# =============================================================
# MagTile Studio - 逐步装配质检 (逐片零差错承诺 P1~P8)
#
# 教程是逐片摆放的: 500 模型 x 平均 80 片 = 4 万次放置指令,
# 任何一片错乱都会让用户在真实桌面上卡住。本脚本对 data/models/
# 下每个模型执行逐片级静态检查 (承诺编号见 docs/MODEL_QUALITY.md):
#
#   检查 1 (P1): final_assembly 中片 id 全模型唯一
#   检查 2 (P3): 任何片不得被多个步骤重复放置 (含同一步内重复)
#   检查 3 (P2): 第 K 步的片不得已在第 J < K 步出现 (顺序错乱)
#   检查 4 (P4): highlight_tiles 只能引用本步开始前已放置的片
#   检查 5 (P6): final_assembly id 集合 == 全部 tiles_to_add id 集合
#                (无孤儿片、无幽灵片, 严格集合相等)
#   检查 6 (P6): 片数据完好: type 在形状目录登记, position/rotation
#                为 3 维有限数值; 不存在两片 type+position+rotation
#                完全相同 (完美重叠即数据复制错误); 若步骤内嵌片
#                数据 (dict 形式), 须与 final_assembly 一致 (容差内)
#   检查 7 (P7): 空间连续性: 每片新片在放下的那一刻必须接地
#                (z <= 0.02) 或与已放置结构 (含本步内先放的片)
#                至少一条磁力边完全吸合 (容差 0.02, 与 C++ R7a 一致)
#   检查 8 (P8): step_number 从 1 严格连续递增, 无跳号无重号
#   检查 9:      任何失败输出人类可读差异明细 (步骤/片 id/期望/实际)
#
# 几何约定与 C++ 端严格一致, 见 tests/magtile_geom.py 头注。
# 本脚本不依赖 C++ 构建产物, 内容作者提交前可直接自查。
#
# 用法: test_step_assembly.py <models_dir 或 model.json ...> [--catalog 形状目录.json]
# 退出码: 0 = 全部通过 (WARN 不算失败), 1 = 存在 FAIL, 2 = 用法/环境错误
# =============================================================

import json
import math
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from magtile_geom import (  # noqa: E402
    CONNECT_TOLERANCE, GROUND_TOLERANCE, EdgeIndex, TransformedTile,
    collect_model_files, find_tile_catalog, load_tile_catalog,
)

# 检查 6 内嵌数据比对容差: 生成工具输出与成品记录之间不允许有实际差异,
# 仅容忍浮点序列化噪声
DATA_EPSILON = 1e-6


def fmt_ids(ids, limit=8):
    """截断展示 id 列表: 前 limit 个 + 总数。"""
    ids = sorted(ids)
    shown = ", ".join(ids[:limit])
    if len(ids) > limit:
        shown += f", ... (共 {len(ids)} 片)"
    return shown


def is_finite_triple(value):
    return (isinstance(value, (list, tuple)) and len(value) == 3
            and all(isinstance(x, (int, float)) and math.isfinite(x)
                    for x in value))


def check_tile_records(model, shapes):
    """检查 6 (数据部分): 每片记录完好、无完美重叠副本。"""
    fails = []
    pose_seen = {}
    for tile in model["final_assembly"]:
        tid = tile.get("id", "<无id>")
        if tile.get("type") not in shapes:
            fails.append(
                f"片 {tid}: type={tile.get('type')!r} 未在形状目录 "
                f"tile_catalog.json 中登记, 渲染与物理均无法处理")
            continue
        if not is_finite_triple(tile.get("position")):
            fails.append(
                f"片 {tid}: position={tile.get('position')!r} 非法, "
                f"必须是 3 维有限数值")
            continue
        if not is_finite_triple(tile.get("rotation")):
            fails.append(
                f"片 {tid}: rotation={tile.get('rotation')!r} 非法, "
                f"必须是 3 维有限数值 (度)")
            continue
        key = (tile["type"],
               tuple(round(v / DATA_EPSILON) for v in tile["position"]),
               tuple(round(v / DATA_EPSILON) for v in tile["rotation"]))
        if key in pose_seen:
            fails.append(
                f"片 {tid} 与片 {pose_seen[key]} 的 type/position/rotation "
                f"完全相同: 同一位置放了两片, 属于数据复制错误")
        else:
            pose_seen[key] = tid
    return fails


def check_step_entry_data(step_number, entry, tiles_by_id):
    """检查 6 (内嵌数据部分): 步骤内嵌 dict 片数据须与成品一致。

    返回 (tile_id 或 None, fail 列表)。当前 schema 中 tiles_to_add 为
    id 字符串; 若未来扩展为内嵌对象, 本检查保证两处数据不漂移。
    """
    fails = []
    if isinstance(entry, str):
        return entry, fails
    if not isinstance(entry, dict) or "id" not in entry:
        fails.append(
            f"第 {step_number} 步 tiles_to_add 含非法条目 {entry!r}: "
            f"必须是片 id 字符串或含 id 的对象")
        return None, fails
    tid = entry["id"]
    master = tiles_by_id.get(tid)
    if master is None:
        return tid, fails  # 幽灵片由检查 5 统一报告
    for field in ("type",):
        if field in entry and entry[field] != master[field]:
            fails.append(
                f"第 {step_number} 步内嵌片 {tid} 的 {field}={entry[field]!r} "
                f"与 final_assembly 的 {master[field]!r} 不一致")
    for field in ("position", "rotation"):
        if field in entry and is_finite_triple(entry[field]) \
                and is_finite_triple(master.get(field)):
            delta = max(abs(a - b)
                        for a, b in zip(entry[field], master[field]))
            if delta > DATA_EPSILON:
                fails.append(
                    f"第 {step_number} 步内嵌片 {tid} 的 {field}="
                    f"{entry[field]} 与 final_assembly 的 {master[field]} "
                    f"偏差 {delta:.2e} > 容差 {DATA_EPSILON:.0e}")
    return tid, fails


def nearest_structure_distance(transformed, placed_geo):
    """诊断用: 新片各磁力边中点到已放结构磁力边中点的最近距离。"""
    best = float("inf")
    for (a, b) in transformed.magnet_edges:
        mid = ((a[0] + b[0]) / 2, (a[1] + b[1]) / 2, (a[2] + b[2]) / 2)
        for other in placed_geo:
            for (c, d) in other.magnet_edges:
                omid = ((c[0] + d[0]) / 2, (c[1] + d[1]) / 2,
                        (c[2] + d[2]) / 2)
                best = min(best, math.dist(mid, omid))
    return best


def check_model(path, shapes):
    """返回 (fail 列表, warn 列表, 统计信息字符串)。"""
    fails, warns = [], []
    model = json.loads(path.read_text(encoding="utf-8"))

    tiles = model["final_assembly"]
    steps = model["steps"]
    tiles_by_id = {}

    # ---- 检查 1: 片 id 全模型唯一 ----------------------------------
    id_counter = Counter(t.get("id") for t in tiles)
    for tid, count in sorted(id_counter.items()):
        if count > 1:
            fails.append(
                f"[检查1] final_assembly 中 id={tid!r} 出现 {count} 次, "
                f"id 是教程/高亮/进度的唯一外键, 必须全模型唯一")
        if not tid or not isinstance(tid, str):
            fails.append(f"[检查1] 存在非法片 id: {tid!r} (必须为非空字符串)")
    for t in tiles:
        tiles_by_id.setdefault(t.get("id"), t)

    # ---- 检查 6a: 片记录完好 (type/position/rotation/无完美重叠) ----
    fails.extend(f"[检查6] {msg}" for msg in check_tile_records(model, shapes))

    # ---- 检查 8: 步骤序号 1..N 严格连续 -----------------------------
    if not steps:
        fails.append("[检查8] steps 为空: 模型没有任何教程步骤")
    for i, step in enumerate(steps, start=1):
        actual = step.get("step_number")
        if actual != i:
            fails.append(
                f"[检查8] 第 {i} 个步骤的 step_number={actual!r}, 期望 {i} "
                f"(序号必须从 1 连续递增, 进度显示与存档都依赖它)")

    # ---- 检查 2/3/4/5/6b/7: 逐步走查 --------------------------------
    placed_in_step = {}      # tile_id -> 首次放置的步骤号
    placed_geo = []          # 已放置片的几何 (诊断用)
    edge_index = EdgeIndex() # 已放置磁力边的空间索引
    connectivity_checked = 0
    highlight_refs = 0

    for i, step in enumerate(steps, start=1):
        # 检查 4: 高亮参照物必须在本步开始前就已在结构上
        step_tile_ids = set()
        for entry in step.get("tiles_to_add", []):
            if isinstance(entry, str):
                step_tile_ids.add(entry)
            elif isinstance(entry, dict) and "id" in entry:
                step_tile_ids.add(entry["id"])
        for hid in step.get("highlight_tiles", []):
            highlight_refs += 1
            if hid in placed_in_step:
                continue
            if hid in step_tile_ids:
                fails.append(
                    f"[检查4] 第 {i} 步 highlight_tiles 引用了本步才放置的片 "
                    f"{hid}: 高亮是'参照物', 必须在本步开始前已在结构上, "
                    f"本步新片不能给自己当参照物")
            elif hid in tiles_by_id:
                fails.append(
                    f"[检查4] 第 {i} 步 highlight_tiles 引用了尚未放置的片 "
                    f"{hid}: 该片直到后续步骤才会放置, 高亮时桌面上还不存在")
            else:
                fails.append(
                    f"[检查4] 第 {i} 步 highlight_tiles 引用了模型中不存在的片 "
                    f"{hid}")

        # 检查 2/3: 本步每片必须是新片; 检查 6b: 内嵌数据一致;
        # 检查 7: 逐片空间连续性 (按 tiles_to_add 顺序, 与真人搭建一致)
        seen_in_this_step = set()
        for entry in step.get("tiles_to_add", []):
            tid, entry_fails = check_step_entry_data(i, entry, tiles_by_id)
            fails.extend(f"[检查6] {msg}" for msg in entry_fails)
            if tid is None:
                continue

            if tid in seen_in_this_step:
                fails.append(
                    f"[检查2] 第 {i} 步 tiles_to_add 内部重复列出片 {tid}")
                continue
            seen_in_this_step.add(tid)

            if tid in placed_in_step:
                fails.append(
                    f"[检查3] 第 {i} 步要求放置片 {tid}, 但它已在第 "
                    f"{placed_in_step[tid]} 步放置过: 用户会发现"
                    f"'这片已经在结构上了'")
                continue

            master = tiles_by_id.get(tid)
            if master is None:
                # 幽灵片: 检查 5 统一汇总, 这里先登记避免重复报告
                placed_in_step[tid] = i
                continue

            # 检查 7: 接地或与已放结构磁力吸合 (含本步内先放的片)
            try:
                transformed = TransformedTile(master, shapes[master["type"]])
            except (KeyError, TypeError):
                placed_in_step[tid] = i
                continue  # 记录损坏已由检查 6a 报告
            connectivity_checked += 1
            grounded = transformed.touches_ground(GROUND_TOLERANCE)
            connection = None
            if not grounded:
                for edge in transformed.magnet_edges:
                    connection = edge_index.find_connection(
                        edge, CONNECT_TOLERANCE)
                    if connection is not None:
                        break
            if not grounded and connection is None:
                nearest = nearest_structure_distance(transformed, placed_geo)
                nearest_text = ("(结构上还没有任何片)" if not placed_geo else
                                f"最近磁力边中点距 {nearest:.3f}")
                fails.append(
                    f"[检查7] 第 {i} 步的片 {tid} (type={master['type']}, "
                    f"position={master['position']}) 空间不连续: 既不接地 "
                    f"(最低顶点 z={transformed.min_z:.3f} > "
                    f"{GROUND_TOLERANCE}), 也没有任何磁力边与已放置结构吸合 "
                    f"(容差 {CONNECT_TOLERANCE}), {nearest_text}; "
                    f"教程叙事上属于'隔空搭', 松手即掉")

            placed_in_step[tid] = i
            placed_geo.append(transformed)
            edge_index.add_tile(transformed)

    # ---- 检查 5: final_assembly ids == 全部 tiles_to_add ids --------
    final_ids = set(tiles_by_id)
    placed_ids = set(placed_in_step)
    orphans = final_ids - placed_ids
    ghosts = placed_ids - final_ids
    if orphans:
        fails.append(
            f"[检查5] 孤儿片: {len(orphans)} 片存在于 final_assembly 但"
            f"不属于任何步骤, 用户搭完教程后成品缺这些片: {fmt_ids(orphans)}")
    if ghosts:
        fails.append(
            f"[检查5] 幽灵片: {len(ghosts)} 片被步骤引用但在 final_assembly "
            f"中不存在, 位置/旋转/颜色无从谈起: {fmt_ids(ghosts)}")
    declared_total = model.get("total_pieces")
    if declared_total != len(tiles):
        fails.append(
            f"[检查5] total_pieces={declared_total} != final_assembly "
            f"实际片数 {len(tiles)}")

    stats = (f"{len(tiles)} 片 / {len(steps)} 步 / "
             f"高亮引用 {highlight_refs} 处 / "
             f"逐片连通检查 {connectivity_checked} 片")
    return fails, warns, stats


def main(argv):
    catalog_override = None
    args = []
    i = 1
    while i < len(argv):
        if argv[i] == "--catalog":
            if i + 1 >= len(argv):
                print("错误: --catalog 需要一个路径参数", file=sys.stderr)
                return 2
            catalog_override = Path(argv[i + 1])
            i += 2
        else:
            args.append(argv[i])
            i += 1

    if not args:
        print("用法: test_step_assembly.py <models_dir 或 model.json ...> "
              "[--catalog tile_catalog.json]", file=sys.stderr)
        return 2

    model_files = collect_model_files(args)
    if not model_files:
        print("错误: 没有找到任何模型 JSON", file=sys.stderr)
        return 1

    catalog_path = catalog_override or find_tile_catalog(model_files[0].parent)
    if catalog_path is None or not Path(catalog_path).is_file():
        print("错误: 找不到 tile_catalog.json (可用 --catalog 显式指定)",
              file=sys.stderr)
        return 2
    shapes = load_tile_catalog(catalog_path)

    print("==============================================================")
    print(f" 逐步装配质检 (逐片零差错 P1~P8): 共 {len(model_files)} 个模型")
    print(f" 形状目录: {catalog_path}")
    print("==============================================================")

    failed_models = 0
    for path in model_files:
        try:
            fails, warns, stats = check_model(path, shapes)
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
        print(f" 结果: {len(model_files)} 个模型中有 {failed_models} 个"
              f"违反逐片零差错承诺, 拒绝入库")
        return 1
    print(f" 结果: 全部 {len(model_files)} 个模型逐步装配质检通过")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
