#!/usr/bin/env python3
"""生成模型 data/models/cruise_ship_01.json (阳光号游轮)。

海洋航行主题新作, 全库第一艘客运游轮 —— 与货轮 (甲板堆箱)、
渔船/帆船 (单层小艇) 都不同, 本作的招牌是"逐级退台的客舱楼 +
双直角三角拼尖的船头": 船体箱环之上, 主甲板 -> 舷窗客舱层 ->
阳光甲板逐级退台 (T12), 舰桥骑在船头一侧与客舱共用一面墙
(共墙技法), 船尾一片红色长板烟囱骑墙横立; 船头两片直角三角
平板互咬拼出尖尖的船艏 —— 全库唯一的"客轮阶梯剪影 + 尖艏"。

结构总览 (世界单位: 1.0 = 正方形磁力片边长, 船头朝东):
  - 海面 8x4 (x [0,8], y [0,4]): 长板 x8 + 单位方板 x16       24 片
  - 船体箱环 (x [1,7], y [1,3], z 0..1): 舷门/舷窗/白墙 x16   16 片
  - 主甲板 (z=1): 纵向长板 x6                                  6 片
  - 尖船艏: 直角三角平板 x2 互咬拼尖 + 船尾救生圈 x2           4 片
  - 客舱层 (x [2,5], z 1..2): 舷窗 x6 + 横楣端墙 x2            8 片
  - 阳光甲板 (z=2): 纵向长板 x3 (中间一片是泳池)               3 片
  - 红烟囱: 长板骑西端墙顶横立                                  1 片
  - 舰桥 (x [5,6], z 1..2): 前窗 x2 + 横楣 x1 (西端共墙)
    + 舰桥顶长板 x1 + 信号灯 x1                                5 片
  合计 67 片, 14 个教程步骤, 6 种磁力片形状 (全部 CORE-9 之内)。

物理规则要点 (validate 常规 + strict 双档零警告):
  - 船体箱环墙脚踩海面拼缝整边吸合, 四角竖边互咬闭环;
  - 主甲板纵向长板短边搭南北墙顶、长边互吸 —— 双边支承零悬挑;
  - 客舱层舷窗踩甲板短边, 两端用横楣 (长方形立板) 整边吸
    甲板纵缝; 阳光甲板同构再退一级;
  - 舰桥西墙就是客舱层东横楣 (共墙技法), 舰桥顶长板四边
    分别搭前后窗顶与两条横楣顶 —— 四边全支承;
  - 船艏两片直角三角平板: 直角边各自整边吸船头墙顶, 另一条
    直角边两片互咬 —— 单片力矩远小于预算, 且互为冗余;
  - 烟囱/信号灯/救生圈各自独立吸附, 剪断任何一条装饰连接
    最多失联 1 片 (< 3), R8 单点失效通过。

用法: python3 tools/generate_cruise_ship_01.py  (在 magtile-studio 目录下运行)
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from magtile_gen import ModelBuilder  # noqa: E402

b = ModelBuilder()

SEA = "blue"        # 海面
KEEL = "cyan"       # 船底水线 (船体围合的内水面)
HULL = "clear"      # 船体白墙
PORT = "cyan"       # 舷窗
GANG = "orange"     # 舷门
DECK = "yellow"     # 主甲板
CABIN = "clear"     # 客舱端墙
SUN = "yellow"      # 阳光甲板
POOL = "cyan"       # 甲板泳池
FUNNEL = "red"      # 烟囱
BRIDGE = "cyan"     # 舰桥前窗
BOW = "clear"       # 船艏
LIFE = "orange"     # 救生圈
LIGHT = "yellow"    # 信号灯


def wall_ns_t(tid, tile_type, x0, y, z0, color):
    b.add(tid, tile_type, (x0 + 0.5, y, z0 + 0.5), (90, 0, 0), color)


# =================================================================
# 1. 海面 8x4: 南北两行长板, 中间两行单位方板 (船体围合处用青色水线)
# =================================================================
for i, x0 in enumerate((0, 2, 4, 6)):
    b.flat_rect(f"sea_s_{i}", x0, 0, 0.0, SEA)        # 南行 y [0,1]
for x0 in range(8):
    color = KEEL if 1 <= x0 <= 6 else SEA
    b.flat(f"sea_m1_{x0}", x0, 1, 0.0, color)         # 中行 y [1,2]
for x0 in range(8):
    color = KEEL if 1 <= x0 <= 6 else SEA
    b.flat(f"sea_m2_{x0}", x0, 2, 0.0, color)         # 中行 y [2,3]
for i, x0 in enumerate((0, 2, 4, 6)):
    b.flat_rect(f"sea_n_{i}", x0, 3, 0.0, SEA)        # 北行 y [3,4]

# =================================================================
# 2. 船体箱环 (x [1,7], y [1,3], z 0..1): 舷门居中, 舷窗排开
# =================================================================
HULL_S = []
for x0 in range(1, 7):
    if x0 == 3:
        wall_ns_t(f"hull_s_{x0}", "door_frame", x0, 1.0, 0, GANG)   # 舷门
    elif x0 in (2, 4):
        wall_ns_t(f"hull_s_{x0}", "window_square", x0, 1.0, 0, PORT)
    else:
        b.wall_ns(f"hull_s_{x0}", x0, 1.0, 0, HULL)
    HULL_S.append(f"hull_s_{x0}")
HULL_N = []
for x0 in range(1, 7):
    if x0 in (2, 4):
        wall_ns_t(f"hull_n_{x0}", "window_square", x0, 3.0, 0, PORT)
    else:
        b.wall_ns(f"hull_n_{x0}", x0, 3.0, 0, HULL)
    HULL_N.append(f"hull_n_{x0}")
b.wall_ew("hull_w1", 1.0, 1, 0, HULL)                 # 船尾 (西)
b.wall_ew("hull_w2", 1.0, 2, 0, HULL)
b.wall_ew("hull_e1", 7.0, 1, 0, HULL)                 # 船头 (东)
b.wall_ew("hull_e2", 7.0, 2, 0, HULL)

# =================================================================
# 3. 主甲板 (z=1): 六片纵向长板, 短边搭南北墙顶
# =================================================================
for x0 in range(1, 7):
    b.flat_rect(f"deck_{x0}", x0, 1, 1.0, DECK, axis="y")

# =================================================================
# 4. 尖船艏 (z=1) + 船尾救生圈
# =================================================================
b.place_tri("bow_s", "right_triangle",
            (7.0, 2.0, 1.0), (7.0, 1.0, 1.0), (8.0, 2.0, 1.0), BOW)
b.place_tri("bow_n", "right_triangle",
            (7.0, 2.0, 1.0), (8.0, 2.0, 1.0), (7.0, 3.0, 1.0), BOW)
b.crest_ns("life_s", 1, 1.0, 1.0, LIFE)               # 船尾救生圈
b.crest_ns("life_n", 1, 3.0, 1.0, LIFE)

# =================================================================
# 5. 客舱层 (x [2,5], z 1..2): 舷窗 x6 + 两端横楣墙
# =================================================================
CABIN_WIN = []
for x0 in range(2, 5):
    wall_ns_t(f"cabin_s_{x0}", "window_square", x0, 1.0, 1, PORT)
    wall_ns_t(f"cabin_n_{x0}", "window_square", x0, 3.0, 1, PORT)
    CABIN_WIN += [f"cabin_s_{x0}", f"cabin_n_{x0}"]
b.lintel_ew("cabin_w", 2.0, 1, 1, CABIN)              # 西端横楣
b.lintel_ew("cabin_e", 5.0, 1, 1, CABIN)              # 东端横楣 (舰桥共墙)

# =================================================================
# 6. 阳光甲板 (z=2) + 红烟囱
# =================================================================
b.flat_rect("sun_w", 2, 1, 2.0, SUN, axis="y")
b.flat_rect("sun_pool", 3, 1, 2.0, POOL, axis="y")    # 甲板泳池
b.flat_rect("sun_e", 4, 1, 2.0, SUN, axis="y")
b.lintel_ew("funnel", 2.0, 1, 2, FUNNEL)              # 红烟囱骑横楣顶

# =================================================================
# 7. 舰桥 (x [5,6], z 1..2): 与客舱共用西墙, 前窗朝海
# =================================================================
wall_ns_t("bridge_s", "window_square", 5, 1.0, 1, BRIDGE)
wall_ns_t("bridge_n", "window_square", 5, 3.0, 1, BRIDGE)
b.lintel_ew("bridge_e", 6.0, 1, 1, CABIN)             # 东横楣
b.flat_rect("bridge_roof", 5, 1, 2.0, DECK, axis="y")
b.crest_ns("mast_light", 5, 1.0, 2.0, LIGHT)          # 信号灯

# =================================================================
# 教程步骤 (14 步)
# =================================================================
b.step(
    "铺南行海面: 四片蓝色长板短边互吸连成一排。",
    [f"sea_s_{i}" for i in range(4)],
    tip="风平浪静的出航日 —— 先把大海铺出来。",
)
b.step(
    "铺中行海面 (南): 船体围合处用青色水线方板。",
    [f"sea_m1_{x0}" for x0 in range(8)],
    highlight=["sea_s_0"],
    tip="青色的一段就是船底的位置 —— 船体墙脚要踩它的拼缝。",
)
b.step(
    "铺中行海面 (北): 再来八片, 水线与海面行行互吸。",
    [f"sea_m2_{x0}" for x0 in range(8)],
    highlight=["sea_m1_0"],
    tip="两行水线并排, 船体箱环就围在它们四周。",
)
b.step(
    "铺北行海面: 四片长板合拢海面, 航道全线贯通。",
    [f"sea_n_{i}" for i in range(4)],
    highlight=["sea_m2_0"],
    tip="海面连成一整张网 —— 阳光号马上开始铺龙骨。",
)
b.step(
    "立船体南舷: 舷门居中, 两侧舷窗与白墙一字排开。",
    HULL_S,
    highlight=["sea_m1_3"],
    tip="墙脚整边吸水线拼缝, 竖边逐片互吸 —— 乘客从舷门登船。",
)
b.step(
    "立船体北舷: 六片对称排开, 舷窗对齐南舷。",
    HULL_N,
    highlight=["hull_s_1"],
    tip="南北舷像镜子一样对称 —— 船身左右一样重才稳。",
)
b.step(
    "合拢船尾船头: 四片端墙竖边咬进舷墙拐角, 箱环闭合。",
    ["hull_w1", "hull_w2", "hull_e1", "hull_e2"],
    highlight=["hull_s_1", "hull_s_6"],
    tip="四角竖边互咬 —— 船体箱环从此滴水不进。",
)
b.step(
    "铺主甲板: 六片纵向长板短边搭南北墙顶, 长边互吸。",
    [f"deck_{x0}" for x0 in range(1, 7)],
    highlight=["hull_s_1", "hull_n_1"],
    tip="双边支承零悬挑 —— 甲板铺完, 船就有了第一层楼面。",
)
b.step(
    "拼尖船艏挂救生圈: 两片直角三角平板互咬拼出尖尖的船头。",
    ["bow_s", "bow_n", "life_s", "life_n"],
    highlight=["hull_e1", "hull_e2"],
    tip="直角边各吸一段船头墙顶, 斜边合成箭头 —— 破浪前进!",
)
b.step(
    "立客舱层舷窗: 六片窗格方踩甲板短边, 南北各三片。",
    CABIN_WIN,
    highlight=["deck_2"],
    tip="每一扇舷窗后面都是一间海景房。",
)
b.step(
    "装客舱端墙: 两条横楣立板整边吸甲板纵缝, 客舱层合环。",
    ["cabin_w", "cabin_e"],
    highlight=["cabin_s_2", "cabin_s_4"],
    tip="横楣一片顶两格 —— 东端这面墙待会儿还是舰桥的西墙。",
)
b.step(
    "铺阳光甲板并竖烟囱: 三片纵向长板退一级压顶, 中间是泳池。",
    ["sun_w", "sun_pool", "sun_e", "funnel"],
    highlight=["cabin_w", "cabin_e"],
    tip="红烟囱骑在西端墙顶整边吸合 —— 游轮的经典剪影来了。",
)
b.step(
    "立舰桥: 南北前窗踩甲板短边, 东横楣合环 (西墙与客舱共用)。",
    ["bridge_s", "bridge_n", "bridge_e"],
    highlight=["cabin_e"],
    tip="共墙技法: 一面墙同时属于客舱层与舰桥, 省片又结实。",
)
b.step(
    "盖舰桥顶点信号灯: 长板四边全支承, 黄色信号灯立在顶前沿。",
    ["bridge_roof", "mast_light"],
    highlight=["bridge_s", "bridge_e"],
    tip="信号灯亮起 —— 呜 —— 阳光号鸣笛启航!",
)

b.finalize(
    model_id="cruise_ship_01",
    name="阳光号游轮",
    name_en="Sunshine Cruise Ship 01",
    description=(
        "只用核心九片型的客运游轮: 船体箱环墙脚踩海面拼缝四角互咬, "
        "主甲板 -> 舷窗客舱层 -> 阳光甲板逐级退台 (中间一片青色泳池), "
        "舰桥与客舱层共用一面横楣端墙 (共墙技法), 船尾红色长板烟囱"
        "骑墙横立; 招牌是船头两片直角三角平板 —— 直角边各自整边吸"
        "船头墙顶、另一条直角边互咬, 拼出全库唯一的尖船艏; 舷门居中"
        "两侧舷窗排开, 橙色救生圈挂在船尾甲板沿 —— 呜 —— 阳光号"
        "鸣笛启航, 下一站阳光海岸!"
    ),
    difficulty=3,
    tags=["海洋", "游轮", "航行", "度假", "载具"],
    min_pieces=67,
    min_steps=14,
)
