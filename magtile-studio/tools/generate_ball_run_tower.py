#!/usr/bin/env python3
"""生成旗舰模型 data/models/ball_run_tower_01.json (螺旋滚珠塔 · 双轨竞速)。

内容策略 2.4 节"反幼稚规则"的标杆样板之一 (简报 ⑬):
不是"看的模型", 是每天都会拿出来玩的弹珠机 —— 三层发球塔向东西
两侧甩出镜像双螺旋轨道, 双珠同放比谁先落港。

结构总览 (世界单位: 1.0 = 正方形磁力片边长):
  - 中央发球塔: 2x2 占地三层高, 顶层发球台四周围栏, 东西各留出珠口   42 片
  - 东线轨道 (顺时针绕塔): 30 度坡道 -> 转角平台 -> 30 度坡道 ->
    转角平台 -> 冲线坡道落地, 每段坡尾由独立栈桥墩接住,
    第一转角台外缘另立双层门式立柱 (R9 抖动加固)                     14 片
  - 西线轨道: 与东线严格镜像 (T11), 双轨竞速                        14 片
  - 东西接珠港: 地面广场 + 三面围墙的接珠池                          24 片
  - 装饰: 接珠港六边形靶标 x2 + 竖长方形冲线旗门 x2                    4 片
  合计 94 片, 19 个教程步骤。

滚珠动线 (东线, 西线镜像):
  发球台 (z=3) --东坡道--> 转角台 (z=2) 直角转向 --南坡道-->
  转角台 (z=1) 直角转向 --西冲线坡道--> 落地滚入接珠港。

物理规则要点 (通过 R1~R9 全部校验):
  - 每段坡道顶边整边吸在平台沿口, 坡尾由"栈桥墩"顶边接住,
    坡道-桥墩-转角台三件互吸成三角刚性节点 -> 零悬挑零悬挂;
  - 第一转角台外缘由双层门式立柱从地面顶住 (桥墩+立柱构成门式框架):
    没有它, 转角台+两片挡珠三角绕桥墩顶铰链的悬臂力矩约 34.5g·单位,
    紧贴 strict 档 35.0 预算, 注入 ±1.5mm/±2° 放置误差 (R9) 即越限;
    立柱使铰链剪切后转角台仍有接地路径, 悬臂分析自然消失;
  - 冲线坡道坡尾直接落地 (自身接地);
  - 转角平台面与上一段坡尾平齐 (z 相同), 弹珠平滑过渡;
  - 教程按"桥墩 -> 坡道 -> 转角台"整段成组安装, 任何中间态无悬空件。

坐标约定与 C++ 端一致 (include/magtile/core/tile_instance.hpp):
  旋转为欧拉角 (度), 施加顺序 R = Rz * Ry * Rx。

用法: python3 tools/generate_ball_run_tower.py  (在 magtile-studio 目录下运行)
"""

import json
import math
from pathlib import Path

TRI_CENTROID = round(math.sqrt(3) / 6, 6)     # 等边三角形质心到底边 0.288675
ISO_CENTROID = 0.666667                       # 等腰三角形质心到底边 (底 1 高 2)
HEX_CENTROID = round(math.sqrt(3) / 2, 6)     # 六边形中心到边 0.866025
COS30 = round(math.cos(math.radians(30)), 6)  # 0.866025
SQ3 = round(math.sqrt(3), 6)                  # 30 度坡道的水平投影长 1.732051

tiles = []


def add(tile_id, tile_type, pos, rot, color):
    tiles.append({
        "id": tile_id,
        "type": tile_type,
        "position": [round(v, 6) for v in pos],
        "rotation": [round(v, 6) for v in rot],
        "color": color,
    })


def flat(tile_id, x0, y0, z, color):
    """平铺正方形, 覆盖 [x0,x0+1] x [y0,y0+1], 高度 z。"""
    add(tile_id, "square", (x0 + 0.5, y0 + 0.5, z), (0, 0, 0), color)


def wall_ns(tile_id, x0, y, z0, color):
    """南北朝向立墙 (平面 y=y), 覆盖 x [x0,x0+1], z [z0,z0+1]。"""
    add(tile_id, "square", (x0 + 0.5, y, z0 + 0.5), (90, 0, 0), color)


def wall_ew(tile_id, x, y0, z0, color):
    """东西朝向立墙 (平面 x=x), 覆盖 y [y0,y0+1], z [z0,z0+1]。"""
    add(tile_id, "square", (x, y0 + 0.5, z0 + 0.5), (90, 0, 90), color)


def ramp(tile_id, direction, edge, lane0, z_top, color):
    """30 度长方形坡道。

    direction: 下坡朝向 (+x / -x / +y / -y);
    edge:      坡道顶边所在的网格线坐标 (x 或 y);
    lane0:     顶边另一轴的起点 (顶边长 1, 覆盖 lane0..lane0+1);
    z_top:     顶边高度。坡尾落在 z_top - 1, 水平外伸 sqrt(3)。
    """
    if direction == "+x":
        add(tile_id, "rectangle", (edge + COS30, lane0 + 0.5, z_top - 0.5), (0, 30, 0), color)
    elif direction == "-x":
        add(tile_id, "rectangle", (edge - COS30, lane0 + 0.5, z_top - 0.5), (0, -30, 0), color)
    elif direction == "+y":
        add(tile_id, "rectangle", (lane0 + 0.5, edge + COS30, z_top - 0.5), (0, 30, 90), color)
    elif direction == "-y":
        add(tile_id, "rectangle", (lane0 + 0.5, edge - COS30, z_top - 0.5), (0, -30, 90), color)
    else:
        raise ValueError(direction)


def rail_ns(tile_id, x0, y, z, color, shape="equilateral_triangle"):
    """挡珠围栏: 三角形立在南北向沿口上, 底边落在高度 z。"""
    centroid = ISO_CENTROID if shape == "isosceles_triangle" else TRI_CENTROID
    add(tile_id, shape, (x0 + 0.5, y, z + centroid), (90, 0, 0), color)


def rail_ew(tile_id, x, y0, z, color, shape="equilateral_triangle"):
    centroid = ISO_CENTROID if shape == "isosceles_triangle" else TRI_CENTROID
    add(tile_id, shape, (x, y0 + 0.5, z + centroid), (90, 0, 90), color)


# =================================================================
# 1. 地面: 塔基 2x2 + 东西两侧广场与接珠港地台
#    东港在塔南偏东 (y -3..-1), 西港在塔北偏西 (y 3..5), 各带连接广场
# =================================================================
for j in range(2):
    for i in range(2):
        flat(f"g_{i}_{j}", i, j, 0.0, "green" if (i + j) % 2 == 0 else "cyan")

for i in range(2):                       # 东港连接广场 (y -1..0)
    flat(f"pe_{i}", i, -1, 0.0, "gray")
for i in range(2):                       # 东接珠港地台 (y -3..-1)
    flat(f"fe_{i}_1", i, -2, 0.0, "blue")
for i in range(2):
    flat(f"fe_{i}_2", i, -3, 0.0, "blue")

for i in range(2):                       # 西港连接广场 (y 2..3)
    flat(f"pw_{i}", i, 2, 0.0, "gray")
for i in range(2):                       # 西接珠港地台 (y 3..5)
    flat(f"fw_{i}_1", i, 3, 0.0, "blue")
for i in range(2):
    flat(f"fw_{i}_2", i, 4, 0.0, "blue")

# =================================================================
# 2. 中央发球塔: 2x2 占地, 三层墙 + 顶层发球台
# =================================================================
LEVEL_COLOR = {0: "green", 1: "cyan", 2: "green"}
for lv in range(3):
    c = LEVEL_COLOR[lv]
    for i in range(2):
        wall_ns(f"tw{lv}_s_{i}", i, 0.0, lv, c)
    for j in range(2):
        wall_ew(f"tw{lv}_w_{j}", 0.0, j, lv, c)
    for i in range(2):
        wall_ns(f"tw{lv}_n_{i}", i, 2.0, lv, c)
    for j in range(2):
        wall_ew(f"tw{lv}_e_{j}", 2.0, j, lv, c)

for j in range(2):                       # 发球台 (z=3)
    for i in range(2):
        flat(f"plat_{i}_{j}", i, j, 3.0, "yellow")

# 发球台围栏: 北缘 2 根等腰高塔柱, 南缘 2 片红三角;
# 东缘只拦 y1..2 (y0..1 是东线出珠口), 西缘只拦 y0..1 (y1..2 是西线出珠口)
rail_ns("prail_n_0", 0, 2.0, 3.0, "purple", "isosceles_triangle")
rail_ns("prail_n_1", 1, 2.0, 3.0, "purple", "isosceles_triangle")
rail_ns("prail_s_0", 0, 0.0, 3.0, "red")
rail_ns("prail_s_1", 1, 0.0, 3.0, "red")
rail_ew("prail_e", 2.0, 1, 3.0, "red")
rail_ew("prail_w", 0.0, 0, 3.0, "red")

# =================================================================
# 3. 接珠港围墙 (三面围合, 迎珠面敞开)
# =================================================================
for r, y0 in ((1, -2), (2, -3)):         # 东港西墙 x=0
    wall_ew(f"bwE_w_{r}", 0.0, y0, 0, "cyan")
for i in range(2):                       # 东港南墙 y=-3
    wall_ns(f"bwE_s_{i}", i, -3.0, 0, "cyan")
for i in range(2):                       # 东港北墙 y=-1
    wall_ns(f"bwE_n_{i}", i, -1.0, 0, "cyan")

for r, y0 in ((1, 3), (2, 4)):           # 西港东墙 x=2
    wall_ew(f"bwW_e_{r}", 2.0, y0, 0, "cyan")
for i in range(2):                       # 西港北墙 y=5
    wall_ns(f"bwW_n_{i}", i, 5.0, 0, "cyan")
for i in range(2):                       # 西港南墙 y=3
    wall_ns(f"bwW_s_{i}", i, 3.0, 0, "cyan")

# =================================================================
# 4. 东线轨道 (出珠口 z=3 东缘 y0..1, 顺时针绕塔: 东 -> 南 -> 西)
#    段 1: 东坡道 z3->z2, 栈桥墩双层, 转角台 z=2
# =================================================================
X1 = 2 + SQ3                              # 第一转角台西缘 3.732051
wall_ew("tre_e1a", X1, 0, 0, "gray")      # 栈桥墩下层
wall_ew("tre_e1b", X1, 0, 1, "gray")      # 栈桥墩上层, 顶边接坡尾
wall_ew("tre_e1c", X1 + 1, 0, 0, "gray")  # 外缘门式立柱下层 (R9 抖动加固)
wall_ew("tre_e1d", X1 + 1, 0, 1, "gray")  # 外缘门式立柱上层, 顶边接转角台东缘
ramp("ramp_e1", "+x", 2.0, 0, 3.0, "orange")
flat("cor_e1", X1, 0, 2.0, "yellow")      # 转角台: 西缘与坡尾/墩顶三件互吸, 东缘压立柱顶
rail_ew("rail_e1_out", X1 + 1, 0, 2.0, "red")     # 外侧挡珠
rail_ns("rail_e1_n", X1, 1.0, 2.0, "red")         # 北侧挡珠 (逼珠南转)

#    段 2: 南坡道 z2->z1, 单层栈桥墩, 转角台 z=1
Y2 = -SQ3                                 # 第二转角台北缘 -1.732051
wall_ns("tre_e2", X1, Y2, 0, "gray")
ramp("ramp_e2", "-y", 0.0, X1, 2.0, "orange")
flat("cor_e2", X1, Y2 - 1, 1.0, "yellow")
rail_ew("rail_e2_out", X1 + 1, Y2 - 1, 1.0, "red")
rail_ns("rail_e2_s", X1, Y2 - 1, 1.0, "red")      # 南侧挡珠 (逼珠西转)

#    段 3: 西向冲线坡道 z1->落地, 坡尾停在 x=2, 弹珠滚入东接珠港
ramp("ramp_e3", "-x", X1, Y2 - 1, 1.0, "orange")

# =================================================================
# 5. 西线轨道: 与东线严格镜像 (出珠口 z=3 西缘 y1..2, 逆时针绕塔)
# =================================================================
X2 = -SQ3                                 # 西线第一转角台东缘 -1.732051
wall_ew("tre_w1a", X2, 1, 0, "gray")
wall_ew("tre_w1b", X2, 1, 1, "gray")
wall_ew("tre_w1c", X2 - 1, 1, 0, "gray")  # 外缘门式立柱下层 (与东线镜像)
wall_ew("tre_w1d", X2 - 1, 1, 1, "gray")  # 外缘门式立柱上层, 顶边接转角台西缘
ramp("ramp_w1", "-x", 0.0, 1, 3.0, "orange")
flat("cor_w1", X2 - 1, 1, 2.0, "yellow")
rail_ew("rail_w1_out", X2 - 1, 1, 2.0, "red")
rail_ns("rail_w1_s", X2 - 1, 1.0, 2.0, "red")     # 南侧挡珠 (逼珠北转)

Y3 = 2 + SQ3                              # 西线第二转角台南缘 3.732051
wall_ns("tre_w2", X2 - 1, Y3, 0, "gray")
ramp("ramp_w2", "+y", 2.0, X2 - 1, 2.0, "orange")
flat("cor_w2", X2 - 1, Y3, 1.0, "yellow")
rail_ew("rail_w2_out", X2 - 1, Y3, 1.0, "red")
rail_ns("rail_w2_n", X2 - 1, Y3 + 1, 1.0, "red")  # 北侧挡珠 (逼珠东转)

ramp("ramp_w3", "+x", X2, Y3, 1.0, "orange")      # 冲线坡道, 坡尾停在 x=0

# =================================================================
# 6. 装饰: 接珠港六边形靶标 + 竖长方形冲线旗门
# =================================================================
add("hex_e", "hexagon", (0.5, -3.0, 1 + HEX_CENTROID), (90, 0, 0), "yellow")
add("hex_w", "hexagon", (1.5, 5.0, 1 + HEX_CENTROID), (90, 0, 0), "yellow")
add("ban_e", "rectangle", (0.0, -2.5, 2.0), (0, -90, 0), "pink")   # 东港旗门 x=0
add("ban_w", "rectangle", (2.0, 4.5, 2.0), (0, -90, 0), "pink")    # 西港旗门 x=2

# =================================================================
# 教程步骤 (19 步)
# 步骤内 tiles_to_add 顺序 = 真人放片顺序 (装配可达规则 R7):
# 轨道按"挡珠围栏 -> 桥墩 -> 坡道 -> 转角台"分段成组安装,
# 每个转角的挡珠围栏单独一步 —— 它决定弹珠的转向, 值得专门讲清楚。
# =================================================================
steps = []


def step(description, tiles_to_add, highlight=(), tip=""):
    steps.append({
        "step_number": len(steps) + 1,
        "description": description,
        "tip": tip,
        "tiles_to_add": list(tiles_to_add),
        "highlight_tiles": list(highlight),
    })


step(
    "铺设塔基: 桌面中央平放 2x2 共 4 片正方形, 相邻边互相吸合。",
    [f"g_{i}_{j}" for j in range(2) for i in range(2)],
    tip="塔基周围要留足空地: 东西两条轨道各需约三格宽的场地。",
)
step(
    "铺设东侧场地: 塔基南面接 2 片灰色广场, 再向南铺 4 片蓝色接珠港地台。",
    ["pe_0", "pe_1", "fe_0_1", "fe_1_1", "fe_0_2", "fe_1_2"],
    highlight=["g_0_0", "g_1_0"],
    tip="广场片先吸住塔基南缘, 港区地台再一排一排向南延伸。",
)
step(
    "铺设西侧场地: 塔基北面接 2 片广场, 再向北铺 4 片接珠港地台, 与东侧对称。",
    ["pw_0", "pw_1", "fw_0_1", "fw_1_1", "fw_0_2", "fw_1_2"],
    highlight=["g_0_1", "g_1_1"],
    tip="东西两侧场地完全镜像 —— 这是双轨竞速的跑道地基。",
)
step(
    "发球塔第 1 层: 沿塔基四周立 8 片绿色正方形, 转角竖边两两互吸。",
    ["tw0_s_0", "tw0_s_1", "tw0_w_0", "tw0_w_1",
     "tw0_n_0", "tw0_n_1", "tw0_e_0", "tw0_e_1"],
    highlight=[f"g_{i}_{j}" for j in range(2) for i in range(2)],
    tip="每面 2 片, 四角都要互相吸住; 合围后轻推应整体联动。",
)
step(
    "发球塔第 2 层: 在第 1 层墙顶再立 8 片青色正方形, 上下边完整贴合。",
    ["tw1_s_0", "tw1_s_1", "tw1_w_0", "tw1_w_1",
     "tw1_n_0", "tw1_n_1", "tw1_e_0", "tw1_e_1"],
    highlight=["tw0_s_0", "tw0_e_0"],
    tip="第二层与第一层完全对齐, 磁条整边贴合吸力才最强。",
)
step(
    "发球塔第 3 层: 再向上立 8 片, 塔身升到三层高。",
    ["tw2_s_0", "tw2_s_1", "tw2_w_0", "tw2_w_1",
     "tw2_n_0", "tw2_n_1", "tw2_e_0", "tw2_e_1"],
    highlight=["tw1_s_0", "tw1_e_0"],
    tip="塔越高越要轻放: 一手扶住下层塔身, 另一手放片。",
)
step(
    "盖上发球台: 塔顶平铺 4 片黄色正方形, 四周边缘都吸在第 3 层墙顶上。",
    ["plat_0_0", "plat_1_0", "plat_0_1", "plat_1_1"],
    highlight=["tw2_s_0", "tw2_n_0", "tw2_w_0", "tw2_e_0"],
    tip="发球台就是赛道起点 —— 弹珠从这里同时出发。",
)
step(
    "安装发球台围栏: 北缘立 2 根紫色高塔柱, 南缘 2 片红三角; 东缘只拦北半格、"
    "西缘只拦南半格 —— 空出的两个缺口就是东西赛道的出珠口。",
    ["prail_n_0", "prail_n_1", "prail_s_0", "prail_s_1", "prail_e", "prail_w"],
    highlight=["plat_0_0", "plat_1_1"],
    tip="出珠口一东一西、一南一北错开, 两颗弹珠不会在台上相撞。",
)
step(
    "东接珠港围墙: 西、南、北三面各立 2 片青色矮墙, 东面敞开迎接冲线弹珠。",
    ["bwE_w_1", "bwE_w_2", "bwE_s_0", "bwE_s_1", "bwE_n_0", "bwE_n_1"],
    highlight=["fe_0_1", "fe_1_2"],
    tip="围墙底边吸港区地台边缘; 三面围合后弹珠冲进来就跑不掉了。",
)
step(
    "西接珠港围墙: 东、北、南三面各立 2 片, 西面敞开, 与东港镜像。",
    ["bwW_e_1", "bwW_e_2", "bwW_n_0", "bwW_n_1", "bwW_s_0", "bwW_s_1"],
    highlight=["fw_0_1", "fw_1_2"],
    tip="两座接珠港分别面向自己的赛道终点方向敞开。",
)
step(
    "东线第 1 段 (整段成组安装): 先在塔东侧立双层灰色栈桥墩, 再在墩外一格立"
    "双层门式立柱, 把橙色坡道顶边整边吸在发球台东缘出珠口, 坡尾搭上墩顶, "
    "最后铺黄色转角台 —— 西缘压住墩顶与坡尾, 东缘压住立柱顶。",
    ["tre_e1a", "tre_e1b", "tre_e1c", "tre_e1d", "ramp_e1", "cor_e1"],
    highlight=["plat_1_0", "tw2_e_0"],
    tip="桥墩与立柱像门框一样从两侧顶住转角台: 台面两条边都有支撑才扛得住碰撞。",
)
step(
    "东线第 1 转角挡珠: 转角台外缘与北缘各装 1 片红色挡珠三角, 逼弹珠向南转弯。",
    ["rail_e1_out", "rail_e1_n"],
    highlight=["cor_e1"],
    tip="挡珠三角立在弹珠冲来的方向, 弹珠撞上它就会拐进下一段坡道。",
)
step(
    "东线第 2 段: 立第二座栈桥墩, 南向坡道从转角台南缘下探, 再铺第二块转角台"
    "压住墩顶与坡尾。",
    ["tre_e2", "ramp_e2", "cor_e2"],
    highlight=["cor_e1", "tre_e1b"],
    tip="仍然是桥墩-坡道-转角台三件互吸的三角刚性节点, 装完轻摇应纹丝不动。",
)
step(
    "东线冲线段: 第二转角台装外缘与南缘挡珠三角, 最后一片冲线坡道从台西缘"
    "直落地面 —— 弹珠将沿它冲进东接珠港!",
    ["rail_e2_out", "rail_e2_s", "ramp_e3"],
    highlight=["cor_e2", "bwE_n_0"],
    tip="冲线坡道顶边吸台缘, 坡尾自然落地, 不需要任何支撑。",
)
step(
    "西线第 1 段: 与东线镜像 —— 塔西侧立双层栈桥墩与双层门式立柱, 坡道吸住"
    "发球台西缘出珠口, 转角台两缘分别压住墩顶/坡尾与立柱顶。",
    ["tre_w1a", "tre_w1b", "tre_w1c", "tre_w1d", "ramp_w1", "cor_w1"],
    highlight=["plat_0_1", "tw2_w_1"],
    tip="对照东线检查: 西线每一件都应出现在镜像位置上。",
)
step(
    "西线第 1 转角挡珠: 转角台外缘与南缘各装 1 片红色挡珠三角, 逼弹珠向北转弯。",
    ["rail_w1_out", "rail_w1_s"],
    highlight=["cor_w1"],
    tip="注意方向与东线相反: 西线的弹珠要被逼着向北拐。",
)
step(
    "西线第 2 段: 立栈桥墩, 北向坡道从转角台北缘下探, 铺第二块转角台。",
    ["tre_w2", "ramp_w2", "cor_w2"],
    highlight=["cor_w1", "tre_w1b"],
    tip="西线绕塔方向与东线相反 —— 两条轨道像双螺旋一样对称盘下。",
)
step(
    "西线冲线段: 第二转角台装外缘与北缘挡珠三角, 最后一片冲线坡道从台东缘"
    "直落地面, 弹珠将沿它冲进西接珠港。",
    ["rail_w2_out", "rail_w2_n", "ramp_w3"],
    highlight=["cor_w2", "bwW_e_1"],
    tip="与东线冲线段镜像: 坡道顶边吸台缘, 坡尾自然落地。",
)
step(
    "装饰与旗门: 两港港尾各挂 1 片六边形靶标, 港口立粉色冲线旗门 —— "
    "双轨竞速滚珠塔完工, 放珠开赛!",
    ["hex_e", "ban_e", "hex_w", "ban_w"],
    highlight=["bwE_s_0", "bwW_n_1"],
    tip="两颗弹珠同时从发球台放下, 听哪边先撞响旗门 —— 每次比赛结果都不一样。",
)

# ---- 汇总与输出 --------------------------------------------------
placed = [t for s in steps for t in s["tiles_to_add"]]
assert len(placed) == len(tiles) == len(set(placed)), "步骤必须恰好覆盖全部磁力片"
assert len(tiles) >= 70, f"滚珠塔片数 {len(tiles)} 低于旗舰标准 70"
assert len(steps) >= 16, f"滚珠塔步数 {len(steps)} 低于旗舰标准 16"

# BOM 备料清单: tests/test_model_logic.py 会核对该清单与 final_assembly 完全一致
bom: dict[str, int] = {}
for t in tiles:
    bom[t["type"]] = bom.get(t["type"], 0) + 1
bom = dict(sorted(bom.items(), key=lambda kv: (-kv[1], kv[0])))

model = {
    "schema_version": 1,
    "id": "ball_run_tower_01",
    "name": "螺旋滚珠塔",
    "name_en": "Spiral Ball Run Tower 01",
    "description": (
        "双轨竞速弹珠机: 三层发球塔向东西两侧甩出严格镜像的双螺旋轨道, 每段 30 度"
        "坡道的顶边整边吸在平台沿口、坡尾由栈桥墩接住, 弹珠沿 东坡道-转角-南坡道-"
        "转角-冲线坡道 盘旋而下冲进接珠港。两颗弹珠同时出发, 听哪边先撞响旗门 —— "
        "这不是看的模型, 是每天都会拿出来玩的玩具。"
    ),
    "difficulty": 4,
    "total_pieces": len(tiles),
    "tags": ["滚珠", "轨道", "竞速", "滚珠乐园", "旗舰", "需要扩展装"],
    "content_meta": {
        "structural_signature": {
            "tile_histogram": bom,
        },
    },
    "final_assembly": tiles,
    "steps": steps,
}

out = Path(__file__).resolve().parent.parent / "data" / "models" / "ball_run_tower_01.json"
out.write_text(json.dumps(model, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

by_type = {}
for t in tiles:
    by_type[t["type"]] = by_type.get(t["type"], 0) + 1
print(f"已生成 {out} ({len(tiles)} 片, {len(steps)} 步)")
print("片形统计: " + ", ".join(f"{k} x {v}" for k, v in sorted(by_type.items())))
