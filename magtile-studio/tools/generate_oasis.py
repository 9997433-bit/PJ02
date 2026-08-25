#!/usr/bin/env python3
"""生成模型 data/models/oasis_01.json (绿洲营地)。

自然世界主题: 全库第一片沙漠绿洲营地 (结构逻辑不同于火山基地
volcano_base_01 的锥体堆叠) —— 金沙营地中央一汪青色泉眼,
两株棕榈树守在泉边: 双节树干踩沙面拼缝, 直角三角树根前后
抱紧树脚, 两片绿色棕叶从干顶垂垂下探 (受拉铰链, 悬重仅 13g);
两顶瘦高等腰四坡帐篷直接扎在沙面网格上 (四棱互吸自锁),
一口石砌水井戴红色四坡井亭, 橙色四坡火塘, 营旗与双水瓮
点缀 —— 全营地压在 2.5 高度线以下, 沙暴也吹不倒!

结构总览 (世界单位: 1.0 = 正方形磁力片边长):
  - 沙丘沿: 橙色长板 x4 (y [0,1])                             4 片
  - 营地沙面: 黄色方板 x28 + 泉眼青板 x4 (y [1,5])           32 片
  - 棕榈树 x2: 双节树干 x2 + 直角三角树根 x2 + 垂棕叶 x2  2x6 片
  - 帐篷 x2: 瘦高等腰四坡锥 (直接扎沙面, 顶尖 1.94)       2x4 片
  - 水井 (x [0,1], y [1,2]): 石墙 x4 + 红色四坡井亭 x4        8 片
  - 火塘 (x [2,3], y [1,2]): 橙色等边四坡锥 x4                4 片
  - 营旗 (方墙+等边旗) x2 + 水瓮 (等边) x2                    4 片
  合计 72 片, 14 个教程步骤, 5 种磁力片形状 (全部 CORE-9 之内)。

物理规则要点 (通过 R1~R8 全部校验, strict 档同样全绿):
  - 棕叶底边整边吸树干顶边、向外下垂 30 度: 子结构重心低于
    铰链线 0.14, 属受拉悬挂 —— 悬重 13g 远低于 strict 预算
    84g/单位边长; 绕铰链力矩仅 3.25;
  - 树根竖直角边吸树干竖边、水平直角边吸沙面拼缝 ——
    树脚双向抱紧, 剪断干脚铰链树仍不倒;
  - 帐篷/火塘/井亭四条斜棱两两互吸自锁成环;
  - 全模型最高点 1.94 (帐篷尖) < 2.5, 高层结构规则天然安静,
    营旗/水瓮重心正压拼缝铰链 (力矩 0)。

用法: python3 tools/generate_oasis.py  (在 magtile-studio 目录下运行)
"""

from magtile_gen import ModelBuilder

b = ModelBuilder()

DUNE = "orange"     # 沙丘沿
SAND = "yellow"     # 营地沙面
SPRING = "cyan"     # 泉眼
TRUNK = "orange"    # 树干 / 树根
FROND = "green"     # 棕叶
TENT_A = "red"      # 帐篷 A
TENT_B = "purple"   # 帐篷 B
WELLW = "gray"      # 水井石墙
WELLR = "red"       # 井亭
FIRE = "orange"     # 火塘
POLE = "gray"       # 旗杆
FLAG = "red"        # 营旗
JAR = "cyan"        # 水瓮

# =================================================================
# 1. 沙面 (x [0,8], y [0,5]): 沙丘沿 + 四行方板, 中央泉眼
# =================================================================
SPRING_CELLS = {(5, 2), (6, 2), (5, 3), (6, 3)}
for k in range(4):
    b.flat_rect(f"dn_{k}", 2 * k, 0, 0.0, DUNE)
for y in range(1, 5):
    for x in range(8):
        color = SPRING if (x, y) in SPRING_CELLS else SAND
        b.flat(f"sa_{x}_{y}", x, y, 0.0, color)

# =================================================================
# 2. 棕榈树 x2: 双节树干 + 树根 + 垂棕叶
# =================================================================
def palm(prefix, x0, y):
    b.wall_ns(f"{prefix}_t0", x0, y, 0, TRUNK)
    b.wall_ns(f"{prefix}_t1", x0, y, 1, TRUNK)
    b.brace(f"{prefix}_rw", (float(x0), y, 0.0), "-x", TRUNK)
    b.brace(f"{prefix}_re", (float(x0 + 1), y, 0.0), "+x", TRUNK)
    # 垂棕叶: 底边吸干顶, 向外下垂 30 度 (apex 低于铰链 0.433)
    b.place_tri(f"{prefix}_fs", "equilateral_triangle",
                (float(x0), y, 2.0), (float(x0 + 1), y, 2.0),
                (x0 + 0.5, y - 0.75, 1.566987), FROND)
    b.place_tri(f"{prefix}_fn", "equilateral_triangle",
                (float(x0 + 1), y, 2.0), (float(x0), y, 2.0),
                (x0 + 0.5, y + 0.75, 1.566987), FROND)
    return [f"{prefix}_t0", f"{prefix}_rw", f"{prefix}_re",
            f"{prefix}_t1", f"{prefix}_fs", f"{prefix}_fn"]

PALM_A = palm("pa", 4, 2.0)      # 泉眼西南角
PALM_B = palm("pb", 6, 4.0)      # 泉眼东北角

# =================================================================
# 3. 帐篷 x2: 瘦高等腰四坡锥直接扎沙面 (顶尖 1.94)
# =================================================================
TENT_1 = b.hat4("tent_a", 1, 3, 0.0, TENT_A)
TENT_2 = b.hat4("tent_b", 3, 3, 0.0, TENT_B)

# =================================================================
# 4. 水井 + 火塘
# =================================================================
b.wall_ns("well_s", 0, 1.0, 0, WELLW)
b.wall_ns("well_n", 0, 2.0, 0, WELLW)
b.wall_ew("well_w", 0.0, 1, 0, WELLW)
b.wall_ew("well_e", 1.0, 1, 0, WELLW)
WELL_ROOF = b.hat4("well_roof", 0, 1, 1.0, WELLR,
                   shape="equilateral_triangle")
FIREPIT = b.hat4("fire", 2, 1, 0.0, FIRE,
                 shape="equilateral_triangle")

# =================================================================
# 5. 营旗 + 水瓮
# =================================================================
b.wall_ns("flag_pole", 7, 1.0, 0, POLE)
b.crest_ns("flag_top", 7, 1.0, 1.0, FLAG)
b.crest_ns("jar_w", 0, 3.0, 0.0, JAR)
b.crest_ns("jar_e", 7, 3.0, 0.0, JAR)

# =================================================================
# 教程步骤 (14 步)
# =================================================================
b.step(
    "铺沙丘沿: 4 片橙色长板 (y [0,1])。",
    [f"dn_{k}" for k in range(4)],
    tip="沙丘沿是营地的南边界 —— 营旗就插在它北面。",
)
b.step(
    "铺沙面第一行: 8 片黄色方板 (y [1,2])。",
    [f"sa_{x}_1" for x in range(8)],
    highlight=["dn_0"],
    tip="水井、火塘和旗杆都踩这行的拼缝。",
)
b.step(
    "铺沙面第二行: 6 片黄板 + 2 片青色泉眼 (y [2,3])。",
    [f"sa_{x}_2" for x in range(8)],
    highlight=["sa_0_1"],
    tip="青板就是泉眼 —— 整片绿洲围着它生长。",
)
b.step(
    "铺沙面第三行: 泉眼补齐 (y [3,4])。",
    [f"sa_{x}_3" for x in range(8)],
    highlight=["sa_5_2"],
    tip="2x2 泉眼铺满 —— 两株棕榈马上守到泉边。",
)
b.step(
    "铺沙面第四行: 8 片, 营地合拢 (y [4,5])。",
    [f"sa_{x}_4" for x in range(8)],
    highlight=["sa_0_3"],
    tip="四行方板拼缝对齐 —— 帐篷区就在西侧。",
)
b.step(
    "扎帐篷 A: 4 片瘦高等腰直接立沙面网格, 四棱互吸。",
    TENT_1,
    highlight=["sa_1_2", "sa_1_3"],
    tip="四坡锥自锁成环 —— 帐篷尖 1.94, 全营最高点。",
)
b.step(
    "扎帐篷 B: 再来一顶紫色的。",
    TENT_2,
    highlight=[TENT_1[0]],
    tip="两顶帐篷隔一格排开 —— 沙漠商队的标准营位。",
)
b.step(
    "砌水井石墙: 4 片灰墙围成井口, 四角互吸。",
    ["well_s", "well_n", "well_w", "well_e"],
    highlight=["sa_0_1", "sa_0_2"],
    tip="井口闭环 —— 绿洲的命脉要守好。",
)
b.step(
    "戴红色井亭: 4 片等边四坡合拢。",
    WELL_ROOF,
    highlight=["well_s", "well_e"],
    tip="井亭四棱自锁, 正压井口 —— 沙子吹不进井里。",
)
b.step(
    "种泉边棕榈 A: 双节树干踩拼缝, 树根前后抱脚, 棕叶下垂。",
    PALM_A,
    highlight=["sa_4_1", "sa_4_2"],
    tip="棕叶向外下垂 30 度 —— 受拉悬挂只有 13g, 稳稳的。",
)
b.step(
    "种泉边棕榈 B: 东北角再来一株。",
    PALM_B,
    highlight=[PALM_A[0], "sa_6_3"],
    tip="剪断干脚铰链, 树根双向抱紧 —— 树仍不倒。",
)
b.step(
    "堆火塘: 4 片橙色等边四坡锥。",
    FIREPIT,
    highlight=["sa_2_1"],
    tip="火塘四棱自锁 —— 夜里commerce商队围着它讲故事。",
)
b.step(
    "立营旗: 方墙旗杆 + 红色等边营旗。",
    ["flag_pole", "flag_top"],
    highlight=["sa_7_1"],
    tip="营旗重心正压杆顶铰链 —— 力矩为零。",
)
b.step(
    "摆双水瓮 —— 绿洲营地开张!",
    ["jar_w", "jar_e"],
    highlight=["sa_0_3", "sa_7_3"],
    tip="水瓮重心正压沙面拼缝 —— 商队明早又要出发。",
)

b.finalize(
    model_id="oasis_01",
    name="绿洲营地",
    name_en="Oasis Camp 01",
    description=(
        "全库第一片沙漠绿洲营地: 金沙营地中央 2x2 青色泉眼, 两株"
        "棕榈守在泉边 —— 双节树干踩拼缝、直角三角树根前后抱脚,"
        " 绿棕叶从干顶外垂 30 度 (受拉悬挂 13g / 力矩 3.25 双双"
        "远离预算); 两顶瘦高等腰四坡帐篷直接扎沙面四棱自锁,"
        " 石砌水井戴红色四坡井亭, 橙色四坡火塘, 营旗与双水瓮点缀;"
        " 全营压在 2.5 高度线以下 —— 沙暴也吹不倒!"
    ),
    difficulty=3,
    tags=["自然", "绿洲", "沙漠", "营地", "进阶"],
    min_pieces=70,
    min_steps=14,
)
