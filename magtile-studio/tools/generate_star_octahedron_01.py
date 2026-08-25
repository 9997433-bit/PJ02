#!/usr/bin/env python3
"""生成模型 data/models/star_octahedron_01.json (星形八面体摆件)。

内容批 K 模型 3/4: 几何艺术主题 D2 —— 全库首个多面体摆件。
招牌是 T05 平面翻折 + T11 镜像: 2x2 底座对角直角三角互锁,
上下两组等边三角星芒 + 顶上一枚四坡锥。

结构总览 (世界单位: 1.0 = 正方形磁力片边长):
  - 底座 2x2 + 对角自锁 brace x2 + 外扩台沿 x4                      10 片
  - 底坐墙环 x4 + 中台 2x2                                          8 片
  - 下星芒 x4 + 中心四坡锥 x4 + 台内立柱 x4                          12 片
  合计 30 片, 6 个教程步骤, 3 种磁力片形状 (全部 CORE-9 之内)。

用法: python3 tools/generate_star_octahedron_01.py  (在 magtile-studio 目录下运行)
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from magtile_gen import ModelBuilder  # noqa: E402

b = ModelBuilder()

BASE_A = "gray"
BASE_B = "clear"
BRACE = "purple"
PED = "blue"
LOWER = "cyan"
UPPER = "yellow"
APEX = "red"
BT = 1.866025
# 1. 底座 + 对角自锁 + 外扩台沿
# =================================================================
for j in range(2):
    for i in range(2):
        b.flat(f"base_{i}_{j}", i, j, 0.0, BASE_A if (i + j) % 2 == 0 else BASE_B)
b.flat("pad_n0", 0, 2, 0.0, BASE_A)
b.flat("pad_n1", 1, 2, 0.0, BASE_B)
b.flat("pad_e0", 2, 0, 0.0, BASE_A)
b.flat("pad_e1", 2, 1, 0.0, BASE_B)
b.brace("lock_a", (1.0, 0.0, 0.0), "+y", BRACE)
b.brace("lock_b", (0.0, 1.0, 0.0), "+x", BRACE)

# =================================================================
# 2. 底坐墙环 + 中台
# =================================================================
b.wall_ns("ped_s", 0, 0.0, 0, PED)
b.wall_ns("ped_n", 0, 2.0, 0, PED)
b.wall_ew("ped_w", 0.0, 0, 0, PED)
b.wall_ew("ped_e", 2.0, 0, 0, PED)
for j in range(2):
    for i in range(2):
        b.flat(f"deck_{i}_{j}", i, j, 1.0, BASE_B if (i + j) % 2 else BASE_A)

# =================================================================
# 3. 下星芒 + 中心四坡锥 + 台内立柱
# =================================================================
b.crest_ns("low_s", 0, 0.0, 1.0, LOWER)
b.crest_ns("low_n", 0, 2.0, 1.0, LOWER)
b.crest_ew("low_w", 0.0, 0, 1.0, LOWER)
b.crest_ew("low_e", 2.0, 0, 1.0, LOWER)
b.hat4("apex", 0, 0, 1.0, APEX, shape="equilateral_triangle")
b.spire_ns("spk_sw", 0, 1.0, 1.0, UPPER)
b.spire_ns("spk_ne", 1, 2.0, 1.0, UPPER)
b.spire_ew("spk_nw", 0.0, 1, 1.0, UPPER)
b.spire_ew("spk_se", 2.0, 1, 1.0, UPPER)

# =================================================================
# 教程步骤 (6 步)
# =================================================================
b.step(
    "铺底座并装对角自锁: 四片方板 + 四片外扩台沿, 两片直角三角互穿 (T11)。",
    [f"base_{i}_{j}" for j in range(2) for i in range(2)]
    + ["pad_n0", "pad_n1", "pad_e0", "pad_e1", "lock_a", "lock_b"],
    tip="正对角自锁 —— 底座从此推不散。",
)
b.step(
    "立底坐墙环并铺中台: 四片立墙 + 四片方板封住 z=1 平台。",
    ["ped_s", "ped_n", "ped_w", "ped_e"]
    + [f"deck_{i}_{j}" for j in range(2) for i in range(2)],
    highlight=["base_0_1"],
    tip="墙环是下星芒的沿口。",
)
b.step(
    "装下星芒与中心四坡锥: 四片沿口三角 + 四坡锥在 1x1 洞口自锁 (T05)。",
    ["low_s", "low_n", "low_w", "low_e", "apex_s", "apex_e", "apex_n", "apex_w"],
    highlight=["deck_0_0"],
    tip="先在桌面拼展开图, 再整体翻折立起。",
)
b.step(
    "装台内立柱并收尾: 四片瘦高三角点缀台面 (T11 镜像) —— 星形八面体摆件落成!",
    ["spk_sw", "spk_ne", "spk_nw", "spk_se"],
    highlight=["apex_s"],
    tip="上下体互穿成星芒 —— 几何艺术第一座多面体作品。",
)

b.finalize(
    model_id="star_octahedron_01",
    name="星形八面体摆件",
    name_en="Star Octahedron Display 01",
    description=(
        "几何艺术 D2: 2x2 底座对角直角三角互锁, 上下两组等边三角互穿成"
        "星芒, 顶上一枚等边四坡锥合拢上四面体 —— T05 翻折 + T11 镜像"
        "的入库示范。与密铺屏风/测地穹顶完全不同, 这是全库第一座星形"
        "多面体摆件。"
    ),
    difficulty=2,
    tags=["几何艺术", "多面体", "星形", "摆件", "进阶"],
    min_pieces=30,
    min_steps=4,
    series="geometric_art",
)
