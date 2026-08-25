#!/usr/bin/env python3
"""生成模型 data/models/open_air_cinema_01.json (夏夜露天电影院)。

城市生活主题新作, 全库第一座露天放映场 —— 与音乐舞台 (钢琴台)
和看台类模型都不同, 本作的主角是"银幕墙 + 放映亭 + 爆米花餐车"
的三件套: 3x2 的透明银幕墙立在广场北缘, 两端红色边柱收边,
两片直角三角斜撑从正面锁住幕墙两端 (斜撑-边柱-银幕成刚性节点),
幕顶三角彩旗迎风排开; 广场中央的放映亭窗格方正对银幕投出光束,
东侧爆米花餐车驮在双车轮底座上, 草坪上三位小观众骑着拼缝
面朝银幕坐好 —— 夏夜的电影就要开场了。

结构总览 (世界单位: 1.0 = 正方形磁力片边长, 银幕在北):
  - 草坪广场 6x4: 单位方板 x22 (含三块野餐垫) + 餐车底长板 x1  23 片
  - 银幕墙 (y=4 立面): 透明银幕 3x2 x6 + 红边柱 x2
    + 直角三角斜撑 x2 + 幕顶彩旗 x3                           13 片
  - 放映亭 (x [2,3], y [0,1]): 四墙 (放映窗朝幕/门朝南)
    + 等边四坡锥顶                                             8 片
  - 爆米花餐车: 车轮底座 x2 + 甲板 x1 + 招牌 x1 + 遮阳伞 x1    5 片
  - 灯柱 x2 (瘦高等腰) + 小观众 x3 (等边骑拼缝)                5 片
  合计 54 片, 12 个教程步骤, 8 种磁力片形状 (全部 CORE-9 之内)。

物理规则要点 (validate 常规 + strict 双档零警告):
  - 银幕墙是竖直连续墙体: 下环踩广场北缘拼缝整边吸合, 上环
    整边压下环, 竖边逐片互吸 —— 无侧向力矩;
  - 直角三角斜撑两条直角边分别整边吸草坪拼缝与银幕竖边,
    斜撑-边柱-银幕锁成刚性节点 (摩天大楼同款 T14);
  - 放映亭四墙合环, 等边四坡锥顶斜棱两两互吸自锁 (锥尖 1.71);
  - 餐车车轮底座底边整边吸底长板两条长边, 甲板长边压双轮顶
    锁成门式框架 —— 招牌与遮阳伞立在甲板短边上;
  - 彩旗/观众/灯柱各自独立吸附, 剪断任何一条装饰连接最多
    失联 1 片 (< 3), R8 单点失效通过。

用法: python3 tools/generate_open_air_cinema_01.py  (在 magtile-studio 目录下运行)
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from magtile_gen import ModelBuilder  # noqa: E402

b = ModelBuilder()

LAWN = "green"      # 草坪
MAT_A = "red"       # 野餐垫
MAT_B = "blue"
MAT_C = "pink"
SCREEN = "clear"    # 银幕
PILLAR = "red"      # 银幕边柱
BRACE = "red"       # 斜撑
BOOTH = "gray"      # 放映亭墙
PROJ = "cyan"       # 放映窗
DOOR = "orange"     # 放映亭门
ROOF = "purple"     # 放映亭锥顶
CART = "yellow"     # 餐车
WHEEL = "gray"      # 车轮
POP = "red"         # 爆米花招牌
BRELLA = "orange"   # 遮阳伞
LAMP = "purple"     # 灯柱
FLAGS = [("flag_w", 1, "orange"), ("flag_m", 2, "yellow"), ("flag_e", 3, "pink")]
CROWD = [("kid_w", 0, "orange"), ("kid_m", 2, "cyan"), ("kid_e", 4, "pink")]


def wall_ns_t(tid, tile_type, x0, y, z0, color):
    b.add(tid, tile_type, (x0 + 0.5, y, z0 + 0.5), (90, 0, 0), color)


# =================================================================
# 1. 草坪广场 6x4 (y [0,4]): 南行留出餐车底长板, 草坪散落野餐垫
# =================================================================
for x0 in range(4):
    b.flat(f"lawn_{x0}_0", x0, 0, 0.0, LAWN)          # 南行 x [0,4]
b.flat_rect("cart_base", 4, 0, 0.0, LAWN)             # 餐车底长板 [4,6]
for x0 in range(6):
    color = MAT_A if x0 == 1 else (MAT_B if x0 == 3 else LAWN)
    b.flat(f"lawn_{x0}_1", x0, 1, 0.0, color)         # 野餐垫行
for x0 in range(6):
    color = MAT_C if x0 == 5 else LAWN
    b.flat(f"lawn_{x0}_2", x0, 2, 0.0, color)         # 观众行
for x0 in range(6):
    b.flat(f"lawn_{x0}_3", x0, 3, 0.0, LAWN)          # 银幕前行

# =================================================================
# 2. 银幕墙 (y=4 立面): 3x2 透明银幕 + 红边柱 + 斜撑 + 彩旗
# =================================================================
for i, x0 in enumerate((1, 2, 3)):
    b.wall_ns(f"screen_lo_{i}", x0, 4.0, 0, SCREEN)   # 银幕下环
b.wall_ns("pillar_w", 0, 4.0, 0, PILLAR)              # 西边柱
b.wall_ns("pillar_e", 4, 4.0, 0, PILLAR)              # 东边柱
for i, x0 in enumerate((1, 2, 3)):
    b.wall_ns(f"screen_hi_{i}", x0, 4.0, 1, SCREEN)   # 银幕上环
b.brace("brace_w", (1.0, 4.0, 0.0), "-y", BRACE)      # 正面斜撑锁两端
b.brace("brace_e", (4.0, 4.0, 0.0), "-y", BRACE)
for tid, x0, color in FLAGS:
    b.crest_ns(tid, x0, 4.0, 2.0, color)              # 幕顶彩旗

# =================================================================
# 3. 放映亭 (x [2,3], y [0,1]): 放映窗朝幕, 门朝南
# =================================================================
wall_ns_t("booth_s", "door_frame", 2, 0.0, 0, DOOR)   # 门朝南
wall_ns_t("booth_n", "window_square", 2, 1.0, 0, PROJ)  # 放映窗朝银幕
b.wall_ew("booth_w", 2.0, 0, 0, BOOTH)
b.wall_ew("booth_e", 3.0, 0, 0, BOOTH)
BOOTH_ROOF = b.hat4("booth_roof", 2, 0, 1.0, ROOF,
                    shape="equilateral_triangle")     # 锥尖 1.71

# =================================================================
# 4. 爆米花餐车 (x [4,6], y [0,1]): 双轮 + 甲板 + 招牌 + 遮阳伞
# =================================================================
b.add("cart_wheel_s", "wheel_base", (5.0, 0.0, 0.5), (90, 0, 0), WHEEL)
b.add("cart_wheel_n", "wheel_base", (5.0, 1.0, 0.5), (90, 0, 0), WHEEL)
b.flat_rect("cart_deck", 4, 0, 1.0, CART)             # 甲板 [4,6]x[0,1]
b.crest_ew("pop_sign", 4.0, 0, 1.0, POP)              # 爆米花招牌 (朝亭)
b.spire_ew("cart_brella", 6.0, 0, 1.0, BRELLA)        # 遮阳伞

# =================================================================
# 5. 灯柱 x2 + 小观众 x3 (骑观众行拼缝面朝银幕)
# =================================================================
b.spire_ew("lamp_w", 0.0, 1, 0.0, LAMP)               # 西灯柱
b.spire_ew("lamp_e", 6.0, 2, 0.0, LAMP)               # 东灯柱
for tid, x0, color in CROWD:
    b.crest_ns(tid, x0, 2.0, 0.0, color)              # 小观众

# =================================================================
# 教程步骤 (12 步)
# =================================================================
b.step(
    "铺南行草坪与餐车底长板: 长板两条长边是车轮的落脚缝。",
    [f"lawn_{x0}_0" for x0 in range(4)] + ["cart_base"],
    tip="夏夜的草坪电影院, 先把场地铺出来。",
)
b.step(
    "铺野餐垫行: 红蓝两块野餐垫散落在草坪里。",
    [f"lawn_{x0}_1" for x0 in range(6)],
    highlight=["lawn_0_0"],
    tip="行行等边互吸 —— 观众提着零食已经在路上啦。",
)
b.step(
    "铺观众行: 粉色野餐垫留给来得最晚的那一家。",
    [f"lawn_{x0}_2" for x0 in range(6)],
    highlight=["lawn_0_1"],
    tip="小观众们就坐在这一行的拼缝上。",
)
b.step(
    "铺银幕前行: 六片草坪合拢广场, 北缘拼缝就是幕墙的地基线。",
    [f"lawn_{x0}_3" for x0 in range(6)],
    highlight=["lawn_0_2"],
    tip="银幕墙脚要整边吸住这条北缘拼缝。",
)
b.step(
    "立银幕下环与红边柱: 三片透明银幕一字排开, 两端红柱收边。",
    ["screen_lo_0", "screen_lo_1", "screen_lo_2", "pillar_w", "pillar_e"],
    highlight=["lawn_1_3", "lawn_3_3"],
    tip="底边整边吸拼缝, 竖边逐片互吸 —— 幕墙先立第一环。",
)
b.step(
    "叠银幕上环: 三片透明方板整边压上下环, 银幕升到两层高。",
    ["screen_hi_0", "screen_hi_1", "screen_hi_2"],
    highlight=["screen_lo_1"],
    tip="上环压下环竖直连续 —— 3x2 的大银幕拼好了。",
)
b.step(
    "锁斜撑挂彩旗: 两片直角三角从正面锁住幕墙两端, 幕顶彩旗迎风。",
    ["brace_w", "brace_e"] + [tid for tid, _, _ in FLAGS],
    highlight=["pillar_w", "pillar_e"],
    tip="斜撑两条直角边分别吸草坪拼缝与银幕竖边 —— 刚性节点锁定。",
)
b.step(
    "立放映亭四墙: 窗格方放映窗正对银幕, 门框方朝南。",
    ["booth_s", "booth_n", "booth_w", "booth_e"],
    highlight=["lawn_2_0"],
    tip="放映窗与银幕正对成一条光路 —— 电影从这里射向幕布。",
)
b.step(
    "盖放映亭锥顶: 四片紫色等边三角斜棱互咬自锁。",
    BOOTH_ROOF,
    highlight=["booth_n"],
    tip="锥尖 1.71 —— 对角顺序合拢, 最后一片同时吸双棱。",
)
b.step(
    "架爆米花餐车: 双车轮底座沿长板拼缝立起, 黄甲板压双轮顶。",
    ["cart_wheel_s", "cart_wheel_n", "cart_deck"],
    highlight=["cart_base"],
    tip="轮组+甲板锁成门式框架 —— 散场前的爆米花最抢手。",
)
b.step(
    "装招牌遮阳伞并点灯: 红招牌朝亭, 橙伞遮车, 两根紫灯柱立场边。",
    ["pop_sign", "cart_brella", "lamp_w", "lamp_e"],
    highlight=["cart_deck"],
    tip="招牌和伞立在甲板短边上, 灯柱底边整边吸场边拼缝。",
)
b.step(
    "请小观众入座: 三位小观众骑上拼缝, 面朝银幕坐好 —— 开演!",
    [tid for tid, _, _ in CROWD],
    highlight=["screen_hi_1"],
    tip="嘘 —— 灯光暗下来了, 夏夜的电影正式开场!",
)

b.finalize(
    model_id="open_air_cinema_01",
    name="夏夜露天电影院",
    name_en="Open-Air Cinema 01",
    description=(
        "只用核心九片型的露天放映场: 3x2 的透明大银幕立在草坪北缘 "
        "(下环踩拼缝、上环整边压顶、红边柱收边), 两片直角三角斜撑"
        "从正面锁住幕墙两端成刚性节点, 幕顶三角彩旗迎风排开; 广场"
        "中央的放映亭窗格方正对银幕投出光路, 等边锥顶斜棱自锁; "
        "东侧爆米花餐车驮在双车轮底座门式框架上, 红招牌与橙色遮阳伞"
        "立在甲板两端; 草坪上野餐垫散落, 三位小观众骑着拼缝面朝"
        "银幕坐好 —— 灯光暗下来, 夏夜的电影开场了!"
    ),
    difficulty=3,
    tags=["城市", "电影", "夏夜", "广场", "生活场景"],
    min_pieces=54,
    min_steps=12,
)
