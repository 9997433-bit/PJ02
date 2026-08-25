#!/usr/bin/env python3
"""生成模型 data/models/dragon_cave_01.json (火龙藏宝洞)。

童话/奇幻主题 2/4: 全库第一座 "洞窟 + 生物" 双主角场景 —— 与
volcano_base_01 (锥体收分火山) / medieval_gate_01 (门框方城门) 的
结构逻辑刻意区分: 岩洞不是收分锥也不用门框方, 而是箱式山体开出
一张 2 格宽的洞口 —— 洞口横楣双端竖边纯剪锁进两侧岩壁 (负空间
洞口), 洞顶再隆起一座等边四坡岩峰; 洞前一条火龙整装卧地: 箱式
龙身 + 立颈昂首 + 双翼 45 度展开 + 30 度坡道龙尾扫地, 龙口前
一簇火舌; 洞内金色宝堆四棱自锁 —— 先藏宝再封顶, 装配顺序即
寻宝叙事。

结构总览 (世界单位: 1.0 = 正方形磁力片边长, 洞口朝南):
  - 地面 (x [0,7], y [0,5]): 草甸 + 石板道 + 洞内岩地 5 行      28 片
  - 岩洞第 1 层 (x [1,5], y [3,5], z 0..1): 洞口两侧岩壁 x2 +
    东西山壁 x4 + 后山壁 x4                                     10 片
  - 岩洞第 2 层 (z 1..2): 岩壁 x8 + 洞口横楣 x1 (纯剪) +
    窗格方风洞 x2                                               11 片
  - 洞顶 (z=2): 前排方板 x4 + 后排长板 x2                        6 片
  - 岩峰: 等边四坡锥 x4 (峰顶 2.71)                              4 片
  - 火龙: 龙身侧板 x2 + 首尾立板 x2 + 龙背方板 x2 + 立颈 x1 +
    龙首 x1 + 双翼 x2 (45 度) + 龙尾坡道 x1                     11 片
  - 洞内宝堆: 等边四坡锥 x4 + 火舌 x1                            5 片
  合计 75 片, 14 个教程步骤, 4 种磁力片形状 (全部 CORE-9 之内)。

物理规则要点 (通过 R1~R8 全部校验, strict 档同样全绿):
  - 山体两层墙环四角竖边互吸闭环, 洞口横楣双端竖边吸进第 2 层
    岩壁竖棱 (纯剪), 剪断任一端仍经另一端绕行;
  - 洞顶每片同时吸山壁顶与邻板拼缝, 岩峰/宝堆四棱两两互吸自锁;
  - 龙身是完整箱体 (侧板-首尾板-背板处处成环); 双翼底边整边吸
    龙背方板沿口, 45 度外展力矩仅 2.7 g·单位 (strict 预算 35);
    龙尾 30 度坡道顶边一线双吸 (背板短边 + 尾板顶边), 坡尾扫地;
  - 宝堆先于洞顶放置 (R7b 装配可达: 封顶前洞内伸手可及)。

用法: python3 tools/generate_dragon_cave.py  (在 magtile-studio 目录下运行)
"""

from magtile_gen import ModelBuilder

b = ModelBuilder()

MEADOW = "green"    # 草甸
TRAIL = "gray"      # 石板道
ROCKF = "gray"      # 洞内岩地
ROCK = "gray"       # 山体岩壁
ROCK2 = "purple"    # 第 2 层岩壁 (魔石)
WIND = "clear"      # 窗格方风洞
ROOF = "gray"       # 洞顶
PEAK = "purple"     # 岩峰
DRAGON = "green"    # 龙身
WINGC = "red"       # 龙翼
GOLD = "yellow"     # 宝堆
FIRE = "red"        # 火舌

# =================================================================
# 1. 地面 (x [0,7], y [0,5]): 5 行; 洞内两行铺岩地
# =================================================================
b.flat_rect("dg0_a", 0, 0, 0.0, MEADOW)
b.flat_rect("dg0_b", 2, 0, 0.0, TRAIL)
b.flat_rect("dg0_c", 4, 0, 0.0, MEADOW)
b.flat("dg0_d", 6, 0, 0.0, MEADOW)

b.flat("dg1_a", 0, 1, 0.0, MEADOW)
b.flat("dg1_b", 1, 1, 0.0, MEADOW)
b.flat_rect("dg1_c", 2, 1, 0.0, MEADOW)      # 龙床
b.flat("dg1_d", 4, 1, 0.0, MEADOW)
b.flat("dg1_e", 5, 1, 0.0, MEADOW)
b.flat("dg1_f", 6, 1, 0.0, MEADOW)

b.flat("dg2_a", 0, 2, 0.0, MEADOW)
b.flat("dg2_b", 1, 2, 0.0, MEADOW)
b.flat_rect("dg2_c", 2, 2, 0.0, TRAIL)       # 洞口前庭
b.flat("dg2_d", 4, 2, 0.0, MEADOW)
b.flat("dg2_e", 5, 2, 0.0, MEADOW)
b.flat("dg2_f", 6, 2, 0.0, MEADOW)

b.flat("dg3_a", 0, 3, 0.0, MEADOW)
b.flat("dg3_b", 1, 3, 0.0, ROCKF)
b.flat("dg3_c", 2, 3, 0.0, ROCKF)            # 宝堆岩座
b.flat("dg3_d", 3, 3, 0.0, ROCKF)
b.flat("dg3_e", 4, 3, 0.0, ROCKF)
b.flat_rect("dg3_f", 5, 3, 0.0, MEADOW)

b.flat("dg4_a", 0, 4, 0.0, MEADOW)
b.flat("dg4_b", 1, 4, 0.0, ROCKF)
b.flat("dg4_c", 2, 4, 0.0, ROCKF)
b.flat("dg4_d", 3, 4, 0.0, ROCKF)
b.flat("dg4_e", 4, 4, 0.0, ROCKF)
b.flat_rect("dg4_f", 5, 4, 0.0, MEADOW)

# =================================================================
# 2. 岩洞第 1 层 (x [1,5], y [3,5], z 0..1): 洞口 x [2,4] 留空
# =================================================================
b.wall_ns("cv1_sw", 1, 3.0, 0, ROCK)
b.wall_ns("cv1_se", 4, 3.0, 0, ROCK)
b.wall_ew("cv1_w1", 1.0, 3, 0, ROCK)
b.wall_ew("cv1_w2", 1.0, 4, 0, ROCK)
b.wall_ew("cv1_e1", 5.0, 3, 0, ROCK)
b.wall_ew("cv1_e2", 5.0, 4, 0, ROCK)
for x in (1, 2, 3, 4):
    b.wall_ns(f"cv1_n{x}", x, 5.0, 0, ROCK)

# =================================================================
# 3. 洞内宝堆 (x [2,3], y [3,4]): 先藏宝, 后封顶
# =================================================================
GOLD_IDS = b.hat4("gold", 2, 3, 0.0, GOLD, shape="equilateral_triangle")

# =================================================================
# 4. 岩洞第 2 层 (z 1..2): 洞口横楣纯剪 + 后壁两扇窗格方风洞
# =================================================================
b.wall_ns("cv2_sw", 1, 3.0, 1, ROCK2)
b.lintel_ns("cv2_lintel", 2, 3.0, 1, ROCK)
b.wall_ns("cv2_se", 4, 3.0, 1, ROCK2)
b.wall_ew("cv2_w1", 1.0, 3, 1, ROCK2)
b.wall_ew("cv2_w2", 1.0, 4, 1, ROCK2)
b.wall_ew("cv2_e1", 5.0, 3, 1, ROCK2)
b.wall_ew("cv2_e2", 5.0, 4, 1, ROCK2)
b.wall_ns("cv2_n1", 1, 5.0, 1, ROCK2)
b.add("cv2_n2", "window_square", (2.5, 5.0, 1.5), (90, 0, 0), WIND)
b.add("cv2_n3", "window_square", (3.5, 5.0, 1.5), (90, 0, 0), WIND)
b.wall_ns("cv2_n4", 4, 5.0, 1, ROCK2)

# =================================================================
# 5. 洞顶 (z=2) + 岩峰 (x [3,4], y [4,5])
# =================================================================
for x in (1, 2, 3, 4):
    b.flat(f"rf_s{x}", x, 3, 2.0, ROOF)
b.flat_rect("rf_nw", 1, 4, 2.0, ROOF)
b.flat_rect("rf_ne", 3, 4, 2.0, ROOF)
PEAK_IDS = b.hat4("peak", 3, 4, 2.0, PEAK, shape="equilateral_triangle")

# =================================================================
# 6. 火龙 (龙身 x [2,4], y [1,2], 龙首朝东)
# =================================================================
b.lintel_ns("drg_flank_s", 2, 1.0, 0, DRAGON)
b.lintel_ns("drg_flank_n", 2, 2.0, 0, DRAGON)
b.wall_ew("drg_tail_cap", 2.0, 1, 0, DRAGON)
b.wall_ew("drg_chest", 4.0, 1, 0, DRAGON)
b.flat("drg_back_w", 2, 1, 1.0, DRAGON)
b.flat("drg_back_e", 3, 1, 1.0, DRAGON)
b.wall_ew("drg_neck", 4.0, 1, 1, DRAGON)
b.crest_ew("drg_head", 4.0, 1, 2.0, DRAGON)
b.place_tri("drg_wing_s", "equilateral_triangle",
            (4.0, 1.0, 1.0), (3.0, 1.0, 1.0),
            (3.5, 0.387628, 1.612372), WINGC)
b.place_tri("drg_wing_n", "equilateral_triangle",
            (3.0, 2.0, 1.0), (4.0, 2.0, 1.0),
            (3.5, 2.612372, 1.612372), WINGC)
b.ramp("drg_tail", "-x", 2.0, 1, 1.0, DRAGON)
b.crest_ew("fire", 5.0, 1, 0.0, FIRE)

# =================================================================
# 教程步骤 (14 步)
# =================================================================
b.step(
    "铺场地南行 (y [0,1]): 4 片, 灰色石板道对准洞口。",
    ["dg0_a", "dg0_b", "dg0_c", "dg0_d"],
    tip="寻宝小径 (x [2,4]) 正对洞口 —— 火龙就守在路边。",
)
b.step(
    "铺龙床一行 (y [1,2]): 6 片, 长板草甸给火龙当卧榻。",
    ["dg1_a", "dg1_b", "dg1_c", "dg1_d", "dg1_e", "dg1_f"],
    highlight=["dg0_b"],
    tip="x=2 与 x=4 的拼缝就是龙身首尾立板的位置。",
)
b.step(
    "铺洞口前庭 (y [2,3]): 6 片, 石板道一直铺到洞口。",
    ["dg2_a", "dg2_b", "dg2_c", "dg2_d", "dg2_e", "dg2_f"],
    highlight=["dg1_c"],
    tip="岩洞前壁就踩这一行的北缝。",
)
b.step(
    "铺洞内岩地第一行 (y [3,4]): 6 片, 正中灰色岩座留给宝堆。",
    ["dg3_a", "dg3_b", "dg3_c", "dg3_d", "dg3_e", "dg3_f"],
    highlight=["dg2_c"],
    tip="洞里的地面也要铺满 —— 宝堆的四条基线全靠它。",
)
b.step(
    "铺洞内岩地第二行 (y [4,5]): 6 片, 地面合拢。",
    ["dg4_a", "dg4_b", "dg4_c", "dg4_d", "dg4_e", "dg4_f"],
    highlight=["dg3_c"],
    tip="7x5 场地铺满, 山体与火龙都有了地基。",
)
b.step(
    "砌岩洞第 1 层前壁与西壁: 4 片, 洞口 (x [2,4]) 留空。",
    ["cv1_sw", "cv1_w1", "cv1_w2", "cv1_se"],
    highlight=["dg2_c", "dg3_b"],
    tip="洞口是负空间 —— 两侧岩壁先立起来, 横楣下一层再锁。",
)
b.step(
    "砌岩洞第 1 层东壁与后壁: 6 片, 墙环转角互吸闭合。",
    ["cv1_e1", "cv1_e2", "cv1_n1", "cv1_n2", "cv1_n3", "cv1_n4"],
    highlight=["cv1_sw"],
    tip="闭合墙环是山体的骨架 —— 轻推应整体联动。",
)
b.step(
    "洞内藏宝: 金色宝堆四棱两两互吸自锁 (趁封顶前伸手放好)。",
    GOLD_IDS,
    highlight=["dg3_c"],
    tip="先藏宝再封顶 —— 装配顺序就是寻宝故事的顺序。",
)
b.step(
    "砌第 2 层前壁并架洞口横楣: 横楣双端竖边纯剪锁进岩壁。",
    ["cv2_sw", "cv2_se", "cv2_lintel", "cv2_w1", "cv2_w2"],
    highlight=["cv1_sw", "cv1_se"],
    tip="横楣跨过 2 格洞口, 剪断任一端仍经另一端绕行。",
)
b.step(
    "砌第 2 层东壁与后壁: 后壁嵌两扇窗格方风洞。",
    ["cv2_e1", "cv2_e2", "cv2_n1", "cv2_n2", "cv2_n3", "cv2_n4"],
    highlight=["cv2_lintel"],
    tip="风洞给洞里透光 —— 金子在暗处也会闪。",
)
b.step(
    "盖洞顶: 前排 4 片方板 + 后排 2 片长板, 每片多路吸合。",
    ["rf_s1", "rf_s2", "rf_s3", "rf_s4", "rf_nw", "rf_ne"],
    highlight=["cv2_n2", "cv2_n3"],
    tip="每片同时压山壁顶与邻板拼缝 —— 洞顶就是新的山脊。",
)
b.step(
    "隆起岩峰: 4 片等边三角四棱自锁 (峰顶 2.71)。",
    PEAK_IDS,
    highlight=["rf_ne"],
    tip="岩峰骑在洞顶拼缝上 —— 山有了尖, 洞有了深。",
)
b.step(
    "拼火龙龙身: 两片长板侧腹 + 首尾立板 + 两片龙背方板锁成箱体。",
    ["drg_flank_s", "drg_flank_n", "drg_tail_cap", "drg_chest",
     "drg_back_w", "drg_back_e"],
    highlight=["dg1_c"],
    tip="侧板-首尾板-背板处处成环, 龙身是一只结实的箱子。",
)
b.step(
    "立颈昂首、展翼、扫尾、喷火 —— 火龙藏宝洞落成!",
    ["drg_neck", "drg_head", "drg_wing_s", "drg_wing_n",
     "drg_tail", "fire"],
    highlight=["drg_back_e", "drg_chest"],
    tip="双翼 45 度整边吸背板沿; 龙尾坡道一线双吸扫到地面。",
)

b.finalize(
    model_id="dragon_cave_01",
    name="火龙藏宝洞",
    name_en="Dragon Treasure Cave 01",
    description=(
        "全库第一座洞窟+生物双主角场景: 箱式山体开出 2 格宽的负空间"
        "洞口, 横楣双端竖边纯剪锁进岩壁, 洞顶隆起等边四坡岩峰; 洞前"
        "火龙整装卧地 —— 箱式龙身处处成环, 立颈昂首, 双翼 45 度整边"
        "外展 (力矩仅 2.7), 30 度坡道龙尾扫地, 龙口火舌正红; 洞内"
        "金色宝堆四棱自锁, 先藏宝再封顶 —— 装配顺序即寻宝叙事。"
    ),
    difficulty=3,
    tags=["童话", "奇幻", "火龙", "洞穴", "进阶"],
    min_pieces=72,
    min_steps=14,
)
