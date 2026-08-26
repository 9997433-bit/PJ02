#!/usr/bin/env python3
"""生成模型 data/models/soccer_goal_01.json (足球门与球场).

运动场景主题: 全库第一座足球场 —— 8x6 绿茵场两端各立一座
带顶网的白色球门 (侧网方墙 + 后网方墙 + 顶网长板锁成门形环),
西侧点球点上一颗四坡合拢的白色足球; 北看台一排 30 度彩色
坐席坡道 (顶边整边吸背墙顶、坡尾落地, 双端受力), 背墙顶
三名彩色球迷探出头; 两角红色角旗高高竖起, 西南角计分牌
待命 —— 哔! 点球开踢!

结构总览 (世界单位: 1.0 = 正方形磁力片边长, 看台在北):
  - 绿茵场 8x6 (两端方砖列 + 中场长板)                    36 片
  - 球门 x2 (侧网 2 + 后网 2 + 顶网长板 1)                10 片
  - 足球 (四坡等边三角自锁)                                4 片
  - 看台: 步道 x6 + 座席排 x6 + 背墙 x6 + 坐席坡道 x6     24 片
  - 球迷三角 x3 + 角旗 x2 + 计分牌 x2                      7 片
  合计 81 片, 18 个教程步骤, 5 种磁力片形状。

物理规则要点 (通过 R1~R8 全部校验, 常规+strict 双档):
  - 球门五片围合: 侧网 / 后网竖边互吸, 顶网长板两条短边
    整边压侧网顶 —— 门形闭环, 无单点失效;
  - 坐席坡道 30 度: 顶边整边吸背墙顶、坡尾落地, 双端受力
    (滚珠塔坡道同款), 六条坡道并排成看台大斜面;
  - 足球四坡等边三角四棱两两互吸自锁, 底边整边吸点球格边;
  - 球迷 / 角旗 / 计分牌全部立在方砖单位格边上。

用法: python3 tools/generate_soccer_goal.py  (在 magtile-studio 目录下运行)
"""

from magtile_gen import ModelBuilder

b = ModelBuilder()

GRASS = "green"
LINE = "clear"      # 禁区白线
NET = "clear"       # 球门与网
WALK = "gray"       # 看台步道
STAND = "blue"      # 看台
SEAT_COLORS = ("red", "yellow", "blue", "red", "yellow", "blue")
FAN_COLORS = ("red", "orange", "yellow")

# =================================================================
# 1. 绿茵场 [0,8]x[0,6]: 两端方砖列 (x[0,2] 与 [6,8]) + 中场长板
# =================================================================
for y in range(6):
    b.flat(f"p_w0_{y}", 0, y, 0.0, LINE)       # 西禁区白列
    b.flat(f"p_w1_{y}", 1, y, 0.0, GRASS)
    b.flat_rect(f"p_m0_{y}", 2, y, 0.0, GRASS)
    b.flat_rect(f"p_m1_{y}", 4, y, 0.0, GRASS)
    b.flat(f"p_e0_{y}", 6, y, 0.0, GRASS)
    b.flat(f"p_e1_{y}", 7, y, 0.0, LINE)       # 东禁区白列

# =================================================================
# 2. 球门 x2: 门口 2 格宽, 面向中场
# =================================================================
# 西门 (开口朝东): 侧网 y=2/y=4, 后网 x=0, 顶网 [0,1]x[2,4]
b.wall_ns("gw_side_s", 0, 2.0, 0, NET)
b.wall_ns("gw_side_n", 0, 4.0, 0, NET)
b.wall_ew("gw_back_0", 0.0, 2, 0, NET)
b.wall_ew("gw_back_1", 0.0, 3, 0, NET)
b.flat_rect("gw_top", 0, 2, 1.0, NET, axis="y")
# 东门 (开口朝西)
b.wall_ns("ge_side_s", 7, 2.0, 0, NET)
b.wall_ns("ge_side_n", 7, 4.0, 0, NET)
b.wall_ew("ge_back_0", 8.0, 2, 0, NET)
b.wall_ew("ge_back_1", 8.0, 3, 0, NET)
b.flat_rect("ge_top", 7, 2, 1.0, NET, axis="y")

# =================================================================
# 3. 足球: 西点球点上的四坡等边三角自锁球
# =================================================================
BALL_IDS = b.hat4("ball", 1, 2, 0.0, "clear",
                  shape="equilateral_triangle")

# =================================================================
# 4. 北看台 [1,7]x[6,8]: 步道 + 座席排 + 背墙 + 30 度坐席坡道
# =================================================================
for x in range(1, 7):
    b.flat(f"st_walk_{x}", x, 6, 0.0, WALK)
for x in range(1, 7):
    b.flat(f"st_row_{x}", x, 7, 0.0, STAND)
for x in range(1, 7):
    b.wall_ns(f"st_wall_{x}", x, 8.0, 0, STAND)
for i, x in enumerate(range(1, 7)):
    b.ramp(f"st_seat_{x}", "-y", 8.0, x, 1.0, SEAT_COLORS[i])

# =================================================================
# 5. 球迷 + 角旗 + 计分牌
# =================================================================
for i, x in enumerate((1, 3, 5)):
    b.crest_ns(f"fan_{x}", x, 8.0, 1.0, FAN_COLORS[i])
b.spire_ns("flag_w", 0, 6.0, 0.0, "red")
b.spire_ns("flag_e", 7, 6.0, 0.0, "red")
b.wall_ns("board", 0, 0.0, 0, "clear")
b.crest_ns("board_top", 0, 0.0, 1.0, "red")

# =================================================================
# 教程步骤 (18 步)
# =================================================================
for y in range(6):
    b.step(
        f"绿茵场第 {y + 1} 行: 两端方砖 (白色禁区列在最外侧) + "
        f"中场两条长板, 自南向北逐行铺齐。",
        [f"p_w0_{y}", f"p_w1_{y}", f"p_m0_{y}", f"p_m1_{y}",
         f"p_e0_{y}", f"p_e1_{y}"],
        highlight=[] if y == 0 else [f"p_w0_{y - 1}", f"p_e1_{y - 1}"],
        tip="白色方砖列就是禁区白线 —— 球门要立在它的格边上。"
        if y == 0 else "",
    )
b.step(
    "西球门: 两片侧网立在 y=2 与 y=4 格边, 两片后网封住 x=0 线, "
    "顶网长板短边整边压侧网顶 —— 五片锁成门形环。",
    ["gw_side_s", "gw_side_n", "gw_back_0", "gw_back_1", "gw_top"],
    highlight=["p_w0_2", "p_w0_3"],
    tip="先立侧网后网, 顶网最后盖 —— 每片都有依托。",
)
b.step(
    "东球门: 镜像再搭一座, 开口朝西迎着中场。",
    ["ge_side_s", "ge_side_n", "ge_back_0", "ge_back_1", "ge_top"],
    highlight=["p_e1_2", "p_e1_3"],
)
b.step(
    "足球: 4 片白色等边三角在西点球格上四棱互吸, 合拢成一颗"
    "鼓鼓的足球。",
    BALL_IDS,
    highlight=["gw_top"],
    tip="四坡自锁 —— 点球点上的主角登场。",
)
b.step(
    "看台步道: 6 片灰色方砖沿球场北缘铺出入场通道。",
    [f"st_walk_{x}" for x in range(1, 7)],
    highlight=["p_w1_5", "p_e0_5"],
)
b.step(
    "座席排基座: 再铺 6 片蓝色方砖。",
    [f"st_row_{x}" for x in range(1, 7)],
    highlight=["st_walk_1", "st_walk_6"],
)
b.step(
    "看台背墙西段: 3 片蓝色方墙立在 y=8 格边上。",
    ["st_wall_1", "st_wall_2", "st_wall_3"],
    highlight=["st_row_1", "st_row_3"],
)
b.step(
    "看台背墙东段: 再立 3 片, 背墙一字排齐。",
    ["st_wall_4", "st_wall_5", "st_wall_6"],
    highlight=["st_wall_3", "st_row_6"],
)
b.step(
    "坐席坡道西段: 3 条彩色长板 30 度斜铺 —— 顶边整边吸背墙顶, "
    "坡尾落地, 双端受力。",
    ["st_seat_1", "st_seat_2", "st_seat_3"],
    highlight=["st_wall_1", "st_wall_3"],
    tip="和滚珠塔的坡道同款 —— 两头都有依托才稳。",
)
b.step(
    "坐席坡道东段: 再铺 3 条, 看台大斜面合拢。",
    ["st_seat_4", "st_seat_5", "st_seat_6"],
    highlight=["st_seat_3", "st_wall_6"],
)
b.step(
    "球迷入场: 3 名彩色球迷三角从背墙顶探出头 —— 加油声一片!",
    ["fan_1", "fan_3", "fan_5"],
    highlight=["st_wall_1", "st_wall_5"],
)
b.step(
    "角旗: 两支红色角旗立在球场北侧两角的格边上。",
    ["flag_w", "flag_e"],
    highlight=["p_w0_5", "p_e1_5"],
)
b.step(
    "计分牌: 西南角立方板计分牌、戴红顶 —— 哔! 点球开踢!",
    ["board", "board_top"],
    highlight=["p_w0_0"],
)

b.finalize(
    model_id="soccer_goal_01",
    name="足球门与球场",
    name_en="Soccer Goal 01",
    description=(
        "全库第一座足球场: 8x6 绿茵场两端白色禁区列上各立一座带顶网"
        "的球门 —— 侧网后网竖边互吸、顶网长板短边整边压侧网顶, 五片"
        "锁成门形环; 西点球点上 4 片等边三角四坡自锁成一颗足球; 北看"
        "台 6 条 30 度彩色坐席坡道顶边吸背墙顶、坡尾落地双端受力, 背"
        "墙顶 3 名彩色球迷探头助威; 两角红色角旗与西南角计分牌就位 "
        "—— 哔! 点球开踢!"
    ),
    difficulty=4,
    tags=["足球", "运动", "球场", "看台", "场景"],
    min_pieces=78,
    min_steps=18,
)
