#!/usr/bin/env python3
"""生成旗舰模型 data/models/skyscraper_01.json (城市摩天大楼)。

内容策略 2.4 节"反幼稚规则"的标杆样板之一 (简报 ⑫):
全库最高剪影 —— 四级旋位退台塔楼, 顶到 z=6.87 (实物近半米)。

结构总览 (世界单位: 1.0 = 正方形磁力片边长):
  - 裙楼 4x4 两层 (z 0..2): 大堂门洞 + 长方形门楣 + 瞭望窗       43 片
  - 一级露台 (z=2 整层楼板) + 南缘女儿墙三角冠                  20 片
  - 二级塔身 3x3 两层 (z 2..4, 向西北旋位) + 斜撑 4 根           24 片
  - 二级露台 (z=4) + 女儿墙                                    12 片
  - 三级塔身 2x2 一层 (z 4..5, 向东北旋位) + 斜撑 2 根            9 片
  - 三级露台 (z=5) + 西缘女儿墙                                  6 片
  - 顶层观景阁 1x1 (z 5..6, 向东南旋位) + 等腰三角锥形金顶        8 片
  合计 122 片, 26 个教程步骤。

招牌技法 (T06 螺旋塔 + T12 层叠退台 + T14 斜撑加固):
  退台不居中收分, 而是绕塔心逐级旋位 (西北 -> 东北 -> 东南),
  退出的露台绕大楼盘旋而上; 每级塔身根部用直角三角形斜撑与
  露台楼板双边吸合锁定 (T14 是结构件, 不是装饰)。

物理规则要点 (通过 R1~R8 全部校验):
  - 每层楼板四周坐在下层墙顶上, 剪断任何单条铰链线仍有正交支撑;
  - 斜撑两条直角边分别吸住露台面与塔身墙竖边, 形成三角刚性节点;
  - 金顶四片等腰三角形底边吸墙顶、四条斜棱两两互吸, 自锁成环。

用法: python3 tools/generate_skyscraper.py  (在 magtile-studio 目录下运行)
"""

import json
import math
from pathlib import Path

TRI_CENTROID = round(math.sqrt(3) / 6, 6)   # 等边三角形质心到底边距离 0.288675
THIRD = 1 / 3

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
    add(tile_id, "square", (x0 + 0.5, y0 + 0.5, z), (0, 0, 0), color)


def wall_ns(tile_id, x0, y, z0, color):
    add(tile_id, "square", (x0 + 0.5, y, z0 + 0.5), (90, 0, 0), color)


def wall_ew(tile_id, x, y0, z0, color):
    add(tile_id, "square", (x, y0 + 0.5, z0 + 0.5), (90, 0, 90), color)


def crest_ns(tile_id, x0, y, z, color):
    """女儿墙三角冠: 等边三角形立在南北向边沿上, 底边落在高度 z。"""
    add(tile_id, "equilateral_triangle", (x0 + 0.5, y, z + TRI_CENTROID), (90, 0, 0), color)


GLASS = ["blue", "cyan"]  # 幕墙层交替配色


# =================================================================
# 1. 裙楼 (Tier 1): 4x4 占地, 两层
# =================================================================
for j in range(4):
    for i in range(4):
        flat(f"g_{i}_{j}", i, j, 0.0, "gray" if (i + j) % 2 == 0 else "cyan")

# 一层墙 (z 0..1): 南面留双开大堂门洞 (x 1..3)
for i in (0, 3):
    wall_ns(f"L1_s_{i}", i, 0.0, 0, "blue")
for j in range(4):
    wall_ew(f"L1_e_{j}", 4.0, j, 0, GLASS[j % 2])
for i in range(4):
    wall_ns(f"L1_n_{i}", i, 4.0, 0, GLASS[i % 2])
for j in range(4):
    wall_ew(f"L1_w_{j}", 0.0, j, 0, GLASS[j % 2])

# 二层墙 (z 1..2): 南面门楣用长方形横跨门洞; 东西各留一扇瞭望窗
for i in (0, 3):
    wall_ns(f"L2_s_{i}", i, 0.0, 1, "blue")
add("L2_lintel", "rectangle", (2.0, 0.0, 1.5), (90, 0, 0), "orange")  # 门楣 x 1..3
for j in (0, 2, 3):   # 窗洞 y 1..2
    wall_ew(f"L2_e_{j}", 4.0, j, 1, GLASS[j % 2])
for i in range(4):
    wall_ns(f"L2_n_{i}", i, 4.0, 1, GLASS[i % 2])
for j in (0, 1, 3):   # 窗洞 y 2..3
    wall_ew(f"L2_w_{j}", 0.0, j, 1, GLASS[j % 2])

# 一级露台楼板 (z=2, 4x4 整层)
for j in range(4):
    for i in range(4):
        flat(f"d1_{i}_{j}", i, j, 2.0, "gray" if (i + j) % 2 == 0 else "blue")

# 一级露台南缘女儿墙 (4 片三角冠)
for i in range(4):
    crest_ns(f"p1_{i}", i, 0.0, 2.0, "yellow")

# =================================================================
# 2. 二级塔身 (Tier 2): 3x3, 旋位至西北 (x 0..3, y 1..4), z 2..4
# =================================================================
# 三层墙 (z 2..3): 南/北各留一扇窗 (x 1..2)
for i in (0, 2):
    wall_ns(f"L3_s_{i}", i, 1.0, 2, GLASS[i % 2])
for j in (1, 2, 3):
    wall_ew(f"L3_e_{j}", 3.0, j, 2, GLASS[j % 2])
for i in (0, 2):
    wall_ns(f"L3_n_{i}", i, 4.0, 2, GLASS[i % 2])
for j in (1, 2, 3):
    wall_ew(f"L3_w_{j}", 0.0, j, 2, GLASS[j % 2])

# 四层墙 (z 3..4): 东/西各留一扇窗 (y 2..3)
for i in range(3):
    wall_ns(f"L4_s_{i}", i, 1.0, 3, GLASS[i % 2])
for j in (1, 3):
    wall_ew(f"L4_e_{j}", 3.0, j, 3, GLASS[j % 2])
for i in range(3):
    wall_ns(f"L4_n_{i}", i, 4.0, 3, GLASS[i % 2])
for j in (1, 3):
    wall_ew(f"L4_w_{j}", 0.0, j, 3, GLASS[j % 2])

# 二级塔身根部斜撑 (T14): 直角三角形, 底边吸露台面, 竖边吸塔身墙竖边
# 南侧露台上两根 (立在平面 x=1 与 x=2 上, 竖边贴 y=1 墙面根部)
add("br2_s_1", "right_triangle", (1.0, 2 * THIRD, 2 + THIRD), (90, 0, 270), "orange")
add("br2_s_2", "right_triangle", (2.0, 2 * THIRD, 2 + THIRD), (90, 0, 270), "orange")
# 东侧露台上两根 (立在平面 y=2 与 y=3 上, 竖边贴 x=3 墙面根部)
add("br2_e_2", "right_triangle", (10 / 3, 2.0, 2 + THIRD), (90, 0, 0), "orange")
add("br2_e_3", "right_triangle", (10 / 3, 3.0, 2 + THIRD), (90, 0, 0), "orange")

# 二级露台楼板 (z=4, 3x3)
for j in range(1, 4):
    for i in range(3):
        flat(f"d2_{i}_{j}", i, j, 4.0, "gray" if (i + j) % 2 == 0 else "blue")

# 二级露台南缘女儿墙 (3 片)
for i in range(3):
    crest_ns(f"p2_{i}", i, 1.0, 4.0, "yellow")

# =================================================================
# 3. 三级塔身 (Tier 3): 2x2, 旋位至东北 (x 1..3, y 2..4), z 4..5
#    西面留一扇窗 (y 2..3)
# =================================================================
for i in (1, 2):
    wall_ns(f"L5_s_{i}", i, 2.0, 4, GLASS[i % 2])
for j in (2, 3):
    wall_ew(f"L5_e_{j}", 3.0, j, 4, GLASS[j % 2])
for i in (1, 2):
    wall_ns(f"L5_n_{i}", i, 4.0, 4, GLASS[i % 2])
wall_ew("L5_w_3", 1.0, 3, 4, GLASS[1])

# 三级塔身斜撑 2 根
add("br3_s", "right_triangle", (2.0, 1 + 2 * THIRD, 4 + THIRD), (90, 0, 270), "orange")
add("br3_w", "right_triangle", (2 * THIRD, 3.0, 4 + THIRD), (90, 0, 180), "orange")

# 三级露台楼板 (z=5, 2x2)
for j in range(2, 4):
    for i in range(1, 3):
        flat(f"d3_{i}_{j}", i, j, 5.0, "gray" if (i + j) % 2 == 0 else "blue")

# 三级露台西缘女儿墙 (2 片, 立在平面 x=1 上)
for j in (2, 3):
    add(f"p3_{j}", "equilateral_triangle", (1.0, j + 0.5, 5 + TRI_CENTROID), (90, 0, 90), "yellow")

# =================================================================
# 4. 顶层观景阁 (Crown): 1x1, 旋位至东南 (x 2..3, y 2..3), z 5..6
# =================================================================
wall_ns("cr_s", 2, 2.0, 5, "purple")
wall_ew("cr_e", 3.0, 2, 5, "purple")
wall_ns("cr_n", 2, 3.0, 5, "purple")
wall_ew("cr_w", 2.0, 2, 5, "purple")

# 锥形金顶: 4 片瘦高等腰三角形 (底 1 高 2) 各内倾 14.48 度,
# 塔尖交汇于 (2.5, 2.5, 7.936); 倾角满足 cos(75.522488°) = 0.25
add("roof_s", "isosceles_triangle", (2.5, 2 + 1 / 6, 6 + 0.645497), (75.522488, 0, 0), "yellow")
add("roof_e", "isosceles_triangle", (3 - 1 / 6, 2.5, 6 + 0.645497), (75.522488, 0, 90), "yellow")
add("roof_n", "isosceles_triangle", (2.5, 3 - 1 / 6, 6 + 0.645497), (104.477512, 0, 0), "yellow")
add("roof_w", "isosceles_triangle", (2 + 1 / 6, 2.5, 6 + 0.645497), (104.477512, 0, 90), "yellow")

# =================================================================
# 教程步骤 (26 步)
# 步骤内 tiles_to_add 顺序 = 真人放片顺序 (装配可达规则 R7):
# 楼板从贴墙一列铺起, 墙从有支撑的一片立起;
# 每层墙体按"两面一步"的节奏合围, 高难模型步子迈小一点。
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
    "铺设大楼地基西半部: 平放 4x2 共 8 片正方形, 相邻边逐一吸合。",
    [f"g_{i}_{j}" for j in range(4) for i in range(2)],
    tip="地基务必铺在平整桌面上, 每片听到轻磁吸声才算到位。",
)
step(
    "补齐地基东半部 (8 片), 连成 4x4 的完整占地。",
    [f"g_{i}_{j}" for j in range(4) for i in range(2, 4)],
    highlight=[f"g_1_{j}" for j in range(4)],
    tip="拼完从侧面看一圈: 16 片应严丝合缝成一个正方形广场。",
)
step(
    "裙楼一层南墙与东墙: 南面只立两端 2 片, 中间空出的两格就是大堂门洞; 东面立满 4 片。",
    ["L1_s_0", "L1_s_3"] + [f"L1_e_{j}" for j in range(4)],
    highlight=["g_0_0", "g_3_0"] + [f"g_3_{j}" for j in range(4)],
    tip="东南角两片竖边互吸成直角, 是整栋楼第一个稳固转角。",
)
step(
    "裙楼一层北墙 (4 片): 沿地基北缘立满, 东北角与东墙竖边互吸。",
    [f"L1_n_{i}" for i in range(4)],
    highlight=["L1_e_3"],
    tip="从东北角开始向西立, 每片先吸地基边、再吸邻片竖边。",
)
step(
    "裙楼一层西墙 (4 片), 一层墙体合围。",
    [f"L1_w_{j}" for j in range(4)],
    highlight=["L1_n_0", "L1_s_0"],
    tip="每个转角的两片都要互相吸住, 合围后轻推墙体应整体联动。",
)
step(
    "二层南立面与门楣: 先立两端 2 片, 再把长方形门楣横跨在大堂门洞正上方, "
    "两条短边分别吸住左右墙片的竖边。",
    ["L2_s_0", "L2_s_3", "L2_lintel"],
    highlight=["L1_s_0", "L1_s_3"],
    tip="门楣要水平: 先对准一侧短边吸住, 再轻压另一侧到位。",
)
step(
    "二层东墙与北墙 (7 片): 东面留一扇通风窗 (y 1..2 空格), 北面立满。",
    [f"L2_e_{j}" for j in (0, 2, 3)] + [f"L2_n_{i}" for i in range(4)],
    highlight=["L2_s_0", "L2_s_3"],
    tip="窗洞位置空着不放片即可 —— 负空间就是立面设计的一部分。",
)
step(
    "二层西墙 (3 片): 同样留一扇窗 (y 2..3 空格), 二层墙体合围。",
    [f"L2_w_{j}" for j in (0, 1, 3)],
    highlight=["L2_n_0", "L2_s_0"],
    tip="东西两扇窗错开半层布置, 大楼立面因此有了节奏感。",
)
step(
    "铺设一级露台楼板西半部 (8 片): 从贴西墙的一列开始, 一列一列向东铺。",
    [f"d1_{i}_{j}" for i in range(2) for j in range(4)],
    highlight=[f"L2_w_{j}" for j in (0, 1, 3)],
    tip="每片楼板至少要吸住一条墙顶边或一片已铺楼板的边。",
)
step(
    "补齐一级露台楼板东半部 (8 片), 裙楼封顶。",
    [f"d1_{i}_{j}" for i in range(2, 4) for j in range(4)],
    highlight=[f"d1_1_{j}" for j in range(4)],
    tip="楼板四周应恰好压在四面墙的顶边上, 铺完后整层是一个平整广场。",
)
step(
    "一级露台南缘装 4 片黄色女儿墙三角冠: 底边吸露台南缘, 尖角朝天。",
    [f"p1_{i}" for i in range(4)],
    highlight=[f"d1_{i}_0" for i in range(4)],
    tip="三角冠底边吸合即可站稳; 它们标出了裙楼屋顶花园的边界。",
)
step(
    "二级塔身向西北旋位起墙 —— 三层南墙与东墙 (5 片): 塔身退到 3x3, "
    "南墙中间留窗, 东墙立满。",
    ["L3_s_0", "L3_s_2"] + [f"L3_e_{j}" for j in (1, 2, 3)],
    highlight=[f"d1_{i}_0" for i in range(4)],
    tip="塔身不居中! 贴住露台的西缘与北缘, 东、南两侧退出 L 形环形露台。",
)
step(
    "三层北墙与西墙 (5 片): 北墙同样留窗, 西墙立满, 三层合围。",
    [f"L3_n_{i}" for i in (0, 2)] + [f"L3_w_{j}" for j in (1, 2, 3)],
    highlight=["L3_e_3", "L3_s_0"],
    tip="转角竖边互吸; 从正上方看, 塔身应贴在露台的西北角。",
)
step(
    "四层南墙与东墙 (5 片): 南面立满 3 片 (骑跨在三层窗洞上方), 东面留窗。",
    [f"L4_s_{i}" for i in range(3)] + [f"L4_e_{j}" for j in (1, 3)],
    highlight=["L3_s_0", "L3_s_2"],
    tip="骑跨窗洞的那片两侧竖边都要吸住相邻墙片, 它就是窗洞的过梁。",
)
step(
    "四层北墙与西墙 (5 片), 二级塔身合围完成。",
    [f"L4_n_{i}" for i in range(3)] + [f"L4_w_{j}" for j in (1, 3)],
    highlight=["L4_s_0", "L4_e_1"],
    tip="完成后二级塔身应是方正的两层筒体, 窗洞南北东西各有分布。",
)
step(
    "安装二级塔身根部斜撑 (4 根橙色直角三角形): 南侧露台 2 根、东侧露台 2 根, "
    "底边吸露台面、竖直边吸塔身墙根竖边, 锁成三角刚性节点。",
    ["br2_s_1", "br2_s_2", "br2_e_2", "br2_e_3"],
    highlight=["L3_s_0", "L3_s_2", "L3_e_1", "L3_e_2"],
    tip="斜撑两条直角边必须都吸牢 —— 只吸一条边就成装饰品了。",
)
step(
    "铺设二级露台楼板西、中两列 (6 片): 从贴西墙一列开始向东铺。",
    [f"d2_{i}_{j}" for i in range(2) for j in range(1, 4)],
    highlight=[f"L4_w_{j}" for j in (1, 3)] + [f"L4_s_{i}" for i in range(3)],
    tip="每片楼板至少吸住一条墙顶边或一片已铺楼板的边。",
)
step(
    "补齐二级露台楼板东列 (3 片), 二级塔身封顶。",
    [f"d2_2_{j}" for j in range(1, 4)],
    highlight=[f"d2_1_{j}" for j in range(1, 4)],
    tip="楼板压实四面墙顶; 东、南边缘悬出的部分就是新一圈环形露台。",
)
step(
    "二级露台南缘装 3 片女儿墙三角冠。",
    [f"p2_{i}" for i in range(3)],
    highlight=[f"d2_{i}_1" for i in range(3)],
    tip="第二圈黄色三角冠与第一圈错层呼应, 大楼的盘旋轮廓开始显现。",
)
step(
    "三级塔身向东北旋位起墙 —— 南墙与东墙 (4 片): 塔身再退到 2x2。",
    ["L5_s_1", "L5_s_2"] + [f"L5_e_{j}" for j in (2, 3)],
    highlight=[f"d2_{i}_3" for i in range(3)],
    tip="这级塔身贴住二级露台的东缘与北缘 —— 与上一级刚好旋向对角。",
)
step(
    "三级塔身北墙与西墙 (3 片): 西面留一扇观景窗, 三级墙体合围。",
    [f"L5_n_{i}" for i in (1, 2)] + ["L5_w_3"],
    highlight=["L5_e_3", "L5_s_1"],
    tip="观景窗朝西 —— 从这里能俯瞰整条盘旋而上的环形露台。",
)
step(
    "安装三级塔身斜撑 (2 根): 南侧、西侧各一根, 做法与二级相同。",
    ["br3_s", "br3_w"],
    highlight=["L5_s_1", "L5_s_2", "L5_w_3"],
    tip="越往高处越要撑牢: 高层结构的抗晃能力全靠这些三角节点。",
)
step(
    "铺设三级露台楼板 (2x2 共 4 片): 从西北角贴墙的一片开始。",
    ["d3_1_3", "d3_2_3", "d3_1_2", "d3_2_2"],
    highlight=["L5_w_3", "L5_n_1", "L5_s_1"],
    tip="第一片要同时吸住西墙顶边, 之后每片吸住相邻楼板或墙顶。",
)
step(
    "三级露台西缘装 2 片女儿墙三角冠。",
    ["p3_2", "p3_3"],
    highlight=["d3_1_2", "d3_1_3"],
    tip="第三圈女儿墙转到了西缘 —— 三圈黄冠绕塔一周, 这就是旋位退台。",
)
step(
    "顶层观景阁向东南旋位起墙: 1x1 四面各立 1 片紫色正方形。",
    ["cr_s", "cr_e", "cr_n", "cr_w"],
    highlight=["d3_2_2"],
    tip="四片依次吸住楼板边与彼此的竖边, 围成大楼最高的小房间。",
)
step(
    "合拢锥形金顶: 4 片黄色等腰三角形底边分别吸在观景阁四条顶边上, 全部向内倾斜, "
    "四条斜棱两两互吸, 塔尖在正中交汇 —— 城市摩天大楼封顶!",
    ["roof_s", "roof_e", "roof_n", "roof_w"],
    highlight=["cr_s", "cr_e", "cr_n", "cr_w"],
    tip="按 南->东->北->西 顺序合拢: 最后一片要同时吸住底边和两条斜棱, 轻压到位。",
)

# ---- 汇总与输出 --------------------------------------------------
placed = [t for s in steps for t in s["tiles_to_add"]]
assert len(placed) == len(tiles) == len(set(placed)), "步骤必须恰好覆盖全部磁力片"
assert len(tiles) >= 90, f"摩天大楼片数 {len(tiles)} 低于旗舰标准 90"
assert len(steps) >= 20, f"摩天大楼步数 {len(steps)} 低于旗舰标准 20"

# BOM 备料清单: tests/test_model_logic.py 会核对该清单与 final_assembly 完全一致
bom: dict[str, int] = {}
for t in tiles:
    bom[t["type"]] = bom.get(t["type"], 0) + 1
bom = dict(sorted(bom.items(), key=lambda kv: (-kv[1], kv[0])))

model = {
    "schema_version": 1,
    "id": "skyscraper_01",
    "name": "城市摩天大楼",
    "name_en": "City Skyscraper 01",
    "description": (
        "全库最高剪影: 4x4 裙楼之上, 塔身以 3x3 -> 2x2 -> 1x1 逐级退台, 且每级绕塔心"
        "旋位 (西北 -> 东北 -> 东南), 退出的环形露台绕大楼盘旋而上; 大堂门洞配长方形"
        "门楣, 每级塔身根部由直角三角形斜撑锁定, 顶层观景阁以四片等腰三角形合拢成"
        "锥形金顶。搭完立在桌上近半米高 —— 这是放进展示柜的作品。"
    ),
    "difficulty": 5,
    "total_pieces": len(tiles),
    "tags": ["摩天大楼", "建筑地标", "退台", "旗舰", "大师"],
    "content_meta": {
        "structural_signature": {
            "tile_histogram": bom,
        },
    },
    "final_assembly": tiles,
    "steps": steps,
}

out = Path(__file__).resolve().parent.parent / "data" / "models" / "skyscraper_01.json"
out.write_text(json.dumps(model, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

by_type = {}
for t in tiles:
    by_type[t["type"]] = by_type.get(t["type"], 0) + 1
print(f"已生成 {out} ({len(tiles)} 片, {len(steps)} 步)")
print("片形统计: " + ", ".join(f"{k} x {v}" for k, v in sorted(by_type.items())))
