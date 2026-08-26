#!/usr/bin/env python3
"""生成模型 data/models/conservatory_01.json (玻璃花房温室)。

内容批 P 模型 2/10: 植物花园主题 D2 —— 主打窗格方 (window_square)
一排窗格立面温室 + 梯形屋檐。与 greenhouse_01 (A 字斜顶帐篷)
/ greenhouse_dome_01 (穹顶) 的"屋顶即墙"逻辑刻意区分: 本作是
标准 T01 盒式墙环合围的维多利亚式花房, 南向整排窗格方玻璃立面
(两层共 6 片) 是招牌, 北墙中央门框方留 T17 负空间入户门洞,
二层东西墙也嵌窗格方凑满扩展片型; 顶沿两片梯形向南挑出雨檐。

结构总览 (世界单位: 1.0 = 正方形磁力片边长, 入户朝北):
  - 园路地台: 四片灰色方板 + 六片泥土色方板 3x2 室内            10 片
  - 一层墙环: 南窗格 x3 + 北门框 + 北窗格 x2 + 西框 x2 + 东窗 x2  10 片
  - 二层墙环: 南窗格 x3 + 北窗格 x3 + 西框 x2 + 东窗 x2          10 片
  - 平顶: 两片长方形盖板 + 一片梯形雨檐 (T04)                          3 片
  - 室内盆栽 x3: 等边三角骑土拼缝                                  3 片
  合计 36 片, 8 个教程步骤, 6 种磁力片形状 (含 1 种扩展片型)。

物理规则要点 (validate 常规 + strict 双档零警告):
  - 盒式墙环每层四角竖边互咬闭环, 墙脚整边踩地台/土格拼缝;
  - 窗格方/门框方物理按实心墙片处理, 负空间仅作造型语义;
  - 梯形雨檐下底整边吸墙顶沿, 腰边互吸, 重心正压铰链线;
  - 盆栽底边整边吸土格拼缝, 力矩为零。

用法: python3 tools/generate_conservatory_01.py  (在 magtile-studio 目录下运行)
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from magtile_gen import EQ_APEX, ModelBuilder, _sub  # noqa: E402

b = ModelBuilder()

PATH = "gray"
SOIL = "orange"
FRAME = "green"
GLASS = "clear"
DOOR = "orange"
PLANTS = ["red", "yellow", "purple"]

EAVE_Z = 2.0 + EQ_APEX


def wall_ns_t(tid, tile_type, x0, y, z0, color):
    b.add(tid, tile_type, (x0 + 0.5, y, z0 + 0.5), (90, 0, 0), color)


def wall_ew_t(tid, tile_type, x, y0, z0, color):
    b.add(tid, tile_type, (x, y0 + 0.5, z0 + 0.5), (90, 0, 90), color)


def trapezoid_eave(tid, x0, x1, y, z, color):
    """一段梯形雨檐: 下底 [x0,x1] 落在墙顶沿, 上底向 -y 挑出。"""
    top_mid = ((x0 + x1) / 2, y - 0.5, EAVE_Z)
    bottom_mid = ((x0 + x1) / 2, y, z)
    b.place_edge(
        tid, "trapezoid", 0,
        (x0, y, z), (x1, y, z),
        _sub(top_mid, bottom_mid), color,
    )


# =================================================================
# 1. 园路与室内土格 (x [1,3], y [1,2] 为花房室内)
# =================================================================
for x in (1, 2, 3, 4):
    b.flat(f"path_{x}", x, 0, 0.0, PATH)
for x in (1, 2, 3):
    for y in (1, 2):
        b.flat(f"soil_{x}_{y}", x, y, 0.0, SOIL)

# =================================================================
# 2. 一层盒式墙环 (T01): 南向整排窗格立面 + 北墙门框入户 (T17)
# =================================================================
for x in (1, 2, 3):
    wall_ns_t(f"gl_s0_{x}", "window_square", x, 1.0, 0, GLASS)
wall_ns_t("door_n", "door_frame", 2, 3.0, 0, DOOR)
wall_ns_t("gl_n0_1", "window_square", 1, 3.0, 0, GLASS)
wall_ns_t("gl_n0_3", "window_square", 3, 3.0, 0, GLASS)
b.wall_ew("frame_w0_1", 1.0, 1, 0, FRAME)
b.wall_ew("frame_w0_2", 1.0, 2, 0, FRAME)
wall_ew_t("gl_e0_1", "window_square", 4.0, 1, 0, GLASS)
wall_ew_t("gl_e0_2", "window_square", 4.0, 2, 0, GLASS)

# =================================================================
# 3. 二层续高: 窗格立面加高, 北墙换清色窗格 (入户门洞留负空间)
# =================================================================
for x in (1, 2, 3):
    wall_ns_t(f"gl_s1_{x}", "window_square", x, 1.0, 1, GLASS)
for x in (1, 2, 3):
    wall_ns_t(f"gl_n1_{x}", "window_square", x, 3.0, 1, GLASS)
b.wall_ew("frame_w1_1", 1.0, 1, 1, FRAME)
b.wall_ew("frame_w1_2", 1.0, 2, 1, FRAME)
wall_ew_t("gl_e1_1", "window_square", 4.0, 1, 1, GLASS)
wall_ew_t("gl_e1_2", "window_square", 4.0, 2, 1, GLASS)

# =================================================================
# 4. 平顶 + 南向梯形雨檐 (T04 屋檐)
# =================================================================
b.flat_rect("rim_s", 1, 1, 2.0, FRAME)
b.flat_rect("roof_n", 1, 2, 2.0, FRAME)
trapezoid_eave("eave_s", 1.0, 3.0, 1.0, 2.0, FRAME)

# =================================================================
# 5. 室内盆栽
# =================================================================
b.crest_ns("pot_a", 2, 2.0, 0.0, PLANTS[0])
b.crest_ns("pot_b", 1, 2.0, 0.0, PLANTS[1])
b.crest_ew("pot_c", 2.0, 2, 0.0, PLANTS[2])

# =================================================================
# 教程步骤 (9 步)
# =================================================================
b.step(
    "铺南向园路: 四片灰色方板一字排开, 正对温室大门。",
    [f"path_{x}" for x in (1, 2, 3, 4)],
    tip="园路是访客的第一眼 —— 拼缝对齐, 墙脚才有整边可吸。",
)
b.step(
    "铺室内土格并种盆栽: 六片泥土方板 3x2, 红/黄/紫三株三角骑土拼缝。",
    [f"soil_{x}_{y}" for x in (1, 2, 3) for y in (1, 2)]
    + ["pot_a", "pot_b", "pot_c"],
    highlight=["path_2"],
    tip="先种花再起墙 —— 盒式框架合拢前手还伸得进花房。",
)
b.step(
    "砌一层南立面: 三片清色窗格方整排朝南 —— 温室玻璃墙的第一层。",
    [f"gl_s0_{x}" for x in (1, 2, 3)],
    highlight=["pot_a"],
    tip="窗格方物理上和实心墙一样稳 —— 一排窗格就是花房的招牌。",
)
b.step(
    "合围一层墙环: 西框两片 + 东窗两片 + 北墙门框入户 (T17 负空间)。",
    ["frame_w0_1", "frame_w0_2", "gl_e0_1", "gl_e0_2",
     "door_n", "gl_n0_1", "gl_n0_3"],
    highlight=["gl_s0_2"],
    tip="门框方留出门洞 —— 北墙少一片墙, 入户却更有花房味道。",
)
b.step(
    "加高二层南立面: 三片窗格方续接, 与下层竖边整边互吸。",
    [f"gl_s1_{x}" for x in (1, 2, 3)],
    highlight=["gl_s0_2"],
    tip="两层窗格叠起来 —— 从园路望进去像一整面玻璃。",
)
b.step(
    "续高二层墙环: 北墙三片窗格 + 西框 + 东窗, 与一层四角竖边互咬。",
    [f"gl_n1_{x}" for x in (1, 2, 3)]
    + ["frame_w1_1", "frame_w1_2", "gl_e1_1", "gl_e1_2"],
    highlight=["door_n", "gl_s1_2"],
    tip="二层北墙全是窗格 —— 门洞上方也透光, 盒式框架合围完成。",
)
b.step(
    "封平顶: 两片长方形盖板骑墙顶 —— 南沿板给雨檐留等长铰链线。",
    ["rim_s", "roof_n"],
    highlight=["gl_n1_2"],
    tip="长板短边吸墙顶 —— 南沿板下底就是梯形雨檐的支座。",
)
b.step(
    "挑南向梯形雨檐: 一片梯形下底吸南沿板, 向南挑出 (T04 屋檐) —— 玻璃花房落成!",
    ["eave_s"],
    highlight=["rim_s"],
    tip="梯形雨檐像给玻璃墙戴遮阳帽 —— 透过南向窗格, 三色花正在生长。",
)

b.finalize(
    model_id="conservatory_01",
    name="玻璃花房",
    name_en="Conservatory 01",
    description=(
        "植物花园 D2: 标准 T01 盒式墙环合围的维多利亚式花房 —— 南向"
        "整排窗格方玻璃立面 (两层共 6 片) 是招牌, 东西墙也嵌窗格方"
        "凑满扩展片型; 北墙中央门框方留 T17 负空间入户门洞, 二层北墙"
        "全窗格让门洞上方也透光; 顶沿长方形楣梁托住一片梯形向南挑出雨檐; 室内"
        "3x2 泥土格上摆着红/黄/紫盆栽。与 A 字斜顶 greenhouse_01 和"
        "穹顶 greenhouse_dome_01 刻意区分 —— 这次是'竖墙 + 一排窗格'"
        "的古典温室。"
    ),
    difficulty=2,
    tags=["植物花园", "温室", "花房", "窗格", "入门"],
    min_pieces=36,
    min_steps=8,
    series="plant_garden",
)
