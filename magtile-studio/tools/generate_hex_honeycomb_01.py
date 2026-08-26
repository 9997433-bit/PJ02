#!/usr/bin/env python3
"""生成模型 data/models/hex_honeycomb_01.json (蜂窝六角亭)。

内容批 P 模型 3/10: 几何艺术 D2 —— 主打六边形 (hexagon), 全库
六边形片数之最 (20 片)。三层蜂窝结构: 七片六边形平铺成蜂窝花地
(T18 密铺), 六片六边形用 place_edge 立在花地最外沿, 围成
"六边环带蜂窝墙"; 顶上再盖一朵同构的七片蜂窝花作平顶 (T13 薄壳)。
地面十二片等边三角形两两成菱, 把蜂窝花的六个凹口铺成石板广场;
广场外圈再沿石板菱格的十二条外沿边各铺一片正方形 —— 六边形 +
三角形 + 正方形正是 3.4.6.4 半正密铺 (rhombitrihexagonal) 的
片型组合, 密铺艺术从蜂窝花一路长到广场边缘。

结构总览 (世界单位: 1.0 = 正方形磁力片边长, 模型以原点为中心):
  - 蜂窝花地 (z=0): 中心六边形 + 六片环绕, 两两整边互吸        7 片
  - 石板菱格 (z=0): 12 片等边三角形两两成菱嵌进六个凹口        12 片
  - 广场外圈 (z=0): 12 片正方形沿菱格外沿铺成 3.4.6.4 环带     12 片
  - 六边环带墙 (z 0..1.732): 六片六边形立在花地外沿             6 片
  - 蜂窝平顶 (z=1.732): 与花地同构的七片蜂窝花                  7 片
  合计 44 片, 8 个教程步骤, 3 种磁力片形状 (六边形 x20 是招牌)。

蜂窝几何 (与 SHAPES["hexagon"] 顶点表逐位一致, 免累积误差):
  - 蜂窝格心 = 相邻两枚单位顶点向量之和 (C_k = V6[k] + V6[k+1]),
    间距 2 x HEX_APOTHEM, 共享整边;
  - 环带墙底边 = 外圈六边形的最外沿边 (apothem 3A ≈ 2.598),
    相邻立墙的平面夹角 120 度, 侧沿在角线处恰好点接不相交;
  - 立墙竖直高 2A ≈ 1.732, 顶边正好落在平顶蜂窝花的外沿边上。

物理规则要点 (validate 常规 + strict 双档零警告):
  - 立墙质心恰在底边铰链正上方, 力矩为零 (逐片立墙的中间态安全);
  - 平顶七片一步合拢: 步末状态即封闭环带, 剪断任意一条墙顶铰链
    仍有其余五面墙承托, R6 悬臂分析不触发;
  - 全高 1.732 < 2.5, 不进入 R8 高层结构口径;
  - 石板菱格两两互吸并整边贴花地, 扩大接地凸包;
  - 广场外圈正方形平铺接地, 底边与菱格外沿整边互吸 (每片剪断
    只失联 1 片), 接地凸包进一步外扩, R4 裕量更足。

用法: python3 tools/generate_hex_honeycomb_01.py  (在 magtile-studio 目录下运行)
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from magtile_gen import HEX_APOTHEM, SHAPES, ModelBuilder  # noqa: E402

b = ModelBuilder()

A = HEX_APOTHEM          # 0.866025
H = 2 * A                # 环带墙高 = 平顶标高 1.73205

FLOOR_CORE = "yellow"
FLOOR_RING = "orange"
PAVE = "gray"
PLAZA_A = "gray"
PLAZA_B = "clear"
WALL_A = "clear"
WALL_B = "yellow"
ROOF_RING = "yellow"
ROOF_CORE = "orange"

# 单位六边形顶点 (角度 60k), 与 tile_catalog / SHAPES 逐位一致
V6 = [tuple(v) for v in SHAPES["hexagon"]]


def vadd(*pts):
    return (sum(p[0] for p in pts), sum(p[1] for p in pts))


# 蜂窝花格心: C_k = V6[k] + V6[k+1] (方位角 30+60k, 间距 2A)
C = [vadd(V6[k], V6[(k + 1) % 6]) for k in range(6)]


# =================================================================
# 1. 蜂窝花地 (z=0): 中心 + 六片环绕, honeycomb flower
# =================================================================
b.add("floor_c", "hexagon", (0.0, 0.0, 0.0), (0, 0, 0), FLOOR_CORE)
for k in range(6):
    b.add(f"floor_{k}", "hexagon", (C[k][0], C[k][1], 0.0), (0, 0, 0), FLOOR_RING)

# =================================================================
# 2. 石板菱格 (z=0): 每个凹口两片等边三角形共边成菱
#    凹口 j 位于方位角 60j, 顶点 N = 2*V6[j], 两条花地闲边
#    N->N+V6[j-1] 与 N->N+V6[j+1], 合尖于 P = N + V6[j]
# =================================================================
for j in range(6):
    N = vadd(V6[j], V6[j])
    FA = vadd(N, V6[(j + 5) % 6])
    FB = vadd(N, V6[(j + 1) % 6])
    P = vadd(N, V6[j])
    b.place_tri(f"pave_{j}a", "equilateral_triangle",
                (N[0], N[1], 0.0), (FA[0], FA[1], 0.0), (P[0], P[1], 0.0), PAVE)
    b.place_tri(f"pave_{j}b", "equilateral_triangle",
                (N[0], N[1], 0.0), (FB[0], FB[1], 0.0), (P[0], P[1], 0.0), PAVE)

# =================================================================
# 2b. 广场外圈 (z=0): 石板菱格的两条外沿边 (FA->P / FB->P) 各铺
#     一片正方形, 内侧提示背向合尖点 N —— 六边形/三角形/正方形
#     恰为 3.4.6.4 半正密铺的顶点组合, 外圈方板互不重叠
# =================================================================
for j in range(6):
    N = vadd(V6[j], V6[j])
    FA = vadd(N, V6[(j + 5) % 6])
    FB = vadd(N, V6[(j + 1) % 6])
    P = vadd(N, V6[j])
    for s, F, color in (("a", FA, PLAZA_A), ("b", FB, PLAZA_B)):
        mid = ((F[0] + P[0]) / 2, (F[1] + P[1]) / 2)
        hint = (mid[0] - N[0], mid[1] - N[1], 0.0)
        b.place_edge(f"plaza_{j}{s}", "square", 0,
                     (F[0], F[1], 0.0), (P[0], P[1], 0.0), hint, color)

# =================================================================
# 3. 六边环带蜂窝墙: 六片六边形以底边 (本地边 4) 立在花地最外沿
# =================================================================
for k in range(6):
    E0 = vadd(C[k], V6[k])
    E1 = vadd(C[k], V6[(k + 1) % 6])
    b.place_edge(f"wall_{k}", "hexagon", 4,
                 (E0[0], E0[1], 0.0), (E1[0], E1[1], 0.0),
                 (0, 0, 1), WALL_A if k % 2 == 0 else WALL_B)

# =================================================================
# 4. 蜂窝平顶 (z=H): 与花地同构, 外圈外沿边整边吸住墙顶边
# =================================================================
for k in range(6):
    b.add(f"roof_{k}", "hexagon", (C[k][0], C[k][1], H), (0, 0, 0), ROOF_RING)
b.add("roof_c", "hexagon", (0.0, 0.0, H), (0, 0, 0), ROOF_CORE)

# =================================================================
# 教程步骤 (8 步)
# =================================================================
b.step(
    "铺蜂窝花地: 中心一片六边形, 六片橙色六边形环绕整边互吸 —— 蜂窝密铺的第一朵花。",
    ["floor_c"] + [f"floor_{k}" for k in range(6)],
    tip="每片六边形和邻居共享整条磁力边 —— 蜂窝是自然界最省料的密铺。",
)
b.step(
    "嵌石板菱格 (前半): 六片灰色等边三角形两两合尖成菱, 铺进花地东北侧三个凹口。",
    [f"pave_{j}{s}" for j in (0, 1, 2) for s in ("a", "b")],
    highlight=["floor_0", "floor_1", "floor_2"],
    tip="两片三角形共边拼成菱形石板, 恰好填满花瓣之间 120 度的凹口。",
)
b.step(
    "嵌石板菱格 (后半): 再用六片三角形补齐西南侧三个凹口, 石板广场合围。",
    [f"pave_{j}{s}" for j in (3, 4, 5) for s in ("a", "b")],
    highlight=["pave_0a", "floor_4"],
    tip="十二片三角形 = 六块菱形石板 —— 广场越大, 亭子越稳。",
)
b.step(
    "铺广场外圈 (东北半): 六片方板沿菱格外沿边整边吸上, 灰清相间。",
    [f"plaza_{j}{s}" for j in (0, 1, 2) for s in ("a", "b")],
    highlight=["pave_0a", "pave_1a", "pave_2a"],
    tip="六边形 + 三角形 + 正方形 —— 这正是 3.4.6.4 半正密铺的搭配。",
)
b.step(
    "铺广场外圈 (西南半): 再六片方板补齐外圈, 广场环带合拢。",
    [f"plaza_{j}{s}" for j in (3, 4, 5) for s in ("a", "b")],
    highlight=["plaza_0a", "pave_4a"],
    tip="每片方板整边吸住一条石板外沿 —— 相邻方板在合尖点恰好留出 60 度豁口。",
)
b.step(
    "立环带墙 (隔一面): 三片清色六边形立在花地最外沿, 底边整边吸住花瓣外边。",
    ["wall_0", "wall_2", "wall_4"],
    highlight=["floor_0", "floor_2", "floor_4"],
    tip="六边形立起来重心正压底边 —— 先隔面立三片, 手好伸进去。",
)
b.step(
    "补环带墙 (剩三面): 三片黄色六边形补齐六边环带 —— 蜂窝墙每面独立站稳, 侧沿在角线恰好相触。",
    ["wall_1", "wall_3", "wall_5"],
    highlight=["wall_0", "wall_2"],
    tip="六面墙围成六边环带, 相邻墙面成 120 度 —— 从任何缝隙都能望进亭子。",
)
b.step(
    "盖蜂窝平顶: 六片黄色六边形外沿边逐一吸上墙顶, 中心橙色一片合拢 —— 蜂窝六角亭落成!",
    [f"roof_{k}" for k in range(6)] + ["roof_c"],
    highlight=["wall_0", "wall_1"],
    tip="平顶与花地是同一朵蜂窝花 —— 六面墙同时托住外圈, 环带封顶最稳。",
)

model = b.finalize(
    model_id="hex_honeycomb_01",
    name="蜂窝六角亭",
    name_en="Hex Honeycomb Pavilion 01",
    description=(
        "几何艺术 D2: 20 片六边形的蜂窝专场 —— 七片六边形平铺成蜂窝"
        "花地 (T18 密铺), 六片六边形立在花地最外沿围成六边环带蜂窝墙"
        "(相邻墙面 120 度, 每面质心正压底边铰链), 顶上再盖一朵同构的"
        "七片蜂窝花作平顶 (T13 薄壳合围); 地面十二片等边三角形两两"
        "合尖成菱, 把花瓣之间六个 120 度凹口铺成石板广场, 外圈再沿"
        "菱格外沿铺十二片方板 —— 六边形 + 三角形 + 正方形恰是 3.4.6.4 "
        "半正密铺的组合。花地-环带-平顶三层全部整边互吸, 无一处悬挑, "
        "是扩展装六边形的招牌玩法。"
    ),
    difficulty=2,
    tags=["几何艺术", "蜂窝", "六边形", "密铺", "亭子"],
    min_pieces=44,
    min_steps=8,
    series="geometric_art",
)
meta = model["content_meta"]
meta["technique_tags"] = {
    "primary": "T18_tessellation_art",
    "secondary": ["T13_hollow_shell"],
}
meta["signature_statement"] = "20 片六边形拼出蜂窝花地 + 六边环带墙 + 蜂窝平顶三层同构。"
Path(__file__).resolve().parent.parent.joinpath("data/models/hex_honeycomb_01.json").write_text(
    json.dumps(model, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
