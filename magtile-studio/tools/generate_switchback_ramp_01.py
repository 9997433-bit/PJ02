#!/usr/bin/env python3
"""生成模型 data/models/switchback_ramp_01.json (折返坡道滚珠塔)。

内容批 P 模型 8/10 (P8): 滚珠乐园 D2 —— 招牌是 T08 滚珠轨道 + T14 直角
三角对角镜台: 弹珠从两层发球塔向东甩下首段坡道, 落上折返镜台 A ——
台面由两片直角三角沿对角缝拼成, 缝上再立一片直角三角当 45° 折返镜;
南北两面镜子连续两次 45° 反弹, 弹珠原速掉头 180° 冲下第二段坡道向西,
在塔脚下的折返镜台 B 再次掉头, 沿冲线直道向东滚进接珠池。

与库内其他滚珠模型动线拓扑均不同: ball_run_tower_01 双轨镜像绕塔,
marble_run_spiral_01 顺时针螺旋, marble_cascade_01 三级退台直落,
marble_splitter_01 门框分流 —— 本作是唯一的 "东下-西折-东冲" 之字折返,
且 180° 掉头由直角三角斜镜的两次反弹真实完成 (镜缝即磁力吸合缝)。

结构总览 (世界单位: 1.0 = 正方形磁力片边长, 弹珠自塔顶 z=2 出发):
  - 发球塔: 塔基 + 两层墙环 + 发球台 + 三面挡珠           12 片
  - 塔角直角三角斜撑 (T14)                                 3 片
  - 双段 30 度坡道 (T08) + 折返台桥墩                      4 片
  - 折返镜台 A (z=1): 台面直角三角 x4 + 折返镜 x2          6 片
  - 折返镜台 B (z=0): 台面直角三角 x4 + 折返镜 x2          6 片
  - 冲线直道 + 南侧护栏 + 接珠池                          11 片
  合计 42 片 (正方形 x19 + 直角三角 x15 + 等边三角 x6 + 长方形 x2)。

物理规则要点 (validate strict 零警告):
  - 折返镜立在对角缝上, 镜底斜边与两片台面三角的斜边三边共线互吸,
    重心正压缝线 (力矩为零), 与台面构成三角闭环;
  - 每段坡道顶边整边吸上级台沿, 坡尾整边吸下级台面, 双端受支;
  - 镜台 A 东缘由双桥墩接住, 桥墩间竖边互吸成门式框架;
  - 塔角斜撑竖边锁墙角, 西南斜撑水平边兼吸镜台 B 台面, 塔-台成环;
  - 最高点为发球台挡珠三角顶 z=2.87, 低于 R8 无桁架红线 4.0。

用法: python3 tools/generate_switchback_ramp_01.py  (在 magtile-studio 目录下运行)
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from magtile_gen import SQ3, ModelBuilder  # noqa: E402

b = ModelBuilder()

BASE = "gray"
TOWER = "blue"
DECK = "yellow"
RAIL = "red"       # 挡珠 + 折返镜: 弹珠会撞上的面统一红色
BRACE = "purple"
PIER = "gray"
RAMP = "orange"
PAD_A = "cyan"     # 折返镜台 A 台面 (z=1)
PAD_B = "green"    # 折返镜台 B 台面 (z=0)
LANE = "yellow"
POOL = "cyan"
POOL_WALL = "blue"

RT_APEX = 0.707107        # 直角三角立在斜边上时直角顶点的高度 (1/sqrt(2))
XA = 1 + SQ3              # 镜台 A 西缘 = 首段坡道坡尾 x = 2.732051
XP = XA + 1               # 镜台 A 东缘 = 桥墩平面 x = 3.732051

BRACES = [
    # (id, 直角顶点, 水平直角边方向): 竖直角边吸塔角竖缝
    ("br_sw", (0.0, 1.0, 0.0), "-y"),   # 西南角: 水平边向南, 兼吸镜台 B 台面西缘
    ("br_nw", (0.0, 2.0, 0.0), "+y"),   # 西北角: 沿西墙面向北外伸
    ("br_ne", (1.0, 2.0, 0.0), "+x"),   # 东北角: 沿北墙面向东外伸 (坡道下方净空)
]


def diag_pad(prefix, x0, y0, z, diag, color):
    """两片直角三角沿对角缝拼 1x1 水平台面。

    diag="ne": 缝从 (x0,y0) 到 (x0+1,y0+1), 直角顶点在东南/西北;
    diag="se": 缝从 (x0,y0+1) 到 (x0+1,y0), 直角顶点在西南/东北。
    返回两片 id (直角边均落在格线上, 斜边共线成缝)。
    """
    if diag == "ne":
        ids = (f"{prefix}_se", f"{prefix}_nw")
        b.place_tri(ids[0], "right_triangle",
                    (x0 + 1, y0, z), (x0 + 1, y0 + 1, z), (x0, y0, z), color)
        b.place_tri(ids[1], "right_triangle",
                    (x0, y0 + 1, z), (x0, y0, z), (x0 + 1, y0 + 1, z), color)
    elif diag == "se":
        ids = (f"{prefix}_sw", f"{prefix}_ne")
        b.place_tri(ids[0], "right_triangle",
                    (x0, y0, z), (x0 + 1, y0, z), (x0, y0 + 1, z), color)
        b.place_tri(ids[1], "right_triangle",
                    (x0 + 1, y0 + 1, z), (x0, y0 + 1, z), (x0 + 1, y0, z), color)
    else:
        raise ValueError(diag)
    return ids


def diag_mirror(tid, x0, y0, z, diag, color):
    """折返镜: 直角三角立在台面对角缝上, 斜边贴缝、直角顶点朝天。

    镜面是竖直的 45 度斜墙 —— 弹珠沿格线方向撞上, 反弹转向 90 度;
    一格台面配一面镜, 两格串联即完成 180 度掉头。
    """
    apex = (x0 + 0.5, y0 + 0.5, z + RT_APEX)
    if diag == "ne":
        b.place_tri(tid, "right_triangle",
                    apex, (x0, y0, z), (x0 + 1, y0 + 1, z), color)
    elif diag == "se":
        b.place_tri(tid, "right_triangle",
                    apex, (x0, y0 + 1, z), (x0 + 1, y0, z), color)
    else:
        raise ValueError(diag)


# =================================================================
# 1. 发球塔 (x [0,1], y [1,2]): 塔基 + 两层墙环 + 发球台 + 挡珠
#    塔身占北巷, 塔南侧空地 (y [0,1]) 留给折返镜台 B
# =================================================================
b.flat("base_0", 0, 1, 0.0, BASE)
for lv in range(2):
    b.wall_ns(f"tw{lv}_s", 0, 1.0, lv, TOWER)
    b.wall_ns(f"tw{lv}_n", 0, 2.0, lv, TOWER)
    b.wall_ew(f"tw{lv}_w", 0.0, 1, lv, TOWER)
    b.wall_ew(f"tw{lv}_e", 1.0, 1, lv, TOWER)

for tid, corner, hdir in BRACES:
    b.brace(tid, corner, hdir, BRACE)

b.flat("deck_0", 0, 1, 2.0, DECK)
b.crest_ew("drail_w", 0.0, 1, 2.0, RAIL)
b.crest_ns("drail_n", 0, 2.0, 2.0, RAIL)
b.crest_ns("drail_s", 0, 1.0, 2.0, RAIL)

# =================================================================
# 2. 首段坡道 (z2->z1, 北巷向东) + 折返镜台 A (x [XA,XP], y [0,2])
#    北格镜缝走 NW-SE (+x 反弹成 -y), 南格镜缝走 SW-NE (-y 反弹成 -x)
# =================================================================
b.wall_ew("pier_n", XP, 1, 0, PIER)
b.wall_ew("pier_s", XP, 0, 0, PIER)
b.ramp("ramp_1", "+x", 1.0, 1, 2.0, RAMP)
diag_pad("pa_n", XA, 1, 1.0, "se", PAD_A)
diag_pad("pa_s", XA, 0, 1.0, "ne", PAD_A)
diag_mirror("mir_a_n", XA, 1, 1.0, "se", RAIL)
diag_mirror("mir_a_s", XA, 0, 1.0, "ne", RAIL)

# =================================================================
# 3. 折返坡道 (z1->z0, 南巷向西) + 塔脚折返镜台 B (x [0,1], y [-1,1])
#    北格镜缝走 SW-NE (-x 反弹成 -y), 南格镜缝走 NW-SE (-y 反弹成 +x)
# =================================================================
b.ramp("ramp_2", "-x", XA, 0, 1.0, RAMP)
diag_pad("pb_n", 0, 0, 0.0, "ne", PAD_B)
diag_pad("pb_s", 0, -1, 0.0, "se", PAD_B)
diag_mirror("mir_b_n", 0, 0, 0.0, "ne", RAIL)
diag_mirror("mir_b_s", 0, -1, 0.0, "se", RAIL)

# =================================================================
# 4. 冲线直道 (y [-1,0] 向东) + 南侧护栏 + 接珠池 (x [4,5])
# =================================================================
for i in range(3):
    b.flat(f"lane_{i}", 1 + i, -1, 0.0, LANE)
    b.crest_ns(f"lrail_{i}", 1 + i, -1.0, 0.0, RAIL)
b.flat("pool_0", 4, -1, 0.0, POOL)
b.wall_ew("pool_e", 5.0, -1, 0, POOL_WALL)
b.wall_ns("pool_n", 4, 0.0, 0, POOL_WALL)
b.wall_ns("pool_s", 4, -1.0, 0, POOL_WALL)

# =================================================================
# 教程步骤 (10 步)
# =================================================================
b.step(
    "铺塔基: 一片灰色方板打底, 四片蓝色方板合围第一层墙环。",
    ["base_0", "tw0_s", "tw0_w", "tw0_n", "tw0_e"],
    tip="塔南侧空地先空着 —— 弹珠折返的最后一跳会回到塔脚下。",
)
b.step(
    "塔角斜撑 (T14): 三片紫色直角三角竖直角边吸墙角竖缝、水平边贴地外伸, "
    "西南/西北/东北三角各锁一角。",
    [tid for tid, _, _ in BRACES],
    highlight=["tw0_w", "tw0_n"],
    tip="东南角刻意留空 —— 那里是折返坡道的落珠口, 斜撑会挡道。",
)
b.step(
    "第二层墙 + 发球台: 四片蓝色方板骑上墙顶, 一片黄色方板盖住 z=2。",
    ["tw1_s", "tw1_w", "tw1_n", "tw1_e", "deck_0"],
    highlight=["tw0_s", "tw0_e"],
    tip="两层墙环够高 —— D2 弹珠从 z=2 出发, 落差刚好跑完全程。",
)
b.step(
    "发球台挡珠: 三片红三角围住台沿 (东缘留口), 弹珠只能向东滑出。",
    ["drail_w", "drail_n", "drail_s"],
    highlight=["deck_0"],
    tip="东缘空着 —— 那是首段坡道的唯一出珠口。",
)
b.step(
    "首段下坡 (整段成组): 东侧立双桥墩 (竖缝互吸成门式框架), 橙色坡道顶边"
    "吸发球台东缘; 四片青色直角三角两两沿对角缝拼出镜台 A 台面, 西缘接坡尾、"
    "东缘压墩顶。",
    ["pier_n", "pier_s", "ramp_1", "pa_n_sw", "pa_n_ne", "pa_s_nw", "pa_s_se"],
    highlight=["deck_0", "tw1_e"],
    tip="台面对角缝要拼严 —— 下一步折返镜就立在这条缝上。",
)
b.step(
    "立折返镜 A: 两片红色直角三角立在对角缝上, 斜边贴缝、直角顶点朝天。",
    ["mir_a_n", "mir_a_s"],
    highlight=["pa_n_sw", "pa_s_nw"],
    tip="北镜把东来的弹珠拍向南, 南镜再拍向西 —— 两次 45 度反弹 = 180 度掉头!",
)
b.step(
    "折返下坡: 橙色坡道从镜台 A 南格西缘下探到地面, 四片绿色直角三角在塔脚"
    "拼出镜台 B 台面 (坡尾整边吸台面东缘)。",
    ["ramp_2", "pb_n_se", "pb_n_nw", "pb_s_ne", "pb_s_sw"],
    highlight=["pa_s_nw", "mir_a_s"],
    tip="这段坡道贴着塔南墙外侧向西俯冲 —— 弹珠会径直冲回塔脚。",
)
b.step(
    "立折返镜 B: 塔脚两片红色直角三角再立一组对角镜, 弹珠二次掉头向东。",
    ["mir_b_n", "mir_b_s"],
    highlight=["pb_n_se", "pb_s_sw"],
    tip="镜台 B 的缝口朝东张开 —— 西来的弹珠拍向南、再拍向东冲线。",
)
b.step(
    "铺冲线直道: 三片黄色方板沿塔南向东铺开, 南缘各立一片红三角护栏。",
    ["lane_0", "lane_1", "lane_2", "lrail_0", "lrail_1", "lrail_2"],
    highlight=["pb_s_ne", "mir_b_s"],
    tip="直道西缘整边吸镜台 B —— 弹珠出镜即上跑道, 不落缝。",
)
b.step(
    "接珠池收尾: 一片青色方板做池底, 东/北/南三面蓝色矮墙围合 —— "
    "折返坡道滚珠塔完工, 放珠开滑!",
    ["pool_0", "pool_e", "pool_n", "pool_s"],
    highlight=["lane_2"],
    tip="东下 → 镜台 A 掉头 → 西折 → 镜台 B 掉头 → 东冲线 —— 听两组镜子各响两声才算验收!",
)

model = b.finalize(
    model_id="switchback_ramp_01",
    name="折返坡道滚珠塔",
    name_en="Switchback Ramp 01",
    description=(
        "滚珠乐园 D2 折返塔: 弹珠从两层发球台向东冲下 30 度坡道, 在直角三角"
        "对角镜台上连续两次 45 度反弹完成 180 度掉头, 折返向西俯冲回塔脚, "
        "经第二组镜台再次掉头后沿冲线直道滚进接珠池; 招牌是 T08 滚珠轨道 + "
        "T14 直角三角镜台 (台面对角拼 + 缝上立镜, 共 15 片直角三角), "
        "之字动线与双轨绕塔/螺旋/退台/分流拓扑均不同, 全部 CORE-9, "
        "实物跑珠即可验证两次掉头。"
    ),
    difficulty=2,
    tags=["滚珠", "轨道", "折返", "滚珠乐园", "直角三角"],
    min_pieces=40,
    min_steps=10,
    series="marble_run",
)

meta = model["content_meta"]
meta["technique_tags"] = {
    "primary": "T08_marble_run",
    "secondary": ["T14_diagonal_bracing"],
}
meta["signature_statement"] = (
    "两片直角三角对角拼台、第三片立缝为镜的折返镜台, 让弹珠靠两次 45 度"
    "反弹完成 180 度掉头, 之字往返后停在塔脚。"
)
meta["structural_signature"]["silhouette_class"] = "switchback_tower"
meta["structural_signature"]["height_layers"] = 3

out = Path(__file__).resolve().parent.parent / "data" / "models" / "switchback_ramp_01.json"
out.write_text(json.dumps(model, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
