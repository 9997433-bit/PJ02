#!/usr/bin/env python3
"""生成模型 data/models/treehouse_02.json (双树树上小屋).

自然居所主题: 与 treehouse_01 (单树 2x2 空心树干 + 梯形四坡顶)
完全不同的第二座树屋 —— 草地上两棵树各驮一方 3x3 空中平台:
每棵树是 1x1 实心树干塔 + 四面各一道两层高跷墙, 树干顶中枢
方板 + 四道高跷顶边同时咬住平台 (五点受力); 西树平台上一座
人字形 A 字小屋 (两片 60 度方板屋面在屋脊互吸自锁 + 两片等边
三角山墙), 东树是瞭望台; 两平台之间一条独木桥长板双端简支,
东树下挂半高小平台再接 30 度滑梯落地 —— 上桥, 过树, 滑下来!

结构总览 (世界单位: 1.0 = 正方形磁力片边长):
  - 草地 10x5 (长板为主, 树干行与高跷脚位用方砖)          31 片
  - 西树: 树干塔 x8 + 高跷墙 x8 + 3x3 平台 x9             25 片
  - A 字小屋: 60 度屋面 x2 + 等边山墙 x2                   4 片
  - 西树护栏三角 x4 + 树冠四坡 x4                          8 片
  - 东树: 树干塔 x8 + 高跷墙 x8 + 3x3 平台 x9             25 片
  - 独木桥长板 x1 + 半高小平台 x1 + 滑梯坡道 x1            3 片
  - 东树护栏三角 x3                                        3 片
  合计 99 片, 18 个教程步骤, 4 种磁力片形状 (纯核心五片型 +
  长方形, 不需要任何扩展片)。

物理规则要点 (通过 R1~R8 全部校验, 常规+strict 双档):
  - 平台五点受力: 中心方板四边吸树干顶, 四道高跷顶边各咬住
    一条平台外缘中点边 —— 任何一条铰链剪断, 平台仍有四条
    支撑路径 (无单点失效);
  - A 字屋面两片 60 度方板在屋脊整边互吸自锁 (放第一片时
    弯矩仅 7.5), 山墙两条斜边与屋面侧边两两互吸成环;
  - 独木桥长板两端短边分别整边吸两侧平台边 —— 双端简支;
  - 滑梯顶边整边吸半高平台东边, 坡尾落地, 双端受力;
    半高平台北边吸树干墙顶、东边吸滑梯 —— 三向受力。

用法: python3 tools/generate_treehouse_two_trees.py  (在 magtile-studio 目录下运行)
"""

from magtile_gen import ModelBuilder

b = ModelBuilder()

GRASS = "green"
DIRT = "orange"     # 树坑
TRUNK = "orange"    # 树干与高跷
DECK = "yellow"     # 平台木板
HUT = "red"         # 小屋屋面
GABLE = "clear"     # 山墙
RAIL = "green"      # 护栏 (树叶)
CANOPY = "green"    # 树冠

# =================================================================
# 1. 草地 [0,10]x[0,5]: 树干行 (y2~3) 与高跷脚位用方砖
# =================================================================
b.flat_rect("g0_a", 0, 0, 0.0, GRASS)
b.flat("g0_b", 2, 0, 0.0, GRASS)
b.flat_rect("g0_c", 3, 0, 0.0, GRASS)
b.flat_rect("g0_d", 5, 0, 0.0, GRASS)
b.flat("g0_e", 7, 0, 0.0, GRASS)
b.flat_rect("g0_f", 8, 0, 0.0, GRASS)
for i, x0 in enumerate((0, 2, 4, 6, 8)):
    b.flat_rect(f"g1_{i}", x0, 1, 0.0, GRASS)
b.flat("g2_a", 0, 2, 0.0, GRASS)
b.flat("g2_b", 1, 2, 0.0, GRASS)
b.flat("g2_c", 2, 2, 0.0, DIRT)                    # 西树坑
b.flat("g2_d", 3, 2, 0.0, GRASS)
b.flat_rect("g2_e", 4, 2, 0.0, GRASS)
b.flat("g2_f", 6, 2, 0.0, GRASS)
b.flat("g2_g", 7, 2, 0.0, DIRT)                    # 东树坑
b.flat("g2_h", 8, 2, 0.0, GRASS)
b.flat("g2_i", 9, 2, 0.0, GRASS)
for i, x0 in enumerate((0, 2, 4, 6, 8)):
    b.flat_rect(f"g3_{i}", x0, 3, 0.0, GRASS)
b.flat_rect("g4_a", 0, 4, 0.0, GRASS)
b.flat("g4_b", 2, 4, 0.0, GRASS)
b.flat_rect("g4_c", 3, 4, 0.0, GRASS)
b.flat_rect("g4_d", 5, 4, 0.0, GRASS)
b.flat("g4_e", 7, 4, 0.0, GRASS)
b.flat_rect("g4_f", 8, 4, 0.0, GRASS)


def tree(prefix, tx):
    """1x1 树干塔 (两层四面) + 四道两层高跷墙 + 3x3 平台。
    tx = 树干格西南角 x (树干格为 [tx,tx+1]x[2,3])。"""
    for lv in (0, 1):
        b.wall_ns(f"{prefix}_tk{lv}_s", tx, 2.0, lv, TRUNK)
        b.wall_ns(f"{prefix}_tk{lv}_n", tx, 3.0, lv, TRUNK)
        b.wall_ew(f"{prefix}_tk{lv}_w", float(tx), 2, lv, TRUNK)
        b.wall_ew(f"{prefix}_tk{lv}_e", float(tx + 1), 2, lv, TRUNK)
    for lv in (0, 1):
        b.wall_ns(f"{prefix}_st{lv}_s", tx, 1.0, lv, TRUNK)
        b.wall_ns(f"{prefix}_st{lv}_n", tx, 4.0, lv, TRUNK)
        b.wall_ew(f"{prefix}_st{lv}_w", float(tx - 1), 2, lv, TRUNK)
        b.wall_ew(f"{prefix}_st{lv}_e", float(tx + 2), 2, lv, TRUNK)
    b.flat(f"{prefix}_p_c", tx, 2, 2.0, DECK)      # 中枢: 四边吸树干顶
    ring = ((tx - 1, 2), (tx + 1, 2), (tx, 1), (tx, 3),
            (tx - 1, 1), (tx + 1, 1), (tx - 1, 3), (tx + 1, 3))
    for i, (px, py) in enumerate(ring):
        b.flat(f"{prefix}_p_{i}", px, py, 2.0, DECK)


tree("w", 2)                                        # 西树 (树干格 [2,3]x[2,3])
tree("e", 7)                                        # 东树 (树干格 [7,8]x[2,3])

# =================================================================
# 2. A 字小屋 (西树平台西南格 [1,2]x[1,2]): 60 度屋面 + 山墙
# =================================================================
b.place_edge("hut_s", "square", 0,
             (1.0, 1.0, 2.0), (2.0, 1.0, 2.0), (0.0, 0.5, 0.866025), HUT)
b.place_edge("hut_n", "square", 0,
             (2.0, 2.0, 2.0), (1.0, 2.0, 2.0), (0.0, -0.5, 0.866025), HUT)
b.place_tri("hut_gw", "equilateral_triangle",
            (1.0, 2.0, 2.0), (1.0, 1.0, 2.0), (1.0, 1.5, 2.866025), GABLE)
b.place_tri("hut_ge", "equilateral_triangle",
            (2.0, 1.0, 2.0), (2.0, 2.0, 2.0), (2.0, 1.5, 2.866025), GABLE)

# =================================================================
# 3. 西树护栏 + 树冠
# =================================================================
b.crest_ns("w_rail_n", 1, 4.0, 2.0, RAIL)
b.crest_ew("w_rail_w", 1.0, 3, 2.0, RAIL)
b.crest_ns("w_rail_s", 3, 1.0, 2.0, RAIL)
b.crest_ew("w_rail_e", 4.0, 1, 2.0, RAIL)
CANOPY_IDS = b.hat4("w_canopy", 3, 3, 2.0, CANOPY,
                    shape="equilateral_triangle")

# =================================================================
# 4. 独木桥 + 半高小平台 + 滑梯 + 东树护栏
# =================================================================
b.flat_rect("bridge", 4, 2, 2.0, DECK)             # [4,6]x[2,3] 双端简支
b.flat("landing", 7, 1, 1.0, DECK)                 # 半高平台 (北吸树干墙顶)
b.ramp("slide", "+x", 8.0, 1, 1.0, "clear")        # 顶边吸半高平台, 坡尾落地
b.crest_ns("e_rail_n", 8, 4.0, 2.0, RAIL)
b.crest_ns("e_rail_s", 6, 1.0, 2.0, RAIL)
b.crest_ew("e_rail_e", 9.0, 3, 2.0, RAIL)

# =================================================================
# 教程步骤 (18 步)
# =================================================================
b.step(
    "草地南缘: 长板与方砖沿 y=0~1 铺出第一排, 方砖格位正对"
    "两树的南高跷脚。",
    ["g0_a", "g0_b", "g0_c", "g0_d", "g0_e", "g0_f"],
    tip="x=2~3 与 7~8 的方砖北边, 就是高跷墙的落脚线。",
)
b.step(
    "草地第二排: 5 条长板铺满 y=1~2。",
    ["g1_0", "g1_1", "g1_2", "g1_3", "g1_4"],
    highlight=["g0_a", "g0_f"],
)
b.step(
    "树干行: y=2~3 整排方砖 —— 两格橙色树坑就是树干的家, "
    "两侧方砖格边给东西高跷落脚。",
    ["g2_a", "g2_b", "g2_c", "g2_d", "g2_e", "g2_f", "g2_g", "g2_h", "g2_i"],
    highlight=["g1_0", "g1_4"],
)
b.step(
    "草地北半: 两排铺齐, 10x5 草地合拢。",
    ["g3_0", "g3_1", "g3_2", "g3_3", "g3_4",
     "g4_a", "g4_b", "g4_c", "g4_d", "g4_e", "g4_f"],
    highlight=["g2_a", "g2_i"],
)
b.step(
    "西树干一层: 4 片橙色方墙绕树坑格边围成 1x1 实心树干塔。",
    ["w_tk0_s", "w_tk0_n", "w_tk0_w", "w_tk0_e"],
    highlight=["g2_c"],
    tip="四面墙竖边两两互吸 —— 树干是一根方筒。",
)
b.step(
    "西树干二层: 再围 4 片, 树干长到 z=2。",
    ["w_tk1_s", "w_tk1_n", "w_tk1_w", "w_tk1_e"],
    highlight=["w_tk0_s", "w_tk0_e"],
)
b.step(
    "西树高跷: 四个方向各立一道两层高跷墙 (先立下层再摞上层), "
    "它们要和树干一起托平台。",
    ["w_st0_s", "w_st0_n", "w_st0_w", "w_st0_e",
     "w_st1_s", "w_st1_n", "w_st1_w", "w_st1_e"],
    highlight=["g0_b", "g4_b"],
    tip="高跷脚踩的正是草地方砖的格边。",
)
b.step(
    "西树平台: 中枢方板四边吸树干顶, 8 片木板绕中枢拼成 3x3 "
    "平台 —— 四道高跷顶边各咬住一条外缘中点边, 五点受力。",
    ["w_p_c", "w_p_0", "w_p_1", "w_p_2", "w_p_3",
     "w_p_4", "w_p_5", "w_p_6", "w_p_7"],
    highlight=["w_tk1_s", "w_st1_s"],
    tip="剪断任何一条铰链, 平台仍有四条支撑路径。",
)
b.step(
    "A 字小屋: 两片红色屋面 60 度对立, 在屋脊整边互吸自锁; "
    "两片透明等边山墙封住东西端, 斜边与屋面互吸成环。",
    ["hut_s", "hut_n", "hut_gw", "hut_ge"],
    highlight=["w_p_4", "w_p_2"],
    tip="第一片屋面弯矩仅 7.5, 第二片一搭上就互锁。",
)
b.step(
    "西树护栏: 4 片绿色三角立在平台外缘 —— 既是栏杆也是树叶。",
    ["w_rail_n", "w_rail_w", "w_rail_s", "w_rail_e"],
    highlight=["w_p_6", "w_p_3"],
)
b.step(
    "西树冠: 平台东北角 4 片绿色等边三角四坡自锁, 合拢成一簇"
    "树冠。",
    CANOPY_IDS,
    highlight=["w_p_7"],
)
b.step(
    "东树干一层: 绕东树坑再围 4 片方墙。",
    ["e_tk0_s", "e_tk0_n", "e_tk0_w", "e_tk0_e"],
    highlight=["g2_g"],
)
b.step(
    "东树干二层: 树干塔长齐 z=2。",
    ["e_tk1_s", "e_tk1_n", "e_tk1_w", "e_tk1_e"],
    highlight=["e_tk0_s", "e_tk0_e"],
)
b.step(
    "东树高跷: 四道两层高跷墙就位。",
    ["e_st0_s", "e_st0_n", "e_st0_w", "e_st0_e",
     "e_st1_s", "e_st1_n", "e_st1_w", "e_st1_e"],
    highlight=["g0_e", "g4_e"],
)
b.step(
    "东树平台: 中枢 + 8 片木板, 第二方 3x3 平台合拢 —— 这是"
    "瞭望台。",
    ["e_p_c", "e_p_0", "e_p_1", "e_p_2", "e_p_3",
     "e_p_4", "e_p_5", "e_p_6", "e_p_7"],
    highlight=["e_tk1_s", "e_st1_e"],
)
b.step(
    "独木桥: 一条黄色长板横跨两平台之间, 两端短边整边吸平台边 "
    "—— 双端简支, 走上去稳稳的。",
    ["bridge"],
    highlight=["w_p_1", "e_p_0"],
)
b.step(
    "半高平台与滑梯: 东树南侧挂一方半高木板 (北边吸树干墙顶), "
    "透明滑梯顶边整边吸它的东边、坡尾落地。",
    ["landing", "slide"],
    highlight=["e_tk0_s", "g2_h"],
    tip="上桥、过树、滑下来 —— 这就是下山的路。",
)
b.step(
    "东树护栏: 3 片绿色三角围住瞭望台外缘 —— 双树树屋完工!",
    ["e_rail_n", "e_rail_s", "e_rail_e"],
    highlight=["e_p_6", "e_p_3"],
)

b.finalize(
    model_id="treehouse_02",
    name="双树树上小屋",
    name_en="Treehouse 02 (Twin Trees)",
    description=(
        "与单树树屋完全不同的第二座树屋: 草地上两棵 1x1 实心树干塔"
        "各配四道两层高跷墙, 3x3 空中平台五点受力 (中枢四边吸树干顶 "
        "+ 四道高跷各咬一条外缘中点边, 无单点失效); 西树平台上一座 "
        "A 字小屋 —— 两片 60 度屋面在屋脊整边互吸自锁、两片等边山墙"
        "锁环, 东树是绿叶护栏的瞭望台; 两平台间独木桥长板双端简支, "
        "东树下半高平台接 30 度滑梯落地 —— 上桥, 过树, 滑下来! "
        "全模型只用核心五片型, 拆开基础装就能搭。"
    ),
    difficulty=4,
    tags=["树屋", "自然", "田园", "A字屋", "双塔"],
    min_pieces=95,
    min_steps=18,
)
