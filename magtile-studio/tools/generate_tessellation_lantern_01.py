#!/usr/bin/env python3
"""生成模型 data/models/tessellation_lantern_01.json (密铺柱面灯笼)。

内容批 J 模型 2/4: 几何艺术主题 D1 引流位 —— 与 tessellation_screen_01
(平面 Z 字三折屏风) 形态相异, 本作把密铺立上柱面成灯笼腔体 (满足
J4 "密铺必须立起来"): 2x2 地台之上四面密铺带 (正倒等边三角互咬),
顶口方环收边, 四坡锥顶自锁合拢, 绿色瓜蒂瘦高尖从顶心缝直上。

结构总览 (世界单位: 1.0 = 正方形磁力片边长):
  - 地台 (x [0,2], y [0,2]): 方板 x4 棋盘格                       4 片
  - 四面密铺带 (T18): 每面正三角 x1 + 倒三角 x1, 红橙黄青四色       8 片
  - 顶口方环 (z=1.866): 方板 x4 骑在倒三角上底                      4 片
  - 四坡顶盖 (T13 薄壳): 等腰四坡锥 x4 自锁                         4 片
  - 瓜蒂 + 内衬 + 角饰: 瘦高尖 x1 + 方板 x1 + 侧冠 x2              4 片
  合计 24 片, 8 个教程步骤, 3 种磁力片形状 (全部 CORE-9 之内)。

物理规则要点 (validate 常规 + strict 双档零警告):
  - 正三角底边吸地台沿口, 倒三角两斜边互吸正三角, 悬臂自然消失;
  - 顶环方板底边整边吸倒三角上底, 四边互咬成框;
  - 四坡锥四条斜棱两两互吸自锁, 瓜蒂骑顶心拼缝;
  - 最高点 (瓜蒂顶) 约 3.87, 低于 R8 无桁架高墙红线 4.0。

用法: python3 tools/generate_tessellation_lantern_01.py  (在 magtile-studio 目录下运行)
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from magtile_gen import ModelBuilder  # noqa: E402

b = ModelBuilder()

BT = 1.866025          # 密铺带上沿 (1 + 等边三角形高)
FLOOR_A = "gray"
FLOOR_B = "clear"
STEM = "green"
# 四面密铺色: (正三角, 倒三角)
FACE_TRI = {
    "s": ("red", "orange"),
    "n": ("yellow", "green"),
    "w": ("cyan", "blue"),
    "e": ("purple", "pink"),
}


def down_tri_ns(tid, xc, y, color):
    """倒等边三角 (南北立面): 上底在高度 BT, 顶点朝下接 z=1 地台顶。"""
    b.place_tri(tid, "equilateral_triangle",
                (xc + 0.5, y, BT), (xc - 0.5, y, BT), (xc, y, 1.0), color)


def down_tri_ew(tid, x, yc, color):
    """倒等边三角 (东西立面)。"""
    b.place_tri(tid, "equilateral_triangle",
                (x, yc - 0.5, BT), (x, yc + 0.5, BT), (x, yc, 1.0), color)


# =================================================================
# 1. 地台 2x2
# =================================================================
for j in range(2):
    for i in range(2):
        b.flat(f"floor_{i}_{j}", i, j, 0.0, FLOOR_A if (i + j) % 2 else FLOOR_B)

# =================================================================
# 2. 四面密铺带 (T18): 每面 1 正 + 1 倒
# =================================================================
# 南面 y=0
up_s, dn_s = FACE_TRI["s"]
b.crest_ns("up_s0", 0, 0.0, 0.0, up_s)
down_tri_ns("dn_s0", 1.0, 0.0, dn_s)
# 北面 y=2
up_n, dn_n = FACE_TRI["n"]
b.crest_ns("up_n0", 0, 2.0, 0.0, up_n)
down_tri_ns("dn_n0", 1.0, 2.0, dn_n)
# 西面 x=0
up_w, dn_w = FACE_TRI["w"]
b.crest_ew("up_w0", 0.0, 0, 0.0, up_w)
down_tri_ew("dn_w0", 0.0, 1.0, dn_w)
# 东面 x=2
up_e, dn_e = FACE_TRI["e"]
b.crest_ew("up_e0", 2.0, 0, 0.0, up_e)
down_tri_ew("dn_e0", 2.0, 1.0, dn_e)

# =================================================================
# 3. 顶口方环 + 四坡顶盖 (1x1 洞口 [0.5,1.5]x[0.5,1.5])
# =================================================================
b.wall_ns("rim_s", 0.5, 0.5, BT, FLOOR_B)
b.wall_ns("rim_n", 0.5, 1.5, BT, FLOOR_A)
b.wall_ew("rim_w", 0.5, 0.5, BT, FLOOR_B)
b.wall_ew("rim_e", 1.5, 0.5, BT, FLOOR_A)
b.hat4("roof", 0, 0, BT, "yellow", shape="isosceles_triangle")

# =================================================================
# 4. 瓜蒂 + 内衬 + 角饰
# =================================================================
b.flat("inner", 1, 1, 0.0, FLOOR_A)                   # 腔底内衬
b.spire_ns("stem", 1, 1.0, BT + 1.936492, STEM)     # 瓜蒂 (骑锥尖上)
b.crest_ns("fin_s", 0, 0.0, BT, "red")
b.crest_ns("fin_n", 1, 2.0, BT, "red")

# =================================================================
# 教程步骤 (8 步)
# =================================================================
b.step(
    "铺地台: 四片清灰相间的方板拼成 2x2 底座 —— 灯笼从这里长起来。",
    ["floor_0_0", "floor_0_1", "floor_1_0", "floor_1_1"],
    tip="地台四边等长 —— 等会儿密铺三角就贴在这些沿口上。",
)
b.step(
    "砌南/北密铺带: 各立一片正三角, 再倒插一片倒三角进缺口 —— 咔哒互咬。",
    ["up_s0", "dn_s0", "up_n0", "dn_n0"],
    highlight=["floor_0_0", "floor_0_1"],
    tip="倒三角两条斜边同时贴住正三角 —— 这就是密铺! 只不过这次是立着的。",
)
b.step(
    "砌西/东密铺带: 换 cyan/blue 与 purple/pink, 四面花纹各不同。",
    ["up_w0", "dn_w0", "up_e0", "dn_e0"],
    highlight=["floor_0_0", "floor_1_0"],
    tip="从上方看, 四面像四段不同颜色的腰带绕成一圈。",
)
b.step(
    "架顶口方环: 四片方板骑在倒三角上底, 竖边互吸围出 1x1 顶口。",
    ["rim_s", "rim_n", "rim_w", "rim_e"],
    highlight=["dn_s0", "dn_n0"],
    tip="顶口不封死 —— 灯光从里面透出来, 才是灯笼。",
)
b.step(
    "合四坡顶盖: 四片黄色瘦高三角围成锥顶, 四条斜棱两两互吸自锁。",
    ["roof_s", "roof_e", "roof_n", "roof_w"],
    highlight=["rim_s", "rim_e"],
    tip="锥顶和整理站照片框顶花同款几何 —— 四棱自锁, 轻推不晃。",
)
b.step(
    "装内衬: 一片方板平放在腔底正中 —— 蜡烛/灯珠就坐在这里。",
    ["inner"],
    highlight=["floor_1_1"],
    tip="内衬让灯光不直接贴地 —— 也加重心, 灯笼更稳。",
)
b.step(
    "立瓜蒂: 绿色瘦高尖从锥尖顶心拼缝直上 —— 密铺灯笼有了冒。",
    ["stem"],
    highlight=["roof_s"],
    tip="瓜蒂只吸一条缝 —— 纯装饰, 但一眼就知道这是灯笼不是塔。",
)
b.step(
    "角饰收尾: 南北各一片红色小冠骑在密铺带顶沿 —— 柱面灯笼完工!",
    ["fin_s", "fin_n"],
    highlight=["up_s0", "up_n0"],
    tip="点灯试试! 密铺花纹会把四色光斑投在桌面上 —— 比屏风更小巧。",
)

b.finalize(
    model_id="tessellation_lantern_01",
    name="密铺柱面灯笼",
    name_en="Tessellation Lantern 01",
    description=(
        "几何艺术 D1 引流作: 正倒等边三角密铺不铺地面, 竖着砌进四面"
        "柱面围成灯笼腔体 —— 红橙、黄绿、青蓝、紫粉四段花纹上下互咬, "
        "顶口方环收边后四坡锥顶自锁合拢, 绿色瓜蒂从顶心缝直上; 与"
        "平面 Z 字屏风完全不同 —— 这次密铺绕成一圈, 像能点灯的小灯笼。"
    ),
    difficulty=1,
    tags=["几何艺术", "密铺", "灯笼", "柱面", "光影"],
    min_pieces=24,
    min_steps=8,
)
