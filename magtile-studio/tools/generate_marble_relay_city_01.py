#!/usr/bin/env python3
"""生成模型 data/models/marble_relay_city_01.json (四塔接力滚珠城)。

四座 2x2 发球塔 + 十字连廊 + 四条换轨顺时针接力 (T08/T16)。
换轨转角台在连廊格 z=1, 桥墩由发球塔出珠面墙兼任 (零重叠)。

用法: python3 tools/generate_marble_relay_city_01.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from magtile_gen import ModelBuilder  # noqa: E402

b = ModelBuilder()

TC = [("green", "cyan"), ("cyan", "green"), ("yellow", "orange"), ("orange", "yellow")]
RAMP, PIER, PLAT, RAIL = "orange", "gray", "yellow", "red"

TOWERS = [
    ("ta", 0, 0, "e", TC[0]),
    ("tb", 3, 0, "n", TC[1]),
    ("tc", 3, 3, "w", TC[2]),
    ("td", 0, 3, "s", TC[3]),
]

LINKS = {
    "ab": {"cx": 2, "cy": 0, "rails": [("ns", 2, 1.0, 2.0), ("ew", 3.0, 0, 2.0)]},
    "bc": {"cx": 4, "cy": 2, "rails": [("ew", 4.0, 2, 2.0), ("ns", 3, 3.0, 2.0)]},
    "cd": {"cx": 2, "cy": 4, "rails": [("ns", 2, 3.0, 2.0), ("ew", 3.0, 3, 2.0)]},
    "da": {"cx": 0, "cy": 2, "rails": [("ew", 0.0, 2, 2.0), ("ns", 0, 3.0, 2.0)]},
}


def build_tower(prefix, x0, y0, exit_side, colors):
    ca, cb = colors
    ids = []
    for j in range(2):
        for i in range(2):
            tid = f"{prefix}_g{i}_{j}"
            b.flat(tid, x0 + i, y0 + j, 0.0, ca if (i + j) % 2 == 0 else cb)
            ids.append(tid)
    for lv in range(2):
        c = ca if lv == 0 else cb
        if exit_side != "s":
            for i in range(2):
                b.wall_ns(f"{prefix}_w{lv}s{i}", x0 + i, float(y0), lv, c)
                ids.append(f"{prefix}_w{lv}s{i}")
        if exit_side != "n":
            for i in range(2):
                b.wall_ns(f"{prefix}_w{lv}n{i}", x0 + i, float(y0 + 2), lv, c)
                ids.append(f"{prefix}_w{lv}n{i}")
        if exit_side != "w":
            for j in range(2):
                b.wall_ew(f"{prefix}_w{lv}w{j}", float(x0), y0 + j, lv, c)
                ids.append(f"{prefix}_w{lv}w{j}")
        if exit_side != "e":
            for j in range(2):
                b.wall_ew(f"{prefix}_w{lv}e{j}", float(x0 + 2), y0 + j, lv, c)
                ids.append(f"{prefix}_w{lv}e{j}")
    if exit_side == "e":
        b.wall_ew(f"{prefix}_pd0", float(x0 + 2), y0, 0, PIER)
        b.wall_ew(f"{prefix}_pd1", float(x0 + 2), y0, 1, PIER)
        b.ramp(f"{prefix}_ramp", "+x", float(x0 + 2), y0, 2.0, RAMP)
    elif exit_side == "n":
        b.wall_ns(f"{prefix}_pd0", x0, float(y0 + 2), 0, PIER)
        b.wall_ns(f"{prefix}_pd1", x0 + 1, float(y0 + 2), 0, PIER)
        b.ramp(f"{prefix}_ramp", "+y", float(y0 + 2), x0, 2.0, RAMP)
    elif exit_side == "w":
        b.wall_ew(f"{prefix}_pd0", float(x0), y0, 0, PIER)
        b.wall_ew(f"{prefix}_pd1", float(x0), y0, 1, PIER)
        b.ramp(f"{prefix}_ramp", "-x", float(x0), y0, 2.0, RAMP)
    else:
        b.wall_ns(f"{prefix}_pd0", x0, float(y0), 0, PIER)
        b.wall_ns(f"{prefix}_pd1", x0 + 1, float(y0), 0, PIER)
        b.ramp(f"{prefix}_ramp", "-y", float(y0), x0, 2.0, RAMP)
    ids += [f"{prefix}_pd0", f"{prefix}_pd1", f"{prefix}_ramp"]
    for j in range(2):
        for i in range(2):
            tid = f"{prefix}_p{i}_{j}"
            b.flat(tid, x0 + i, y0 + j, 2.0, PLAT)
            ids.append(tid)
    if exit_side == "e":
        b.crest_ew(f"{prefix}_cr0", float(x0), y0 + 1, 2.0, RAIL)
    elif exit_side == "n":
        b.crest_ns(f"{prefix}_cr0", x0 + 1, float(y0), 2.0, RAIL)
    elif exit_side == "w":
        b.crest_ns(f"{prefix}_cr0", x0, float(y0 + 1), 2.0, RAIL)
    else:
        b.crest_ns(f"{prefix}_cr0", x0 + 1, float(y0 + 2), 2.0, RAIL)
    ids.append(f"{prefix}_cr0")
    b.spire_ns(f"{prefix}_rn", x0 + 1, float(y0 + 2), 2.0, "purple")
    ids.append(f"{prefix}_rn")
    return ids


def build_link(key):
    s = LINKS[key]
    cx, cy = s["cx"], s["cy"]
    c = f"lk_{key}_c"
    b.flat(c, cx, cy, 2.0, PLAT)
    b.brace(f"lk_{key}_br", (float(cx), float(cy), 1.0), "+y" if cy <= 2 else "-y", PIER)
    rails = []
    for i, (kind, a, lane, z) in enumerate(s["rails"]):
        rid = f"lk_{key}_r{i}"
        if kind == "ew":
            b.crest_ew(rid, a, lane, z, RAIL)
        else:
            b.crest_ns(rid, a, lane, z, RAIL)
        rails.append(rid)
    return [c, f"lk_{key}_br"] + rails


BRIDGE = []
for y in (0, 1):
    b.flat(f"bridge_ab_{y}", 2, y, 0.0, "gray")
    b.flat(f"bridge_ab_{y}_d", 2, y, 1.0, "gray")
    BRIDGE += [f"bridge_ab_{y}", f"bridge_ab_{y}_d"]
for x in (3, 4):
    b.flat(f"bridge_bc_{x}", x, 2, 0.0, "gray")
    b.flat(f"bridge_bc_{x}_d", x, 2, 1.0, "gray")
    BRIDGE += [f"bridge_bc_{x}", f"bridge_bc_{x}_d"]
for y in (3, 4):
    b.flat(f"bridge_cd_{y}", 2, y, 0.0, "gray")
    b.flat(f"bridge_cd_{y}_d", 2, y, 1.0, "gray")
    BRIDGE += [f"bridge_cd_{y}", f"bridge_cd_{y}_d"]
for x in (0, 1):
    b.flat(f"bridge_da_{x}", x, 2, 0.0, "gray")
    b.flat(f"bridge_da_{x}_d", x, 2, 1.0, "gray")
    BRIDGE += [f"bridge_da_{x}", f"bridge_da_{x}_d"]

tower_parts = {spec[0]: build_tower(*spec) for spec in TOWERS}
link_parts = {k: build_link(k) for k in LINKS}


def part(p, kind):
    out = []
    for tid in tower_parts[p]:
        bn = tid[len(p) + 1:]
        if kind == "base" and (bn.startswith("g") or bn.startswith("pd")):
            out.append(tid)
        elif kind == "body" and (
            bn.startswith("w") or bn == "rn"
            or (bn.startswith("p") and not bn.startswith("pd"))
        ):
            out.append(tid)
        elif kind == "crest" and bn.startswith("cr"):
            out.append(tid)
        elif kind == "ramp" and bn == "ramp":
            out.append(tid)
    return out


b.step(
    "铺十字连廊: 十六片方板 (地面 + 一层栈道) 一次闭合。",
    BRIDGE,
    tip="连廊是四塔接力的公共地基 —— 必须整圈互吸。",
)

TOWER_SEQ = [
    ("A (西南)", "ta", "bridge_ab_0", "ab"),
    ("B (东南)", "tb", "bridge_ab_0", "bc"),
    ("C (东北)", "tc", "bridge_bc_3", "cd"),
    ("D (西北)", "td", "bridge_cd_3", "da"),
]

for label, p, hl, lk in TOWER_SEQ:
    b.step(
        f"塔 {label} 模块: 广场 + 换轨 {lk.upper()} 成组对接连廊。",
        part(p, "base") + link_parts[lk],
        highlight=(hl,),
        tip="T16 分体对接: 趁墙未合围先装完整换轨段, 与发球塔桥墩互吸。",
    )

for label, p, hl, lk in TOWER_SEQ:
    b.step(
        f"塔 {label} 第 1 层墙: 三面合围 (出珠面保持敞开)。",
        [t for t in part(p, "body") if "_w0" in t],
        highlight=(f"{p}_g0_0",),
    )

for label, p, hl, lk in TOWER_SEQ:
    b.step(
        f"塔 {label} 第 2 层 + 发球台 + 塔尖。",
        [t for t in part(p, "body") if "_w1" in t or t.endswith("_rn")
         or t.endswith("_p0_0") or t.endswith("_p0_1")
         or t.endswith("_p1_0") or t.endswith("_p1_1")],
        highlight=(f"{p}_pd0",),
    )

for label, p, hl, lk in TOWER_SEQ:
    b.step(
        f"塔 {label} 出珠坡道 + 围栏 —— 顺时针接力就绪。",
        part(p, "ramp") + part(p, "crest"),
        highlight=(f"{p}_p0_0", f"lk_{lk}_c"),
        tip="坡道顶边吸发球台沿口 —— 轻摇应纹丝不动。",
    )

b.finalize(
    model_id="marble_relay_city_01",
    name="四塔接力滚珠城",
    name_en="Marble Relay City 01",
    description=(
        "滚珠乐园 D5 灯塔: 四座 2x2 发球塔在 6x6 紧凑方阵分体预制 (T16), "
        "十字地面连廊贯通全场, 四条短换轨顺时针接力 (T08), 四象限镜像"
        " (T11) —— 弹珠跨塔换轨跑完全程。"
    ),
    difficulty=5,
    tags=["滚珠", "轨道", "接力", "滚珠乐园", "旗舰", "分体对接"],
    min_pieces=120,
    min_steps=18,
    series="marble_run",
)
