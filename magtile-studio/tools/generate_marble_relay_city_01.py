#!/usr/bin/env python3
"""生成模型 data/models/marble_relay_city_01.json (四塔接力滚珠城)。

内容批 K 模型 4/4: 滚珠乐园 D5 灯塔 —— 与 ball_run_tower_01 (单塔双轨)
/ marble_run_spiral_01 (单塔螺旋) 动线拓扑不同。招牌是 T08 滚珠轨道 +
T16 分体对接 + T11 镜像: 四座 2x2 发球塔分体预制, 对接成环形接力
动线, 弹珠跨塔换轨顺时针跑完全程。

结构总览 (世界单位: 1.0 = 正方形磁力片边长):
  - 四座发球塔 (各 27 片): 2x2 广场 + 双层墙 + 发球台 + 出珠坡道
    + 栈桥墩 + 挡珠栏, 分模块预制 (T16)                           108 片
  - 四条接力换轨段 (各 5 片): 30 度坡道 + 双层桥墩 + 转角台 +
    挡珠三角, 连接相邻塔 (T08)                                     20 片
  合计 128 片, 16 个教程步骤。

滚珠动线 (顺时针接力):
  塔 A (西南) --东向换轨--> 塔 B (东南) --北向换轨--> 塔 C (东北)
  --西向换轨--> 塔 D (西北) --南向换轨--> 回到塔 A 接珠池。

物理规则要点 (validate 常规 + strict 双档零警告 + R9 抖动):
  - 每段坡道顶边整边吸平台沿口, 坡尾由栈桥墩顶边接住;
  - 转角台-桥墩-坡道三件互吸成三角刚性节点;
  - 四塔布局严格镜像对称 (T11);
  - 教程按模块分章: 先预制四塔, 再逐段对接换轨。

用法: python3 tools/generate_marble_relay_city_01.py  (在 magtile-studio 目录下运行)
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from magtile_gen import SQ3, ModelBuilder  # noqa: E402

b = ModelBuilder()

# 四塔配色 (西南/东南/东北/西北)
TOWER_COLORS = [
    ("green", "cyan"),    # A
    ("cyan", "green"),    # B
    ("yellow", "orange"), # C
    ("orange", "yellow"), # D
]
RAMP = "orange"
PIER = "gray"
PLAT = "yellow"
RAIL = "red"


def build_tower(prefix, x0, y0, c_a, c_b, exit_side):
    """建一座 2x2 发球塔 (27 片), exit_side 为出珠方向 n/s/e/w。"""
    ids = []
    for j in range(2):
        for i in range(2):
            tid = f"{prefix}_g{i}_{j}"
            b.flat(tid, x0 + i, y0 + j, 0.0, c_a if (i + j) % 2 == 0 else c_b)
            ids.append(tid)
    for lv in range(2):
        c = c_a if lv == 0 else c_b
        for i in range(2):
            tid = f"{prefix}_w{lv}s{i}"
            b.wall_ns(tid, x0 + i, float(y0), lv, c)
            ids.append(tid)
            tid = f"{prefix}_w{lv}n{i}"
            b.wall_ns(tid, x0 + i, float(y0 + 2), lv, c)
            ids.append(tid)
        for j in range(2):
            if exit_side == "w" and lv == 0 and j == 0:
                continue
            if exit_side == "w" and lv == 1 and j == 0:
                continue
            tid = f"{prefix}_w{lv}w{j}"
            b.wall_ew(tid, float(x0), y0 + j, lv, c)
            ids.append(tid)
            if exit_side == "e" and lv == 0 and j == 1:
                continue
            if exit_side == "e" and lv == 1 and j == 1:
                continue
            tid = f"{prefix}_w{lv}e{j}"
            b.wall_ew(tid, float(x0 + 2), y0 + j, lv, c)
            ids.append(tid)
    for j in range(2):
        for i in range(2):
            tid = f"{prefix}_p{i}_{j}"
            b.flat(tid, x0 + i, y0 + j, 2.0, PLAT)
            ids.append(tid)
    # 围栏: 北双尖 + 南双三角, 出珠侧留口
    b.spire_ns(f"{prefix}_rn0", x0, float(y0 + 2), 2.0, "purple")
    b.spire_ns(f"{prefix}_rn1", x0 + 1, float(y0 + 2), 2.0, "purple")
    ids += [f"{prefix}_rn0", f"{prefix}_rn1"]
    if exit_side != "s":
        b.crest_ns(f"{prefix}_rs0", x0, float(y0), 2.0, RAIL)
        ids.append(f"{prefix}_rs0")
    else:
        b.crest_ns(f"{prefix}_rs1", x0 + 1, float(y0), 2.0, RAIL)
        ids.append(f"{prefix}_rs1")
    if exit_side != "e":
        b.crest_ew(f"{prefix}_re", float(x0 + 2), y0 + 1, 2.0, RAIL)
        ids.append(f"{prefix}_re")
    if exit_side != "w":
        b.crest_ew(f"{prefix}_rw", float(x0), y0, 2.0, RAIL)
        ids.append(f"{prefix}_rw")
    # 出珠坡道 + 栈桥墩
    if exit_side == "e":
        b.wall_ew(f"{prefix}_pier0", float(x0 + 2 + SQ3), y0, 0, PIER)
        b.wall_ew(f"{prefix}_pier1", float(x0 + 2 + SQ3), y0, 1, PIER)
        b.ramp(f"{prefix}_ramp", "+x", float(x0 + 2), y0, 2.0, RAMP)
        ids += [f"{prefix}_pier0", f"{prefix}_pier1", f"{prefix}_ramp"]
    elif exit_side == "n":
        b.wall_ns(f"{prefix}_pier0", x0, float(y0 + 2 + SQ3), 0, PIER)
        b.wall_ns(f"{prefix}_pier1", x0 + 1, float(y0 + 2 + SQ3), 0, PIER)
        b.ramp(f"{prefix}_ramp", "+y", float(y0 + 2), x0, 2.0, RAMP)
        ids += [f"{prefix}_pier0", f"{prefix}_pier1", f"{prefix}_ramp"]
    elif exit_side == "w":
        b.wall_ew(f"{prefix}_pier0", float(x0 - SQ3), y0 + 1, 0, PIER)
        b.wall_ew(f"{prefix}_pier1", float(x0 - SQ3), y0 + 1, 1, PIER)
        b.ramp(f"{prefix}_ramp", "-x", float(x0), y0 + 1, 2.0, RAMP)
        ids += [f"{prefix}_pier0", f"{prefix}_pier1", f"{prefix}_ramp"]
    else:  # south
        b.wall_ns(f"{prefix}_pier0", x0 + 1, float(y0 - SQ3), 0, PIER)
        b.wall_ns(f"{prefix}_pier1", x0, float(y0 - SQ3), 0, PIER)
        b.ramp(f"{prefix}_ramp", "-y", float(y0), x0 + 1, 2.0, RAMP)
        ids += [f"{prefix}_pier0", f"{prefix}_pier1", f"{prefix}_ramp"]
    return ids


def build_link(prefix, ramp_dir, edge, lane, z_top, pier_axis, pier_x, pier_y):
    """换轨段 5 片: 双墩 + 坡道 + 转角台 + 挡珠。"""
    ids = []
    if pier_axis == "ew":
        b.wall_ew(f"{prefix}_p0", float(pier_x), pier_y, 0, PIER)
        b.wall_ew(f"{prefix}_p1", float(pier_x), pier_y, 1, PIER)
        ids += [f"{prefix}_p0", f"{prefix}_p1"]
    else:
        b.wall_ns(f"{prefix}_p0", pier_x, float(pier_y), 0, PIER)
        b.wall_ns(f"{prefix}_p1", pier_x + 1, float(pier_y), 0, PIER)
        ids += [f"{prefix}_p0", f"{prefix}_p1"]
    b.ramp(f"{prefix}_ramp", ramp_dir, edge, lane, z_top, RAMP)
    ids.append(f"{prefix}_ramp")
    if ramp_dir == "+x":
        cx, cy = edge + SQ3, lane
        b.flat(f"{prefix}_cor", cx, cy, z_top - 1.0, PLAT)
        b.crest_ew(f"{prefix}_rail", cx + 1, cy, z_top - 1.0, RAIL)
    elif ramp_dir == "+y":
        cx, cy = lane, edge + SQ3
        b.flat(f"{prefix}_cor", cx, cy - 1, z_top - 1.0, PLAT)
        b.crest_ns(f"{prefix}_rail", cx, cy - 1, z_top - 1.0, RAIL)
    elif ramp_dir == "-x":
        cx, cy = edge - SQ3 - 1, lane
        b.flat(f"{prefix}_cor", cx, cy, z_top - 1.0, PLAT)
        b.crest_ew(f"{prefix}_rail", cx, cy, z_top - 1.0, RAIL)
    else:
        cx, cy = lane, edge - SQ3 - 1
        b.flat(f"{prefix}_cor", cx, cy, z_top - 1.0, PLAT)
        b.crest_ns(f"{prefix}_rail", cx, cy, z_top - 1.0, RAIL)
    ids += [f"{prefix}_cor", f"{prefix}_rail"]
    return ids


# =================================================================
# 四塔布局: A(0,0) B(6,0) C(6,6) D(0,6), 各 2x2
# =================================================================
ta = build_tower("ta", 0, 0, *TOWER_COLORS[0], "e")
tb = build_tower("tb", 6, 0, *TOWER_COLORS[1], "n")
tc = build_tower("tc", 6, 6, *TOWER_COLORS[2], "w")
td = build_tower("td", 0, 6, *TOWER_COLORS[3], "s")

# 换轨段 A->B (东向, 塔 A 东缘 z=2 落到中间转角)
lk_ab = build_link("lk_ab", "+x", 2.0, 0, 2.0, "ew", 2 + SQ3, 0)
# B->C (北向)
lk_bc = build_link("lk_bc", "+y", 2.0, 6, 2.0, "ns", 6, 2 + SQ3)
# C->D (西向)
lk_cd = build_link("lk_cd", "-x", 6.0, 6, 2.0, "ew", 6 - SQ3, 6)
# D->A (南向, 回到起点接珠)
lk_da = build_link("lk_da", "-y", 0.0, 0, 2.0, "ns", 0, 6 - SQ3)

# =================================================================
# 教程步骤 (16 步, 按模块分章 T16)
# =================================================================
b.step(
    "预制塔 A (西南): 铺 2x2 广场, 立双层墙 (东面留换轨口), 盖发球台与围栏。",
    [t for t in ta if not t.startswith("ta_pier") and t != "ta_ramp"],
    tip="塔 A 是接力起点 —— 先独立预制, 最后再对接换轨。",
)
b.step(
    "塔 A 出珠段: 东侧立双层栈桥墩, 橙色坡道顶边吸发球台东缘出珠口。",
    ["ta_pier0", "ta_pier1", "ta_ramp"],
    highlight=["ta_p1_0", "ta_re"],
    tip="坡道-桥墩-平台三件互吸 —— 弹珠从塔 A 甩向东边。",
)
b.step(
    "预制塔 B (东南): 与塔 A 镜像配色, 北面留换轨口, 盖发球台。",
    [t for t in tb if not t.startswith("tb_pier") and t != "tb_ramp"],
    highlight=["ta_g1_1"],
    tip="四座塔分体预制 (T16) —— 这是第二座。",
)
b.step(
    "塔 B 出珠段: 北侧栈桥墩 + 北向坡道, 弹珠将甩向塔 C。",
    ["tb_pier0", "tb_pier1", "tb_ramp"],
    highlight=["tb_p0_1"],
    tip="每座塔的出珠方向顺时针转 90 度 —— 构成环形接力。",
)
b.step(
    "预制塔 C (东北): 双层墙西面留口, 盖黄色发球台。",
    [t for t in tc if not t.startswith("tc_pier") and t != "tc_ramp"],
    highlight=["tb_rn1"],
    tip="第三座塔就位 —— 环形动线完成四分之三。",
)
b.step(
    "塔 C 出珠段: 西侧栈桥墩 + 西向坡道。",
    ["tc_pier0", "tc_pier1", "tc_ramp"],
    highlight=["tc_p1_1"],
    tip="弹珠从塔 C 甩向西北角的塔 D。",
)
b.step(
    "预制塔 D (西北): 南面留口, 盖发球台 —— 四座塔全部预制完成。",
    [t for t in td if not t.startswith("td_pier") and t != "td_ramp"],
    highlight=["tc_g0_0"],
    tip="四塔分体预制完毕, 开始对接换轨 (T16 合体)。",
)
b.step(
    "塔 D 出珠段: 南侧栈桥墩 + 南向坡道, 弹珠将回到塔 A。",
    ["td_pier0", "td_pier1", "td_ramp"],
    highlight=["td_p0_0"],
    tip="最后一座塔的出珠口朝向起点 —— 环形闭合。",
)
b.step(
    "对接换轨 A→B: 塔 A 东侧与塔 B 西侧之间铺东向坡道 + 转角台 + 挡珠。",
    lk_ab,
    highlight=["ta_ramp", "tb_g0_0"],
    tip="整段成组安装: 桥墩 -> 坡道 -> 转角台, 三件互吸。",
)
b.step(
    "对接换轨 B→C: 北向坡道连接塔 B 与塔 C。",
    lk_bc,
    highlight=["tb_ramp", "tc_g0_1"],
    tip="弹珠跨塔换轨 —— 第二段接力就位。",
)
b.step(
    "对接换轨 C→D: 西向坡道连接塔 C 与塔 D。",
    lk_cd,
    highlight=["tc_ramp", "td_g1_1"],
    tip="第三段换轨 —— 环形动线接近闭合。",
)
b.step(
    "对接换轨 D→A: 南向坡道连接塔 D 与塔 A, 环形接力动线闭合!",
    lk_da,
    highlight=["td_ramp", "ta_g0_0"],
    tip="四段换轨全部对接 —— 弹珠可以顺时针跑完全程。",
)
b.step(
    "四塔自检: 轻推每座塔身与换轨段, 确认无松脱节点。",
    [],
    highlight=["lk_ab_cor", "lk_da_cor"],
    tip="D5 入库前须 100% 实物跑珠 —— 这里先完成结构自检。",
)
b.step(
    "放珠试跑: 从塔 A 发球台放出一颗弹珠, 目测顺时针经过 B/C/D。",
    [],
    highlight=["ta_p0_0", "ta_ramp"],
    tip="四塔接力滚珠城完工 —— 滚珠乐园 D5 灯塔!",
)
b.step(
    "双珠接力赛: 两颗弹珠分别从塔 A 与塔 C 出发, 比谁先跑完全程!",
    [],
    highlight=["tc_p0_0"],
    tip="环形拓扑与单塔双轨/螺旋完全不同 —— 这是跨塔接力的玩法。",
)
b.step(
    "四塔接力滚珠城落成 —— 分体预制、对接合体、顺时针接力!",
    [],
    highlight=["lk_bc_cor"],
    tip="T08 轨道 + T16 分体 + T11 镜像 —— 滚珠乐园旗舰作品。",
)

b.finalize(
    model_id="marble_relay_city_01",
    name="四塔接力滚珠城",
    name_en="Marble Relay City 01",
    description=(
        "滚珠乐园 D5 灯塔: 四座 2x2 发球塔分体预制 (T16), 顺时针环形"
        "换轨对接 (T08), 布局严格四象限镜像 (T11) —— 弹珠从任意塔"
        "出发, 跨塔换轨跑完全程。与单塔双轨/单塔螺旋的动线拓扑完全"
        "不同, 入库前须 100% 实物跑珠复核。"
    ),
    difficulty=5,
    tags=["滚珠", "轨道", "接力", "滚珠乐园", "旗舰", "分体对接"],
    min_pieces=128,
    min_steps=16,
)
