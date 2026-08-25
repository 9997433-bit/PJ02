#!/usr/bin/env python3
"""生成模型 data/models/lighthouse_01.json (灯塔)。

第三批模型 ②: 海岸主题 —— 全库第一个用扇形磁力片的模型:
礁石小岛上立起四层红灰条纹的六边形灯塔, 塔顶六边形廊台板向外
悬挑一圈瞭望环廊 (环廊外沿立护栏), 环廊中央是透明灯室与等腰
锥形灯冠; 一条两格栈桥把小岛与岸边的守塔人小屋连成整体,
岛边 3 片扇形浪花贴着礁石打旋。

结构总览 (世界单位: 1.0 = 正方形磁力片边长):
  - 小岛: 六边形岛心 + 4 片等边三角礁石 + 3 片扇形浪花           8 片
  - 栈桥与岸: 栈桥 2 + 系缆桩 1 + 岸滩 3 方 + 屋前路 1           7 片
  - 灯塔鼓身: 六边形筒壁 4 层 (一层朝栈桥留门洞)                23 片
  - 瞭望环廊: 廊台板 1 + 悬挑深板 6 + 护栏 6                    13 片
  - 灯室与灯冠: 透明灯室 6 + 压盖 1 + 等腰锥冠 6                13 片
  - 守塔人小屋: 地板 2 + 长方形圈层 4 + 梯形四坡顶 5            11 片
  - 岸边路灯: 灯柱 1 + 灯尖 1                                    2 片
  合计 77 片, 16 个教程步骤, 8 种磁力片形状。

几何要点:
  - 六边形岛心转 30 度, 让东西两条边的外法向正对坐标轴,
    栈桥与岸滩方格网才能整边吸合;
  - 环廊深板悬挑在廊台板边上, 同一条铰链线上还叠着灯室墙的底边,
    抗弯预算按边长合计翻倍 —— 悬挑板加护栏也吃不满预算;
  - 扇形只有两条直边是磁力边, 弧边纯装饰, 贴着礁石斜边打旋。

用法: python3 tools/generate_lighthouse.py  (在 magtile-studio 目录下运行)
"""

import math

from magtile_gen import EQ_APEX, ModelBuilder

b = ModelBuilder()

# 六边形岛心转 30 度: 顶点位于 30+60k 度, 东西两条边正对 x 轴
V = [(math.cos(math.radians(30 + 60 * k)),
      math.sin(math.radians(30 + 60 * k))) for k in range(6)]
# 边 k: V[k] -> V[k+1]; 边 5 (V5->V0) 是正东边, 边 2 (V2->V3) 是正西边
EAST, WEST = 5, 2
X0 = 2.866025          # 岸滩西界 = 0.866025 + 2 (两跨栈桥)


def n_out(k):
    """第 k 条边的水平外法向。"""
    ang = math.radians(60 + 60 * k)
    return (math.cos(ang), math.sin(ang), 0.0)


def hex_edge(k, z):
    v0, v1 = V[k], V[(k + 1) % 6]
    return (v0[0], v0[1], z), (v1[0], v1[1], z)


# =================================================================
# 1. 小岛: 六边形岛心 + 斜角礁石 + 扇形浪花
# =================================================================
b.add("island", "hexagon", (0, 0, 0), (0, 0, 30), "gray")
for k in (0, 1, 3, 4):                       # 4 条斜边向外铺礁石
    e0, e1 = hex_edge(k, 0.0)
    b.place_edge(f"rock_{k}", "equilateral_triangle", 0, e0, e1,
                 n_out(k), "gray")
# 浪花: 扇形边 0 贴住礁石的一条斜边, 弧边向外打旋
ROCK0_APEX = (V[0][0] + n_out(0)[0] * 0.866025,
              V[0][1] + n_out(0)[1] * 0.866025 + 0.0, 0.0)
b.place_edge("wave_ne", "sector", 0,
             (0.866025, 1.5, 0.0), (0.866025, 0.5, 0.0), (1, 0, 0), "cyan")
b.place_edge("wave_se", "sector", 0,
             (0.866025, -0.5, 0.0), (0.866025, -1.5, 0.0), (1, 0, 0), "cyan")
b.place_edge("wave_w", "sector", 0,
             (-0.866025, 0.5, 0.0), (-0.866025, -0.5, 0.0), (-1, 0, 0), "cyan")

# =================================================================
# 2. 栈桥 (向东两跨) + 岸滩方格网
# =================================================================
b.place_edge("pier_0", "square", 0,
             (0.866025, -0.5, 0.0), (0.866025, 0.5, 0.0), (1, 0, 0), "orange")
b.place_edge("pier_1", "square", 0,
             (1.866025, -0.5, 0.0), (1.866025, 0.5, 0.0), (1, 0, 0), "orange")
b.crest_ew("bollard", 1.866025, -0.5, 0.0, "red")   # 栈桥中缝系缆桩
b.flat("shore_sw", X0, -1.5, 0, "green")            # 岸滩西列 3 方
b.flat("shore_w", X0, -0.5, 0, "green")
b.flat("shore_nw", X0, 0.5, 0, "green")
b.flat_rect("house_floor_w", X0 + 1, -1.5, 0, "yellow", axis="y")
b.flat_rect("house_floor_e", X0 + 2, -1.5, 0, "yellow", axis="y")
b.flat_rect("house_path", X0 + 1, 0.5, 0, "green")  # 屋前小路

# =================================================================
# 3. 灯塔鼓身: 六边形筒壁 4 层, 红灰相间条纹, 一层正东留门洞
# =================================================================
STRIPE = ["red", "gray", "red", "gray"]
for lv in range(4):
    for k in range(6):
        if lv == 0 and k == EAST:
            continue                          # 一层东门洞正对栈桥
        e0, e1 = hex_edge(k, float(lv))
        b.place_edge(f"drum{lv}_{k}", "square", 0, e0, e1,
                     (0, 0, 1), STRIPE[lv])

# =================================================================
# 4. 瞭望环廊: 廊台板 + 6 片悬挑深板 + 6 片护栏
# =================================================================
b.add("gallery_plate", "hexagon", (0, 0, 4.0), (0, 0, 30), "yellow")
for k in range(6):
    e0, e1 = hex_edge(k, 4.0)
    b.place_edge(f"deck_{k}", "square", 0, e0, e1, n_out(k), "yellow")
for k in range(6):
    nx, ny, _ = n_out(k)
    e0, e1 = hex_edge(k, 4.0)
    o0 = (e0[0] + nx, e0[1] + ny, 4.0)
    o1 = (e1[0] + nx, e1[1] + ny, 4.0)
    b.place_edge(f"rail_{k}", "equilateral_triangle", 0, o0, o1,
                 (0, 0, 1), "gray")

# =================================================================
# 5. 灯室 (透明) + 压盖 + 等腰锥形灯冠
# =================================================================
for k in range(6):
    e0, e1 = hex_edge(k, 4.0)
    b.place_edge(f"lamp_{k}", "square", 0, e0, e1, (0, 0, 1), "clear")
b.add("lamp_cap", "hexagon", (0, 0, 5.0), (0, 0, 30), "gray")
APEX = (0.0, 0.0, 5.5)
for k in range(6):
    e0, e1 = hex_edge(k, 5.0)
    b.place_tri(f"crown_{k}", "isosceles_triangle", e0, e1, APEX, "red")

# =================================================================
# 6. 守塔人小屋: 长方形圈层一周 + 梯形四坡顶, 岸边路灯
# =================================================================
b.lintel_ew("house_w", X0 + 1, -1.5, 0, "clear")    # 西窗带朝灯塔
b.lintel_ew("house_e", X0 + 3, -1.5, 0, "orange")
b.lintel_ns("house_s", X0 + 1, -1.5, 0, "orange")
b.lintel_ns("house_n", X0 + 1, 0.5, 0, "orange")
HROOF, HCAP = b.hip_roof2("hroof", X0 + 1, -1.5, 1.0, "red", cap_color="gray")
b.wall_ns("post", X0, 1.5, 0, "gray")               # 岸边路灯
b.spire_ns("post_lamp", X0, 1.5, 1.0, "yellow")

# =================================================================
# 教程步骤 (16 步)
# =================================================================
b.step(
    "搭小岛: 1 片灰色六边形转 30 度平放做岛心 (让两条边正对东西), "
    "4 片灰色等边三角形沿四条斜边向外铺成礁石。",
    ["island", "rock_0", "rock_1", "rock_3", "rock_4"],
    tip="转 30 度是本模型的钥匙: 东西两边的外法向正对坐标轴。",
)
b.step(
    "搭栈桥: 2 片橙色正方形从岛心正东边一跨一跨伸向岸边, "
    "桥缝上立 1 片红色等边三角形做系缆桩。",
    ["pier_0", "pier_1", "bollard"],
    highlight=["island"],
    tip="第一跨整边吸住岛心东边, 第二跨接力向东。",
)
b.step(
    "铺岸滩: 西列 3 片绿色方板接住栈桥, 中间 2 根黄色长方形做小屋"
    "地板, 北面再铺 1 根绿色长方形小路。",
    ["shore_sw", "shore_w", "shore_nw",
     "house_floor_w", "house_floor_e", "house_path"],
    highlight=["pier_1"],
    tip="岸滩中格的西边正好整边吸住栈桥第二跨。",
)
b.step(
    "贴浪花: 3 片青色扇形平贴海面, 直边吸住礁石斜边, 弧边向外打旋。",
    ["wave_ne", "wave_se", "wave_w"],
    highlight=["rock_0", "rock_4"],
    tip="扇形只有两条直边有磁力, 弧边是纯装饰的浪线。",
)
b.step(
    "竖鼓身第一层: 5 片红色正方形沿岛心边缘立起, 正东留出门洞。",
    ["drum0_0", "drum0_1", "drum0_2", "drum0_3", "drum0_4"],
    highlight=["island", "pier_0"],
    tip="每面墙底边吸岛心边、竖边吸邻墙, 门洞正对栈桥。",
)
b.step(
    "叠鼓身第二层: 6 片灰色正方形叠上第一层墙顶, 补上门楣。",
    ["drum1_0", "drum1_1", "drum1_2", "drum1_3", "drum1_4", "drum1_5"],
    highlight=["drum0_0"],
    tip="门楣那片没有下层墙托底, 全靠两侧竖边吸牢。",
)
b.step(
    "叠鼓身第三层: 6 片红色正方形 —— 红灰条纹是灯塔的经典涂装。",
    ["drum2_0", "drum2_1", "drum2_2", "drum2_3", "drum2_4", "drum2_5"],
    highlight=["drum1_0"],
    tip="上下层墙的竖缝对齐, 筒壁才挺拔。",
)
b.step(
    "叠鼓身第四层: 6 片灰色正方形, 塔身到达 4 格高。",
    ["drum3_0", "drum3_1", "drum3_2", "drum3_3", "drum3_4", "drum3_5"],
    highlight=["drum2_0"],
    tip="立高墙时用手指从内侧轻扶, 放稳再松手。",
)
b.step(
    "盖廊台板并悬挑环廊: 1 片黄色六边形盖住筒口, 6 片黄色方板沿"
    "板边向外悬挑成瞭望环廊。",
    ["gallery_plate", "deck_0", "deck_1", "deck_2",
     "deck_3", "deck_4", "deck_5"],
    highlight=["drum3_0"],
    tip="悬挑板一条边吸廊台板, 像给灯塔戴上一圈帽檐。",
)
b.step(
    "立环廊护栏: 6 片灰色等边三角形立在悬挑板外沿。",
    ["rail_0", "rail_1", "rail_2", "rail_3", "rail_4", "rail_5"],
    highlight=["deck_0"],
    tip="护栏底边吸悬挑板外沿 —— 瞭望员再也不怕海风了。",
)
b.step(
    "起透明灯室: 6 片透明正方形沿廊台板边立起一圈。",
    ["lamp_0", "lamp_1", "lamp_2", "lamp_3", "lamp_4", "lamp_5"],
    highlight=["gallery_plate", "deck_0"],
    tip="灯室墙与悬挑板共用同一条沿边 —— 一条铰链线双重受力。",
)
b.step(
    "盖灯室压盖: 1 片灰色六边形转 30 度盖住灯室筒口, 6 条边同时吸合。",
    ["lamp_cap"],
    highlight=["lamp_0"],
    tip="从正上方对准再放下, 六边一次吸到位。",
)
b.step(
    "合拢灯冠: 6 片红色等腰三角形底边吸压盖边, 斜棱两两互吸, "
    "锥尖在压盖上方 0.5 格处自锁会合。",
    ["crown_0", "crown_1", "crown_2", "crown_3", "crown_4", "crown_5"],
    highlight=["lamp_cap"],
    tip="最后一片轻轻卡进去, 灯冠合拢 —— 灯塔封顶!",
)
b.step(
    "砌守塔人小屋: 4 根长方形横放立起围成圈层, 朝灯塔的西面用"
    "透明窗带, 先立西/东两根, 再用南/北两根咬合四角。",
    ["house_w", "house_e", "house_s", "house_n"],
    highlight=["house_floor_w", "house_floor_e"],
    tip="西/东两根的底边吸地板长边, 南/北两根靠竖边咬合传力。",
)
b.step(
    "盖小屋四坡顶: 4 片红色梯形下底吸圈层顶沿, 腰两两互吸, "
    "1 片灰色正方形压顶收口。",
    HROOF + [HCAP],
    highlight=["house_w", "house_e"],
    tip="梯形下底长 2, 正好与长方形圈层的长边等长贴合。",
)
b.step(
    "立岸边路灯: 1 片灰色正方形灯柱立在小路北沿, 1 片黄色等腰"
    "三角形灯尖收顶 —— 灯塔与守塔人小屋整晚相望!",
    ["post", "post_lamp"],
    highlight=["shore_nw", "house_path"],
    tip="从塔顶环廊俯瞰: 岛、桥、岸、屋连成一条东西轴线。",
)

b.finalize(
    model_id="lighthouse_01",
    name="海岬灯塔",
    name_en="Lighthouse 01",
    description=(
        "海岸主题: 礁石小岛上立起四层红灰条纹的六边形灯塔, 一层门洞"
        "正对两跨栈桥; 塔顶廊台板向外悬挑一圈瞭望环廊 (环廊与灯室墙"
        "共用铰链线, 抗弯预算翻倍), 透明灯室之上等腰锥冠自锁封顶; "
        "岸边守塔人小屋用长方形圈层加梯形四坡顶, 3 片扇形浪花贴着"
        "礁石打旋 —— 全库第一次用上扇形磁力片。"
    ),
    difficulty=4,
    tags=["海岸", "灯塔", "悬挑环廊", "扇形", "挑战"],
    min_pieces=75,
    min_steps=16,
)
