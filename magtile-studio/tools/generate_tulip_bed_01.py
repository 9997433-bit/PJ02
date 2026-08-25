#!/usr/bin/env python3
"""生成模型 data/models/tulip_bed_01.json (郁金香花坛)。

内容批 K 模型 2/4: 植物花园主题 D1 —— 补"花"原型空白, 与 rose_pergola_01
(长廊花架) 结构不同。招牌是 T01 盒式围栏围合 + T18 密铺色带: 围栏墙片
按红/白/绿/黄四色周期交替 (密铺节奏), 框内三支等腰郁金香立柱是花园主角。

结构总览 (世界单位: 1.0 = 正方形磁力片边长):
  - 园路地台: 五片灰色方板围出框外走道                               5 片
  - 花坛底板 (x [1,3], y [1,3]): 四片泥土色方板                      4 片
  - 围栏墙环: 四色周期交替立墙 x12 (T18 密铺色带, 两层)             12 片
  - 郁金香 x3: 红/黄/紫等腰三角立柱                                   3 片
  - 围栏角柱 x2: 等边三角骑对角沿口                                   2 片
  合计 26 片, 7 个教程步骤, 3 种磁力片形状 (全部 CORE-9 之内)。

物理规则要点 (validate 常规 + strict 双档零警告):
  - 围栏墙脚整边踩花坛底板/园路拼缝, 四角竖边互咬闭环;
  - 色带按固定周期交替, 相邻墙片竖边整边互吸;
  - 郁金香底边整边吸围栏内沿口;
  - 角柱骑围栏顶沿, 重心正压铰链线。

用法: python3 tools/generate_tulip_bed_01.py  (在 magtile-studio 目录下运行)
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from magtile_gen import ModelBuilder  # noqa: E402

b = ModelBuilder()

PATH = "gray"
SOIL = "orange"
PATTERN = ["red", "white", "green", "yellow"]
TULIP = ["red", "yellow", "purple"]
POST = "green"


def fence_color(idx):
    return PATTERN[idx % len(PATTERN)]


# =================================================================
# 1. 园路 (3x3 外圈, 中心 2x2 留给花床)
# =================================================================
for i in range(3):
    b.flat(f"path_{i}_0", i, 0, 0.0, PATH)
b.flat("path_0_1", 0, 1, 0.0, PATH)
b.flat("path_0_2", 0, 2, 0.0, PATH)

# =================================================================
# 2. 花坛底板
# =================================================================
for i in (1, 2):
    for j in (1, 2):
        b.flat(f"soil_{i}_{j}", i, j, 0.0, SOIL)

# =================================================================
# 3. 围栏 (四色密铺, 两层)
# =================================================================
for i, x in enumerate((1, 2)):
    b.wall_ns(f"fence_s0_{i}", x, 1.0, 0, fence_color(i))
    b.wall_ns(f"fence_n0_{i}", x, 2.0, 0, fence_color(i + 2))
    b.wall_ns(f"fence_s1_{i}", x, 1.0, 1, fence_color(i + 4))
    b.wall_ns(f"fence_n1_{i}", x, 2.0, 1, fence_color(i + 6))
b.wall_ew("fence_w0", 1.0, 1, 0, fence_color(8))
b.wall_ew("fence_w1", 1.0, 2, 0, fence_color(9))
b.wall_ew("fence_e0", 3.0, 1, 0, fence_color(10))
b.wall_ew("fence_e1", 3.0, 2, 0, fence_color(11))

# =================================================================
# 4. 郁金香 + 角柱
# =================================================================
b.crest_ns("tulip_w", 1, 1.0, 2.0, TULIP[0])
b.crest_ns("tulip_m", 2, 1.0, 2.0, TULIP[1])
b.crest_ns("tulip_e", 2, 2.0, 2.0, TULIP[2])
b.crest_ns("post_sw", 1, 1.0, 2.0, POST)
b.crest_ns("post_ne", 2, 2.0, 2.0, POST)

# =================================================================
# 教程步骤 (7 步)
# =================================================================
b.step(
    "铺园路: 五片灰色方板围出框外走道, 中间留 2x2 给花床。",
    [f"path_{i}_0" for i in range(3)] + ["path_0_1", "path_0_2"],
    tip="园路是围栏的脚位 —— 拼缝对齐, 墙才站得稳。",
)
b.step(
    "铺花坛底: 四片橙色泥土方板填满框内, 行行整边互吸。",
    [f"soil_{i}_{j}" for i in (1, 2) for j in (1, 2)],
    highlight=["path_1_0"],
    tip="泥土区就是郁金香的家。",
)
b.step(
    "砌围栏第一层: 红/白/绿/黄四色周期交替, 八片立墙踩住花床拼缝。",
    [f"fence_s0_{i}" for i in (0, 1)]
    + [f"fence_n0_{i}" for i in (0, 1)]
    + ["fence_w0", "fence_w1", "fence_e0", "fence_e1"],
    highlight=["soil_1_1"],
    tip="色带按固定节奏走 —— 这就是 T18 密铺变奏。",
)
b.step(
    "围栏加高第二层: 四片续接色带, 与下层竖边整边互吸。",
    [f"fence_s1_{i}" for i in (0, 1)] + [f"fence_n1_{i}" for i in (0, 1)],
    highlight=["fence_s0_0"],
    tip="两层围栏才够高 —— 郁金香要从框里探出头来。",
)
b.step(
    "种郁金香: 三支等边三角立在围栏顶沿, 底边吸墙顶。",
    ["tulip_w", "tulip_m", "tulip_e"],
    highlight=["fence_s1_0"],
    tip="红/黄/紫三色 —— 三支立柱就是这座花坛的主角。",
)
b.step(
    "装围栏角柱收尾: 西南与东北角各立一片绿色等边三角 —— 郁金香花坛落成!",
    ["post_sw", "post_ne"],
    highlight=["tulip_m"],
    tip="色带、立柱、角柱齐了 —— 植物花园第一座 D1 花作品。",
)

b.finalize(
    model_id="tulip_bed_01",
    name="郁金香花坛",
    name_en="Tulip Flower Bed 01",
    description=(
        "植物花园 D1: 四色周期围栏 (T18 密铺色带) 围合 2x2 泥土花床, 框内"
        "立着红/黄/紫三支等腰郁金香立柱; 对角绿色角柱锁住围栏沿口。与玫瑰"
        "长廊的门式花架不同, 这次主角就是花本身 —— 孩子能独立完成的第一个"
        "花坛作品。"
    ),
    difficulty=1,
    tags=["植物花园", "郁金香", "花坛", "入门", "密铺"],
    min_pieces=26,
    min_steps=6,
)
