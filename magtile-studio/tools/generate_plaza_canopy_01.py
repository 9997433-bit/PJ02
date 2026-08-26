#!/usr/bin/env python3
"""生成模型 data/models/plaza_canopy_01.json (广场遮阳展台)。

内容批 P 模型 1/10: 扩展片型 large_square 引流 D1 —— 两片大正方形
拼 4x2 台面, 两片平拼 4x2 遮阳顶棚 (z=2); 四柱 + 双层檐轨, 中央
1x1 盒式展框 (T01); 四角直角三角斜撑 (T14) 锁剪力。

结构要点: 四角东西/南北双层横楣正交叠合成四柱; 展框占北半 1x1;
斜撑沿 booth 南沿 ±y/±x 外张贴台面, 不压侧柱与南檐轨。

用法: python3 tools/generate_plaza_canopy_01.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from magtile_gen import ModelBuilder  # noqa: E402

b = ModelBuilder()

SLAB = "gray"
CANOPY = "cyan"
BOOTH = "orange"
BRACE = "gray"

b.add("lg_fl_w", "large_square", (1.0, 1.0, 0.0), (0, 0, 0), SLAB)
b.add("lg_fl_e", "large_square", (3.0, 1.0, 0.0), (0, 0, 0), SLAB)

b.wall_ns("booth_s", 1, 1.0, 0, BOOTH)
b.wall_ns("booth_n", 1, 2.0, 0, BOOTH)
b.wall_ew("booth_w", 1.0, 1, 0, BOOTH)
b.wall_ew("booth_e", 2.0, 1, 0, BOOTH)

b.lintel_ew("tie_w0", 0.0, 0, 0, SLAB)
b.lintel_ew("tie_w1", 0.0, 0, 1, SLAB)
b.lintel_ew("tie_e0", 4.0, 0, 0, SLAB)
b.lintel_ew("tie_e1", 4.0, 0, 1, SLAB)

b.lintel_ns("tie_s0", 0, 0.0, 0, SLAB)
b.lintel_ns("tie_s2", 2, 0.0, 0, SLAB)
b.lintel_ns("tie_s1", 0, 0.0, 1, SLAB)
b.lintel_ns("tie_s3", 2, 0.0, 1, SLAB)

b.lintel_ns("tie_n1", 0, 2.0, 1, SLAB)
b.lintel_ns("tie_n3", 2, 2.0, 1, SLAB)

b.brace("br_ws", (1.0, 1.0, 0.0), "-y", BRACE)
b.brace("br_es", (2.0, 1.0, 0.0), "-y", BRACE)
b.brace("br_ww", (1.0, 1.0, 0.0), "-x", BRACE)
b.brace("br_ew", (2.0, 1.0, 0.0), "+x", BRACE)

b.add("cn_w", "large_square", (1.0, 1.0, 2.0), (0, 0, 0), CANOPY)
b.add("cn_e", "large_square", (3.0, 1.0, 2.0), (0, 0, 0), CANOPY)

b.step(
    "铺台面: 两片灰色大正方形整边互吸, 拼成 4x2 广场地台。",
    ["lg_fl_w", "lg_fl_e"],
    tip="大正方形边长 2.0 —— 两片拼缝对齐, 四角才有整边可叠檐轨。",
)
b.step(
    "围展框: 四片橙色方墙在北半拼 1x1 盒式框架 (T01)。",
    ["booth_s", "booth_n", "booth_w", "booth_e"],
    highlight=["lg_fl_w"],
)
b.step(
    "立东西柱脚: 四片横楣沿 x=0/4 叠成侧柱 (z=0..1)。",
    ["tie_w0", "tie_e0", "tie_w1", "tie_e1"],
    highlight=["lg_fl_w"],
)
b.step(
    "铺南向双层檐轨: 四片横楣沿 y=0 与东西柱正交叠合。",
    ["tie_s0", "tie_s2", "tie_s1", "tie_s3"],
    highlight=["tie_w0"],
    tip="角点处南北/东西横楣正交 —— 四柱成型。",
)
b.step(
    "封北向顶层檐轨: 两片横楣在 y=2 接到 z=1 顶沿。",
    ["tie_n1", "tie_n3"],
    highlight=["tie_w1", "tie_s1"],
)
b.step(
    "装展框斜撑 (T14): 四片直角三角沿 booth 南沿外张, 双边吸合。",
    ["br_ws", "br_es", "br_ww", "br_ew"],
    highlight=["booth_s", "tie_s0"],
    tip="两向各一对 —— 竖边吸展框、横边吸台面, 不碰侧柱。",
)
b.step(
    "盖西半遮阳顶: 一片青色大正方形平放到 z=2。",
    ["cn_w"],
    highlight=["tie_w1", "tie_s1"],
)
b.step(
    "盖东半遮阳顶 —— 广场遮阳展台落成!",
    ["cn_e"],
    highlight=["cn_w", "tie_e1"],
    tip="两片大正方形整边互吸 —— 4x2 青色顶棚遮阳完毕!",
)

b.finalize(
    model_id="plaza_canopy_01",
    name="广场遮阳展台",
    name_en="Plaza Canopy 01",
    description=(
        "扩展片型 large_square 引流 D1: 两片大正方形拼 4x2 台面,"
        "北半 1x1 橙色盒式展框 (T01); 四角东西/南北双层檐轨正交"
        "叠合成四柱, 四片直角斜撑 (T14) 沿展框南沿外张双边吸合;"
        "顶面两片大正方形平拼 4x2 青色遮阳顶棚 —— 与手机架、"
        "相框画架剪影均不同。"
    ),
    difficulty=1,
    tags=["实用功能", "遮阳棚", "展台", "广场", "入门", "大正方形"],
    min_pieces=22,
    min_steps=8,
    series="practical_utility",
)
