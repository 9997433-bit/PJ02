#!/usr/bin/env python3
"""生成模型 data/models/expansion_orb_01.json (扩展合球摆件).

内容批 P 模型 10/10: 几何艺术 D4, 豪华 198 片套装扩展片型 showcase。
基于 geodesic_dome_01 验证骨架 + 菱/梯/六/扇四扩展片型。

用法: python3 tools/generate_expansion_orb_01.py
"""

import json
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from magtile_gen import ModelBuilder, world_vertices  # noqa: E402

b = ModelBuilder()
CX, CY = 1.5, 1.5
R = 1.0
Z0 = 0.0
BAND_H = math.sqrt(1.0 - (2.0 * math.sin(math.radians(15))) ** 2)
Z_RING = Z0 + 2.0 + BAND_H

V = [(CX + R * math.cos(math.radians(60 * k)),
      CY + R * math.sin(math.radians(60 * k))) for k in range(6)]
T = [(CX + R * math.cos(math.radians(60 * k + 30)),
      CY + R * math.sin(math.radians(60 * k + 30))) for k in range(6)]


def n_out(k):
    ang = math.radians(60 * k + 30)
    return (math.cos(ang), math.sin(ang), 0.0)


def e_hex(k, z):
    a, c = V[k], V[(k + 1) % 6]
    return (a[0], a[1], z), (c[0], c[1], z)


def cap_edge(k, z):
    a0 = math.radians(30 + 60 * k)
    a1 = math.radians(30 + 60 * (k + 1))
    return ((CX + R * math.cos(a0), CY + R * math.sin(a0), z),
            (CX + R * math.cos(a1), CY + R * math.sin(a1), z))


# ---- 球底 (geodesic 广场) ----
b.add("floor", "hexagon", (CX, CY, Z0), (0, 0, 0), "cyan")
for k in range(6):
    a, c = e_hex(k, Z0)
    b.place_edge(f"pl_sq_{k}", "square", 0, a, c, n_out(k), "blue")
for k in range(6):
    vk = (V[k][0], V[k][1], Z0)
    p0 = (V[k][0] + n_out(k - 1)[0], V[k][1] + n_out(k - 1)[1], Z0)
    p1 = (V[k][0] + n_out(k)[0], V[k][1] + n_out(k)[1], Z0)
    b.place_tri(f"pl_tri_{k}", "equilateral_triangle", p0, p1, vk, "blue")

# ---- 菱形外饰 (6) ----
for k in range(6):
    a, c = e_hex(k, Z0)
    o0 = (a[0] + n_out(k)[0], a[1] + n_out(k)[1], Z0)
    o1 = (c[0] + n_out(k)[0], c[1] + n_out(k)[1], Z0)
    hint = (o0[0] + n_out(k)[0] * 0.5, o0[1] + n_out(k)[1] * 0.5, 0.5)
    b.place_edge(f"rh_{k}", "rhombus", 0, o0, o1, hint, "purple" if k % 2 else "pink")

# ---- 展台围边 (6, 立在菱形外饰外沿) ----
for k in range(6):
    t = next(x for x in b.tiles if x["id"] == f"rh_{k}")
    v = world_vertices(t)
    best = None
    for i in range(4):
        e0, e1 = v[i], v[(i + 1) % 4]
        mid = ((e0[0] + e1[0]) / 2, (e0[1] + e1[1]) / 2, e0[2])
        d = (mid[0] - CX) ** 2 + (mid[1] - CY) ** 2
        if best is None or d > best[0]:
            best = (d, e0, e1)
    _, e0, e1 = best
    b.place_edge(f"rim_{k}", "square", 0, e0, e1, (0, 0, 1), "gray")

# ---- 展台角饰 (5) ----
for k in range(5):
    t = next(x for x in b.tiles if x["id"] == f"rim_{k}")
    v = world_vertices(t)
    top_z = max(p[2] for p in v)
    for i in range(4):
        e0, e1 = v[i], v[(i + 1) % 4]
        if abs(e0[2] - top_z) < 0.01 and abs(e1[2] - top_z) < 0.01:
            b.place_edge(f"fin_{k}", "equilateral_triangle", 0, e0, e1, (0, 0, 1), "yellow")
            break

# ---- 筒身两层 (封闭薄壳) ----
for k in range(6):
    a, c = e_hex(k, Z0)
    b.place_edge(f"dr1_{k}", "square", 0, a, c, (0, 0, 1), "clear")
for k in range(6):
    a, c = e_hex(k, Z0 + 1.0)
    b.place_edge(f"dr2_{k}", "square", 0, a, c, (0, 0, 1), "cyan")

# ---- 测地三角带 (12) ----
for k in range(6):
    a, c = e_hex(k, Z0 + 2.0)
    apex = (T[k][0], T[k][1], Z_RING)
    b.place_tri(f"up_{k}", "equilateral_triangle", a, c, apex, "clear")
for k in range(6):
    t0 = (T[k - 1][0], T[k - 1][1], Z_RING)
    t1 = (T[k][0], T[k][1], Z_RING)
    vk = (V[k][0], V[k][1], Z0 + 2.0)
    b.place_tri(f"dn_{k}", "equilateral_triangle", t1, t0, vk, "cyan")

# ---- 赤道六棱 (6) ----
for k in range(6):
    t0, t1 = T[k], T[(k + 1) % 6]
    b.place_edge(f"hex_{k}", "hexagon", 0,
                 (t0[0], t0[1], Z_RING), (t1[0], t1[1], Z_RING), (0, 0, 1), "green")

# ---- 顶盖 + 梯形冠 (4) + 扇形极冠 (4) ----
b.add("cap", "hexagon", (CX, CY, Z_RING), (0, 0, 30), "yellow")
for k in range(4):
    a, c = cap_edge(k, Z_RING)
    mid = ((a[0] + c[0]) / 2, (a[1] + c[1]) / 2, Z_RING)
    hint = (mid[0] - CX, mid[1] - CY, 1.0)
    b.place_edge(f"trap_{k}", "trapezoid", 2, a, c, hint, "orange")
for k in range(4):
    t = next(x for x in b.tiles if x["id"] == f"trap_{k}")
    v = world_vertices(t)
    e0, e1 = v[1], v[2]
    mid = tuple((e0[i] + e1[i]) / 2 for i in range(3))
    hint = (mid[0] - CX, mid[1] - CY, 1.0)
    b.place_edge(f"sec_{k}", "sector", 0, e0, e1, hint,
                 "red" if k % 2 else "orange")

# ---- 广场旗饰 (6) ----
for k in range(6):
    e0 = (V[k][0] + n_out(k)[0], V[k][1] + n_out(k)[1], Z0)
    e1 = (V[(k + 1) % 6][0] + n_out(k)[0], V[(k + 1) % 6][1] + n_out(k)[1], Z0)
    b.place_edge(f"fl_{k}", "equilateral_triangle", 0, e0, e1, (0, 0, 1), "red")

# ---- 教程 (18 步) ----
b.step("放球底六边形。", ["floor"])
b.step("铺六瓣方环。", [f"pl_sq_{k}" for k in range(6)], highlight=["floor"])
b.step("补楔角 (闭合广场环)。", [f"pl_tri_{k}" for k in range(6)], highlight=["pl_sq_0"],
       tip="六片楔角合拢, 广场环闭合。")
b.step("贴菱形外饰 (前半)。", ["rh_0", "rh_1", "rh_2"], highlight=["pl_sq_0"])
b.step("菱形外饰 (后半)。", ["rh_3", "rh_4", "rh_5"], highlight=["rh_0"])
b.step("立展台围边 (前半)。", ["rim_0", "rim_1", "rim_2"], highlight=["rh_0"])
b.step("围边 (后半) + 角饰。", ["rim_3", "rim_4", "rim_5"] + [f"fin_{k}" for k in range(5)],
       highlight=["rim_0"])
b.step("旗饰 (前半)。", ["fl_0", "fl_1", "fl_2"], highlight=["pl_tri_0"])
b.step("旗饰 (后半)。", ["fl_3", "fl_4", "fl_5"], highlight=["fl_0"])
b.step("立筒身下层 (前半)。", ["dr1_0", "dr1_1", "dr1_2"], highlight=["floor"])
b.step("筒身下层 (后半)。", ["dr1_3", "dr1_4", "dr1_5"], highlight=["dr1_0"])
b.step("立筒身上层 (前半)。", ["dr2_0", "dr2_1", "dr2_2"], highlight=["dr1_0"])
b.step("筒身上层 (后半)。", ["dr2_3", "dr2_4", "dr2_5"], highlight=["dr2_0"])
b.step("测地三角带正立 (前半)。", ["up_0", "up_1", "up_2"], highlight=["dr2_0"], tip="T07 测地收分。")
b.step("测地三角带正立 (后半)。", ["up_3", "up_4", "up_5"], highlight=["up_0"])
b.step("嵌入倒立三角 (前半)。", ["dn_0", "dn_1", "dn_2"], highlight=["up_0"])
b.step("嵌入倒立三角 (后半) + 赤道六棱 (前半)。", ["dn_3", "dn_4", "dn_5", "hex_0", "hex_1", "hex_2"],
       highlight=["dn_0"], tip="T13 薄壳合围。")
b.step("赤道六棱 (后半) + 顶盖。", ["hex_3", "hex_4", "hex_5", "cap"], highlight=["hex_0"])
b.step("装梯形冠 (前半)。", ["trap_0", "trap_1"], highlight=["cap"], tip="梯形收分 —— 扩展片型。")
b.step("装梯形冠 (后半) + 扇形极冠 —— 扩展合球摆件落成!",
       ["trap_2", "trap_3", "sec_0", "sec_1", "sec_2", "sec_3"],
       highlight=["trap_0"], tip="豪华 198 片四扩展片型 showcase!")

model = b.finalize(
    model_id="expansion_orb_01",
    name="扩展合球摆件",
    name_en="Expansion Orb Display 01",
    description=(
        "几何艺术 D4: 六瓣广场围边上立空心测地球壳 —— 六边形底 + 菱形外饰 + "
        "反棱柱测地带 (T07) + 赤道六棱环 + 顶盖梯形冠 + 四扇形极冠 (T13); "
        "菱/梯/六/扇四扩展片型齐聚, 无内支撑, 是豪华 198 片套装 showcase。"
    ),
    difficulty=4,
    tags=["几何艺术", "多面体", "测地网格", "扩展片型", "摆件", "挑战", "需要扩展装"],
    min_pieces=75,
    min_steps=18,
    series="geometric_art",
)
meta = model["content_meta"]
meta["technique_tags"] = {
    "primary": "T07_geodesic_dome_approx",
    "secondary": ["T13_hollow_shell", "T05_folding_net_to_3d"],
}
meta["signature_statement"] = "四扩展片型拼成测地近似空心球壳, 无内支撑。"
Path(__file__).resolve().parent.parent.joinpath("data/models/expansion_orb_01.json").write_text(
    json.dumps(model, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
