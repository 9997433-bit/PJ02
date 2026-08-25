#!/usr/bin/env python3
"""生成模型 data/models/marble_relay_city_01.json (四塔接力滚珠城)。

四座 2x2 发球塔 + 十字连廊 + 四条换轨顺时针接力 (T08/T16)。

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
    "ab": {"cx": 2, "cy": 0, "rails": [], "gps": [("ns", 2, 0.0), ("ns", 2, 1.0)]},
    "bc": {"cx": 4, "cy": 2, "rails": [], "gps": [("ew", 4.0, 2), ("ew", 4.0, 3)]},
    "cd": {"cx": 2, "cy": 4, "rails": [], "gps": [("ns", 2, 3.0), ("ns", 2, 4.0)]},
    "da": {"cx": 0, "cy": 2, "rails": [], "gps": [("ew", 1.0, 2), ("ew", 0.0, 2)]},
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
        b.crest_ns(f"{prefix}_cr0", x0 + 1, float(y0), 2.0, RAIL)
    ids.append(f"{prefix}_cr0")
    b.spire_ns(f"{prefix}_rn", x0 + 1, float(y0 + 2), 2.0, "purple")
    ids.append(f"{prefix}_rn")
    return ids


def build_link(key):
    s = LINKS[key]
    cx, cy = s["cx"], s["cy"]
    c = f"lk_{key}_c"
    b.flat(c, cx, cy, 2.0, PLAT)
    gps = []
    for i, (gk, ga, gl) in enumerate(s["gps"]):
        for z0 in (0, 1):
            gid = f"lk_{key}_gp{i}_{z0}"
            if gk == "ns":
                b.wall_ns(gid, ga, float(gl), z0, PIER)
            else:
                b.wall_ew(gid, float(ga), gl, z0, PIER)
        gps.append(f"lk_{key}_gp{i}_0")
        gps.append(f"lk_{key}_gp{i}_1")
    rails = []
    for i, (kind, a, lane, z) in enumerate(s["rails"]):
        rid = f"lk_{key}_r{i}"
        if kind == "ew":
            b.crest_ew(rid, a, lane, z, RAIL)
        else:
            b.crest_ns(rid, a, lane, z, RAIL)
        rails.append(rid)
    return gps + [c] + rails


BRIDGE = []
for y in (0, 1):
    b.flat(f"bridge_ab_{y}", 2, y, 0.0, "gray")
    BRIDGE.append(f"bridge_ab_{y}")
for x in (3, 4):
    tid = f"bridge_bc_{x}"
    b.flat(tid, x, 2, 0.0, "gray")
    BRIDGE.append(tid)
b.flat("bridge_cd_4", 2, 4, 0.0, "gray")
BRIDGE.append("bridge_cd_4")
for x in (0, 1):
    b.flat(f"bridge_da_{x}", x, 2, 0.0, "gray")
    BRIDGE.append(f"bridge_da_{x}")
for i, j in ((2, 2), (2, 3)):
    b.flat(f"bridge_c_{i}_{j}", i, j, 0.0, "gray")
    BRIDGE.append(f"bridge_c_{i}_{j}")

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


def w0(p):
    open_side = next(spec[3] for spec in TOWERS if spec[0] == p)
    order = {"s": ["e", "n", "w"], "n": ["e", "s", "w"], "w": ["e", "s", "n"], "e": ["w", "s", "n"]}
    out = []
    for side in order[open_side]:
        out += [t for t in part(p, "body") if f"_w0{side[0]}" in t]
    return out


def w1_pad_rn(p):
    walls = [t for t in part(p, "body") if "_w1" in t]
    pads = [t for t in part(p, "body") if t.endswith("_p0_0") or t.endswith("_p0_1")
            or t.endswith("_p1_0") or t.endswith("_p1_1")]
    rn = [t for t in part(p, "body") if t.endswith("_rn")]
    return walls + pads + rn


def link_piers(key):
    return [f"lk_{key}_gp{i}_{z}" for i in (0, 1) for z in (0, 1)]


def link_track(key):
    return [f"lk_{key}_c"]


b.step(
    "铺十字连廊: 十片方板拼成十字地基 —— 四象限一次闭合。",
    BRIDGE,
    tip="连廊是四塔接力的公共地基 —— 必须整圈互吸。",
)

TOWER_SEQ = [
    ("A (西南)", "ta", "bridge_ab_0", "ab"),
    ("B (东南)", "tb", "bridge_ab_0", "bc"),
    ("C (东北)", "tc", "bridge_bc_3", "cd"),
    ("D (西北)", "td", "bridge_c_2_3", "da"),
]

for label, p, hl, lk in TOWER_SEQ:
    b.step(
        f"塔 {label} 基座 + 换轨桥墩: 广场对接连廊, 门式立柱先落地。",
        part(p, "base") + link_piers(lk),
        highlight=(hl,),
    )
    b.step(
        f"塔 {label} 第 1 层墙: 三面合围 (出珠面保持敞开)。",
        w0(p),
        highlight=(f"{p}_g0_0",),
    )
    b.step(
        f"塔 {label} 第 2 层 + 发球台 + 塔尖。",
        w1_pad_rn(p),
        highlight=(f"{p}_pd0",),
    )
    b.step(
        f"塔 {label} 出站滑道 + 换轨 {lk.upper()} + 围栏 —— 顺时针接力就绪。",
        part(p, "ramp") + link_track(lk) + part(p, "crest"),
        highlight=(f"{p}_p0_0", f"lk_{lk}_c"),
        tip="T16 分体对接: 坡道顶 z=2 锁发球台 —— 换轨台与门式立柱同组互吸。",
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
    min_pieces=105,
    min_steps=17,
    series="marble_run",
)
