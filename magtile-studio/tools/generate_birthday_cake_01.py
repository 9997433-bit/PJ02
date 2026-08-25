#!/usr/bin/env python3
"""生成模型 data/models/birthday_cake_01.json (三层生日蛋糕)。

内容批 M 模型 1/4: 节日限定主题首个 D1 —— 与 birthday_party_01
(D3 派对场景) 主角不同, 这次蛋糕本体就是模型。招牌是 T12 层叠退台
+ T18 密铺: 3x3 底层粉白密铺, 其上升 2x2 / 1x1 墙环逐层收分,
 顶层蜡烛瘦高尖 + 底层东沿生日火花 —— 吹蜡烛前先许愿!

结构总览 (世界单位: 1.0 = 正方形磁力片边长):
  - 底层 (3x3, z=0): 粉白棋盘方板 x9 (T18 密铺)                    9 片
  - 中层 (2x2 墙环 z 0..1 + 盖板 z=1): 墙 x4 + 奶油色盖板 x4       8 片
  - 顶层 (1x1 墙环 z 1..2 + 盖板): 墙 x4 + 粉色盖板 x1              5 片
  - 蜡烛 + 火花: 瘦高尖 x1 + 等边 x1                                2 片
  合计 24 片, 6 个教程步骤, 3 种磁力片形状 (全部 CORE-9 之内)。

用法: python3 tools/generate_birthday_cake_01.py  (在 magtile-studio 目录下运行)
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from magtile_gen import ModelBuilder  # noqa: E402

b = ModelBuilder()

PATTERN = ["pink", "clear", "pink", "clear"]
CREAM = ["yellow", "orange", "yellow", "orange"]
TOP = "pink"
CANDLE = "yellow"
SPARK = "orange"


def pattern_color(idx):
    return PATTERN[idx % len(PATTERN)]


# =================================================================
# 1. 底层 3x3 (z=0): 粉白密铺
# =================================================================
for j in range(3):
    for i in range(3):
        b.flat(f"t1_{i}_{j}", i, j, 0.0, pattern_color(i + j))

# =================================================================
# 2. 中层 2x2 墙环 (z 0..1) + 奶油色盖板 (z=1)
# =================================================================
b.wall_ns("t2_s0", 0, 0.0, 0, CREAM[0])
b.wall_ns("t2_s1", 1, 0.0, 0, CREAM[1])
b.wall_ns("t2_n0", 0, 2.0, 0, CREAM[2])
b.wall_ns("t2_n1", 1, 2.0, 0, CREAM[3])
for j in range(2):
    for i in range(2):
        b.flat(f"t2_cap_{i}_{j}", i, j, 1.0, CREAM[i + 2 * j])

# =================================================================
# 3. 顶层 1x1 墙环 (z 1..2) + 盖板 (z=2)
# =================================================================
b.wall_ns("t3_s", 0, 0.0, 1, TOP)
b.wall_ns("t3_n", 0, 1.0, 1, TOP)
b.wall_ew("t3_w", 0.0, 0, 1, TOP)
b.wall_ew("t3_e", 1.0, 0, 1, TOP)
b.flat("t3_cap", 0, 0, 2.0, TOP)

# =================================================================
# 4. 蜡烛 + 火花
# =================================================================
b.spire_ns("candle", 0, 0.0, 2.0, CANDLE)
b.crest_ew("spark", 2.0, 0, 0.0, SPARK)

# =================================================================
# 教程步骤 (6 步)
# =================================================================
b.step(
    "铺底层圆台: 九片粉白相间的方板拼成 3x3, 行行整边互吸 —— 这是最大的一层蛋糕。",
    [f"t1_{i}_{j}" for j in range(3) for i in range(3)],
    tip="粉白交替就是 T18 密铺 —— 像奶油裱花一样有节奏。",
)
b.step(
    "砌中层墙环: 四片黄橙墙围成 2x2, 墙脚整边踩底层拼缝 (T12 收分)。",
    ["t2_s0", "t2_s1", "t2_n0", "t2_n1"],
    highlight=["t1_0_0", "t1_1_1"],
    tip="第二层比第一层小一圈 —— 墙环立在底层上, 不是悬空叠板。",
)
b.step(
    "盖中层奶油: 四片黄橙盖板压墙顶, 中层圆台完成。",
    [f"t2_cap_{i}_{j}" for j in range(2) for i in range(2)],
    highlight=["t2_s0"],
    tip="盖板四边吸墙顶 —— 中层蛋糕面平整了。",
)
b.step(
    "砌顶层墙环: 四片粉墙围成 1x1, 墙脚吸中层盖板拼缝。",
    ["t3_s", "t3_n", "t3_w", "t3_e"],
    highlight=["t2_cap_0_0"],
    tip="最小的一圈 —— 第三层圆台只剩正中一格。",
)
b.step(
    "盖顶层 + 插蜡烛: 粉色顶板, 黄色瘦高蜡烛从正中向上立起。",
    ["t3_cap", "candle"],
    highlight=["t3_s"],
    tip="蜡烛要插正 —— 顶层第三层圆台完成。",
)
b.step(
    "点火花收尾: 橙色三角骑在底层东沿 —— 三层生日蛋糕完工, 生日快乐!",
    ["spark"],
    highlight=["candle", "t1_2_0"],
    tip="吹蜡烛前先许愿 —— 节日限定第一座 D1 蛋糕!",
)

b.finalize(
    model_id="birthday_cake_01",
    name="三层生日蛋糕",
    name_en="Birthday Cake 01",
    description=(
        "节日限定 D1: 3x3 粉白密铺底层 (T18) 上逐层收分 2x2 / 1x1 墙环"
        "与盖板 (T12), 顶层黄色瘦高蜡烛 + 底层东沿生日火花。"
        "蛋糕本体就是主角, 与派对场景模型完全不同。吹蜡烛前先许愿!"
    ),
    difficulty=1,
    tags=["节日", "生日", "蛋糕", "入门", "密铺"],
    min_pieces=24,
    min_steps=6,
    series="holiday_seasonal",
)
