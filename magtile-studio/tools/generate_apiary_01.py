#!/usr/bin/env python3
"""生成模型 data/models/apiary_01.json (蜜蜂养蜂场)。

田园主题新作, 全库第一座昆虫养殖场 —— 与鸡舍 (单层棚屋)、
羊圈 (围栏场) 的结构词汇完全错开: 本作的主角是两座"叠箱式"
蜂箱塔 —— 真实养蜂场的继箱蜂箱就是一层层叠上去的, 模型用
两层四墙合环的箱体逐层叠高, 底层门框方是蜜蜂的出入口 (巢门),
顶上等边四坡锥顶当箱盖; 花田里四色蜜源花沿拼缝排开, 青色
蜂蜜售卖牌立在场边 —— 全库唯一的"双塔叠箱 + 巢门朝南"剪影。

结构总览 (世界单位: 1.0 = 正方形磁力片边长, 巢门朝南):
  - 花田草地 (x [0,6], y [0,3]): 三行单位方板 x18            18 片
  - 蜂箱塔 x2 (1x1 足印, x [1,2] 与 [4,5], y [1,2]):
    底箱四墙 (含南面巢门门框) x4 + 继箱四墙 x4
    + 等边四坡箱盖 x4, 每塔 12 片                            24 片
  - 蜜源花 x4: 四色等边三角骑草地拼缝                          4 片
  - 蜂蜜售卖牌: 青色窗格方立在场边                             1 片
  合计 47 片, 10 个教程步骤, 4 种磁力片形状 (全部 CORE-9 之内)。

物理规则要点 (validate 常规 + strict 双档零警告):
  - 蜂箱塔是标准叠箱: 底箱四墙脚踩草地拼缝整边吸合、四角竖边
    互咬闭环; 继箱四墙底边整边压底箱墙顶, 竖直连续无侧向力矩;
  - 等边四坡箱盖直接骑继箱墙顶: 四条斜棱两两互吸自锁成环,
    底边各吸一道墙顶 (锥尖 2.71) —— 值班小屋同款自锁封顶;
  - 蜜源花/售卖牌底边整边吸草地拼缝, 各自独立吸附, 剪断任何
    一条装饰连接最多失联 1 片 (< 3), R8 单点失效通过;
  - 草地拼缝纪律: 全部草地为单位方板, 蜂箱墙脚线处处有等长
    拼缝可吸, 行行等边互吸全场连通。

用法: python3 tools/generate_apiary_01.py  (在 magtile-studio 目录下运行)
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from magtile_gen import ModelBuilder  # noqa: E402

b = ModelBuilder()

GRASS = "green"     # 花田草地
PATH = "yellow"     # 场内小径
BOX_A1 = "yellow"   # A 塔底箱
BOX_A2 = "orange"   # A 塔继箱
LID_A = "red"       # A 塔箱盖
BOX_B1 = "cyan"     # B 塔底箱
BOX_B2 = "blue"     # B 塔继箱
LID_B = "purple"    # B 塔箱盖
GATE_A = "orange"   # A 塔巢门
GATE_B = "blue"     # B 塔巢门
SIGN = "cyan"       # 蜂蜜售卖牌
FLOWERS = [("flower_pink", 0, "pink"), ("flower_red", 2, "red"),
           ("flower_purple", 3, "purple"), ("flower_orange", 5, "orange")]


def wall_ns_t(tid, tile_type, x0, y, z0, color):
    b.add(tid, tile_type, (x0 + 0.5, y, z0 + 0.5), (90, 0, 0), color)


# =================================================================
# 1. 花田草地三行 (y [0,3]): 全单位方板, 中行留出黄色小径
# =================================================================
for x0 in range(6):
    b.flat(f"grass_{x0}_0", x0, 0, 0.0, GRASS)        # 南行 (花行)
for x0 in range(6):
    color = PATH if x0 in (0, 3) else GRASS           # 小径通向两塔
    b.flat(f"grass_{x0}_1", x0, 1, 0.0, color)        # 蜂箱行
for x0 in range(6):
    b.flat(f"grass_{x0}_2", x0, 2, 0.0, GRASS)        # 北行

# =================================================================
# 2. 蜂箱塔 A (x [1,2], y [1,2]): 底箱 + 继箱 + 等边四坡箱盖
# =================================================================
wall_ns_t("boxa1_s", "door_frame", 1, 1.0, 0, GATE_A)  # 巢门朝南
b.wall_ns("boxa1_n", 1, 2.0, 0, BOX_A1)
b.wall_ew("boxa1_w", 1.0, 1, 0, BOX_A1)
b.wall_ew("boxa1_e", 2.0, 1, 0, BOX_A1)
b.wall_ns("boxa2_s", 1, 1.0, 1, BOX_A2)                # 继箱整层
b.wall_ns("boxa2_n", 1, 2.0, 1, BOX_A2)
b.wall_ew("boxa2_w", 1.0, 1, 1, BOX_A2)
b.wall_ew("boxa2_e", 2.0, 1, 1, BOX_A2)
LID_A_IDS = b.hat4("lida", 1, 1, 2.0, LID_A,
                   shape="equilateral_triangle")       # 锥尖 2.71

# =================================================================
# 3. 蜂箱塔 B (x [4,5], y [1,2]): 同构叠箱, 换青蓝配色
# =================================================================
wall_ns_t("boxb1_s", "door_frame", 4, 1.0, 0, GATE_B)  # 巢门朝南
b.wall_ns("boxb1_n", 4, 2.0, 0, BOX_B1)
b.wall_ew("boxb1_w", 4.0, 1, 0, BOX_B1)
b.wall_ew("boxb1_e", 5.0, 1, 0, BOX_B1)
b.wall_ns("boxb2_s", 4, 1.0, 1, BOX_B2)
b.wall_ns("boxb2_n", 4, 2.0, 1, BOX_B2)
b.wall_ew("boxb2_w", 4.0, 1, 1, BOX_B2)
b.wall_ew("boxb2_e", 5.0, 1, 1, BOX_B2)
LID_B_IDS = b.hat4("lidb", 4, 1, 2.0, LID_B,
                   shape="equilateral_triangle")

# =================================================================
# 4. 蜜源花 x4 (南行花田拼缝) + 蜂蜜售卖牌
# =================================================================
for tid, x0, color in FLOWERS:
    b.crest_ns(tid, x0, 1.0, 0.0, color)               # 骑 y=1 拼缝朝南
wall_ns_t("honey_sign", "window_square", 3, 3.0, 0, SIGN)  # 场边售卖牌

# =================================================================
# 教程步骤 (10 步)
# =================================================================
b.step(
    "铺南行花田: 六片绿色草地方板边边互吸连成一排。",
    [f"grass_{x0}_0" for x0 in range(6)],
    tip="蜜源花田在蜂箱南边 —— 蜜蜂出巢门就能上班采蜜。",
)
b.step(
    "铺蜂箱行: 两格黄色小径正对两座蜂箱的位置。",
    [f"grass_{x0}_1" for x0 in range(6)],
    highlight=["grass_0_0"],
    tip="行行等边互吸 —— 蜂箱墙脚要踩的拼缝就在这行上。",
)
b.step(
    "铺北行草地: 再来六片, 花田连成一整张网。",
    [f"grass_{x0}_2" for x0 in range(6)],
    highlight=["grass_0_1"],
    tip="草地是全场的地基, 每条拼缝都是磁力吸合线。",
)
b.step(
    "立 A 塔底箱: 四墙合环, 南面用门框方当巢门。",
    ["boxa1_s", "boxa1_n", "boxa1_w", "boxa1_e"],
    highlight=["grass_1_1"],
    tip="墙脚踩拼缝整边吸合, 四角竖边互咬 —— 巢门朝南晒太阳。",
)
b.step(
    "叠 A 塔继箱: 四片橙色墙整层压上底箱墙顶。",
    ["boxa2_s", "boxa2_n", "boxa2_w", "boxa2_e"],
    highlight=["boxa1_s"],
    tip="上环整边压下环 —— 蜂群壮大了, 养蜂人就再叠一层继箱。",
)
b.step(
    "盖 A 塔箱盖: 四片红色等边三角合成锥顶, 斜棱互咬自锁。",
    LID_A_IDS,
    highlight=["boxa2_s"],
    tip="锥尖 2.71 —— 四条斜棱两两吸住, 不用盖板照样封顶。",
)
b.step(
    "立 B 塔底箱: 蓝色巢门朝南, 四墙合环踩稳拼缝。",
    ["boxb1_s", "boxb1_n", "boxb1_w", "boxb1_e"],
    highlight=["grass_4_1"],
    tip="两座蜂箱隔两格排开 —— 蜂群各回各家不迷路。",
)
b.step(
    "叠 B 塔继箱: 四片蓝色墙整层压顶, 双塔一样高。",
    ["boxb2_s", "boxb2_n", "boxb2_w", "boxb2_e"],
    highlight=["boxb1_s"],
    tip="叠箱是养蜂场的招牌 —— 箱子越高, 蜂蜜越多。",
)
b.step(
    "盖 B 塔箱盖: 紫色锥顶合拢, 两座蜂箱塔完工。",
    LID_B_IDS,
    highlight=["boxb2_s"],
    tip="对角顺序放四片斜棱, 最后一片同时吸住两条棱。",
)
b.step(
    "种蜜源花并立售卖牌: 四色花朵骑上花田拼缝, 青色窗格方朝路。",
    [tid for tid, _, _ in FLOWERS] + ["honey_sign"],
    highlight=["grass_0_0", "grass_5_0"],
    tip="花底边整边吸拼缝 —— 开张啦, 新鲜蜂蜜等你来尝!",
)

b.finalize(
    model_id="apiary_01",
    name="蜜蜂养蜂场",
    name_en="Honeybee Apiary 01",
    description=(
        "只用核心九片型的昆虫养殖场景: 主角是两座叠箱式蜂箱塔 —— "
        "真实养蜂场的继箱蜂箱一层层叠高, 模型用两层四墙合环的箱体"
        "整层互压 (底层门框方是蜜蜂进出的巢门, 巢门一律朝南), 等边"
        "四坡箱盖四条斜棱两两互咬自锁封顶 (锥尖 2.71); 黄橙红与"
        "青蓝紫的双塔配色一暖一冷, 花田里粉红紫橙四色蜜源花骑拼缝"
        "排开, 青色蜂蜜售卖牌立在场边 —— 嗡嗡嗡, 采蜜小队出发!"
    ),
    difficulty=2,
    tags=["田园", "昆虫", "蜜蜂", "农场", "自然"],
    min_pieces=47,
    min_steps=10,
)
