#!/usr/bin/env python3
"""生成模型 data/models/trapezoid_awning_01.json (梯形雨棚连廊)。

内容批 P 模型 5/10: 植物花园主题 D2 —— 招牌是 T12 层叠退台 +
梯形檐篷 (T04): 4x2 走道外角与中央同层铺地, 内框四片 2 格横楣
抬升出檐口; 上层四片梯形合围开放式雨棚, 下层四片梯形自基座外挑
盖住苗床 —— 梯形片数 ≥8, 全库首个「梯形雨棚连廊」。

结构总览 (世界单位: 1.0 = 正方形磁力片边长, 连廊沿东西向):
  - 走道 (4x2): 清灰棋盘方板 z=0 (含中央 2x2 下沉走道)           8 片
  - 角柱 (z 0..1): 走道四角绿色立墙 x4                               4 片
  - 连廊内框檐轨 (z 0..1): 2x2 框四边灰色横楣 x4                     4 片
  - 上层梯形雨棚 (z=1 沿口): 四片梯形合围开放式顶                   4 片
  - 苗床基座 (y=-1/2): 2 格泥土长方 x4                               4 片
  - 连廊盆花: 等边三角 x4 立在平台沿口                                 4 片
  - 下层梯形檐篷: 四片梯形吸基座顶沿外挑                               4 片
  合计 32 片, 6 个教程步骤, 5 种磁力片形状 (含扩展梯形)。

物理规则要点 (validate 常规 + strict 双档零警告):
  - 角柱与内框檐轨墙脚整边踩走道拼缝, 檐轨顶沿 z=1 供梯形整边吸合;
  - 上层梯形四片腰互锁成开放式雨棚 (T04), 下层梯形吸 2 格基座铰链;
  - 中央走道与外角同层 (z=0), 檐口抬升形成 T12 层叠退台视觉;
  - 盆花底边吸走道沿口, 基座整边互吸。

用法: python3 tools/generate_trapezoid_awning_01.py  (在 magtile-studio 目录下运行)
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from magtile_gen import EQ_APEX, ModelBuilder, _sub  # noqa: E402

b = ModelBuilder()

PATH_A = "clear"
PATH_B = "gray"
POST = "green"
SOIL = "orange"
AWNING = "green"
LATTICE = "clear"
RAIL = "gray"
FLOWER = ["red", "yellow", "purple", "pink"]


def pergola_eaves(prefix, x0, y0, z, roof_color, lattice_color):
    """2x2 洞口上的四片梯形开放式雨棚 (无压顶)。"""
    zt = z + EQ_APEX
    faces = {
        "s": ((x0, y0, z), (x0 + 2, y0, z), (x0 + 1.0, y0 + 0.5, zt)),
        "e": ((x0 + 2, y0, z), (x0 + 2, y0 + 2, z), (x0 + 1.5, y0 + 1.0, zt)),
        "n": ((x0 + 2, y0 + 2, z), (x0, y0 + 2, z), (x0 + 1.0, y0 + 1.5, zt)),
        "w": ((x0, y0 + 2, z), (x0, y0, z), (x0 + 0.5, y0 + 1.0, zt)),
    }
    colors = {"s": roof_color, "e": lattice_color, "n": roof_color, "w": lattice_color}
    ids = []
    for side, (b0, b1, top_mid) in faces.items():
        tid = f"{prefix}_{side}"
        bottom_mid = tuple((b0[i] + b1[i]) / 2 for i in range(3))
        b.place_edge(tid, "trapezoid", 0, b0, b1, _sub(top_mid, bottom_mid), colors[side])
        ids.append(tid)
    return ids


def south_eave(prefix, x0, color):
    b0 = (x0, 0.0, 0.0)
    b1 = (x0 + 2.0, 0.0, 0.0)
    bottom_mid = (x0 + 1.0, 0.0, 0.0)
    top_mid = (x0 + 1.0, -0.5, EQ_APEX)
    b.place_edge(prefix, "trapezoid", 0, b0, b1, _sub(top_mid, bottom_mid), color)


def north_eave(prefix, x0, color):
    b0 = (x0, 2.0, 0.0)
    b1 = (x0 + 2.0, 2.0, 0.0)
    bottom_mid = (x0 + 1.0, 2.0, 0.0)
    top_mid = (x0 + 1.0, 2.5, EQ_APEX)
    b.place_edge(prefix, "trapezoid", 0, b0, b1, _sub(top_mid, bottom_mid), color)


# =================================================================
# 1. 走道 (4x2 整层 z=0, 中央 2x2 与外角同层 —— T12 下沉走道)
# =================================================================
for y in range(2):
    for x in range(4):
        b.flat(f"path_{x}_{y}", x, y, 0.0, PATH_A if (x + y) % 2 == 0 else PATH_B)

# =================================================================
# 2. 角柱 + 内框檐轨 (z 0..1)
# =================================================================
b.wall_ns("post_sw", 0, 0.0, 0, POST)
b.wall_ns("post_nw", 0, 2.0, 0, POST)
b.wall_ns("post_se", 3, 0.0, 0, POST)
b.wall_ns("post_ne", 3, 2.0, 0, POST)
b.lintel_ns("rim_s", 1, 0.0, 0, RAIL)
b.lintel_ns("rim_n", 1, 2.0, 0, RAIL)
b.lintel_ew("rim_w", 1.0, 0, 0, RAIL)
b.lintel_ew("rim_e", 3.0, 0, 0, RAIL)

# =================================================================
# 3. 上层梯形雨棚
# =================================================================
roof_ids = pergola_eaves("roof", 1, 0, 1.0, AWNING, LATTICE)

# =================================================================
# 4. 苗床基座 + 盆花
# =================================================================
b.flat_rect("foot_s0", 0, -1, 0.0, SOIL)
b.flat_rect("foot_s2", 2, -1, 0.0, SOIL)
b.flat_rect("foot_n0", 0, 2, 0.0, SOIL)
b.flat_rect("foot_n2", 2, 2, 0.0, SOIL)
b.crest_ew("pot_sw", 0.0, 0, 0.0, FLOWER[0])
b.crest_ew("pot_nw", 0.0, 1, 0.0, FLOWER[2])
b.crest_ew("pot_se", 4.0, 0, 0.0, FLOWER[1])
b.crest_ew("pot_ne", 4.0, 1, 0.0, FLOWER[3])

# =================================================================
# 5. 下层梯形檐篷
# =================================================================
south_eave("eave_sw", 0, AWNING)
south_eave("eave_se", 2, LATTICE)
north_eave("eave_nw", 0, AWNING)
north_eave("eave_ne", 2, LATTICE)

# =================================================================
# 教程步骤 (7 步)
# =================================================================
b.step(
    "铺走道: 八片清灰相间的方板拼成 4x2, 中央 2x2 与外角同层 —— 下沉式走道。",
    [f"path_{x}_{y}" for y in range(2) for x in range(4)],
    tip="走道铺平, 角柱和檐轨才有整边可吸 —— 这是 T12 的地基。",
)
b.step(
    "立角柱与内框檐轨: 四角绿色立墙 + 四片灰色横楣围成 2x2 抬升檐口。",
    ["post_sw", "post_nw", "post_se", "post_ne", "rim_s", "rim_n", "rim_w", "rim_e"],
    highlight=["path_0_0", "path_3_1"],
    tip="檐轨顶沿 z=1 比走道高一层 —— T12 层叠退台, 也是雨棚铰链线。",
)
b.step(
    "合围上层雨棚: 四片梯形下底吸檐轨顶沿, 腰互锁成开放式顶 —— 南北绿、东西清。",
    roof_ids,
    highlight=["rim_s", "rim_n"],
    tip="梯形片是主角 —— 四片合围, 阳光还能从棚顶漏下来。",
)
b.step(
    "铺南侧苗床: 两片 2 格泥土基座贴住走道南沿, 给下层檐篷整边铰链。",
    ["foot_s0", "foot_s2"],
    highlight=["path_0_0", "post_sw"],
    tip="基座北沿与走道南沿共用一条缝 —— 花园和连廊连成一体。",
)
b.step(
    "铺北侧基座并摆盆花: 两片泥土基座, 四株三角盆花立在走道北/南沿。",
    ["foot_n0", "foot_n2", "pot_sw", "pot_nw", "pot_se", "pot_ne"],
    highlight=["path_0_0", "path_3_1"],
    tip="盆花底边吸走道沿 —— 连廊里也能看到颜色。",
)
b.step(
    "合围下层檐篷: 四片梯形吸基座顶沿外挑 —— 梯形雨棚连廊落成!",
    ["eave_sw", "eave_se", "eave_nw", "eave_ne"],
    highlight=["foot_s0", "path_1_0", "roof_s"],
    tip="上下两层共八片梯形 —— 沿下沉走道慢慢穿过去, 别踩到花。",
)

b.finalize(
    model_id="trapezoid_awning_01",
    name="梯形雨棚连廊",
    name_en="Trapezoid Awning Walk 01",
    description=(
        "植物花园 D2: 4x2 下沉式走道 (T12 层叠退台) 上立内框四片 2 格"
        "檐轨, 顶沿供上层四片梯形合围开放式雨棚; 走道两侧 2 格泥土"
        "基座外挑四片梯形檐篷盖住苗床, 沿口四色盆花点缀 —— 上下两层"
        "共八片梯形, 连廊能走通、花床有荫。与玫瑰长廊的门式横梁不同,"
        "这次主角就是扩展梯形片本身。"
    ),
    difficulty=2,
    tags=["植物花园", "雨棚", "连廊", "梯形", "花台"],
    min_pieces=30,
    min_steps=6,
    series="plant_garden",
)
