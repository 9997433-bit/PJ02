#!/usr/bin/env python3
"""生成模型 data/models/ferry_terminal_01.json (轮渡码头)。

海洋航行主题: 全库第一座轮渡码头 —— 灰色岸线广场西侧一栋黄墙
候船厅 (双门框方检票口 + 整圈透明高侧窗带), 屋顶立起信号桅;
栈桥踩着六根桩柱伸进海面, 两条长板坡道从广场缓缓登桥,
东舷护栏西舷开敞 —— 红色渡轮正靠泊在栈桥西侧, 甲板与桥面
齐平直接跨步登船, 船头两片等边三角劈开波浪, 驾驶室戴着
红色四坡尖顶。近岸青色浅滩、中带蓝色航道、外海大方深水
(大正方形铺海一片顶四片) —— 呜 —— 开船咯!

结构总览 (世界单位: 1.0 = 正方形磁力片边长):
  - 岸线广场 (y [0,3]): 长板 x8 + 方板 x8                    16 片
  - 海面 (y [3,7]): 浅滩方板 x8 + 航道长板 x4 + 深水大方 x4  16 片
  - 候船厅 (x [1,5], y [1,2]): 一层 门框方x2+方板x6+端墙x2,
    高侧窗带 窗格方x10, 屋顶方板x4                           24 片
  - 屋顶信号桅 (等腰) + 角旗 (等边)                           2 片
  - 栈桥 (x [5,7], y [3,5]): 桩柱立墙 x6 + 桥面方板 x4
    + 登桥长板坡道 x2 + 东舷/桥头护栏等边 x3 + 灯桅等腰 x1   16 片
  - 渡轮 (x [2,5], y [3,5]): 船壳立墙 x10 + 甲板方板 x6
    + 船头等边 x2 + 驾驶室 方板x3+窗格方x1 + 四坡顶等边 x4   26 片
  合计 100 片, 19 个教程步骤, 7 种磁力片形状 (全部 CORE-9 之内)。

物理规则要点 (通过 R1~R8 全部校验, strict 档同样全绿):
  - 桩柱踩海面拼缝, 桥面双列三排桩柱多路受力, 桥面不外悬,
    桥头护栏与灯桅重心正压第三排桩顶铰链 (力矩 0);
  - 渡轮船壳围成闭合环, 甲板压壳顶锁箱形; 船壳东墙顶边
    与栈桥桥面西沿整边互吸 —— 船桥同高, 结构上连成大环;
  - 船头两片等边平挑 (单片力矩 3.75), 信号桅/灯桅/角旗
    重心均正压铰链线; 登桥坡道顶边整边吸桥面、坡尾落地;
  - 坡道落点 (x [5,7]) 与候船厅 (x [1,5]) 错开, 互不侵入。

用法: python3 tools/generate_ferry_terminal.py  (在 magtile-studio 目录下运行)
"""

from magtile_gen import ModelBuilder

b = ModelBuilder()

QUAY = "gray"       # 岸线广场
SHALLOW = "cyan"    # 近岸浅滩
CHANNEL = "blue"    # 航道
DEEP = "blue"       # 外海深水 (大正方形)
HALL = "yellow"     # 候船厅墙
GATE = "red"        # 检票口门框
GLASS = "clear"     # 高侧窗 / 驾驶室窗
ROOF = "gray"       # 候船厅屋顶
MAST = "red"        # 信号桅
FLAG = "yellow"     # 角旗
PILE = "gray"       # 栈桥桩柱 / 灯桅
PLANK = "orange"    # 栈桥桥面 / 坡道
RAIL = "yellow"     # 护栏
HULL = "red"        # 船壳 / 船头 / 驾驶室
DECK = "gray"       # 渡轮甲板

# =================================================================
# 1. 岸线广场 (y [0,3]): 南北两行长板夹一行方板
# =================================================================
for k in range(4):
    b.flat_rect(f"qy_s_{k}", 2 * k, 0, 0.0, QUAY)
    b.flat_rect(f"qy_n_{k}", 2 * k, 2, 0.0, QUAY)
for x in range(8):
    b.flat(f"qy_m_{x}", x, 1, 0.0, QUAY)

# =================================================================
# 2. 海面 (y [3,7]): 浅滩方板 -> 航道长板 -> 深水大方
# =================================================================
for x in range(8):
    b.flat(f"sea_a_{x}", x, 3, 0.0, SHALLOW)
for k in range(4):
    b.flat_rect(f"sea_b_{k}", 2 * k, 4, 0.0, CHANNEL)
for k in range(4):
    b.add(f"sea_c_{k}", "large_square", (2 * k + 1.0, 6.0, 0.0), (0, 0, 0), DEEP)

# =================================================================
# 3. 候船厅 (x [1,5], y [1,2]): 一层墙 + 高侧窗带 + 屋顶
# =================================================================
# 一层: 南脸中央两扇红色检票门, 两侧黄墙; 北脸黄墙; 山墙封两端
for x in (2, 3):
    b.add(f"hall_gate_{x}", "door_frame", (x + 0.5, 1.0, 0.5), (90, 0, 0), GATE)
for x in (1, 4):
    b.wall_ns(f"hall_s_{x}", x, 1.0, 0, HALL)
for x in (1, 2, 3, 4):
    b.wall_ns(f"hall_n_{x}", x, 2.0, 0, HALL)
b.wall_ew("hall_w0", 1.0, 1, 0, HALL)
b.wall_ew("hall_e0", 5.0, 1, 0, HALL)
# 高侧窗带 (z 1~2): 整圈窗格方
for x in (1, 2, 3, 4):
    b.add(f"hall_ws_{x}", "window_square", (x + 0.5, 1.0, 1.5), (90, 0, 0), GLASS)
    b.add(f"hall_wn_{x}", "window_square", (x + 0.5, 2.0, 1.5), (90, 0, 0), GLASS)
b.add("hall_ww", "window_square", (1.0, 1.5, 1.5), (90, 0, 90), GLASS)
b.add("hall_we", "window_square", (5.0, 1.5, 1.5), (90, 0, 90), GLASS)
# 屋顶 + 信号桅 + 角旗
for x in (1, 2, 3, 4):
    b.flat(f"hall_roof_{x}", x, 1, 2.0, ROOF)
b.spire_ew("hall_mast", 3.0, 1, 2.0, MAST)
b.crest_ew("hall_flag", 1.0, 1, 2.0, FLAG)

# =================================================================
# 4. 栈桥 (x [5,7], y [3,6]): 桩柱 + 桥面 + 坡道 + 护栏 + 灯桅
# =================================================================
for y in (3, 4, 5):
    b.wall_ns(f"pile_w_{y}", 5, float(y), 0, PILE)
    b.wall_ns(f"pile_e_{y}", 6, float(y), 0, PILE)
for y in (3, 4):
    b.flat(f"deck_w_{y}", 5, y, 1.0, PLANK)
    b.flat(f"deck_e_{y}", 6, y, 1.0, PLANK)
b.ramp("gang_w", "-y", 3.0, 5, 1.0, PLANK)      # 登桥坡道 (坡尾落岸)
b.ramp("gang_e", "-y", 3.0, 6, 1.0, PLANK)
for y in (3, 4):
    b.crest_ew(f"rail_e_{y}", 7.0, y, 1.0, RAIL)  # 东舷护栏
b.crest_ns("rail_n", 6, 5.0, 1.0, RAIL)           # 桥头护栏 (正压第三排桩顶)
b.spire_ns("pier_mast", 5, 5.0, 1.0, PILE)        # 桥头灯桅 (正压第三排桩顶)

# =================================================================
# 5. 渡轮 (x [2,5], y [3,5]): 船壳 + 甲板 + 船头 + 驾驶室
# =================================================================
for x in (2, 3, 4):
    b.wall_ns(f"hull_s_{x}", x, 3.0, 0, HULL)
    b.wall_ns(f"hull_n_{x}", x, 5.0, 0, HULL)
for y in (3, 4):
    b.wall_ew(f"hull_w_{y}", 2.0, y, 0, HULL)
    b.wall_ew(f"hull_e_{y}", 5.0, y, 0, HULL)
for x in (2, 3, 4):
    for y in (3, 4):
        b.flat(f"fdeck_{x}_{y}", x, y, 1.0, DECK)
# 船头 (西端): 两片等边三角平挑劈浪
b.add("bow_s", "equilateral_triangle", (1.711325, 3.5, 1.0), (0, 0, 90), HULL)
b.add("bow_n", "equilateral_triangle", (1.711325, 4.5, 1.0), (0, 0, 90), HULL)
# 驾驶室 (x [4,5], y [3,4], z 1~2): 西脸开瞭望窗, 戴四坡尖顶
b.wall_ns("cab_s", 4, 3.0, 1, HULL)
b.wall_ns("cab_n", 4, 4.0, 1, HULL)
b.add("cab_w", "window_square", (4.0, 3.5, 1.5), (90, 0, 90), GLASS)
b.wall_ew("cab_e", 5.0, 3, 1, HULL)
CAB_HAT = b.hat4("cab_hat", 4, 3, 2.0, HULL, shape="equilateral_triangle")

# =================================================================
# 教程步骤 (20 步)
# =================================================================
b.step(
    "铺岸线广场南半: 4 片灰色长板 + 中行 8 片方板逐缝贴合。",
    [f"qy_s_{k}" for k in range(4)] + [f"qy_m_{x}" for x in range(8)],
    tip="方板行的南北两条拼缝, 就是候船厅墙脚的落点。",
)
b.step(
    "铺岸线北行与近岸浅滩: 4 片长板 + 8 片青色方板。",
    [f"qy_n_{k}" for k in range(4)] + [f"sea_a_{x}" for x in range(8)],
    highlight=["qy_m_0"],
    tip="浅滩紧贴岸线 —— 栈桥桩柱与渡轮船壳都立在这排方板上。",
)
b.step(
    "铺航道与外海: 4 片蓝色长板 + 4 片深水大正方形。",
    [f"sea_b_{k}" for k in range(4)] + [f"sea_c_{k}" for k in range(4)],
    highlight=["sea_a_0"],
    tip="大正方形一片顶四片 —— 长边与航道长板整边等长互吸。",
)
b.step(
    "砌候船厅一层: 南脸两扇红色检票门居中, 黄墙合围。",
    ["hall_s_1", "hall_gate_2", "hall_gate_3", "hall_s_4",
     "hall_n_1", "hall_n_2", "hall_n_3", "hall_n_4"],
    highlight=["qy_m_1", "qy_m_4"],
    tip="门框方外框与方板完全一致 —— 检票口照样整边吸合。",
)
b.step(
    "封候船厅两端山墙, 一层合拢成环。",
    ["hall_w0", "hall_e0"],
    highlight=["hall_s_1", "hall_n_4"],
    tip="山墙两条竖边同时吸住南北墙 —— 闭合环最结实。",
)
b.step(
    "装高侧窗带 (南北): 8 扇透明窗格方压在一层墙顶。",
    ["hall_ws_1", "hall_ws_2", "hall_ws_3", "hall_ws_4",
     "hall_wn_1", "hall_wn_2", "hall_wn_3", "hall_wn_4"],
    highlight=["hall_gate_2"],
    tip="候船厅要亮堂 —— 整圈高侧窗让阳光洒满大厅。",
)
b.step(
    "补两端高侧窗, 窗带合圈。",
    ["hall_ww", "hall_we"],
    highlight=["hall_ws_1", "hall_wn_4"],
    tip="窗带四角竖边互吸 —— 第二圈闭环。",
)
b.step(
    "盖候船厅屋顶: 4 片灰色方板双边压窗带顶。",
    [f"hall_roof_{x}" for x in (1, 2, 3, 4)],
    highlight=["hall_ww", "hall_we"],
    tip="屋顶一盖, 墙-窗-顶锁成箱形 —— 候船厅完工。",
)
b.step(
    "立屋顶信号桅与角旗。",
    ["hall_mast", "hall_flag"],
    highlight=["hall_roof_2"],
    tip="高桅立拼缝、角旗立沿口, 重心都正压铰链线。",
)
b.step(
    "打栈桥桩柱: 六根立墙踩海面拼缝, 双列排开。",
    ["pile_w_3", "pile_e_3", "pile_w_4", "pile_e_4", "pile_w_5", "pile_e_5"],
    highlight=["sea_a_5", "sea_a_6"],
    tip="桩柱双列受力 —— 栈桥断一根桩也不塌。",
)
b.step(
    "铺栈桥桥面: 4 片橙色方板压桩柱顶。",
    ["deck_w_3", "deck_e_3", "deck_w_4", "deck_e_4"],
    highlight=["pile_w_3", "pile_e_5"],
    tip="先铺南端: 板边正好吸住第一排桩顶。",
)
b.step(
    "架登桥坡道: 两条长板顶边吸桥面南沿, 坡尾落回广场。",
    ["gang_w", "gang_e"],
    highlight=["deck_w_3", "deck_e_3"],
    tip="顶铰链 + 落地斜撑 —— 旅客推着行李也稳稳当当。",
)
b.step(
    "装东舷护栏、桥头护栏与灯桅。",
    ["rail_e_3", "rail_e_4", "rail_n", "pier_mast"],
    highlight=["deck_e_3", "deck_e_4"],
    tip="桥头护栏与灯桅重心正压第三排桩顶铰链 —— 西舷留作登船口。",
)
b.step(
    "砌渡轮南北船壳: 各 3 片红色立墙踩海面拼缝。",
    ["hull_s_2", "hull_s_3", "hull_s_4", "hull_n_2", "hull_n_3", "hull_n_4"],
    highlight=["sea_a_2", "sea_b_1"],
    tip="船壳墙脚踩海面拼缝 —— 渡轮稳稳浮在泊位上。",
)
b.step(
    "封渡轮首尾船壳, 船体合拢成环。",
    ["hull_w_3", "hull_w_4", "hull_e_3", "hull_e_4"],
    highlight=["hull_s_2", "hull_n_4"],
    tip="东壳顶边与栈桥桥面西沿同高 —— 下一步就把它们吸在一起。",
)
b.step(
    "铺渡轮甲板: 6 片灰色方板压壳顶, 与桥面齐平。",
    [f"fdeck_{x}_{y}" for x in (2, 3, 4) for y in (3, 4)],
    highlight=["hull_e_3", "deck_w_4"],
    tip="甲板与桥面同高 0 台阶 —— 直接跨步登船!",
)
b.step(
    "装船头: 两片等边三角平挑劈浪。",
    ["bow_s", "bow_n"],
    highlight=["fdeck_2_3", "fdeck_2_4"],
    tip="每片力矩只有 3.75 —— 远在预算之内, 船头越尖越帅。",
)
b.step(
    "起驾驶室: 三面红墙 + 西脸透明瞭望窗。",
    ["cab_s", "cab_n", "cab_w", "cab_e"],
    highlight=["fdeck_4_3", "fdeck_4_4"],
    tip="驾驶室踩甲板拼缝, 四面墙锁成小环。",
)
b.step(
    "戴驾驶室四坡尖顶 —— 呜! 开船咯!",
    CAB_HAT,
    highlight=["cab_s", "cab_w"],
    tip="四条斜棱两两互吸自锁成环, 尖顶正压驾驶室。",
)

b.finalize(
    model_id="ferry_terminal_01",
    name="轮渡码头",
    name_en="Ferry Terminal 01",
    description=(
        "全库第一座轮渡码头: 黄墙候船厅嵌双门框方检票口与整圈透明"
        "高侧窗带, 屋顶立信号桅; 六根桩柱托起栈桥伸进海面, 双坡道"
        "登桥、东舷护栏、桥头灯桅; 红色渡轮靠泊栈桥西侧 —— 船壳闭环"
        "甲板锁箱, 甲板与桥面齐平直接跨步登船, 船头两片等边三角劈浪,"
        " 驾驶室戴四坡尖顶。近岸浅滩-航道-深水大正方形三层海色 ——"
        " 呜 —— 开船咯!"
    ),
    difficulty=4,
    tags=["港口", "轮渡", "码头", "交通", "进阶"],
    min_pieces=98,
    min_steps=19,
)
