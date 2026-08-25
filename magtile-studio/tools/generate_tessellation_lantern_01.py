#!/usr/bin/env python3
"""生成模型 data/models/tessellation_lantern_01.json (密铺柱面灯笼)。

几何艺术 D1: 2x2 盒式地台 + 四面墙环, 每面墙顶两片正三角密铺带,
内顶四片方板收边。

用法: python3 tools/generate_tessellation_lantern_01.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from magtile_gen import ModelBuilder  # noqa: E402

b = ModelBuilder()

for j in range(2):
    for i in range(2):
        b.flat(f"f_{i}_{j}", i, j, 0.0, "gray" if (i + j) % 2 else "clear")

for i in range(2):
    b.wall_ns(f"s_{i}", i, 0.0, 0, "gray")
    b.wall_ns(f"n_{i}", i, 2.0, 0, "clear")
    b.wall_ew(f"w_{i}", 0.0, i, 0, "gray")
    b.wall_ew(f"e_{i}", 2.0, i, 0, "clear")

PAIRS = [("ts", "s", 0.0, ("red", "orange")),
         ("tn", "n", 2.0, ("yellow", "green")),
         ("tw", "w", None, ("cyan", "blue")),
         ("te", "e", None, ("purple", "pink"))]
for prefix, axis, y_fixed, (c0, c1) in PAIRS:
    if axis in ("s", "n"):
        for i in range(2):
            b.crest_ns(f"{prefix}_{i}", i, y_fixed, 1.0, c0 if i == 0 else c1)
    else:
        x_fixed = 0.0 if axis == "w" else 2.0
        for i in range(2):
            b.crest_ew(f"{prefix}_{i}", x_fixed, i, 1.0, c0 if i == 0 else c1)

b.flat("ceil_00", 0, 0, 1.0, "clear")
b.flat("ceil_10", 1, 0, 1.0, "gray")
b.flat("ceil_01", 0, 1, 1.0, "gray")
b.flat("ceil_11", 1, 1, 1.0, "clear")

b.step("铺地台: 四片清灰方板拼成 2x2 底座。",
       ["f_0_0", "f_0_1", "f_1_0", "f_1_1"])
b.step("立墙环: 八片方板沿四边合围, 墙脚踩地台拼缝。",
       ["s_0", "s_1", "n_0", "n_1", "w_0", "w_1", "e_0", "e_1"],
       highlight=["f_0_0"])
b.step("砌南/北/西/东密铺带: 每面两片正三角骑墙顶, 四色交替。",
       ["ts_0", "ts_1", "tn_0", "tn_1", "tw_0", "tw_1", "te_0", "te_1"],
       highlight=["s_0"])
b.step("封内顶: 四片方板骑在密铺带顶沿, 围成灯笼腔顶 —— 完工!",
       ["ceil_00", "ceil_10", "ceil_01", "ceil_11"],
       highlight=["ts_0", "tn_1"])

b.finalize(
    model_id="tessellation_lantern_01",
    name="密铺柱面灯笼",
    name_en="Tessellation Lantern 01",
    description=(
        "几何艺术 D1: 2x2 盒式框架四面墙环, 每面墙顶立两片"
        "正三角形成密铺带 (T18), 内顶方板收边成腔。"
    ),
    difficulty=1,
    tags=["几何艺术", "密铺", "灯笼", "柱面", "光影"],
    min_pieces=24,
    min_steps=4,
    series="geometric_art",
)
