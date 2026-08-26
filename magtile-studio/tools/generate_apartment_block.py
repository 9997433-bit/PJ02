#!/usr/bin/env python3
"""生成模型 data/models/apartment_block_01.json (居民楼).

城市生活主题: 全库第一组"住宅小区" —— 高低错落的两栋居民楼
围出一方院子: 西楼三层橙墙、东楼两层黄墙, 层层窗格方住户窗,
一层各嵌一扇门框方单元门; 西楼南立面挑出三方绿色阳台 (二层
一对 + 三层一方), 东楼屋顶是种着两丛绿植的露台; 院子里红色
滑梯从横墙顶滑下, 绿色四坡小树与黄色路灯把生活气息补满 ——
放学了, 院子里玩一会儿再回家!

结构总览 (世界单位: 1.0 = 正方形磁力片边长, 单元门朝南):
  - 院子一排 + 楼基两排地坪                               27 片
  - 西楼三层 (每层 8 墙) + 楼板 x8 + 屋面 x4              36 片
  - 西楼阳台: 二层绿色方板 x2 + 三层 x1                    3 片
  - 东楼两层 (每层 8 墙) + 楼板 x4 + 露台 x4              24 片
  - 露台绿植三角 x2                                        2 片
  - 滑梯 (横墙 + 30 度坡道) + 四坡小树 + 路灯              7 片
  合计 99 片, 18 个教程步骤, 7 种磁力片形状。

物理规则要点 (通过 R1~R8 全部校验, 常规+strict 双档):
  - 两楼逐层箱形围合 (四面墙竖边互吸成环 + 楼板四边压墙顶),
    上下层墙单位边对吸, 荷载沿墙身直落地面;
  - 阳台方板铰在墙顶单位边上外挑: 单方弯矩 15、双方并挑
    合计 30, 均低于对应铰链预算 (strict 17.5 / 35);
  - 滑梯坡道顶边整边吸横墙顶, 坡尾落地 —— 双端受力;
  - 四坡小树四棱两两互吸自锁, 底边整边吸院子方砖格边。

用法: python3 tools/generate_apartment_block.py  (在 magtile-studio 目录下运行)
"""

from magtile_gen import ModelBuilder

b = ModelBuilder()

YARD = "green"      # 院子草坪
BASE = "gray"       # 楼基地坪
WALL_A = "orange"   # 西楼墙身
WALL_B = "yellow"   # 东楼墙身
WIN = "clear"       # 窗格方
BALCONY = "green"   # 阳台
ROOF = "gray"       # 屋面

# =================================================================
# 1. 地坪: 院子 [0,9]x[0,1] 全方砖 + 楼基两排 [0,9]x[1,3]
# =================================================================
for x in range(9):
    b.flat(f"yd_{x}", x, 0, 0.0, YARD)
for x in range(9):
    b.flat(f"g1_{x}", x, 1, 0.0, BASE)
for x in range(9):
    b.flat(f"g2_{x}", x, 2, 0.0, BASE)


def tower_floor(prefix, x0, z, wall_color, south_tiles):
    """2x2 楼层: south_tiles 给出南面两格的 (类型, 颜色);
    北墙 2 方 + 东西山墙各 2 方, 四面竖边互吸成环。"""
    for i, (ttype, color) in enumerate(south_tiles):
        b.add(f"{prefix}_s{i}", ttype,
              (x0 + 0.5 + i, 1.0, z + 0.5), (90, 0, 0), color)
    for i in range(2):
        b.add(f"{prefix}_n{i}", "window_square",
              (x0 + 0.5 + i, 3.0, z + 0.5), (90, 0, 0), WIN)
    b.wall_ew(f"{prefix}_w0", float(x0), 1, z, wall_color)
    b.wall_ew(f"{prefix}_w1", float(x0), 2, z, wall_color)
    b.wall_ew(f"{prefix}_e0", float(x0 + 2), 1, z, wall_color)
    b.wall_ew(f"{prefix}_e1", float(x0 + 2), 2, z, wall_color)


def tower_deck(prefix, x0, z, color):
    for i, (dx, dy) in enumerate(((0, 1), (1, 1), (0, 2), (1, 2))):
        b.flat(f"{prefix}_{i}", x0 + dx, dy, float(z), color)


# =================================================================
# 2. 西楼 [1,3]x[1,3]: 三层橙墙 + 三方绿色阳台
# =================================================================
tower_floor("a1", 1, 0, WALL_A,
            [("door_frame", WALL_A), ("window_square", WIN)])
tower_deck("ad1", 1, 1, WALL_A)
tower_floor("a2", 1, 1, WALL_A,
            [("window_square", WIN), ("window_square", WIN)])
b.flat("bal_a2_0", 1, 0, 2.0, BALCONY)             # 二层阳台一对
b.flat("bal_a2_1", 2, 0, 2.0, BALCONY)
tower_deck("ad2", 1, 2, WALL_A)
tower_floor("a3", 1, 2, WALL_A,
            [("window_square", WIN), ("window_square", WIN)])
b.flat("bal_a3", 1, 0, 3.0, BALCONY)               # 三层阳台一方
tower_deck("ar", 1, 3, ROOF)                       # 西楼屋面

# =================================================================
# 3. 东楼 [5,7]x[1,3]: 两层黄墙 + 屋顶露台
# =================================================================
tower_floor("b1", 5, 0, WALL_B,
            [("door_frame", WALL_B), ("window_square", WIN)])
tower_deck("bd1", 5, 1, WALL_B)
tower_floor("b2", 5, 1, WALL_B,
            [("window_square", WIN), ("window_square", WIN)])
tower_deck("br", 5, 2, "clear")                    # 露台地板
b.crest_ns("plant_a", 5, 2.0, 2.0, "green")        # 露台绿植
b.crest_ew("plant_b", 6.0, 1, 2.0, "green")

# =================================================================
# 4. 院子: 滑梯 + 四坡小树 + 路灯
# =================================================================
b.wall_ew("sl_wall", 4.0, 0, 0, "red")             # 滑梯背墙
b.ramp("slide", "+x", 4, 0, 1.0, "clear")          # 30 度滑道, 坡尾落地
TREE_IDS = b.hat4("tree", 7, 0, 0.0, "green",
                  shape="equilateral_triangle")    # 四坡小树
b.spire_ns("lamp", 0, 1.0, 0.0, "yellow")          # 院口路灯

# =================================================================
# 教程步骤 (18 步)
# =================================================================
b.step(
    "院子: 9 片绿色草坪方砖铺出小区院子 —— 滑梯和小树都要立在"
    "这排格边上。",
    [f"yd_{x}" for x in range(9)],
)
b.step(
    "楼基南排: 9 片灰色方板, 两栋楼的南墙都立在它的格边上。",
    [f"g1_{x}" for x in range(9)],
    highlight=["yd_0", "yd_8"],
)
b.step(
    "楼基北排: 再铺 9 片, 地坪合拢。",
    [f"g2_{x}" for x in range(9)],
    highlight=["g1_0", "g1_8"],
)
b.step(
    "西楼一层: 南面 门框方单元门+窗格方, 北面 2 窗, 东西山墙"
    "各 2 方 —— 四面竖边互吸, 箱形围合。",
    ["a1_s0", "a1_s1", "a1_n0", "a1_n1", "a1_w0", "a1_w1", "a1_e0", "a1_e1"],
    highlight=["g1_1", "g2_2"],
    tip="先立南北墙再合山墙, 每片都吸得住相邻墙的竖边。",
)
b.step(
    "西楼二层楼板: 4 片方板压一层墙顶。",
    ["ad1_0", "ad1_1", "ad1_2", "ad1_3"],
    highlight=["a1_s0", "a1_n1"],
)
b.step(
    "西楼二层: 南面换成两扇窗格方住户窗, 其余同一层。",
    ["a2_s0", "a2_s1", "a2_n0", "a2_n1", "a2_w0", "a2_w1", "a2_e0", "a2_e1"],
    highlight=["ad1_0", "a1_s0"],
)
b.step(
    "二层阳台: 一对绿色方板从南墙顶单位边向院子外挑。",
    ["bal_a2_0", "bal_a2_1"],
    highlight=["a2_s0", "a2_s1"],
    tip="两方并挑合计弯矩 30 < 双单位铰链预算 35 —— 晾衣服稳稳的。",
)
b.step(
    "西楼三层楼板: 再压 4 片方板。",
    ["ad2_0", "ad2_1", "ad2_2", "ad2_3"],
    highlight=["a2_s0", "a2_n1"],
)
b.step(
    "西楼三层: 整圈窗格方 + 山墙, 第三层箱形围合。",
    ["a3_s0", "a3_s1", "a3_n0", "a3_n1", "a3_w0", "a3_w1", "a3_e0", "a3_e1"],
    highlight=["ad2_0", "a2_s0"],
)
b.step(
    "三层阳台: 顶层住户也有一方绿色小阳台。",
    ["bal_a3"],
    highlight=["a3_s0"],
)
b.step(
    "西楼屋面: 4 片灰色方板封顶 —— 三层小高楼完工。",
    ["ar_0", "ar_1", "ar_2", "ar_3"],
    highlight=["a3_s1", "a3_n0"],
)
b.step(
    "东楼一层: 门框方单元门 + 窗格方, 北窗与山墙围合。",
    ["b1_s0", "b1_s1", "b1_n0", "b1_n1", "b1_w0", "b1_w1", "b1_e0", "b1_e1"],
    highlight=["g1_5", "g2_6"],
)
b.step(
    "东楼二层楼板: 4 片方板压墙顶。",
    ["bd1_0", "bd1_1", "bd1_2", "bd1_3"],
    highlight=["b1_s0", "b1_n1"],
)
b.step(
    "东楼二层: 整圈窗格方 + 山墙围合。",
    ["b2_s0", "b2_s1", "b2_n0", "b2_n1", "b2_w0", "b2_w1", "b2_e0", "b2_e1"],
    highlight=["bd1_0", "b1_s0"],
)
b.step(
    "屋顶露台: 4 片透明地板封顶, 拼缝上立两丛绿植三角 —— "
    "东楼住户的空中小花园。",
    ["br_0", "br_1", "br_2", "br_3", "plant_a", "plant_b"],
    highlight=["b2_s1", "b2_n0"],
)
b.step(
    "院里滑梯: 红色横墙立在院子格缝上, 透明滑道顶边整边吸墙顶、"
    "坡尾落地 —— 双端受力。",
    ["sl_wall", "slide"],
    highlight=["yd_3", "yd_4"],
)
b.step(
    "四坡小树: 4 片绿色等边三角在院子东头四棱互吸, 合拢成一棵"
    "小树。",
    TREE_IDS,
    highlight=["yd_7"],
    tip="四坡自锁 —— 和帐篷一个原理。",
)
b.step(
    "院口路灯: 黄色高杆灯立在西楼前 —— 天黑了也能玩!",
    ["lamp"],
    highlight=["yd_0", "g1_0"],
)

b.finalize(
    model_id="apartment_block_01",
    name="居民楼",
    name_en="Apartment Block 01",
    description=(
        "全库第一组住宅小区: 高低错落的两栋居民楼 —— 西楼三层橙墙、"
        "东楼两层黄墙, 逐层箱形围合、上下墙单位边对吸; 层层窗格方"
        "住户窗, 一层各嵌一扇门框方单元门; 西楼南立面挑出三方绿色"
        "阳台 (单方弯矩 15、双方并挑 30, 均在预算内), 东楼屋顶是"
        "种着绿植的露台; 院子里红色滑梯双端受力、绿色四坡小树自锁"
        "合拢、黄色路灯守在院口 —— 放学了, 院子里玩一会儿再回家!"
    ),
    difficulty=4,
    tags=["居民楼", "城市", "住宅", "生活场景", "阳台"],
    min_pieces=95,
    min_steps=18,
)
