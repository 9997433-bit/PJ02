#!/usr/bin/env python3
"""生成模型 data/models/radio_telescope_01.json (射电望远镜)。

第三批模型 ⑥: 科学观测主题 —— 山谷射电望远镜观测站:
5x5 观测场上立起 1x1 两层馈源塔 (四角风车斜撑加固),
塔顶盖板北沿升起竖直大天线盘 —— 六边形反射面主体 +
5 片等腰三角形接收瓣呈星芒展开; 场地西南角一座带天线的
2x2 控制楼, 东侧两块 30 度斜置太阳能板, 四周警戒旗。

结构总览 (世界单位: 1.0 = 正方形磁力片边长):
  - 观测场 5x5                                              25 片
  - 控制楼: 墙体 7 (东面留门) + 平屋顶 4 + 通讯天线 1       12 片
  - 馈源塔: 1x1 两层 8 + 风车斜撑 4 + 塔顶盖板 1            13 片
  - 天线盘: 六边形反射面 1 + 等腰接收瓣 5                    6 片
  - 太阳能板 x2 + 警戒旗 x4                                  6 片
  合计 62 片, 16 个教程步骤, 6 种磁力片形状。

物理规则要点 (通过 R1~R8 全部校验):
  - 天线盘整体位于竖直平面内 (重力力矩为零), 六边形底边整边
    吸塔顶盖板北沿; 接收瓣底边吸六边形各边, 星芒互不重叠;
  - 馈源塔四角直角三角斜撑双边吸合 (月面着陆器起落架同款);
  - 太阳能板 30 度斜置, 底长边整边吸观测场东沿格线, 自身接地。

用法: python3 tools/generate_radio_telescope.py  (在 magtile-studio 目录下运行)
"""

import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from magtile_gen import COS30, HEX_APOTHEM, ModelBuilder, world_vertices  # noqa: E402

b = ModelBuilder()

# =================================================================
# 1. 观测场 5x5: 灰色场坪点缀绿色草斑
# =================================================================
GRASS = {(0, 4), (4, 0), (2, 4), (4, 3)}
for j in range(5):
    for i in range(5):
        b.flat(f"fd_{i}_{j}", i, j, 0.0, "green" if (i, j) in GRASS else "gray")

# =================================================================
# 2. 控制楼 2x2 (x 0..2, y 0..2): 东面北段留门, 平屋顶 + 通讯天线
# =================================================================
b.wall_ns("cb_s_0", 0, 0.0, 0, "cyan")
b.wall_ns("cb_s_1", 1, 0.0, 0, "cyan")
b.wall_ew("cb_w_0", 0.0, 0, 0, "cyan")
b.wall_ew("cb_w_1", 0.0, 1, 0, "clear")              # 西面观测窗
b.wall_ns("cb_n_0", 0, 2.0, 0, "cyan")
b.wall_ns("cb_n_1", 1, 2.0, 0, "cyan")
b.wall_ew("cb_e_0", 2.0, 0, 0, "cyan")               # 东面南段 (北段 y 1..2 为门)
for j in range(2):
    for i in range(2):
        b.flat(f"cb_r_{i}_{j}", i, j, 1.0, "gray")   # 平屋顶
b.spire_ns("cb_ant", 0, 1.0, 1.0, "red")             # 楼顶通讯天线

# =================================================================
# 3. 馈源塔: 1x1 (x 3..4, y 2..3) 两层 + 风车斜撑 + 塔顶盖板
# =================================================================
for z0 in (0, 1):
    b.wall_ns(f"tw_s_{z0}", 3, 2.0, z0, "yellow")
    b.wall_ew(f"tw_e_{z0}", 4.0, 2, z0, "orange")
    b.wall_ns(f"tw_n_{z0}", 3, 3.0, z0, "yellow")
    b.wall_ew(f"tw_w_{z0}", 3.0, 2, z0, "orange")
BRACES = [
    ("br_sw", (3.0, 2.0, 0.0), "-x"),
    ("br_se", (4.0, 2.0, 0.0), "-y"),
    ("br_ne", (4.0, 3.0, 0.0), "+x"),
    ("br_nw", (3.0, 3.0, 0.0), "+y"),
]
for tid, corner, hdir in BRACES:
    b.brace(tid, corner, hdir, "red")
b.flat("tw_cap", 3, 2, 2.0, "gray")                  # 塔顶盖板

# =================================================================
# 4. 天线盘: 六边形反射面立在盖板北沿 (竖直面 y=3),
#    再沿其余 5 条边展开等腰三角接收瓣 (星芒)
# =================================================================
b.add("dish", "hexagon", (3.5, 3.0, 2 + HEX_APOTHEM), (90, 0, 0), "clear")
dish_tile = b.tiles[-1]
hv = world_vertices(dish_tile)
DISH_CENTER = (3.5, 3.0, 2 + HEX_APOTHEM)
PETALS = []
for i in range(6):
    a, c = hv[i], hv[(i + 1) % 6]
    if abs(a[2] - 2.0) < 1e-4 and abs(c[2] - 2.0) < 1e-4:
        continue                                      # 底边坐在盖板上, 跳过
    mid = tuple((a[k] + c[k]) / 2 for k in range(3))
    rad = tuple(mid[k] - DISH_CENTER[k] for k in range(3))
    norm = math.sqrt(sum(v * v for v in rad))
    apex = tuple(round(mid[k] + rad[k] / norm, 6) for k in range(3))
    tid = f"petal_{len(PETALS)}"
    b.place_tri(tid, "isosceles_triangle", a, c, apex, "clear")
    PETALS.append(tid)
PETALS_LOW, PETALS_HIGH = PETALS[:3], PETALS[3:]

# =================================================================
# 5. 太阳能板 x2 (30 度斜置, 底长边吸观测场东沿) + 警戒旗 x4
# =================================================================
PANEL_TOP_X = round(5.0 + 2 * COS30, 6)              # 6.73205
b.ramp("solar_s", "-x", PANEL_TOP_X, 0, 1.0, "blue")
b.ramp("solar_n", "-x", PANEL_TOP_X, 4, 1.0, "blue")
b.crest_ns("wf_nw", 0, 5.0, 0.0, "red")
b.crest_ns("wf_ne", 4, 5.0, 0.0, "red")
b.crest_ew("wf_w", 0.0, 3, 0.0, "yellow")
b.crest_ns("wf_s", 3, 0.0, 0.0, "yellow")

# =================================================================
# 教程步骤 (16 步): 场坪 -> 控制楼 -> 馈源塔 -> 天线盘 -> 配套
# =================================================================
b.step(
    "铺观测场南侧 2 排 10 片: 灰色场坪点缀绿色草斑。",
    [f"fd_{i}_{j}" for j in range(2) for i in range(5)],
    tip="观测场铺在桌面中央 —— 山谷里最平整的一块地。",
)
b.step(
    "铺观测场中部 2 排 10 片。",
    [f"fd_{i}_{j}" for j in range(2, 4) for i in range(5)],
    highlight=["fd_0_1", "fd_4_1"],
    tip="每片先对准一条边再松手, 场坪中间不能留缝。",
)
b.step(
    "补齐观测场最北 1 排 5 片 —— 5x5 场坪就绪。",
    [f"fd_{i}_4" for i in range(5)],
    highlight=["fd_2_3"],
    tip="从上往下看, 草斑应错落分布在灰色场坪四周。",
)
b.step(
    "控制楼起墙: 西南角立南墙 2 片与西墙 2 片 (西面上段用透明观测窗)。",
    ["cb_s_0", "cb_s_1", "cb_w_0", "cb_w_1"],
    highlight=["fd_0_0", "fd_0_1"],
    tip="底边吸场坪格线, 转角竖边互吸。",
)
b.step(
    "控制楼合围: 补北墙 2 片与东墙南段 1 片, 东面北段留 1 格大门。",
    ["cb_n_0", "cb_n_1", "cb_e_0"],
    highlight=["cb_s_1", "cb_w_1"],
    tip="大门朝东正对馈源塔 —— 工程师出门就能检修天线。",
)
b.step(
    "盖控制楼平屋顶: 4 片灰色方板压在墙顶上 (z=1)。",
    ["cb_r_0_0", "cb_r_1_0", "cb_r_0_1", "cb_r_1_1"],
    highlight=["cb_s_0", "cb_n_1"],
    tip="门上方那片两侧整边吸住相邻屋顶片 —— 屋面自然成楣。",
)
b.step(
    "竖楼顶通讯天线: 红色等腰三角立在屋顶中缝上。",
    ["cb_ant"],
    highlight=["cb_r_0_0", "cb_r_0_1"],
    tip="尖端朝天 —— 观测数据从这里发回基地。",
)
b.step(
    "馈源塔第一层: 场坪中央偏东立 1x1 塔身四壁 (黄橙相间)。",
    ["tw_s_0", "tw_e_0", "tw_n_0", "tw_w_0"],
    highlight=["fd_3_2"],
    tip="四角竖边两两互吸, 塔身立稳。",
)
b.step(
    "装风车斜撑: 4 片红色直角三角形, 竖直角边吸塔角竖边、水平直角边"
    "贴场坪格线, 风车状伸向四方。",
    [tid for tid, _, _ in BRACES],
    highlight=["tw_s_0", "tw_e_0"],
    tip="斜撑必须两条直角边同时吸合 —— 大天线全靠它们抗风。",
)
b.step(
    "馈源塔升到第二层: 再围一圈 4 片。",
    ["tw_s_1", "tw_e_1", "tw_n_1", "tw_w_1"],
    highlight=["tw_s_0", "br_sw"],
    tip="上下层竖缝对齐, 塔口即将迎接盖板。",
)
b.step(
    "盖塔顶盖板: 1 片灰色方板压在塔口上 (z=2)。",
    ["tw_cap"],
    highlight=["tw_s_1", "tw_n_1"],
    tip="盖板四边都坐在墙顶上 —— 它就是天线盘的底座。",
)
b.step(
    "竖起反射面: 透明六边形立在盖板北沿的竖直面内, 圆心高 2.87。",
    ["dish"],
    highlight=["tw_cap"],
    tip="底边整边吸住盖板北沿 —— 大盘面正对天空深处。",
)
b.step(
    "展开下排接收瓣: 沿六边形下方 3 条边各吸 1 片等腰三角形。",
    PETALS_LOW,
    highlight=["dish"],
    tip="每片底边与六边形边完全贴合, 星芒向外展开。",
)
b.step(
    "展开上排接收瓣: 再吸 2 片, 五瓣星芒天线盘合成。",
    PETALS_HIGH,
    highlight=PETALS_LOW[:1],
    tip="最高一瓣的尖端升到 5.3 格高 —— 全场最高点。",
)
b.step(
    "架太阳能板: 东沿两块蓝色长板 30 度斜置, 底长边整边吸场坪东沿。",
    ["solar_s", "solar_n"],
    highlight=["fd_4_0", "fd_4_4"],
    tip="板面朝东迎着日出 —— 观测站的电就靠它们。",
)
b.step(
    "插警戒旗: 场界四面各立 1 面三角旗 —— 射电望远镜开始巡天!",
    ["wf_nw", "wf_ne", "wf_w", "wf_s"],
    highlight=["fd_0_4", "fd_4_4"],
    tip="旗子立在场界格线上 —— 观测区内请保持无线电静默。",
)

b.finalize(
    model_id="radio_telescope_01",
    name="射电望远镜",
    name_en="Radio Telescope 01",
    description=(
        "科学观测主题: 5x5 观测场中央立起 1x1 两层馈源塔 (四角风车状直角"
        "三角斜撑双边吸合), 塔顶盖板北沿升起竖直大天线盘 —— 透明六边形"
        "反射面沿 5 条自由边展开等腰三角接收瓣, 五瓣星芒最高点 5.3 格; "
        "西南角 2x2 控制楼开东门戴通讯天线, 东沿两块 30 度太阳能板迎着"
        "日出, 四面警戒旗围场 —— 保持静默, 开始巡天。"
    ),
    difficulty=3,
    tags=["科学", "天文", "望远镜", "星芒", "进阶"],
    min_pieces=50,
    min_steps=16,
)
