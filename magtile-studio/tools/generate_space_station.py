#!/usr/bin/env python3
"""生成模型 data/models/space_station_01.json (空间站)。

第三批模型 ④: 航天主题 —— 与月面着陆器 (分体对接)、火箭发射台
(垂直总装) 都不同的水平舱段搭法: 一节三格长的圆柱舱躺在两道
托架上, 舱体两端各竖一面大六边形对接环, 舱顶鼓起透明穹顶舷窗;
南北两面 3x2 的太阳翼板阵独立站在停机坪上, 东西两块菱形散热板
斜倚 60 度, 角落里还有扇形雷达碟与通讯桅杆。

结构总览 (世界单位: 1.0 = 正方形磁力片边长):
  - 停机坪 7x5: 方板与长方形混铺                                27 片
  - 舱段托架: 两道横向立墙                                       2 片
  - 核心舱: 底板 3 + 侧壁 6 + 端壁 2 + 顶板 3                   14 片
  - 穹顶舷窗: 1x1 洞口等边四坡透明穹顶                           4 片
  - 对接环: 两端各 1 片大六边形立在端壁顶边上                     2 片
  - 太阳翼: 南北各 3x2 立板阵 (蓝/透明相间)                     12 片
  - 散热板: 2 片菱形斜倚 60 度                                   2 片
  - 地面设施: 雷达塔 (2 墙 + 扇形碟) + 通讯桅杆 (2 墙 + 尖)      6 片
  合计 69 片, 16 个教程步骤, 7 种磁力片形状。

几何要点:
  - 六边形对接环底边与端壁顶边等长互吸, 重心正压铰链线上方,
    力矩为零 —— 大片六边形也能稳稳竖着;
  - 太阳翼板阵是独立接地的竖直墙网, 整阵位于铰链线正上方,
    切断底缝力矩仍为零;
  - 菱形散热板斜倚 60 度落地, 是"接地斜板"而非悬挑。

用法: python3 tools/generate_space_station.py  (在 magtile-studio 目录下运行)
"""

from magtile_gen import ModelBuilder

b = ModelBuilder()

# =================================================================
# 1. 停机坪 7x5 ([0,7]x[0,5]): 太阳翼/托架/塔架的落点旁必须是单格方板
# =================================================================
b.flat_rect("pad_s_w", 0, 0, 0, "gray")
for i in range(3):
    b.flat(f"pad_s_{i}", 2 + i, 0, 0, "gray")
b.flat("pad_s_e0", 5, 0, 0, "gray")
b.flat("pad_s_e1", 6, 0, 0, "gray")
b.flat_rect("pad_r1_w", 0, 1, 0, "gray")
for i in range(3):
    b.flat(f"pad_r1_{i}", 2 + i, 1, 0, "yellow")     # 南太阳翼落线
b.flat_rect("pad_r1_e", 5, 1, 0, "gray")
for i in range(7):
    b.flat(f"pad_core_{i}", i, 2, 0, "gray")         # 核心舱轴线一排
b.flat_rect("pad_r3_w", 0, 3, 0, "gray")
for i in range(3):
    b.flat(f"pad_r3_{i}", 2 + i, 3, 0, "yellow")     # 北太阳翼落线
b.flat_rect("pad_r3_e", 5, 3, 0, "gray")
b.flat("pad_n_w", 0, 4, 0, "gray")
b.flat_rect("pad_n_0", 1, 4, 0, "gray")
b.flat_rect("pad_n_1", 3, 4, 0, "gray")
b.flat_rect("pad_n_2", 5, 4, 0, "gray")

# =================================================================
# 2. 托架 + 核心舱 (z 1..2, 占 [2,5]x[2,3] 上空)
# =================================================================
b.wall_ew("cradle_w", 3, 2, 0, "orange")
b.wall_ew("cradle_e", 4, 2, 0, "orange")
b.flat("hull_floor_w", 2, 2, 1, "gray")
b.flat("hull_floor_c", 3, 2, 1, "gray")
b.flat("hull_floor_e", 4, 2, 1, "gray")
for i in range(3):
    b.wall_ns(f"hull_s{i}", 2 + i, 2, 1, "gray")     # 南侧壁
    b.wall_ns(f"hull_n{i}", 2 + i, 3, 1, "gray")     # 北侧壁
b.wall_ew("hull_w", 2, 2, 1, "orange")               # 西端壁
b.wall_ew("hull_e", 5, 2, 1, "orange")               # 东端壁
b.flat("hull_top_w", 2, 2, 2, "gray")
b.flat("hull_top_c", 3, 2, 2, "clear")               # 穹顶下的天窗
b.flat("hull_top_e", 4, 2, 2, "gray")

# 穹顶舷窗: 中段顶板上的等边四坡透明穹顶
b.hat4("cupola", 3, 2, 2.0, "clear", shape="equilateral_triangle")

# 对接环: 两端各 1 片大六边形立在端壁顶边上
b.place_edge("dock_w", "hexagon", 4,
             (2.0, 2.0, 2.0), (2.0, 3.0, 2.0), (0, 0, 1), "yellow")
b.place_edge("dock_e", "hexagon", 4,
             (5.0, 2.0, 2.0), (5.0, 3.0, 2.0), (0, 0, 1), "yellow")

# =================================================================
# 3. 太阳翼: 南北各 3x2 竖直板阵 (蓝/透明相间), 独立站在坪缝上
# =================================================================
for i in range(3):
    b.wall_ns(f"wing_s_lo{i}", 2 + i, 1, 0, "blue" if i % 2 == 0 else "clear")
    b.wall_ns(f"wing_n_lo{i}", 2 + i, 4, 0, "blue" if i % 2 == 0 else "clear")
for i in range(3):
    b.wall_ns(f"wing_s_hi{i}", 2 + i, 1, 1, "clear" if i % 2 == 0 else "blue")
    b.wall_ns(f"wing_n_hi{i}", 2 + i, 4, 1, "clear" if i % 2 == 0 else "blue")

# =================================================================
# 4. 散热板 (菱形斜倚 60 度) + 雷达塔 + 通讯桅杆
# =================================================================
b.place_edge("radiator_w", "rhombus", 0,
             (1.0, 2.0, 0.0), (1.0, 3.0, 0.0), (-0.5, 0, 0.866025), "pink")
b.place_edge("radiator_e", "rhombus", 0,
             (6.0, 3.0, 0.0), (6.0, 2.0, 0.0), (0.5, 0, 0.866025), "pink")
b.wall_ns("radar_lo", 0, 5, 0, "gray")               # 西北角雷达塔
b.wall_ns("radar_hi", 0, 5, 1, "gray")
b.place_edge("radar_dish", "sector", 0,
             (0.0, 5.0, 2.0), (1.0, 5.0, 2.0), (0, 0, 1), "yellow")
b.wall_ns("mast_lo", 6, 0, 0, "gray")                # 东南角通讯桅杆
b.wall_ns("mast_hi", 6, 0, 1, "gray")
b.spire_ns("mast_tip", 6, 0, 2, "red")

# =================================================================
# 教程步骤 (16 步)
# =================================================================
b.step(
    "铺停机坪南半: 南排与第二排混铺灰色长方形与方板, "
    "太阳翼落线处 (黄色) 必须是单格方板。",
    ["pad_s_w", "pad_s_0", "pad_s_1", "pad_s_2", "pad_s_e0", "pad_s_e1",
     "pad_r1_w", "pad_r1_0", "pad_r1_1", "pad_r1_2", "pad_r1_e"],
    tip="立板只吸等长整边 —— 落线旁的地砖必须与板同宽。",
)
b.step(
    "铺核心舱轴线: 7 片灰色方板从西到东排成一条中轴。",
    ["pad_core_0", "pad_core_1", "pad_core_2", "pad_core_3",
     "pad_core_4", "pad_core_5", "pad_core_6"],
    highlight=["pad_r1_0"],
    tip="舱段、托架、散热板全都落在这条轴线两侧。",
)
b.step(
    "铺停机坪北半: 第四排与北排合拢, 停机坪成为 7x5 整体。",
    ["pad_r3_w", "pad_r3_0", "pad_r3_1", "pad_r3_2", "pad_r3_e",
     "pad_n_w", "pad_n_0", "pad_n_1", "pad_n_2"],
    highlight=["pad_core_0"],
    tip="注意北排西端留一片单格方板 —— 雷达塔要立在它的北沿。",
)
b.step(
    "竖舱段托架: 2 片橙色立墙横向立在轴线排的拼缝上。",
    ["cradle_w", "cradle_e"],
    highlight=["pad_core_3"],
    tip="托架像船坞龙骨墩, 即将托起整节核心舱。",
)
b.step(
    "架核心舱底板: 3 片灰色板在 z=1 高度架上托架顶边。",
    ["hull_floor_c", "hull_floor_w", "hull_floor_e"],
    highlight=["cradle_w", "cradle_e"],
    tip="先放中段 (两边各吸一道托架), 再向两端悬挑。",
)
b.step(
    "立舱体侧壁: 南北各 3 片灰色正方形沿底板边缘立起。",
    ["hull_s0", "hull_s1", "hull_s2", "hull_n0", "hull_n1", "hull_n2"],
    highlight=["hull_floor_c"],
    tip="侧壁底边与托架顶边共线 —— 一条铰链线双重受力。",
)
b.step(
    "封舱体两端: 2 片橙色正方形封住东西端面。",
    ["hull_w", "hull_e"],
    highlight=["hull_s0", "hull_n2"],
    tip="端壁竖边与侧壁竖边互吸, 舱体成为刚性箱。",
)
b.step(
    "盖舱顶: 3 片顶板盖住舱体, 中段用透明片留出天窗。",
    ["hull_top_w", "hull_top_c", "hull_top_e"],
    highlight=["hull_s1", "hull_n1"],
    tip="透明天窗正上方就是下一步的穹顶舷窗。",
)
b.step(
    "鼓起穹顶舷窗: 4 片透明等边三角形在天窗上方合拢成浅穹顶。",
    ["cupola_s", "cupola_e", "cupola_n", "cupola_w"],
    highlight=["hull_top_c"],
    tip="四条斜棱两两互吸自锁 —— 宇航员的全景观察窗。",
)
b.step(
    "竖对接环: 2 片黄色大六边形分别立在东西端壁的顶边上。",
    ["dock_w", "dock_e"],
    highlight=["hull_w", "hull_e"],
    tip="六边形底边与端壁顶边等长, 重心正压铰链线上方, 稳如泰山。",
)
b.step(
    "立南太阳翼下排: 3 片立板 (蓝/透明相间) 站上南侧落线。",
    ["wing_s_lo0", "wing_s_lo1", "wing_s_lo2"],
    highlight=["pad_r1_0", "pad_r1_2"],
    tip="板底边吸坪缝, 相邻板竖边互吸连成整面翼板。",
)
b.step(
    "叠南太阳翼上排: 再叠 3 片, 颜色与下排错开成棋盘格。",
    ["wing_s_hi0", "wing_s_hi1", "wing_s_hi2"],
    highlight=["wing_s_lo0"],
    tip="整面翼板位于底缝正上方 —— 竖直板阵天生零力矩。",
)
b.step(
    "立北太阳翼整面: 6 片立板照南翼样式一次搭完。",
    ["wing_n_lo0", "wing_n_lo1", "wing_n_lo2",
     "wing_n_hi0", "wing_n_hi1", "wing_n_hi2"],
    highlight=["wing_s_hi1"],
    tip="南北两翼严格对称, 空间站的招牌剪影完成。",
)
b.step(
    "斜倚散热板: 2 片粉色菱形贴着东西两侧的坪缝斜倚 60 度。",
    ["radiator_w", "radiator_e"],
    highlight=["pad_core_1", "pad_core_5"],
    tip="散热板是接地斜板, 底边吸缝、板身斜靠, 不算悬挑。",
)
b.step(
    "架雷达塔: 西北角 2 片灰色立墙叠成塔, 1 片黄色扇形碟立在塔顶。",
    ["radar_lo", "radar_hi", "radar_dish"],
    highlight=["pad_n_w"],
    tip="扇形的直边吸塔顶边, 弧边指向天空扫描轨道。",
)
b.step(
    "竖通讯桅杆: 东南角 2 片灰色立墙叠高, 红色等腰尖顶收杆 —— "
    "空间站全站通电!",
    ["mast_lo", "mast_hi", "mast_tip"],
    highlight=["pad_s_e1"],
    tip="从穹顶舷窗望出去: 对接环、太阳翼、雷达碟一览无余。",
)

b.finalize(
    model_id="space_station_01",
    name="轨道空间站",
    name_en="Space Station 01",
    description=(
        "航天主题第三课 (着陆器搞分体对接、发射台搞垂直总装, 本课搞"
        "水平舱段): 三格长核心舱躺在双托架上, 底板/侧壁/端壁/顶板锁成"
        "箱形环, 舱顶鼓起透明等边穹顶舷窗, 两端各竖一片大六边形对接环 "
        "(重心正压铰链线, 零力矩); 南北 3x2 太阳翼板阵独立接地站立, "
        "菱形散热板斜倚 60 度, 角落配扇形雷达碟与通讯桅杆。"
    ),
    difficulty=3,
    tags=["航天", "空间站", "太阳翼", "对接环", "进阶"],
    min_pieces=65,
    min_steps=16,
)
