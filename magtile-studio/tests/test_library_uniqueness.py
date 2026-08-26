#!/usr/bin/env python3
# =============================================================
# MagTile Studio - 模型库唯一性检查 (逐片零差错承诺 P10, 批量克隆检测)
#
# 500 个模型的价值在于"每个模型结构逻辑各异" (CONTENT_STRATEGY.md 第 2 节)。
# 换色、镜像、微调尺寸的"换皮克隆"会稀释整个内容库。本脚本对全库模型
# 两两计算结构签名相似度 (算法与 CONTENT_STRATEGY.md 5.2 节一致):
#
#   sim = 0.6 x WL 连接图指纹 Jaccard
#       + 0.25 x 片形直方图余弦
#       + 0.15 x 步骤节奏相似度 (每步新增片数序列, DTW 归一化)
#
#   WL 指纹: 从 final_assembly 构建磁力连接图 (节点标签 = 片形类型,
#   边标签 = 相对姿态类别: 共面 / 90° 折 / 其他角度), 跑 3 轮
#   Weisfeiler-Lehman 迭代取标签多重集。对颜色、全局平移/旋转、片 id
#   命名天然不敏感 —— 换色 (F1) 与镜像翻版 (F3) 在算法层面自动同构。
#
# 判定:
#   [FAIL] 任意一对模型 sim > 0.85           -> 克隆, 拒绝入库
#   [WARN] 0.70 < sim <= 0.85                -> 边界案例, 送人工比对
#                                               (结论记入 curator_review)
#   [WARN] 同主题 (content_meta.series) + 同主技法 (technique_tags.primary)
#          的模型 > 2 个                     -> 主题/技法组合过度开采
#
# 规模化: 签名 (WL 指纹/直方图/节奏) 每模型只算一次并缓存, 两两比对
# 阶段是纯字典运算; 500 模型 = 124,750 对, 单机分钟级以内。
# 报告只展开可疑对 (sim > 0.5) 与全库最相似对, 避免 CI 日志爆炸。
#
# 用法: test_library_uniqueness.py <models_dir 或 model.json ...> [--catalog 形状目录.json]
# 退出码: 0 = 全部通过 (WARN 不算失败), 1 = 存在 FAIL, 2 = 用法/环境错误
# =============================================================

import hashlib
import json
import math
import sys
from collections import Counter
from itertools import combinations
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from magtile_geom import (  # noqa: E402
    build_connection_graph, collect_model_files, find_tile_catalog,
    load_tile_catalog, transform_tiles,
)

FAIL_THRESHOLD = 0.85       # 全库克隆判定 (CONTENT_STRATEGY.md 5.2 第 4 条)
BOUNDARY_THRESHOLD = 0.70   # 边界案例下限, 0.70~0.85 送人工比对
REPORT_THRESHOLD = 0.50     # 报告展开阈值: 低于此值的对只计入统计
WL_ROUNDS = 3               # Weisfeiler-Lehman 迭代轮数
MAX_PER_THEME_TECHNIQUE = 2 # 同主题+同主技法的模型数上限 (超出 WARN)

W_WL, W_HIST, W_RHYTHM = 0.6, 0.25, 0.15


def wl_fingerprint(model, shapes):
    """连接图 WL 标签多重集: 含第 0 轮 (片形类型) 与 3 轮迭代标签。"""
    tiles = model["final_assembly"]
    transformed = transform_tiles(tiles, shapes)
    adjacency = build_connection_graph(transformed)

    labels = [t.tile_type for t in transformed]
    multiset = Counter(labels)
    for _ in range(WL_ROUNDS):
        refined = []
        for i in range(len(labels)):
            neighborhood = tuple(sorted(
                (pose, labels[j]) for j, pose in adjacency[i]))
            digest = hashlib.sha256(
                repr((labels[i], neighborhood)).encode()).hexdigest()[:16]
            refined.append(digest)
        labels = refined
        multiset.update(labels)
    return multiset


def multiset_jaccard(a, b):
    keys = set(a) | set(b)
    intersection = sum(min(a[k], b[k]) for k in keys)
    union = sum(max(a[k], b[k]) for k in keys)
    return intersection / union if union else 1.0


def histogram_cosine(a, b):
    keys = set(a) | set(b)
    dot = sum(a[k] * b[k] for k in keys)
    norm_a = math.sqrt(sum(v * v for v in a.values()))
    norm_b = math.sqrt(sum(v * v for v in b.values()))
    return dot / (norm_a * norm_b) if norm_a and norm_b else 1.0


def rhythm_similarity(a, b):
    """步骤节奏: 每步新增片数序列的 DTW 距离, 按对齐路径长度归一化,
    映射到 (0, 1]: 序列完全相同 -> 1.0。"""
    if not a or not b:
        return 1.0 if a == b else 0.0
    inf = float("inf")
    n, m = len(a), len(b)
    dist = [[inf] * (m + 1) for _ in range(n + 1)]
    dist[0][0] = 0.0
    for i in range(1, n + 1):
        for j in range(1, m + 1):
            cost = abs(a[i - 1] - b[j - 1])
            dist[i][j] = cost + min(dist[i - 1][j], dist[i][j - 1],
                                    dist[i - 1][j - 1])
    normalized = dist[n][m] / max(n, m)
    return 1.0 / (1.0 + normalized)


def load_signature(path, shapes):
    """每模型只计算一次的结构签名 (规模化的关键)。"""
    model = json.loads(path.read_text(encoding="utf-8"))
    meta = model.get("content_meta", {})
    technique = meta.get("technique_tags") or {}
    return {
        "name": path.name,
        "model_id": model.get("id", path.stem),
        "pieces": len(model["final_assembly"]),
        "steps": len(model["steps"]),
        "wl": wl_fingerprint(model, shapes),
        "histogram": Counter(t["type"] for t in model["final_assembly"]),
        "rhythm": [len(s["tiles_to_add"]) for s in model["steps"]],
        "series": meta.get("series"),
        "primary_technique": technique.get("primary"),
    }


def similarity(sig_a, sig_b):
    wl = multiset_jaccard(sig_a["wl"], sig_b["wl"])
    hist = histogram_cosine(sig_a["histogram"], sig_b["histogram"])
    rhythm = rhythm_similarity(sig_a["rhythm"], sig_b["rhythm"])
    return W_WL * wl + W_HIST * hist + W_RHYTHM * rhythm, wl, hist, rhythm


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
        print("用法: test_library_uniqueness.py <models_dir 或 model.json ...> "
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
    print(f" 模型库唯一性检查 (克隆检测): 共 {len(model_files)} 个模型")
    print(f" 判定: sim > {FAIL_THRESHOLD} FAIL / "
          f"{BOUNDARY_THRESHOLD} < sim <= {FAIL_THRESHOLD} WARN (边界送人工)")
    print("==============================================================")

    # ---- 阶段 1: 逐模型计算结构签名 (每模型一次, 可缓存) -------------
    signatures = []
    parse_failures = 0
    for path in model_files:
        try:
            sig = load_signature(path, shapes)
        except Exception as exc:
            print(f"[FAIL] {path.name}: 无法计算结构签名 ({exc})")
            parse_failures += 1
            continue
        signatures.append(sig)
        print(f"  签名: {sig['name']}: {sig['pieces']} 片 / "
              f"{sig['steps']} 步 / WL 标签 {sum(sig['wl'].values())} 个 / "
              f"主题 {sig['series'] or '未标注'} / "
              f"主技法 {sig['primary_technique'] or '未标注'}")

    # ---- 阶段 2: 两两相似度比对 --------------------------------------
    fails, warns = [], []
    max_pair = None
    pair_count = 0
    print("")
    for sig_a, sig_b in combinations(signatures, 2):
        sim, wl, hist, rhythm = similarity(sig_a, sig_b)
        pair_count += 1
        if max_pair is None or sim > max_pair[0]:
            max_pair = (sim, sig_a["name"], sig_b["name"])

        detail = (f"{sig_a['name']} <-> {sig_b['name']}: sim={sim:.3f} "
                  f"(WL={wl:.3f}, 直方图={hist:.3f}, 节奏={rhythm:.3f})")
        if sim > FAIL_THRESHOLD:
            fails.append(
                f"克隆嫌疑: {detail} > {FAIL_THRESHOLD}: 两模型结构签名过近, "
                f"属于换皮/微调翻版, 拒绝入库 (换色与镜像在 WL 指纹层面同构, "
                f"无法靠改颜色规避)")
        elif sim > BOUNDARY_THRESHOLD:
            warns.append(
                f"边界案例: {detail} 位于 ({BOUNDARY_THRESHOLD}, "
                f"{FAIL_THRESHOLD}] 区间, 须人工比对并把结论记入 "
                f"content_meta.curator_review.boundary_case_note")
        elif sim > REPORT_THRESHOLD:
            print(f"  [关注] {detail}")

    if max_pair is not None:
        print(f"  全库最相似对: {max_pair[1]} <-> {max_pair[2]} "
              f"(sim={max_pair[0]:.3f}), 共比对 {pair_count} 对")

    # ---- 阶段 3: 主题 + 主技法拥挤度 ---------------------------------
    groups = Counter()
    unlabeled = []
    for sig in signatures:
        if sig["series"] and sig["primary_technique"]:
            groups[(sig["series"], sig["primary_technique"])] += 1
        else:
            unlabeled.append(sig["name"])
    for (series, technique), count in sorted(groups.items()):
        if count > MAX_PER_THEME_TECHNIQUE:
            warns.append(
                f"主题/技法拥挤: 主题 {series!r} + 主技法 {technique!r} "
                f"已有 {count} 个模型 (> {MAX_PER_THEME_TECHNIQUE}), "
                f"内容规划应审视该组合是否过度开采")
    if unlabeled:
        print(f"  [提示] {len(unlabeled)} 个模型缺少 content_meta.series / "
              f"technique_tags.primary 标注, 未参与主题拥挤度统计: "
              f"{', '.join(unlabeled[:6])}")

    # ---- 汇总 --------------------------------------------------------
    print("")
    for message in fails:
        print(f"[FAIL] {message}")
    for message in warns:
        print(f"[WARN] {message}")

    print("==============================================================")
    if fails or parse_failures:
        print(f" 结果: 发现 {len(fails)} 对克隆嫌疑, "
              f"{parse_failures} 个模型签名计算失败, 拒绝入库")
        return 1
    print(f" 结果: {len(signatures)} 个模型两两比对全部通过 "
          f"(警告 {len(warns)} 条, 不阻断)")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
