#!/usr/bin/env python3
"""生成模型 data/models/marble_splitter_01.json (双轨分流滚珠台)。

内容批 P 模型 6/10: 滚珠乐园 D2 —— 与 marble_cascade_01 (三级退台瀑布)
动线不同, 本作是"双轨门框分流": 两层发射台向东甩出首段坡道, 四座
橙色门框方在分流枢纽立成两道门洞 (T17 负空间), 弹珠随机或交替滑入
南北两轨, 各经一段 30 度坡道落进独立接珠池 (T08 滚珠轨道)。

结构总览 (世界单位: 1.0 = 正方形磁力片边长, 弹珠自西向东):
  - 西端发射台 (x [0,1], y [0,2], z 0..2): 地台 x2 + 墙环 x12 +
    发球台 x2 + 台沿挡珠 x3                                              19 片
  - 首段坡道 (z2->z1): 桥墩 x1 + 门框立柱 x1 + 坡道 + 南轨转接台 +
    挡珠 x1                                                               5 片
  - 分流枢纽: 北轨转接台 + 三座门框分流门 (与首段立柱合计门框方 x4)       4 片
  - 双轨下坡 (z1->z0): 南北各桥墩 + 坡道 + 转接台                        6 片
  - 双接珠池: 池底 x2 + 矮墙 x1 + 铃靶 x2                                5 片
  合计 39 片, 8 个教程步骤, 5 种磁力片形状 (全部 CORE-9 之内)。

物理规则要点 (validate strict 零警告):
  - 每段坡道顶边整边吸上一级台面东沿, 坡尾由桥墩顶边接住;
  - 门框方按实心墙校验, 门洞负空间仅作分流造型表达 (T17);
  - 发射台最高点约 3.87, 低于 R8 红线 4.0。

用法: python3 tools/generate_marble_splitter_01.py  (在 magtile-studio 目录下运行)
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from magtile_gen import SQ3, ModelBuilder  # noqa: E402

b = ModelBuilder()

BASE = "gray"
TOWER = "blue"
DECK = "yellow"
RAIL = "red"
PIER = "gray"
RAMP = "orange"
GATE = "orange"     # 门框方分流门 (T17)
POOL_N = "cyan"
POOL_S = "green"
BELL = "pink"


def wall_ew_t(tid, tile_type, x, y0, z0, color):
    b.add(tid, tile_type, (x, y0 + 0.5, z0 + 0.5), (90, 0, 90), color)


X1 = 1 + SQ3       # 首段转接台西缘 2.732051
X2 = X1 + 1 + SQ3  # 双轨桥墩 / 转接台线 5.464102
X_POOL = X2 + 1    # 接珠池西缘 (紧接轨末转接台东沿)

# =================================================================
# 1. 西端发射台 (x [0,1], y [0,2]): 地台 + 两层墙环 + 发球台
# =================================================================
b.flat("base_0", 0, 0, 0.0, BASE)
b.flat("base_1", 0, 1, 0.0, BASE)
for lv in range(2):
    c = TOWER
    b.wall_ns(f"tw{lv}_s", 0, 0.0, lv, c)
    b.wall_ns(f"tw{lv}_n", 0, 2.0, lv, c)
    b.wall_ew(f"tw{lv}_w_0", 0.0, 0, lv, c)
    b.wall_ew(f"tw{lv}_w_1", 0.0, 1, lv, c)
    b.wall_ew(f"tw{lv}_e_0", 1.0, 0, lv, c)
    b.wall_ew(f"tw{lv}_e_1", 1.0, 1, lv, c)
b.flat("deck_0", 0, 0, 2.0, DECK)
b.flat("deck_1", 0, 1, 2.0, DECK)
b.crest_ew("drail_w", 0.0, 0, 2.0, RAIL)
b.crest_ns("drail_n", 0, 2.0, 2.0, RAIL)
b.crest_ns("drail_s", 0, 0.0, 2.0, RAIL)

# =================================================================
# 2. 首段坡道 (z2->z1): 桥墩 + 门框立柱 + 坡道 + 南轨转接台
#    gate_e0 同时是南轨分流门柱 (x=X1+1, y=0)
# =================================================================
b.wall_ew("p1a", X1, 0, 0, PIER)
wall_ew_t("gate_e0", "door_frame", X1 + 1, 0, 0, GATE)
b.ramp("ramp_1", "+x", 1.0, 0, 2.0, RAMP)
b.flat("plat_s", X1, 0, 1.0, DECK)
b.crest_ns("rail1_s", X1, 0.0, 1.0, RAIL)

# =================================================================
# 3. 分流枢纽: 北轨转接台 + 三座门框分流门 (与 gate_e0 合计 x4)
#    门柱沿 x=X1+1 排布, 与双轨桥墩 x=X2 错开
# =================================================================
b.flat("plat_n", X1, 1, 1.0, DECK)
wall_ew_t("gate_n0", "door_frame", X1 + 1, 1, 0, GATE)
wall_ew_t("gate_n1", "door_frame", X1 + 1, 1, 1, GATE)
wall_ew_t("gate_s1", "door_frame", X1 + 1, 0, 1, GATE)

# =================================================================
# 4. 双轨下坡 (z1->z0): 桥墩在 X2, 坡道自 hub 东沿 (x=X1+1) 探出
# =================================================================
b.wall_ew("p2n", X2, 1, 0, PIER)
b.ramp("ramp_n", "+x", X1 + 1, 1, 1.0, RAMP)
b.flat("lane_n", X2, 1, 0.0, DECK)

b.wall_ew("p2s", X2, 0, 0, PIER)
b.ramp("ramp_s", "+x", X1 + 1, 0, 1.0, RAMP)
b.flat("lane_s", X2, 0, 0.0, DECK)

# =================================================================
# 5. 双接珠池 + 铃靶
# =================================================================
b.flat("pool_n", X_POOL, 1, 0.0, POOL_N)
b.flat("pool_s", X_POOL, 0, 0.0, POOL_S)
b.wall_ns("pool_s_s", X_POOL, 0.0, 0, POOL_S)
wall_ew_t("bell_n", "window_square", X_POOL + 1, 1, 0, BELL)
wall_ew_t("bell_s", "window_square", X_POOL + 1, 0, 0, BELL)

# =================================================================
# 教程步骤 (10 步)
# =================================================================
b.step(
    "铺发射塔地台: 两片灰色方板沿西端打底, 六片蓝色方板合围第一层墙环。",
    ["base_0", "base_1",
     "tw0_s", "tw0_w_0", "tw0_w_1", "tw0_n", "tw0_e_0", "tw0_e_1"],
    tip="塔基东边要留出一条直线跑道 —— 弹珠将从这里分流进双轨。",
)
b.step(
    "发射塔第二层: 六片蓝色方板骑上第一层墙顶, 上下边完整贴合。",
    ["tw1_s", "tw1_w_0", "tw1_w_1", "tw1_n", "tw1_e_0", "tw1_e_1"],
    highlight=["tw0_s", "tw0_e_0"],
    tip="两层墙环已经够高 —— D2 不需要三层塔, 弹珠从 z=2 出发。",
)
b.step(
    "盖发球台: 两片黄色方板压住第二层墙顶, 三片挡珠三角围住台沿 (东缘留口)。",
    ["deck_0", "deck_1", "drail_w", "drail_n", "drail_s"],
    highlight=["tw1_s", "tw1_e_0"],
    tip="东缘南半格空着 —— 那是弹珠滑向首段坡道的出珠口。",
)
b.step(
    "首段坡道 (整段成组): 塔东侧立桥墩与橙色门框立柱, 坡道顶边吸出珠口, "
    "南轨转接台压住墩顶与坡尾。",
    ["p1a", "gate_e0", "ramp_1", "plat_s", "rail1_s"],
    highlight=["deck_0", "tw1_e_0"],
    tip="门框立柱就是第一道分流门 —— 桥墩-坡道-转接台三件互吸应纹丝不动。",
)
b.step(
    "分流枢纽: 北轨转接台与三座橙色门框方 —— 与首段立柱合计四道门洞, 弹珠选轨!",
    ["plat_n", "gate_n0", "gate_n1", "gate_s1"],
    highlight=["plat_s", "gate_e0"],
    tip="门框门洞是 T17 负空间 —— 北轨走 y=1, 南轨走 y=0, 实物跑珠看哪轨更顺!",
)
b.step(
    "北轨下坡: 立桥墩, 橙色坡道从北轨转接台东沿下探, 铺转接台与北接珠池。",
    ["p2n", "ramp_n", "lane_n", "pool_n"],
    highlight=["plat_n", "gate_n0"],
    tip="池底西缘紧吸轨末转接台东沿 —— 北轨一路贯通!",
)
b.step(
    "南轨下坡: 对称安装南轨桥墩、坡道、转接台与南接珠池及矮墙。",
    ["p2s", "ramp_s", "lane_s", "pool_s", "pool_s_s"],
    highlight=["plat_s", "gate_e0"],
    tip="两池分色 —— 一眼看出弹珠进了哪条轨!",
)
b.step(
    "立双铃靶: 南北池端各立一片粉色窗格方 —— 双轨分流滚珠台完工, 放珠开跑!",
    ["bell_n", "bell_s"],
    highlight=["pool_n", "pool_s"],
    tip="轮流放珠, 看弹珠会选哪道门洞 —— 实物跑珠才算真正验收!",
)

b.finalize(
    model_id="marble_splitter_01",
    name="双轨分流滚珠台",
    name_en="Marble Splitter 01",
    description=(
        "滚珠乐园 D2 扩展片型示范: 与三级退台瀑布完全不同的双轨分流 —— "
        "两层发射台甩出首段坡道, 四座橙色门框方在枢纽立成两道门洞 (T17 负空间), "
        "弹珠滑入南北两轨各经 30 度坡道落进分色接珠池 (T08 滚珠轨道); "
        "全部 CORE-9, 门框方≥4, 实物跑珠验证分流。"
    ),
    difficulty=2,
    tags=["滚珠", "轨道", "分流", "滚珠乐园", "门框"],
    min_pieces=32,
    min_steps=8,
    series="marble_run",
)
