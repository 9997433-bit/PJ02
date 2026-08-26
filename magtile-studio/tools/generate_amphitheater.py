#!/usr/bin/env python3
"""生成模型 data/models/amphitheater_01.json (圆形剧场)。

第三批模型 ⑧: 古代建筑主题 —— 全库第一座放射状几何建筑:
以舞台圆心为极点, 半个六边形的观众席一圈圈向外、一层层向上:
半径 1 内是等边三角形拼的乐池, 半径 1~2 是梯形环带地坪,
半径 2~3 是第一层看台 (立墙抬高 1 格, 台面用 梯形+菱形 拼环),
半径 3~4 是第二层看台 (再抬 1 格, 台面 菱形+梯形+菱形 拼环),
最外圈立护墙与旗饰。正南是希腊式舞台: 双柱门廊、门楣横跨、
山花收顶 —— 观众席的每一片都指向舞台中心。

结构总览 (世界单位: 1.0 = 正方形磁力片边长):
  - 乐池: 3 片等边三角形拼半六边形                                3 片
  - 环带地坪 (半径 1~2): 每扇区 3 片等边三角形放射拼贴            9 片
  - 一层看台: 立墙 6 + 端墙 2 + 台面 (梯形+菱形) x3              14 片
  - 二层看台: 立墙 9 + 端墙 2 + 台面 (菱形+梯形+菱形) x3         20 片
  - 护墙 6 + 旗饰 2                                               8 片
  - 舞台: 台口 2 + 后台地坪 4 + 双柱两层 4 + 门楣 1 + 山花 2      13 片
  - 火炬 2 + 雕像 1                                               3 片
  合计 70 片, 16 个教程步骤, 5 种磁力片形状。

几何要点:
  - 六边形环带的一个扇区恰是 (下底 n+1, 上底 n) 的大梯形:
    n=1 时就是标准梯形; n=2 拆成 梯形+菱形; n=3 拆成 菱形+梯形+菱形
    —— 梯形与菱形第一次作为放射状"地砖"使用;
  - 看台立墙沿六边形边线立起 (60 度转角竖边互吸), 台面内沿的
    单位边正好落在立墙顶边上;
  - 台面端头的放射边压在端墙顶边上, 剪断任何一条铰链线,
    力都能沿环带绕行。

用法: python3 tools/generate_amphitheater.py  (在 magtile-studio 目录下运行)
"""

import math

from magtile_gen import ModelBuilder, world_vertices

b = ModelBuilder()

V = [(round(math.cos(math.radians(60 * k)), 6),
      round(math.sin(math.radians(60 * k)), 6)) for k in range(4)]  # V0..V3


def pt(base, scale, z):
    return (round(base[0] * scale, 6), round(base[1] * scale, 6), z)


def lerp(p, q, t, z):
    return (round(p[0] + (q[0] - p[0]) * t, 6),
            round(p[1] + (q[1] - p[1]) * t, 6), z)


def ring_points(k, n, z):
    """扇区 k、半径 n 的六边形边上的整数分点 (n+1 个)。"""
    a, c = pt(V[k], n, z), pt(V[k + 1], n, z)
    return [lerp(a, c, j / n, z) for j in range(n + 1)]


def place_trap(tid, o0, o1, i0, i1, color):
    """梯形: 下底 o0->o1 (长 2), 上底居中 i0->i1 (长 1)。"""
    om = tuple((o0[t] + o1[t]) / 2 for t in range(3))
    im = tuple((i0[t] + i1[t]) / 2 for t in range(3))
    hint = tuple(im[t] - om[t] for t in range(3))
    b.place_edge(tid, "trapezoid", 0, o0, o1, hint, color)


def place_rh(tid, o0, o1, i_far, i_near, color):
    """菱形: 外边 o0->o1, 内边与之平行 (i_near 靠 o0 一侧)。

    自动尝试两种粘贴方向, 取重建顶点与目标四点吻合的那一种。
    """
    for a, c, d, e in ((o0, o1, i_far, i_near), (o1, o0, i_near, i_far)):
        om = tuple((a[t] + c[t]) / 2 for t in range(3))
        im = tuple((d[t] + e[t]) / 2 for t in range(3))
        hint = tuple(im[t] - om[t] for t in range(3))
        b.place_edge(tid, "rhombus", 0, a, c, hint, color)
        wv = world_vertices(b.tiles[-1])
        if math.dist(wv[2], d) < 1e-3 and math.dist(wv[3], e) < 1e-3:
            return
        b.tiles.pop()           # 方向不对: 撤下重试
        b._ids.discard(tid)
    raise AssertionError(f"{tid}: 菱形两种方向都对不上目标四点")


def place_wall(tid, p0, p1, color):
    b.place_edge(tid, "square", 0, p0, p1, (0, 0, 1), color)


# =================================================================
# 1. 乐池 (半径 1 内) + 环带地坪 (半径 1~2, 每扇区 3 片三角形)
# =================================================================
for k in range(3):
    b.place_tri(f"orch_{k}", "equilateral_triangle",
                (0.0, 0.0, 0.0), pt(V[k], 1, 0.0), pt(V[k + 1], 1, 0.0),
                "yellow")
for k in range(3):
    P = ring_points(k, 1, 0.0)          # 内圈 2 点
    Q = ring_points(k, 2, 0.0)          # 外圈 3 点
    b.place_tri(f"ring_{k}_a", "equilateral_triangle",
                Q[0], Q[1], P[0], "gray")
    b.place_tri(f"ring_{k}_b", "equilateral_triangle",
                P[0], Q[1], P[1], "yellow")
    b.place_tri(f"ring_{k}_c", "equilateral_triangle",
                Q[1], Q[2], P[1], "gray")

# =================================================================
# 2. 一层看台: 立墙沿半径 2 六边形边线, 台面 (梯形+菱形) 在 z=1
# =================================================================
for k in range(3):
    S = ring_points(k, 2, 0.0)
    place_wall(f"r1w_{k}_0", S[0], S[1], "gray")
    place_wall(f"r1w_{k}_1", S[1], S[2], "gray")
place_wall("r1end_e", (2.0, 0.0, 0.0), (3.0, 0.0, 0.0), "gray")
place_wall("r1end_w", (-3.0, 0.0, 0.0), (-2.0, 0.0, 0.0), "gray")
T1_COLORS = ["red", "orange", "red"]
for k in range(3):
    P = ring_points(k, 2, 1.0)
    Q = ring_points(k, 3, 1.0)
    if k < 2:                            # 扇区 0/1: 梯形在前, 菱形在后
        place_trap(f"t1trap_{k}", Q[0], Q[2], P[0], P[1], T1_COLORS[k])
        place_rh(f"t1rh_{k}", Q[2], Q[3], P[2], P[1], "orange")
    else:                                # 扇区 2: 镜像 (菱形在前)
        place_rh(f"t1rh_{k}", Q[0], Q[1], P[1], P[0], "orange")
        place_trap(f"t1trap_{k}", Q[1], Q[3], P[1], P[2], T1_COLORS[k])

# =================================================================
# 3. 二层看台: 立墙沿半径 3 边线 (z 1..2), 台面 菱形+梯形+菱形 (z=2)
# =================================================================
for k in range(3):
    S = ring_points(k, 3, 1.0)
    # 先放正下方有菱形台面整边可吸的那段, 再向两边接龙
    order = ((2, "a"), (1, "b"), (0, "c")) if k < 2 else \
            ((0, "a"), (1, "b"), (2, "c"))
    for j, tag in order:
        place_wall(f"r2w_{k}_{tag}", S[j], S[j + 1], "gray")
place_wall("r2end_e", (3.0, 0.0, 1.0), (4.0, 0.0, 1.0), "gray")
place_wall("r2end_w", (-4.0, 0.0, 1.0), (-3.0, 0.0, 1.0), "gray")
for k in range(3):
    P = ring_points(k, 3, 2.0)
    Q = ring_points(k, 4, 2.0)
    place_rh(f"t2rh_{k}_a", Q[0], Q[1], P[1], P[0], "red")
    place_trap(f"t2trap_{k}", Q[1], Q[3], P[1], P[2], "orange")
    place_rh(f"t2rh_{k}_b", Q[3], Q[4], P[3], P[2], "red")

# =================================================================
# 4. 护墙 (z 2..3, 立在二层台面外沿的菱形单位边上) + 旗饰
# =================================================================
for k in range(3):
    S = ring_points(k, 4, 2.0)
    place_wall(f"para_{k}_a", S[0], S[1], "gray")
    place_wall(f"para_{k}_b", S[3], S[4], "gray")
S1 = ring_points(1, 4, 3.0)
b.place_edge("banner_w", "equilateral_triangle", 0,
             S1[0], S1[1], (0, 0, 1), "purple")
b.place_edge("banner_e", "equilateral_triangle", 0,
             S1[3], S1[4], (0, 0, 1), "purple")

# =================================================================
# 5. 舞台 (正南): 台口 + 后台地坪 + 双柱门廊 + 门楣 + 山花
# =================================================================
b.flat("stage_w", -1, -1, 0, "yellow")        # 台口
b.flat("stage_e", 0, -1, 0, "yellow")
for i in range(4):                            # 后台地坪
    b.flat(f"skene_{i}", -2 + i, -2, 0, "gray")
b.wall_ns("col_w_lo", -2, -1, 0, "gray")      # 西柱两层
b.wall_ns("col_w_hi", -2, -1, 1, "gray")
b.wall_ns("col_e_lo", 1, -1, 0, "gray")       # 东柱两层
b.wall_ns("col_e_hi", 1, -1, 1, "gray")
b.lintel_ns("architrave", -1, -1, 1, "orange")  # 门楣横跨台口
b.crest_ns("pediment_w", -2, -1, 2, "red")    # 山花
b.crest_ns("pediment_e", 1, -1, 2, "red")
b.crest_ew("torch_w", -1, -2, 0, "yellow")    # 火炬
b.crest_ew("torch_e", 1, -2, 0, "yellow")
b.crest_ew("statue", 0, -1, 0, "purple")      # 乐池雕像

# =================================================================
# 教程步骤 (16 步)
# =================================================================
b.step(
    "拼乐池: 3 片黄色等边三角形共用圆心, 拼成半个六边形 —— "
    "整座剧场的极点就在这里。",
    ["orch_0", "orch_1", "orch_2"],
    tip="三片的放射边两两互吸, 直边冲南 —— 那是舞台的方向。",
)
b.step(
    "铺台口与后台地坪: 2 片黄色台口方板贴住乐池直边, "
    "4 片灰色方板向南铺出后台。",
    ["stage_w", "stage_e", "skene_0", "skene_1", "skene_2", "skene_3"],
    highlight=["orch_0"],
    tip="台口方板与乐池的南直边整边吸合 —— 方格与六边形在此握手。",
)
b.step(
    "铺环带地坪东扇区: 灰-黄-灰 3 片三角形沿半径向外放射拼贴。",
    ["ring_0_a", "ring_0_b", "ring_0_c"],
    highlight=["orch_0"],
    tip="正三角贴外圈边、倒三角尖朝外 —— 环带就是三角形的接龙。",
)
b.step(
    "铺环带地坪北/西扇区: 再各 3 片, 半圆环带合拢。",
    ["ring_1_a", "ring_1_b", "ring_1_c", "ring_2_a", "ring_2_b", "ring_2_c"],
    highlight=["ring_0_a"],
    tip="相邻扇区的放射边互吸, 拼完是一条完整的半环。",
)
b.step(
    "立一层看台墙: 6 片灰色正方形沿半径 2 的六边形边线立起。",
    ["r1w_0_0", "r1w_0_1", "r1w_1_0", "r1w_1_1", "r1w_2_0", "r1w_2_1"],
    highlight=["ring_0_a", "ring_2_c"],
    tip="墙底吸环带外沿, 60 度转角处竖边互吸 —— 环形墙自锁。",
)
b.step(
    "封一层端墙: 东西两端各 1 片正方形立在直径线上。",
    ["r1end_e", "r1end_w"],
    highlight=["r1w_0_0", "r1w_2_1"],
    tip="端墙竖边吸住看台墙的转角竖边, 也是台面端头的支座。",
)
b.step(
    "铺一层台面: 每扇区 1 片大梯形 + 1 片菱形拼成环带坐席, "
    "内沿的单位边压住立墙顶边。",
    ["t1trap_0", "t1rh_0", "t1trap_1", "t1rh_1", "t1rh_2", "t1trap_2"],
    highlight=["r1w_0_0", "r1end_e"],
    tip="梯形与菱形第一次当'地砖'用 —— 放射环带只有它们拼得出。",
)
b.step(
    "立二层看台墙: 9 片灰色正方形沿半径 3 边线立在一层台面外沿, "
    "每边先立菱形正上方那段。",
    ["r2w_0_a", "r2w_0_b", "r2w_0_c",
     "r2w_1_a", "r2w_1_b", "r2w_1_c",
     "r2w_2_a", "r2w_2_b", "r2w_2_c"],
    highlight=["t1rh_0", "t1trap_0"],
    tip="菱形台面的外沿是单位边, 正好给这段墙当底座。",
)
b.step(
    "封二层端墙: 东西两端再各 1 片, 立在直径线 z=1 高度。",
    ["r2end_e", "r2end_w"],
    highlight=["r2w_0_a", "r2w_2_a"],
    tip="端墙竖边吸二层看台墙的转角竖边, 顶边等着接台面。",
)
b.step(
    "铺二层台面: 每扇区 菱形-梯形-菱形 3 片拼环, 环带更宽一圈。",
    ["t2rh_0_a", "t2trap_0", "t2rh_0_b",
     "t2rh_1_a", "t2trap_1", "t2rh_1_b",
     "t2rh_2_a", "t2trap_2", "t2rh_2_b"],
    highlight=["r2w_0_a", "r2end_e"],
    tip="半径越大环带越宽: n 到 n+1 的环带要多拆一片菱形。",
)
b.step(
    "立护墙: 6 片灰色正方形立在二层台面外沿的菱形单位边上。",
    ["para_0_a", "para_0_b", "para_1_a", "para_1_b", "para_2_a", "para_2_b"],
    highlight=["t2rh_0_a", "t2rh_0_b"],
    tip="护墙挡住最后一排观众的后背 —— 也是剧场的天际线。",
)
b.step(
    "挂旗饰: 2 片紫色等边三角形立在正北护墙顶边上。",
    ["banner_w", "banner_e"],
    highlight=["para_1_a", "para_1_b"],
    tip="旗子立在 3 格高的护墙顶上, 全场最高点。",
)
b.step(
    "立门廊双柱下段: 东西各 1 片灰色正方形立在后台地坪北沿。",
    ["col_w_lo", "col_e_lo"],
    highlight=["skene_0", "skene_3"],
    tip="双柱夹出 2 格宽的舞台口, 正对乐池圆心。",
)
b.step(
    "接柱上段并横跨门楣: 双柱各加高 1 格, 1 根橙色长方形横跨"
    "台口上方, 两端竖边吸住柱身。",
    ["col_w_hi", "col_e_hi", "architrave"],
    highlight=["col_w_lo", "col_e_lo"],
    tip="门楣下是 2 格宽的负空间台口 —— 演员从这里登场。",
)
b.step(
    "戴山花: 2 片红色等边三角形立在双柱顶上收顶。",
    ["pediment_w", "pediment_e"],
    highlight=["architrave"],
    tip="山花与门楣组成希腊门廊的经典轮廓。",
)
b.step(
    "点火炬、立雕像: 台口两侧火炬点亮, 乐池中缝立起缪斯雕像 —— "
    "圆形剧场开演!",
    ["torch_w", "torch_e", "statue"],
    highlight=["stage_w", "stage_e"],
    tip="从最高一排俯瞰: 每一片看台都指向舞台中心。",
)

b.finalize(
    model_id="amphitheater_01",
    name="圆形剧场",
    name_en="Amphitheater 01",
    description=(
        "古代建筑主题: 全库第一座放射状几何建筑 —— 以舞台圆心为极点, "
        "半六边形观众席一圈圈向外、一层层向上: 三角形乐池与环带地坪"
        "打底, 两层看台各由立墙抬高 1 格, 台面用 梯形+菱形 的放射"
        "环带拼成 (半径每大 1, 环带就多拆一片菱形), 台面端头压在"
        "直径线端墙上, 剪断任何一条铰链线力都能沿环带绕行; 最外圈"
        "护墙挂旗, 正南希腊门廊双柱托门楣、山花收顶, 火炬与缪斯"
        "雕像守着台口 —— 每一片都指向舞台中心。"
    ),
    difficulty=3,
    tags=["古代建筑", "剧场", "放射环带", "看台", "挑战"],
    min_pieces=68,
    min_steps=16,
)
