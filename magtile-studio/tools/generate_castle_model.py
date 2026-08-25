#!/usr/bin/env python3
"""生成示例模型 data/models/castle_foundation_01.json (城堡地基与城墙)。

模型结构 (世界单位: 1.0 = 正方形磁力片边长):
  - 4x4 正方形地台 (z = 0 平面)                          16 片
  - 四面城墙第 1 层 (z 0~1) + 第 2 层 (z 1~2)             32 片
  - 四角角楼第 3 层 (z 2~3, 每角 2 片成 L 形)              8 片
  - 角楼顶城齿 (等边三角形, 底边 z = 3)                    8 片
  - 城墙中段城齿 (等边三角形, 底边 z = 2)                  8 片
  合计 72 片, 16 个教程步骤。

坐标约定与 C++ 端一致 (include/magtile/core/tile_instance.hpp):
  旋转为欧拉角 (度), 施加顺序 R = Rz * Ry * Rx。
  平铺片 rot = (0,0,0); 南北向立片 rot = (90,0,0); 东西向立片 rot = (90,0,90)。

用法: python3 tools/generate_castle_model.py  (在 magtile-studio 目录下运行)
"""

import json
import math
from pathlib import Path

# 等边三角形质心到底边的距离 (与 data/tile_catalog.json 中的顶点一致)
TRI_CENTROID = round(math.sqrt(3) / 6, 6)  # 0.288675

SIZE = 4  # 地台为 SIZE x SIZE 个正方形

tiles = []


def add(tile_id, tile_type, pos, rot, color):
    tiles.append({
        "id": tile_id,
        "type": tile_type,
        "position": [round(v, 6) for v in pos],
        "rotation": [round(v, 6) for v in rot],
        "color": color,
    })


# ---- 1. 地台: 4x4 平铺正方形, 蓝青棋盘格 ------------------------
for j in range(SIZE):
    for i in range(SIZE):
        color = "blue" if (i + j) % 2 == 0 else "cyan"
        add(f"g_{i}_{j}", "square", (i + 0.5, j + 0.5, 0.0), (0, 0, 0), color)

# ---- 2. 城墙第 1、2 层: 沿地台四周竖立正方形 --------------------
# side -> (每段中心坐标函数, 旋转)
WALL_SIDES = {
    "s": (lambda k, zc: (k + 0.5, 0.0, zc), (90, 0, 0)),   # 南墙, 平面 y=0
    "n": (lambda k, zc: (k + 0.5, float(SIZE), zc), (90, 0, 0)),   # 北墙, 平面 y=4
    "w": (lambda k, zc: (0.0, k + 0.5, zc), (90, 0, 90)),  # 西墙, 平面 x=0
    "e": (lambda k, zc: (float(SIZE), k + 0.5, zc), (90, 0, 90)),  # 东墙, 平面 x=4
}
COURSE_COLOR = {1: "red", 2: "orange"}

for course in (1, 2):
    zc = course - 0.5
    for side, (center, rot) in WALL_SIDES.items():
        for k in range(SIZE):
            add(f"w{course}_{side}_{k}", "square", center(k, zc), rot, COURSE_COLOR[course])

# ---- 3. 四角角楼第 3 层: 每角两片成 L 形 ------------------------
CORNER_SEGMENTS = [
    ("s", 0), ("w", 0),          # 西南角
    ("s", SIZE - 1), ("e", 0),   # 东南角
    ("n", 0), ("w", SIZE - 1),   # 西北角
    ("n", SIZE - 1), ("e", SIZE - 1),  # 东北角
]
for side, k in CORNER_SEGMENTS:
    center, rot = WALL_SIDES[side]
    add(f"w3_{side}_{k}", "square", center(k, 2.5), rot, "purple")

# ---- 4. 角楼顶城齿: 等边三角形, 底边落在 z=3 --------------------
for side, k in CORNER_SEGMENTS:
    center, rot = WALL_SIDES[side]
    x, y, _ = center(k, 0)
    add(f"bt_{side}_{k}", "equilateral_triangle", (x, y, 3.0 + TRI_CENTROID), rot, "yellow")

# ---- 5. 城墙中段城齿: 等边三角形, 底边落在 z=2 ------------------
MID_SEGMENTS = [(side, k) for side in ("s", "n", "w", "e") for k in (1, 2)]
for side, k in MID_SEGMENTS:
    center, rot = WALL_SIDES[side]
    x, y, _ = center(k, 0)
    add(f"bm_{side}_{k}", "equilateral_triangle", (x, y, 2.0 + TRI_CENTROID), rot, "green")

# ---- 教程步骤 ----------------------------------------------------
SIDE_NAME = {"s": "南", "n": "北", "w": "西", "e": "东"}
steps = []


def step(description, tiles_to_add, highlight=(), tip=""):
    steps.append({
        "step_number": len(steps) + 1,
        "description": description,
        "tip": tip,
        "tiles_to_add": list(tiles_to_add),
        "highlight_tiles": list(highlight),
    })


# 步骤 1~4: 逐排铺设地台
for j in range(SIZE):
    prev_row = [f"g_{i}_{j - 1}" for i in range(SIZE)] if j > 0 else []
    step(
        f"在平整桌面上铺设地台第 {j + 1} 排: 将 4 片正方形平放并排, 相邻边对齐吸合。",
        [f"g_{i}_{j}" for i in range(SIZE)],
        highlight=prev_row,
        tip="第一排请沿桌面边缘摆直, 后续每排紧贴上一排, 听到轻微磁吸声即为到位。" if j == 0
            else "新一排的每条边都要与上一排完全对齐, 避免地台出现缝隙。",
    )

# 步骤 5~8: 城墙第 1 层
WALL_BASE_HIGHLIGHT = {
    "s": [f"g_{i}_0" for i in range(SIZE)],
    "n": [f"g_{i}_{SIZE - 1}" for i in range(SIZE)],
    "w": [f"g_0_{j}" for j in range(SIZE)],
    "e": [f"g_{SIZE - 1}_{j}" for j in range(SIZE)],
}
for side in ("s", "n", "w", "e"):
    step(
        f"沿地台{SIDE_NAME[side]}侧边缘竖起第 1 层城墙: 4 片正方形逐一立起, "
        f"底边与地台边缘吸合, 相邻墙片侧边也要互相吸住。",
        [f"w1_{side}_{k}" for k in range(SIZE)],
        highlight=WALL_BASE_HIGHLIGHT[side],
        tip="立片时用一只手扶住地台, 另一只手将墙片垂直放下, 先对准底边再松手。",
    )

# 步骤 9~12: 城墙第 2 层
for side in ("s", "n", "w", "e"):
    step(
        f"在{SIDE_NAME[side]}墙上叠加第 2 层: 4 片正方形对齐下层墙片顶边逐一吸合。",
        [f"w2_{side}_{k}" for k in range(SIZE)],
        highlight=[f"w1_{side}_{k}" for k in range(SIZE)],
        tip="第二层要与第一层完全对齐, 上下边完整贴合磁力才最强。",
    )

# 步骤 13~14: 四角角楼第 3 层
step(
    "建造南侧两座角楼: 在西南角与东南角各竖起 2 片紫色正方形 (第 3 层), "
    "两片在转角处互相垂直并吸住彼此的竖边, 形成稳固的 L 形。",
    ["w3_s_0", "w3_w_0", "w3_s_3", "w3_e_0"],
    highlight=["w2_s_0", "w2_w_0", "w2_s_3", "w2_e_0"],
    tip="转角处两片互相吸住后结构会明显变稳, 若晃动说明竖边没有贴合。",
)
step(
    "建造北侧两座角楼: 在西北角与东北角同样各竖起 2 片紫色正方形, 与南侧对称。",
    ["w3_n_0", "w3_w_3", "w3_n_3", "w3_e_3"],
    highlight=["w2_n_0", "w2_w_3", "w2_n_3", "w2_e_3"],
    tip="完成后从上往下看, 四角应形成四个对称的直角。",
)

# 步骤 15: 角楼顶城齿
step(
    "为四座角楼装上黄色三角城齿: 8 片等边三角形底边分别吸在角楼顶边上, 尖角朝天。",
    [f"bt_{side}_{k}" for side, k in CORNER_SEGMENTS],
    highlight=[f"w3_{side}_{k}" for side, k in CORNER_SEGMENTS],
    tip="三角形只需底边吸合即可站稳, 摆放时捏住尖角轻轻放下。",
)

# 步骤 16: 城墙中段城齿
step(
    "最后为四面城墙的中段装上绿色三角城齿 (每面 2 片), 完成整段城堡地基与城墙。",
    [f"bm_{side}_{k}" for side, k in MID_SEGMENTS],
    highlight=[f"w2_{side}_{k}" for side, k in MID_SEGMENTS],
    tip="全部完成后轻推墙体检查: 结构应整体联动而不散架。",
)

# ---- 汇总与输出 --------------------------------------------------
placed = [t for s in steps for t in s["tiles_to_add"]]
assert len(placed) == len(tiles) == len(set(placed)), "步骤必须恰好覆盖全部磁力片"

model = {
    "schema_version": 1,
    "id": "castle_foundation_01",
    "name": "城堡地基与城墙",
    "name_en": "Castle Foundation 01",
    "description": (
        "经典城堡系列第一课: 从 4x4 地台开始, 逐层搭建双层围墙、四角角楼与三角城齿, "
        "学习磁力片建筑最重要的三个技巧 —— 平铺打底、垂直立墙、逐层加高。"
    ),
    "difficulty": 3,
    "total_pieces": len(tiles),
    "tags": ["城堡", "建筑基础", "进阶"],
    "final_assembly": tiles,
    "steps": steps,
}

out = Path(__file__).resolve().parent.parent / "data" / "models" / "castle_foundation_01.json"
out.write_text(json.dumps(model, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(f"已生成 {out} ({len(tiles)} 片, {len(steps)} 步)")
