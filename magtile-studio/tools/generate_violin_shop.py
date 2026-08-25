#!/usr/bin/env python3
"""生成模型 data/models/violin_shop_01.json (提琴工坊)。

音乐/乐器主题: 全库第一间提琴工坊 —— 结构主角是 "A 字屋脊
自锁 + 吊挂招牌 + 巨琴广告墙": 店面是一栋 4x1 木屋 (门框方
店门 + 三扇窗格方橱窗, 二层横楣长板双端竖边咬进侧墙纯剪锁定),
屋顶两坡各 4 片方片以 60 度对拼、脊线整边互吸自锁, 两端等边
三角山墙同时咬墙顶与两条坡棱 —— 檐-坡-脊-坡-檐处处成环;
店门口方形招牌自屋檐坡底边向外下垂 30 度 (受拉悬挂 30g /
力矩 7.5 双双远低于 strict 预算); 东侧广场立一面 3x2 巨型
提琴广告墙 (琴颈方柱 + 等边琴头), 四只直角三角斜撑前后对撑;
门前长凳简支桥 + 西侧等边四坡花坛。

结构总览 (世界单位: 1.0 = 正方形磁力片边长, 店面朝南):
  - 广场地面 (x [0,6], y [0,3]): 3 行 x 6                      18 片
  - 店面一层 (y=2, z 0..1): 窗-门-窗-窗                          4 片
  - 二层横楣: 前后各 2 条长板 (竖边咬侧墙)                       4 片
  - 侧墙 (x=1 / x=5): 各 2 层                                    4 片
  - 屋顶: 南北坡各 4 片 60 度方片 + 等边山墙 x2                 10 片
  - 吊挂招牌: 方片自屋檐外垂 30 度                               1 片
  - 巨琴广告墙: 琴身 3x2 x6 + 琴颈 x1 + 等边琴头 x1
    + 直角三角斜撑 x4                                           12 片
  - 门前长凳 (简支桥): 腿 x2 + 座面 x1                           3 片
  - 花坛: 等边四坡锥 x4                                          4 片
  合计 64 片, 13 个教程步骤, 6 种磁力片形状 (全部 CORE-9 之内)。

物理规则要点 (通过 R1~R8 全部校验, strict 档同样全绿):
  - A 字屋脊: 两坡 60 度对拼, 脊线上 4 对方片整边互吸,
    山墙底边咬墙顶、两腰咬坡棱 —— 檐-坡-脊闭合成环,
    剪断任何一条檐线铰链, 力都能从脊线绕行;
  - 吊挂招牌: 顶边吸屋檐坡底边, 悬重 30g << 84g (strict),
    外摆力矩 30 x 0.5 x sin30 = 7.5 << 17.5;
  - 巨琴广告墙 3x2 网格自身成环, 琴颈居中骑顶缝重心正压,
    四只斜撑同时咬地缝与琴身竖边 —— 无单点失效;
  - 横楣长板双端竖边与侧墙竖边整边互吸 (纯剪传力)。

用法: python3 tools/generate_violin_shop.py  (在 magtile-studio 目录下运行)
"""

import math

from magtile_gen import ModelBuilder

b = ModelBuilder()

PLAZA = "gray"      # 广场地面
PATH = "orange"     # 门前小径
WALL = "yellow"     # 店面木墙
GLASS = "clear"     # 窗格方橱窗
DOOR = "orange"     # 门框方店门
LINTEL = "yellow"   # 二层横楣
ROOF = "red"        # 屋顶
GABLE = "red"       # 山墙
SIGN = "green"      # 吊挂招牌
VIOLIN = "orange"   # 巨琴琴身
NECK = "gray"       # 琴颈
SCROLL = "yellow"   # 琴头
BRACE = "gray"      # 斜撑
BENCH = "orange"    # 门前长凳
PLANT = "green"     # 花坛

SIGN_SWING = 30.0   # 招牌外摆角 (自竖直)
SIN_S = round(math.sin(math.radians(SIGN_SWING)), 6)
COS_S = round(math.cos(math.radians(SIGN_SWING)), 6)
RIDGE_H = 2.0 + round(math.sin(math.radians(60)), 6)   # 2.866025
RIDGE_Y = 2.5
COS60 = 0.5

# =================================================================
# 1. 广场地面 (x [0,6], y [0,3]): 门前小径通向店门
# =================================================================
for y in range(3):
    for x in range(6):
        b.flat(f"pl_{x}_{y}", x, y, 0.0, PATH if x == 2 and y < 2 else PLAZA)

# =================================================================
# 2. 店面一层 (y=2, z 0..1): 窗-门-窗-窗 + 侧墙
# =================================================================
b.add("shop_win_w", "window_square", (1.5, 2.0, 0.5), (90, 0, 0), GLASS)
b.add("shop_door", "door_frame", (2.5, 2.0, 0.5), (90, 0, 0), DOOR)
b.add("shop_win_m", "window_square", (3.5, 2.0, 0.5), (90, 0, 0), GLASS)
b.add("shop_win_e", "window_square", (4.5, 2.0, 0.5), (90, 0, 0), GLASS)
for x in (1, 2, 3, 4):
    b.wall_ns(f"bk_lo_{x}", x, 3.0, 0, WALL)
b.wall_ew("sd_w_lo", 1.0, 2, 0, WALL)
b.wall_ew("sd_e_lo", 5.0, 2, 0, WALL)
b.wall_ew("sd_w_hi", 1.0, 2, 1, WALL)
b.wall_ew("sd_e_hi", 5.0, 2, 1, WALL)
b.lintel_ns("ln_f_w", 1, 2.0, 1, LINTEL)
b.lintel_ns("ln_f_e", 3, 2.0, 1, LINTEL)
b.lintel_ns("ln_b_w", 1, 3.0, 1, LINTEL)
b.lintel_ns("ln_b_e", 3, 3.0, 1, LINTEL)

# =================================================================
# 3. A 字屋顶: 两坡 60 度对拼 + 等边山墙
# =================================================================
b.place_tri("gable_w", "equilateral_triangle",
            (1.0, 2.0, 2.0), (1.0, 3.0, 2.0), (1.0, RIDGE_Y, RIDGE_H), GABLE)
for i, x in enumerate((1, 2, 3, 4)):
    b.place_edge(f"roof_s{i}", "square", 0,
                 (x + 0.0, 2.0, 2.0), (x + 1.0, 2.0, 2.0),
                 (0.0, COS60, 0.866025), ROOF)
for i, x in enumerate((1, 2, 3, 4)):
    b.place_edge(f"roof_n{i}", "square", 0,
                 (x + 1.0, 3.0, 2.0), (x + 0.0, 3.0, 2.0),
                 (0.0, -COS60, 0.866025), ROOF)
b.place_tri("gable_e", "equilateral_triangle",
            (5.0, 3.0, 2.0), (5.0, 2.0, 2.0), (5.0, RIDGE_Y, RIDGE_H), GABLE)

# =================================================================
# 4. 吊挂招牌: 自店门上方屋檐坡底边外垂 30 度
# =================================================================
b.place_edge("sign", "square", 0,
             (2.0, 2.0, 2.0), (3.0, 2.0, 2.0), (0.0, -SIN_S, -COS_S), SIGN)

# =================================================================
# 5. 巨琴广告墙 (y=1, x [3,6]): 3x2 琴身 + 琴颈 + 琴头 + 斜撑
# =================================================================
for x in (3, 4, 5):
    b.wall_ns(f"vb_lo_{x}", x, 1.0, 0, VIOLIN)
for x in (3, 4, 5):
    b.wall_ns(f"vb_hi_{x}", x, 1.0, 1, VIOLIN)
b.wall_ns("vneck", 4, 1.0, 2, NECK)
b.crest_ns("vscroll", 4, 1.0, 3.0, SCROLL)
b.brace("vbr_w_s", (3.0, 1.0, 0.0), "-y", BRACE)
b.brace("vbr_w_n", (3.0, 1.0, 0.0), "+y", BRACE)
b.brace("vbr_e_s", (6.0, 1.0, 0.0), "-y", BRACE)
b.brace("vbr_e_n", (6.0, 1.0, 0.0), "+y", BRACE)

# =================================================================
# 6. 门前长凳 (x [0,1], y [0,1]) + 西侧花坛 (x [0,1], y [2,3])
# =================================================================
b.wall_ew("bn_w", 0.0, 0, 0, BENCH)
b.wall_ew("bn_e", 1.0, 0, 0, BENCH)
b.flat("bn_seat", 0, 0, 1.0, BENCH)
PLANT_IDS = b.hat4("plant", 0, 2, 0.0, PLANT, shape="equilateral_triangle")

# =================================================================
# 教程步骤 (13 步)
# =================================================================
b.step(
    "铺广场前排 (y [0,1]): 6 片, 橙色小径对准店门。",
    [f"pl_{x}_0" for x in range(6)],
    tip="x=2 的小径尽头就是店门的位置 —— 从地面定下门脸。",
)
b.step(
    "铺广场中排 (y [1,2]): 6 片, 拼缝对齐。",
    [f"pl_{x}_1" for x in range(6)],
    highlight=["pl_2_0"],
    tip="y=1 的整条拼缝留给巨琴广告墙 —— 先记住它。",
)
b.step(
    "铺广场后排 (y [2,3]): 6 片, 店面地基合拢。",
    [f"pl_{x}_2" for x in range(6)],
    highlight=["pl_0_1"],
    tip="y=2 拼缝是店面前墙的墙脚, y=3 拼缝是后墙的墙脚。",
)
b.step(
    "立店面一层 (y=2): 窗-门-窗-窗, 门框方居中迎客。",
    ["shop_win_w", "shop_door", "shop_win_m", "shop_win_e"],
    highlight=["pl_2_1"],
    tip="三扇窗格方是琴行橱窗 —— 里面挂满提琴 (假装)。",
)
b.step(
    "砌后墙一层与两侧墙: 4 + 2 片, 四角竖边互吸。",
    ["bk_lo_1", "bk_lo_2", "bk_lo_3", "bk_lo_4", "sd_w_lo", "sd_e_lo"],
    highlight=["shop_door"],
    tip="前墙-侧墙-后墙锁成矩形环 —— 一层墙体处处成环。",
)
b.step(
    "加侧墙二层, 架 4 条横楣长板: 双端竖边咬进侧墙。",
    ["sd_w_hi", "sd_e_hi", "ln_f_w", "ln_f_e", "ln_b_w", "ln_b_e"],
    highlight=["sd_w_lo", "sd_e_lo"],
    tip="横楣端头与侧墙竖边整边互吸 —— 纯剪传力, 不靠悬挑。",
)
b.step(
    "立西山墙, 铺南坡: 等边山墙咬墙顶, 4 片方片 60 度上坡。",
    ["gable_w", "roof_s0", "roof_s1", "roof_s2", "roof_s3"],
    highlight=["sd_w_hi", "ln_f_w"],
    tip="每片坡面的西棱都咬住前一片 (或山墙腰) —— 顺着搭不悬空。",
)
b.step(
    "铺北坡合脊, 立东山墙: 脊线上 4 对整边互吸自锁。",
    ["roof_n0", "roof_n1", "roof_n2", "roof_n3", "gable_e"],
    highlight=["roof_s0"],
    tip="檐-坡-脊-坡-檐闭合成环: 剪断檐线, 力从脊线绕行。",
)
b.step(
    "挂招牌: 方片自店门上方的屋檐坡底边外垂 30 度。",
    ["sign"],
    highlight=["roof_s1", "shop_door"],
    tip="受拉悬挂 30g << 84g, 外摆力矩 7.5 << 17.5 —— 招牌晃不掉。",
)
b.step(
    "砌巨琴琴身下层: 3 片立墙骑 y=1 拼缝。",
    ["vb_lo_3", "vb_lo_4", "vb_lo_5"],
    highlight=["pl_3_0", "pl_3_1"],
    tip="巨琴是广告墙 —— 骑缝一线双吸, 相邻竖边再互吸。",
)
b.step(
    "叠琴身上层, 竖琴颈, 戴琴头: 3 + 1 + 1 片。",
    ["vb_hi_3", "vb_hi_4", "vb_hi_5", "vneck", "vscroll"],
    highlight=["vb_lo_4"],
    tip="3x2 网格自身成环; 琴颈居中骑顶缝, 琴头重心正压。",
)
b.step(
    "装巨琴斜撑: 直角三角前后对撑, 咬地缝又咬琴身竖边。",
    ["vbr_w_s", "vbr_w_n", "vbr_e_s", "vbr_e_n"],
    highlight=["vb_lo_3", "vb_lo_5"],
    tip="四只斜撑装完, 广告墙剪断任何一条铰链都塌不了。",
)
b.step(
    "摆门前长凳与花坛 —— 提琴工坊开业!",
    ["bn_w", "bn_e", "bn_seat", *PLANT_IDS],
    highlight=["shop_door"],
    tip="长凳座面双端压腿顶如简支桥; 花坛四棱互吸自锁。",
)

b.finalize(
    model_id="violin_shop_01",
    name="提琴工坊",
    name_en="Violin Shop 01",
    description=(
        "全库第一间提琴工坊: 门框方店门 + 三扇窗格方橱窗的 4x1"
        " 木屋, 二层横楣长板双端竖边咬进侧墙 (纯剪传力); 屋顶"
        "两坡各 4 片方片 60 度对拼、脊线整边互吸自锁, 等边山墙"
        "同时咬墙顶与两条坡棱 —— 檐-坡-脊处处成环; 店门口方形"
        "招牌自屋檐坡底边外垂 30 度 (受拉悬挂 30g / 力矩 7.5"
        " 双双远低于 strict 预算); 东侧广场 3x2 巨型提琴广告墙"
        " (琴颈骑顶缝 + 等边琴头), 四只直角三角斜撑前后对撑;"
        " 门前长凳简支桥、西侧等边四坡花坛。A 字自锁、吊挂招牌、"
        "斜撑广告墙 —— 一间琴行三种传力路径。"
    ),
    difficulty=3,
    tags=["音乐", "乐器", "提琴", "商店", "进阶"],
    min_pieces=62,
    min_steps=13,
)
