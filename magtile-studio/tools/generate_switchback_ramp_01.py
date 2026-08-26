#!/usr/bin/env python3
"""生成模型 data/models/switchback_ramp_01.json (之字闸门滚珠廊)。

内容批 P 模型 8/10 (P8) 全新重写: 滚珠乐园 D2 —— 招牌是「直角三角
之字闸门」(T08 滚珠轨道 + T14 斜撑的闸门变奏): 弹珠从单层发球塔
顺 30 度坡道冲进一条 2 格宽的地面长廊, 廊内四道竖立的直角三角闸门
交替封住南半幅 / 北半幅 —— 弹珠被迫走出 S 形之字线, 最后冲进
2x2 接珠池。与库内其他滚珠模型的动线拓扑均不同: 不绕塔 (ball_run
_tower)、不螺旋 (marble_run_spiral)、不分流 (marble_splitter)、
不做多级跌落 (marble_cascade) —— 之字横移是本模型独有的一笔。

结构总览 (世界单位: 1.0 = 正方形磁力片边长, 弹珠自 z=1 出发):
  - 发球塔: 塔基 + 三面墙 + 发球台 + 三片挡珠 + 四角斜撑 (T14)  12 片
  - 30 度坡道 (T08): 塔台东缘下探, 坡尾恰落在 x=3 网格线         1 片
  - 之字长廊: 2x5 地板 + 四道直角三角闸门 + 六片三角边挡        20 片
  - 接珠池: 2x2 池底 + 六面矮墙 + 两片直角三角池角斜撑           12 片
  合计 45 片 (正方形 x25 + 直角三角 x10 + 等边三角 x9 + 长方形 x1)。

物理规则要点 (validate 常规 + strict 双档零警告):
  - 发球台东缘 x = 3 - sqrt(3), 坡道顶边整边吸台沿, 坡尾边恰与
    长廊首块地板西缘共线整边互吸 (脚线落在网格线上);
  - 每道闸门是一片竖立直角三角: 底直角边整边吸两块地板的拼缝,
    竖直角边沿长廊边线升起 —— 自身接地, 不吃任何悬挑力矩;
  - 塔基四角与池外角的直角三角斜撑双边吸合 (T14), 抗侧撞;
  - 全程最高点 1.87 (发球台挡珠尖), 不触发 R8 高层结构条款。

用法: python3 tools/generate_switchback_ramp_01.py  (在 magtile-studio 目录下运行)
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from magtile_gen import SQ3, ModelBuilder  # noqa: E402

b = ModelBuilder()

BASE = "gray"      # 塔基
TOWER = "green"    # 塔墙
DECK = "yellow"    # 发球台
RAIL = "red"       # 挡珠三角
BRACE = "purple"   # 直角三角斜撑
RAMP = "orange"    # 坡道
LANE_A = "cyan"    # 长廊地板 (棋盘浅色)
LANE_B = "blue"    # 长廊地板 (棋盘深色)
GATE = "orange"    # 之字闸门
POOL = "blue"      # 接珠池

XE = 3 - SQ3       # 发球台东缘 = 坡道顶边 x (坡尾恰落在 x=3)
XW = XE - 1.0      # 塔基西缘


def gate_south(tid, x):
    """封南半幅的闸门: 底边压 y[0,1] 拼缝, 竖边沿南边线升起。"""
    b.place_tri(tid, "right_triangle",
                (x, 0.0, 0.0), (x, 1.0, 0.0), (x, 0.0, 1.0), GATE)


def gate_north(tid, x):
    """封北半幅的闸门: 底边压 y[1,2] 拼缝, 竖边沿北边线升起。"""
    b.place_tri(tid, "right_triangle",
                (x, 2.0, 0.0), (x, 1.0, 0.0), (x, 2.0, 1.0), GATE)


# =================================================================
# 1. 发球塔: 塔基 + 三面墙 (东缘留给坡道) + 四角斜撑
# =================================================================
b.flat("base", XW, 0, 0.0, BASE)
b.wall_ew("tw_w", XW, 0, 0, TOWER)
b.wall_ns("tw_s", XW, 0.0, 0, TOWER)
b.wall_ns("tw_n", XW, 1.0, 0, TOWER)

BRACES = [
    ("br_sw", (XW, 0.0, 0.0), "-x"),
    ("br_nw", (XW, 1.0, 0.0), "-x"),
    ("br_se", (XE, 0.0, 0.0), "-y"),
    ("br_ne", (XE, 1.0, 0.0), "+y"),
]
for tid, corner, hdir in BRACES:
    b.brace(tid, corner, hdir, BRACE)

# =================================================================
# 2. 发球台 z=1 + 三片挡珠 (东缘留出珠口)
# =================================================================
b.flat("deck", XW, 0, 1.0, DECK)
b.crest_ew("drail_w", XW, 0, 1.0, RAIL)
b.crest_ns("drail_s", XW, 0.0, 1.0, RAIL)
b.crest_ns("drail_n", XW, 1.0, 1.0, RAIL)

# =================================================================
# 3. 30 度坡道: 顶边吸台沿, 坡尾边与长廊首板西缘共线
# =================================================================
b.ramp("ramp", "+x", XE, 0, 1.0, RAMP)

# =================================================================
# 4. 之字长廊: 2x5 棋盘地板 + 四道交替闸门 + 六片三角边挡
# =================================================================
lane_s, lane_n = [], []
for x in range(3, 8):
    b.flat(f"lane_s{x}", x, 0, 0.0, LANE_A if x % 2 else LANE_B)
    lane_s.append(f"lane_s{x}")
for x in range(3, 8):
    b.flat(f"lane_n{x}", x, 1, 0.0, LANE_B if x % 2 else LANE_A)
    lane_n.append(f"lane_n{x}")

gate_south("gate_4", 4.0)
gate_north("gate_5", 5.0)
gate_south("gate_6", 6.0)
gate_north("gate_7", 7.0)

SIDE_RAILS = [
    ("srail_s3", 3, 0.0), ("srail_s5", 5, 0.0), ("srail_s7", 7, 0.0),
    ("srail_n3", 3, 2.0), ("srail_n4", 4, 2.0), ("srail_n6", 6, 2.0),
]
for tid, x0, y in SIDE_RAILS:
    b.crest_ns(tid, x0, y, 0.0, RAIL)

# =================================================================
# 5. 接珠池: 2x2 池底 + 六面矮墙 + 两片池角斜撑
# =================================================================
for x in (8, 9):
    for y in (0, 1):
        b.flat(f"pool_{x}{y}", x, y, 0.0, LANE_A)
b.wall_ew("pw_e0", 10.0, 0, 0, POOL)
b.wall_ew("pw_e1", 10.0, 1, 0, POOL)
b.wall_ns("pw_s8", 8, 0.0, 0, POOL)
b.wall_ns("pw_s9", 9, 0.0, 0, POOL)
b.wall_ns("pw_n8", 8, 2.0, 0, POOL)
b.wall_ns("pw_n9", 9, 2.0, 0, POOL)
b.brace("pbr_se", (10.0, 0.0, 0.0), "+x", BRACE)
b.brace("pbr_ne", (10.0, 2.0, 0.0), "+x", BRACE)

# =================================================================
# 教程步骤 (11 步)
# =================================================================
b.step(
    "铺塔基立墙: 一片灰色方板打底, 西/南/北三面绿墙围合, 东面空着。",
    ["base", "tw_w", "tw_s", "tw_n"],
    tip="东面不砌墙 —— 那是弹珠唯一的出口, 坡道就从这里下探。",
)
b.step(
    "塔基四角斜撑 (T14): 四片紫色直角三角, 竖直角边吸墙角竖缝、水平边贴地外伸。",
    [tid for tid, _, _ in BRACES],
    highlight=["tw_s", "tw_n"],
    tip="双边吸合的斜撑锁死塔身 —— 之字赛道反复开球也撞不倒。",
)
b.step(
    "盖发球台加挡珠: 黄色方板压住三面墙顶, 三片红三角围住西/南/北台沿。",
    ["deck", "drail_w", "drail_s", "drail_n"],
    highlight=["tw_w"],
    tip="发球台 z=1 —— D2 的弹珠只需一层楼的势能就够跑完全程。",
)
b.step(
    "挂 30 度坡道 (T08): 橙色长板顶边整边吸发球台东缘, 坡尾直落地面网格线。",
    ["ramp"],
    highlight=["deck"],
    tip="坡尾边恰好落在 x=3 的网格线上 —— 与长廊首块地板整边互吸。",
)
b.step(
    "铺长廊南列: 五片蓝青棋盘方板沿东向排开, 首板西缘咬住坡尾。",
    lane_s,
    highlight=["ramp"],
    tip="弹珠从南半幅入场 —— 记住这条线, 之字闸门马上要逼它变道。",
)
b.step(
    "铺长廊北列: 五片方板与南列拼缝逐段对齐互吸, 长廊变成 2 格宽。",
    lane_n,
    highlight=["lane_s5"],
    tip="2 格宽才玩得起之字 —— 一半是路, 一半是闸。",
)
b.step(
    "立之字闸门: 四片橙色直角三角骑在地板拼缝上, 交替封南半幅和北半幅。",
    ["gate_4", "gate_5", "gate_6", "gate_7"],
    highlight=["lane_s3", "lane_n4"],
    tip="底直角边整边吸拼缝, 斜边朝来珠方向 —— 弹珠贴着斜面滑向另一半幅。",
)
b.step(
    "装长廊边挡: 六片红三角站上长廊外沿, 与闸门错位互补, 把弹珠兜在场内。",
    [tid for tid, _, _ in SIDE_RAILS],
    highlight=["gate_4", "gate_5"],
    tip="哪边闸门封路, 对面就要有边挡 —— 之字线的每个折点都被兜住。",
)
b.step(
    "铺接珠池底: 四片青色方板拼成 2x2 池底, 西缘咬住长廊末端。",
    ["pool_80", "pool_81", "pool_90", "pool_91"],
    highlight=["lane_s7", "lane_n7"],
    tip="池底与长廊整边互吸 —— 弹珠冲线后直接滚进池心。",
)
b.step(
    "砌池壁: 东/南/北六面蓝色矮墙围合, 西面敞开当冲线口。",
    ["pw_s8", "pw_s9", "pw_e0", "pw_e1", "pw_n9", "pw_n8"],
    highlight=["pool_80"],
    tip="墙脚整边吸池底 —— 三面合围, 弹珠再快也翻不出去。",
)
b.step(
    "池角斜撑收尾: 两片紫色直角三角锁住东墙外角 —— 之字闸门滚珠廊完工, 放珠开滑!",
    ["pbr_se", "pbr_ne"],
    highlight=["pw_e0", "pw_e1"],
    tip="实物验收听声音: 珠子过一道闸门响一声, 四声之后落池才算通关。",
)

model = b.finalize(
    model_id="switchback_ramp_01",
    name="之字闸门滚珠廊",
    name_en="Switchback Ramp 01",
    description=(
        "滚珠乐园 D2 之字长廊: 单层发球塔顺 30 度坡道把弹珠甩进 2 格宽"
        "的地面长廊, 四道竖立的直角三角闸门交替封住南北半幅, 弹珠被迫"
        "走出 S 形之字线, 最后冲进 2x2 接珠池; 招牌是直角三角的三种用法"
        " (之字闸门 + 塔基斜撑 + 池角斜撑, 共 10 片, T08+T14), 与绕塔/"
        "螺旋/分流/跌落的既有滚珠动线全部不同, 全部 CORE-9, 实物跑珠"
        "即可验证。"
    ),
    difficulty=2,
    tags=["滚珠", "轨道", "之字", "滚珠乐园", "直角三角"],
    min_pieces=45,
    min_steps=11,
    series="marble_run",
)

meta = model["content_meta"]
meta["technique_tags"] = {
    "primary": "T08_marble_run",
    "secondary": ["T14_diagonal_bracing"],
}
meta["signature_statement"] = (
    "四道竖立直角三角闸门交替封半幅, 弹珠在地面长廊里走出 S 形之字线。"
)
meta["structural_signature"]["silhouette_class"] = "slalom_gallery"
meta["structural_signature"]["height_layers"] = 2

out = Path(__file__).resolve().parent.parent / "data" / "models" / "switchback_ramp_01.json"
out.write_text(json.dumps(model, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
