#!/usr/bin/env python3
"""生成模型 data/models/giant_ferris_wheel_01.json (巨型摩天轮骨架)。

D5 幻想与机械: 镜像双 A 形三角桁架 (T02/T11) + 水平轮轴桥 + 竖轮面
(六边形轮毂 + 五外辐 + 四辐间桁弦), 场边斜撑 (T14); 静态展示。
用法: python3 tools/generate_giant_ferris_wheel_01.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from magtile_gen import ModelBuilder, HEX_APOTHEM, world_vertices  # noqa: E402

b = ModelBuilder()

STEEL = "gray"
TRUSS = "red"
TRUSS2 = "orange"
HUB_C = "yellow"
RIM = "purple"
SPOKE = "cyan"
BRACE = "blue"

TRI_H = 0.866025
FRAME_Z = 3
WHEEL_Y = 4.0
WHEEL_X = 4.5
WHEEL_Z = FRAME_Z + HEX_APOTHEM
HUB = (WHEEL_X, WHEEL_Y, WHEEL_Z)


def _hex_verts():
    tmp = ModelBuilder()
    tmp.add("_hex", "hexagon", HUB, (90, 0, 0), "gray")
    return [tuple(round(c, 6) for c in v) for v in world_vertices(tmp.tiles[0])]


HV = _hex_verts()


def star_apex(p0, p1):
    mx, mz = (p0[0] + p1[0]) / 2, (p0[2] + p1[2]) / 2
    return (round(2 * mx - HUB[0], 6), WHEEL_Y, round(2 * mz - HUB[2], 6))


def warren_level(prefix, x, z, color):
    """A 架一层两段桁架弦杆 (南/北 bay), 底边整边吸腿顶。"""
    zt = z + 1
    xe = x + 1
    b.place_tri(f"{prefix}_su", "equilateral_triangle",
                (x, 3, zt), (xe, 3, zt), (x + 0.5, 3 + TRI_H, zt), color)
    b.place_tri(f"{prefix}_nu", "equilateral_triangle",
                (x, 5, zt), (xe, 5, zt), (x + 0.5, 5 - TRI_H, zt), color)


def build_a_frame(prefix, x):
    for z in (0, 1, 2):
        b.wall_ns(f"{prefix}_leg_s_{z}", x, 3, z, STEEL)
        b.wall_ns(f"{prefix}_leg_n_{z}", x, 5, z, STEEL)
        b.wall_ns(f"{prefix}_tie_{z}", x, 4, z, STEEL)
    for z in (0, 1):
        warren_level(f"{prefix}_w{z}", x, z, TRUSS if z % 2 == 0 else TRUSS2)
    b.flat(f"{prefix}_cap_s", x, 3, FRAME_Z, STEEL)
    b.flat(f"{prefix}_cap_n", x, 5, FRAME_Z, STEEL)


# --- 1. 地台 ---
for xi, x in enumerate((0, 1, 2)):
    for yi, y in enumerate((3, 5)):
        b.flat(f"base_L_{xi}_{yi}", x, y, 0.0, STEEL if (xi + yi) % 2 else "cyan")
for xi, x in enumerate((7, 8, 9)):
    for yi, y in enumerate((3, 5)):
        b.flat(f"base_R_{xi}_{yi}", x, y, 0.0, STEEL if (xi + yi) % 2 else "cyan")
b.flat("pad_L", 3, 3, 0.0, STEEL)
b.flat("pad_R", 6, 3, 0.0, "cyan")
b.flat("pad_Ln", 3, 5, 0.0, "cyan")
b.flat("pad_Rn", 6, 5, 0.0, STEEL)
for x, y in ((4, 3), (5, 3), (4, 5), (5, 5)):
    b.flat(f"mid_{x}_{y}", x, y, 0.0, STEEL if (x + y) % 2 else "cyan")
for x in (2, 3, 4, 5, 6, 7):
    b.flat(f"lane_{x}", x, 4, 0.0, STEEL if x % 2 else "cyan")
for x in (1, 8):
    b.flat(f"lane_e_{x}", x, 4, 0.0, "cyan" if x == 1 else STEEL)
b.flat("lane_w", 0, 4, 0.0, STEEL)
b.flat("lane_e9", 9, 4, 0.0, "cyan")
b.flat("deck_n", 4, 6, 0.0, STEEL)
for x, y in ((0, 6), (1, 6), (8, 6), (9, 6)):
    b.flat(f"ext_{x}_{y}", x, y, 0.0, STEEL if (x + y) % 2 else "cyan")

# --- 2. 镜像双 A 架 ---
build_a_frame("la", 2)
build_a_frame("ra", 7)

# --- 3. 轮轴桥 ---
for x in range(3, 7):
    b.flat(f"axle_{x}", x, 3, FRAME_Z, STEEL if x % 2 else "cyan")

# --- 4. 场边斜撑 (24 片直角) ---
b.brace("br_Ls", (0.0, 3.0, 0.0), "+x", BRACE)
b.brace("br_Ln", (0.0, 6.0, 0.0), "+x", BRACE)
b.brace("br_Rs", (9.0, 3.0, 0.0), "-x", BRACE)
b.brace("br_Rn", (9.0, 6.0, 0.0), "-x", BRACE)
b.brace("br_cw", (3.0, 3.0, 0.0), "+x", BRACE)
b.brace("la_bs", (1.0, 3.0, 0.0), "+x", BRACE)
b.brace("la_bn", (1.0, 5.0, 0.0), "+x", BRACE)
b.brace("gr_ex", (9.0, 4.0, 0.0), "-x", BRACE)
b.brace("gr_wl", (0.0, 4.0, 0.0), "+x", BRACE)
b.brace("gr_ctr", (5.0, 4.0, 0.0), "+y", BRACE)
b.brace("gr_aux", (9.0, 5.0, 0.0), "-x", BRACE)
b.brace("ax_bl", (2.0, 3.0, 0.0), "+y", BRACE)
b.brace("ax_br", (2.0, 5.0, 0.0), "+y", BRACE)
b.brace("ax_el", (7.0, 3.0, 0.0), "+y", BRACE)
b.brace("ax_er", (7.0, 5.0, 0.0), "+y", BRACE)
b.brace("gr_pl", (3.0, 3.0, 0.0), "+y", BRACE)
b.brace("gr_pr", (6.0, 3.0, 0.0), "+y", BRACE)
b.brace("gr_Lw", (1.0, 4.0, 0.0), "+x", BRACE)
b.brace("gr_Lm", (1.0, 3.0, 0.0), "+y", BRACE)
b.brace("gr_Nw", (4.0, 5.0, 0.0), "+y", BRACE)
b.brace("gr_Ne", (5.0, 5.0, 0.0), "+y", BRACE)
b.brace("gr_Sw", (4.0, 3.0, 0.0), "+y", BRACE)
b.brace("gr_Se", (5.0, 3.0, 0.0), "+y", BRACE)

# --- 5. 竖轮面: 六角轮毂 + 五外辐 + 四辐间桁 ---
b.add("whub", "hexagon", HUB, (90, 0, 0), HUB_C)
SPOKE_EDGES = [0, 1, 2, 3, 5]
apex = {}
for e in SPOKE_EDGES:
    p0, p1 = HV[e], HV[(e + 1) % 6]
    apex[e] = star_apex(p0, p1)
    b.place_tri(f"spoke_{e}", "equilateral_triangle", p0, p1, apex[e],
                SPOKE if e % 2 else RIM)
for e in (0, 1, 2, 5):
    v = HV[(e + 1) % 6]
    a0, a1 = apex[e], apex[(e + 1) % 6]
    outer = tuple(a0[i] + a1[i] - v[i] for i in range(3))
    b.place_tri(f"rim_{e}", "equilateral_triangle", v, a0, outer, TRUSS2)

# --- 教程步骤 (25) ---
b.step("铺左足地台 + 西桥 (12 片)。", [f"base_L_{xi}_{yi}" for xi in range(3) for yi in range(2)]
       + ["lane_w", "lane_e_1", "lane_2", "lane_3", "lane_4", "pad_L"])
b.step("铺右足 + 东桥合龙 (12 片)。", ["lane_5", "lane_6", "lane_7", "lane_e_8", "lane_e9",
       "pad_R"] + [f"base_R_{xi}_{yi}" for xi in range(3) for yi in range(2)])
b.step("内足中廊 (5 片)。", ["pad_Rn", "pad_Ln", "mid_4_3", "mid_5_3", "mid_4_5"])
b.step("中廊补板。", ["mid_5_5"])
b.step("北沿补板 (3 片)。", ["deck_n"] + [f"ext_{x}_{y}" for x, y in ((0, 6), (1, 6))])
b.step("北沿东端 (2 片)。", [f"ext_{x}_{y}" for x, y in ((8, 6), (9, 6))])
b.step("竖左 A 南/北腿 + 第一层横系 (z=0)。", ["la_leg_s_0", "la_leg_n_0", "la_tie_0"])
b.step("竖右 A 南/北腿 + 第一层横系 (z=0)。", ["ra_leg_s_0", "ra_leg_n_0", "ra_tie_0"],
       highlight=["la_leg_s_0"])
b.step("左 A 二层墙 + 桁 z=0。", ["la_leg_s_1", "la_leg_n_1", "la_w0_su", "la_w0_nu"])
b.step("右 A 二层墙 + 桁 z=0。", ["ra_leg_s_1", "ra_leg_n_1", "ra_w0_su", "ra_w0_nu"])
b.step("左 A 三层墙 + 桁 z=1。", ["la_leg_s_2", "la_leg_n_2", "la_tie_1", "la_w1_su", "la_w1_nu"])
b.step("右 A 三层墙 + 桁 z=1。", ["ra_leg_s_2", "ra_leg_n_2", "ra_tie_1", "ra_w1_su", "ra_w1_nu"])
b.step("双 A 顶横系 (z=2)。", ["la_tie_2", "ra_tie_2"])
b.step("顶盖板 + 轮轴桥 (8 片)。", ["la_cap_s", "la_cap_n", "ra_cap_s", "ra_cap_n",
       "axle_3", "axle_4", "axle_5", "axle_6"], highlight=["la_tie_2"])
b.step("左柱脚斜撑 + 外场撑。", ["la_bs", "la_bn", "br_Ls", "br_Ln", "br_cw", "gr_Lm"])
b.step("右柱脚斜撑 + 外场撑。", ["br_Rs", "br_Rn", "gr_ex"])
b.step("内足与中廊斜撑 (10 片)。", ["gr_pl", "gr_pr", "gr_Lw", "gr_Nw", "gr_Ne", "gr_Sw",
       "gr_Se", "gr_wl", "gr_ctr", "gr_aux"])
b.step("桥墩斜撑 (4 片)。", ["ax_bl", "ax_br", "ax_el", "ax_er"])
b.step("安装六边形轮毂。", ["whub"], highlight=["axle_4"])
b.step("下外辐 e3。", ["spoke_3"], highlight=["whub", "la_cap_s", "axle_3"])
b.step("下外辐 e5。", ["spoke_5"], highlight=["whub", "ra_cap_n", "axle_6"])
b.step("上外辐 e0/e1。", ["spoke_0", "spoke_1"], highlight=["whub"])
b.step("上外辐 e2。", ["spoke_2"], highlight=["spoke_0"])
b.step("辐间桁架弦杆 (2 段)。", ["rim_0", "rim_1"], highlight=["spoke_0"])
b.step("辐间桁架弦杆合龙 (2 段)。", ["rim_2", "rim_5"], highlight=["rim_0"])

if __name__ == "__main__":
    b.finalize(
        model_id="giant_ferris_wheel_01",
        name="巨型摩天轮骨架",
        name_en="Giant Ferris Wheel Frame 01",
        description=(
            "幻想与机械 D5 旗舰: 镜像双 A 形华伦三角桁架同步长高 (各 6 段弦杆, "
            "合计 12 段闭合), 水平轮轴桥贯穿其间; y=4 竖轮面以六边形轮毂 + 五外辐"
            " + 四辐间桁弦拼成星轮, 下外辐落 A 架顶与桥面三点托举; 场边 24 片"
            "直角斜撑加固; 静态展示, 全 CORE-9。"
        ),
        difficulty=5,
        tags=["幻想", "机械", "摩天轮", "桁架", "旗舰", "大师", "镜像"],
        min_pieces=102,
        min_steps=25,
        series="fantasy_machinery",
    )
