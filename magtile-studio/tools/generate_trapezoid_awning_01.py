#!/usr/bin/env python3
"""生成模型 data/models/trapezoid_awning_01.json (梯形雨檐花架墙)。

内容批 P 模型 5/10 (P5): 植物花园主题 D2, 主打片型 trapezoid ——
重写版。招牌是"一面墙上的三层梯形": 4 格宽的花架墙沿口挑出两片
30 度下斜的梯形雨檐, 檐间墙脊立两片梯形女儿墙 (下宽上窄的经典
收分轮廓); 半墙高的拼缝上再平挑两片梯形展台托起盆花; 地面步道
前沿铺两片梯形扇贝形包边 —— 同一种梯形, 斜披 / 直立 / 平挑 / 平铺
四种姿态各司其职。与旧版 (连廊两侧上斜密铺条带) 的"廊"字逻辑
完全不同: 本作是"墙", 所有梯形都长在一面花架墙及其步道上。

结构总览 (世界单位: 1.0 = 正方形磁力片边长, 墙在北、花园朝南):
  - 步道 (4x1): 灰色长方形 x2                                   2 片
  - 花圃带 (4x1): 泥土方板 x4 + 两端碎石方板 x2 + 骑缝三角花 x5 11 片
  - 花架墙 (z 0..2): 长方形横砌 x4 (每层 2 片) + 侧翼护墙 x2     6 片
  - 梯形展台层 (z=1): 平挑梯形 x2 + 台上三角盆花 x2              4 片
  - 梯形檐口层 (z=2): 下斜雨檐 x2 + 直立女儿墙 x2                4 片
  - 步道包边 (z=0): 平铺梯形 x2 + 檐前三角花 x2                  4 片
  合计 31 片, 8 个教程步骤, 4 种磁力片形状 (含扩展梯形 x8)。

物理规则要点 (validate 常规 + strict 双档零警告):
  - 花架墙用长方形横砌: 每层两片、层间与层内边等长互吸成环,
    梯形下底 (长 2) 与长方形横边 (长 2) 恰好等长 —— 这是本作
    所有梯形整边吸合的几何前提;
  - 平挑展台: 下底吸墙腰拼缝 (缝两侧上下两层各一条连接), 单片
    力矩 15g·单位, 连同盆花 26g·单位 < 预算 70g·单位;
  - 下斜雨檐: 下底吸墙顶, 与同段女儿墙下底共线双连接; 剪断墙顶
    铰链线后单片力矩 13g·单位, 远低于预算;
  - 女儿墙尖端 2.87 触发 R8: 墙体横砌环 + 展台双缝连接提供环状
    加固, 无单点失效损失 >= 3 片。

用法: python3 tools/generate_trapezoid_awning_01.py  (在 magtile-studio 目录下运行)
"""

import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from magtile_gen import TRAP_H, ModelBuilder  # noqa: E402

b = ModelBuilder()

WALK = "gray"        # 步道长石板
SOIL = "orange"      # 花圃泥土
GRAVEL = "yellow"    # 花圃两端碎石
WALL = "green"       # 花架墙横砌长方形
WING = "green"       # 侧翼护墙
SHELF = "yellow"     # 平挑梯形展台
AWNING = "green"     # 下斜梯形雨檐
PARAPET = "clear"    # 直立梯形女儿墙 (透光)
APRON = "green"      # 步道梯形包边
BED_FLOWERS = ["red", "purple", "pink", "purple", "red"]
SHELF_FLOWERS = ["pink", "red"]
APRON_FLOWERS = ["yellow", "purple"]

WALL_Y = 2.0                     # 花架墙平面
SLOPE = math.radians(30)         # 雨檐下斜角 (30 度)


# =================================================================
# 1. 步道 (y [0,1]): 两片灰色长方形
# =================================================================
b.flat_rect("walk_w", 0, 0, 0.0, WALK)
b.flat_rect("walk_e", 2, 0, 0.0, WALK)

# =================================================================
# 2. 花圃带 (y [1,2]): 泥土 x4 + 两端碎石 x2, 骑缝三角花 x5
# =================================================================
for x in range(4):
    b.flat(f"bed_{x}", x, 1, 0.0, SOIL)
b.flat("gravel_w", -1, 1, 0.0, GRAVEL)
b.flat("gravel_e", 4, 1, 0.0, GRAVEL)
for i, x in enumerate((0, 1, 2, 3, 4)):
    b.crest_ew(f"flower_{x}", float(x), 1, 0.0, BED_FLOWERS[i])

# =================================================================
# 3. 花架墙 (平面 y=2): 长方形横砌两层 + 两端侧翼护墙
# =================================================================
b.lintel_ns("wall_w0", 0, WALL_Y, 0, WALL)
b.lintel_ns("wall_e0", 2, WALL_Y, 0, WALL)
b.lintel_ns("wall_w1", 0, WALL_Y, 1, WALL)
b.lintel_ns("wall_e1", 2, WALL_Y, 1, WALL)
b.wall_ew("wing_w", 0.0, 2, 0, WING)
b.wall_ew("wing_e", 4.0, 2, 0, WING)

# =================================================================
# 4. 梯形展台层 (z=1): 平挑梯形 x2 骑墙腰拼缝, 台上盆花
# =================================================================
b.place_edge("shelf_w", "trapezoid", 0,
             (0.0, WALL_Y, 1.0), (2.0, WALL_Y, 1.0), (0, -1, 0), SHELF)
b.place_edge("shelf_e", "trapezoid", 0,
             (2.0, WALL_Y, 1.0), (4.0, WALL_Y, 1.0), (0, -1, 0), SHELF)
b.crest_ns("pot_w", 0.5, WALL_Y - TRAP_H, 1.0, SHELF_FLOWERS[0])
b.crest_ns("pot_e", 2.5, WALL_Y - TRAP_H, 1.0, SHELF_FLOWERS[1])

# =================================================================
# 5. 檐口层 (z=2): 下斜雨檐 x2 + 直立女儿墙 x2 (下底共线双连接)
# =================================================================
AW_HINT = (0.0, -math.cos(SLOPE), -math.sin(SLOPE))
b.place_edge("awning_w", "trapezoid", 0,
             (0.0, WALL_Y, 2.0), (2.0, WALL_Y, 2.0), AW_HINT, AWNING)
b.place_edge("awning_e", "trapezoid", 0,
             (2.0, WALL_Y, 2.0), (4.0, WALL_Y, 2.0), AW_HINT, AWNING)
b.place_edge("parapet_w", "trapezoid", 0,
             (0.0, WALL_Y, 2.0), (2.0, WALL_Y, 2.0), (0, 0, 1), PARAPET)
b.place_edge("parapet_e", "trapezoid", 0,
             (2.0, WALL_Y, 2.0), (4.0, WALL_Y, 2.0), (0, 0, 1), PARAPET)

# =================================================================
# 6. 步道包边 (z=0): 平铺梯形 x2 + 檐前三角花 x2
# =================================================================
b.place_edge("apron_w", "trapezoid", 0,
             (0.0, 0.0, 0.0), (2.0, 0.0, 0.0), (0, -1, 0), APRON)
b.place_edge("apron_e", "trapezoid", 0,
             (2.0, 0.0, 0.0), (4.0, 0.0, 0.0), (0, -1, 0), APRON)
b.crest_ns("tuft_w", 0.5, -TRAP_H, 0.0, APRON_FLOWERS[0])
b.crest_ns("tuft_e", 2.5, -TRAP_H, 0.0, APRON_FLOWERS[1])

# =================================================================
# 教程步骤 (8 步)
# =================================================================
b.step(
    "铺步道: 两片灰色长石板整边互吸, 连成 4 格长的赏花步道。",
    ["walk_w", "walk_e"],
    tip="长石板的 2 格横边一会儿正好给梯形包边当吸合线。",
)
b.step(
    "铺花圃带: 四片泥土方板贴住步道北沿, 两端各补一片黄色碎石板。",
    ["bed_0", "bed_1", "bed_2", "bed_3", "gravel_w", "gravel_e"],
    highlight=["walk_w", "walk_e"],
    tip="花圃拼缝落在每条整数线上 —— 那是花苗的位置。",
)
b.step(
    "种花圃: 五株三角花骑上花圃拼缝, 红紫粉相间排成一行。",
    [f"flower_{x}" for x in (0, 1, 2, 3, 4)],
    highlight=["bed_1", "bed_2"],
    tip="花底边与拼缝等长互吸, 重心正压缝上 —— 一排花墙脚。",
)
b.step(
    "横砌墙第一层: 两片绿色长方形踩住花圃北沿, 两端立侧翼护墙。",
    ["wall_w0", "wall_e0", "wing_w", "wing_e"],
    highlight=["bed_0", "bed_3"],
    tip="长方形横着当砖砌 —— 2 格长的顶边就是梯形的专用吸合位。",
)
b.step(
    "横砌墙第二层: 再两片长方形叠上去, 层间整边互吸砌成花架墙。",
    ["wall_w1", "wall_e1"],
    highlight=["wall_w0", "wall_e0"],
    tip="上下两层对缝叠放, 墙腰 z=1 的横缝留给展台。",
)
b.step(
    "平挑展台: 两片黄色梯形下底吸进墙腰横缝, 台前各摆一株盆花。",
    ["shelf_w", "shelf_e", "pot_w", "pot_e"],
    highlight=["wall_w0", "wall_w1"],
    tip="梯形下底同时吸住缝上下两层长方形 —— 平挑出来也稳。",
)
b.step(
    "装檐口: 两片绿色梯形沿墙顶下斜 30 度当雨檐, 两片透明梯形直立"
    "在同一条沿口当女儿墙。",
    ["awning_w", "awning_e", "parapet_w", "parapet_e"],
    highlight=["wall_w1", "wall_e1"],
    tip="雨檐与女儿墙下底共线, 彼此也互吸 —— 一条沿口双份保险。",
)
b.step(
    "铺步道包边: 两片绿色梯形平铺在步道南沿当扇贝形包边, 檐前再种"
    "两丛三角花 —— 梯形雨檐花架墙落成!",
    ["apron_w", "apron_e", "tuft_w", "tuft_e"],
    highlight=["walk_w", "walk_e"],
    tip="斜披、直立、平挑、平铺 —— 同一种梯形摆出四种姿态。",
)

b.finalize(
    model_id="trapezoid_awning_01",
    name="梯形雨檐花架墙",
    name_en="Trapezoid Awning Wall 01",
    description=(
        "植物花园 D2 梯形主打示范: 长方形横砌的 4 格花架墙上, 同一种"
        "梯形摆出四种姿态 —— 墙顶两片 30 度下斜雨檐、同一条沿口两片"
        "直立女儿墙 (下宽上窄的收分轮廓)、墙腰横缝平挑两片盆花展台、"
        "步道南沿再平铺两片扇贝形包边; 花圃带五株骑缝三角花, 檐前两"
        "丛花收边。梯形下底 (长 2) 与长方形横边恰好等长, 是整面墙"
        "整边吸合的几何前提 —— 与旧版连廊密铺条带的动线完全不同。"
    ),
    difficulty=2,
    tags=["植物花园", "花架", "雨檐", "梯形", "进阶"],
    min_pieces=31,
    min_steps=8,
    series="plant_garden",
)
