#!/usr/bin/env python3
"""生成模型 data/models/asteroid_mining_01.json (小行星采矿站)。

太空主题: 全库第一座地外采矿站 —— 紫色小行星表面上, 一台
龙门钻机正对着矿脉开钻: 两根双节立柱墙托起两片方板桥面
(门式刚架, 双端受力), 招牌是一根倒垂的等腰钻杆 —— 底边吸在
桥面南沿铰链上垂直向下, 钻尖恰好触地 (受拉悬垂 + 尖端支承
双保险); 钻位西侧一座储矿仓 —— 四墙围仓, 仓口用四片橙色
等边四坡"堆"出冒尖的矿堆, 青色输送坡道从仓沿俯冲到地面
(顶边铰链 + 坡尾接地); 东侧黄色增压居住舱 1x2 竖排, 门框方
气闸朝钻机、窗格方舷窗朝北, 长板舱顶双端压墙如桥; 两堆
刚出井的橙色矿锥、月岩与信标旗散布场区 —— 太空淘金开工!

结构总览 (世界单位: 1.0 = 正方形磁力片边长):
  - 小行星地表 7x5: 方板 x22 + 长板 x6 (橙色矿脉 + 灰色钻坑) 29 片
  - 龙门钻机: 双节立柱墙 x4 (x=3/x=5) + 方板桥面 x2 (z=2)
    + 倒垂等腰钻杆 x1 (钻尖触地) + 警示旗 x1                   8 片
  - 储矿仓 (x [1,2], y [2,3]): 灰墙 x4 + 橙色四坡矿堆 x4
    + 青色输送坡道 x1                                          9 片
  - 居住舱 (x [6,7], y [1,3]): 墙 x6 (含气闸门 + 舷窗)
    + 长板舱顶 + 天线                                          8 片
  - 矿锥 x2 (等边四坡 x4 各): 刚出井的矿石                     8 片
  - 月岩等边 x3 + 信标旗 (方墙+红旗)                           5 片
  合计 67 片, 14 个教程步骤, 6 种磁力片形状 (全部 CORE-9 之内)。

物理规则要点 (通过 R1~R8 全部校验, strict 档同样全绿):
  - 门式刚架: 桥面两片方板各一边整边压立柱顶、板缝互吸,
    地面-立柱-桥面-立柱-地面锁成大环 (剪断任一连接都有旁路);
  - 倒垂钻杆是全模型的招牌: 底边整边吸桥面南沿 (受拉悬垂,
    悬重 30g << strict 预算 84g), 重心正在铰链正下方力矩 0,
    钻尖又恰好落地 —— 拉压双保险;
  - 输送坡道顶边整边吸仓墙顶 (铰链), 坡尾自然落地成斜撑
    (光伏阵列同款); 矿堆/矿锥四条斜棱两两互吸自锁;
  - 舱顶长板短边整边压舱墙顶, 双端受力如桥; 警示旗/天线/
    月岩重心正压铰链线, 力矩 0; 全模型最高 2.87 (警示旗尖)
    触发 R8 高层检查, 门式大环处处冗余, 零警告。

用法: python3 tools/generate_asteroid_mining.py  (在 magtile-studio 目录下运行)
"""

from magtile_gen import ModelBuilder

b = ModelBuilder()

ROCKY = "purple"    # 小行星地表
VEIN = "orange"     # 矿脉
PIT = "gray"        # 钻坑
LEG = "gray"        # 龙门立柱
BEAM = "yellow"     # 桥面
DRILL = "red"       # 钻杆
FLAGW = "red"       # 警示旗
BIN = "gray"        # 储矿仓
ORE = "orange"      # 矿堆 / 矿锥
BELT = "cyan"       # 输送坡道
HAB = "yellow"      # 居住舱
DOORC = "orange"    # 气闸门
GLASS = "clear"     # 舷窗
ROOF = "gray"       # 舱顶
ANT = "red"         # 舱顶天线
ROCK = "gray"       # 月岩
POLE = "gray"       # 信标旗杆
BFLAG = "red"       # 信标旗

# =================================================================
# 1. 小行星地表 7x5 (x [0,7], y [0,5]): 南北长板收边 + 中三行方板
# =================================================================
VEIN_CELLS = {(0, 1), (2, 1), (5, 3)}
PIT_CELLS = {(3, 2), (4, 2)}
for k in range(3):
    b.flat_rect(f"gd_s_{k}", 2 * k, 0, 0.0, ROCKY)
b.flat("gd_s_3", 6, 0, 0.0, ROCKY)
for y in range(1, 4):
    for x in range(7):
        color = ROCKY
        if (x, y) in VEIN_CELLS:
            color = VEIN
        elif (x, y) in PIT_CELLS:
            color = PIT
        b.flat(f"gd_{x}_{y}", x, y, 0.0, color)
for k in range(3):
    b.flat_rect(f"gd_n_{k}", 2 * k, 4, 0.0, ROCKY)
b.flat("gd_n_3", 6, 4, 0.0, ROCKY)

# =================================================================
# 2. 龙门钻机: 双节立柱 + 方板桥面 + 倒垂钻杆 + 警示旗
# =================================================================
b.wall_ew("leg_w0", 3.0, 2, 0, LEG)
b.wall_ew("leg_w1", 3.0, 2, 1, LEG)
b.wall_ew("leg_e0", 5.0, 2, 0, LEG)
b.wall_ew("leg_e1", 5.0, 2, 1, LEG)
b.flat("beam_w", 3, 2, 2.0, BEAM)
b.flat("beam_e", 4, 2, 2.0, BEAM)
b.place_tri("drill", "isosceles_triangle",
            (4.0, 2.0, 2.0), (3.0, 2.0, 2.0), (3.5, 2.0, 0.0), DRILL)
b.crest_ns("rig_flag", 4, 3.0, 2.0, FLAGW)

# =================================================================
# 3. 储矿仓 (x [1,2], y [2,3]): 四墙 + 四坡矿堆 + 输送坡道
# =================================================================
b.wall_ns("bin_s", 1, 2.0, 0, BIN)
b.wall_ns("bin_n", 1, 3.0, 0, BIN)
b.wall_ew("bin_w", 1.0, 2, 0, BIN)
b.wall_ew("bin_e", 2.0, 2, 0, BIN)
ORE_TOP = b.hat4("ore_top", 1, 2, 1.0, ORE, shape="equilateral_triangle")
b.ramp("belt", "-y", 2.0, 1, 1.0, BELT)

# =================================================================
# 4. 居住舱 (x [6,7], y [1,3]): 1x2 竖排, 气闸朝钻机
# =================================================================
b.wall_ns("hab_s", 6, 1.0, 0, HAB)
b.wall_ns("hab_n", 6, 3.0, 0, HAB)
b.add("hab_door", "door_frame", (6.0, 1.5, 0.5), (90, 0, 90), DOORC)
b.add("hab_win", "window_square", (6.0, 2.5, 0.5), (90, 0, 90), GLASS)
b.wall_ew("hab_e_a", 7.0, 1, 0, HAB)
b.wall_ew("hab_e_b", 7.0, 2, 0, HAB)
b.flat_rect("hab_roof", 6, 1, 1.0, ROOF, axis="y")
b.crest_ns("hab_ant", 6, 3.0, 1.0, ANT)

# =================================================================
# 5. 矿锥 x2 + 月岩 + 信标旗
# =================================================================
PILE_A = b.hat4("pile_a", 4, 3, 0.0, ORE, shape="equilateral_triangle")
PILE_B = b.hat4("pile_b", 2, 3, 0.0, ORE, shape="equilateral_triangle")
b.crest_ns("rock_a", 0, 1.0, 0.0, ROCK)
b.crest_ew("rock_b", 0.0, 2, 0.0, ROCK)
b.crest_ew("rock_c", 7.0, 3, 0.0, ROCK)
b.wall_ns("bea_pole", 0, 4.0, 0, POLE)
b.crest_ns("bea_flag", 0, 4.0, 1.0, BFLAG)

# =================================================================
# 教程步骤 (14 步)
# =================================================================
b.step(
    "铺地表南沿: 3 片紫长板 + 1 片方板 (y [0,1])。",
    ["gd_s_0", "gd_s_1", "gd_s_2", "gd_s_3"],
    tip="小行星的岩面从南沿铺起 —— 输送坡道的坡尾落在这排。",
)
b.step(
    "铺第二行 (y [1,2]): 7 片, 两处橙色矿脉露头。",
    [f"gd_{x}_1" for x in range(7)],
    highlight=["gd_s_0"],
    tip="矿脉露头就是开采目标 —— 钻机对着它落位。",
)
b.step(
    "铺第三行 (y [2,3]): 7 片, 灰色双格是钻坑。",
    [f"gd_{x}_2" for x in range(7)],
    highlight=["gd_0_1"],
    tip="龙门立柱踩这行拼缝, 钻尖直插钻坑沿。",
)
b.step(
    "铺第四行 (y [3,4]): 7 片, 东端再露一条矿脉。",
    [f"gd_{x}_3" for x in range(7)],
    highlight=["gd_2_2"],
    tip="矿锥一会儿就堆在这行 —— 刚出井的矿石。",
)
b.step(
    "铺北沿: 3 片长板 + 1 片方板, 地表合拢。",
    ["gd_n_0", "gd_n_1", "gd_n_2", "gd_n_3"],
    highlight=["gd_0_3"],
    tip="七五岩面铺满 —— 采矿站马上开工。",
)
b.step(
    "砌储矿仓: 4 片灰墙围仓, 四角竖边互吸闭环。",
    ["bin_s", "bin_n", "bin_w", "bin_e"],
    highlight=["gd_1_1", "gd_1_2"],
    tip="仓口闭环 —— 矿石就堆进这一格。",
)
b.step(
    "堆仓口矿堆 + 搭输送坡道: 四坡矿堆冒尖, 坡道俯冲落地。",
    ORE_TOP + ["belt"],
    highlight=["bin_s", "bin_e"],
    tip="坡道顶边吸仓墙顶、坡尾自然落地 —— 越压越稳。",
)
b.step(
    "立龙门立柱: 东西各两节, 底边整边吸拼缝。",
    ["leg_w0", "leg_e0", "leg_w1", "leg_e1"],
    highlight=["gd_3_1", "gd_5_1"],
    tip="两根立柱隔钻坑相望 —— 桥面马上架上去。",
)
b.step(
    "架桥面 + 挂钻杆 + 插警示旗: 门式刚架合龙。",
    ["beam_w", "beam_e", "drill", "rig_flag"],
    highlight=["leg_w1", "leg_e1"],
    tip="钻杆底边吸桥面南沿垂直下探, 钻尖恰好触地 —— 拉压双保险。",
)
b.step(
    "砌居住舱墙: 气闸门朝钻机, 舷窗朝北, 6 片锁环。",
    ["hab_s", "hab_door", "hab_win", "hab_n", "hab_e_a", "hab_e_b"],
    highlight=["gd_6_1", "gd_6_2"],
    tip="宇航员出气闸就是钻位 —— 通勤三步到岗。",
)
b.step(
    "盖舱顶长板 + 立天线: 短边双端压墙如桥。",
    ["hab_roof", "hab_ant"],
    highlight=["hab_s", "hab_n"],
    tip="长板双端受力 —— 天线重心正压舱顶铰链。",
)
b.step(
    "堆第一座矿锥: 4 片橙色等边四坡, 就在钻位东侧。",
    PILE_A,
    highlight=["gd_4_2"],
    tip="刚出井的矿石还带着钻头的热气。",
)
b.step(
    "堆第二座矿锥: 储矿仓北侧再来一堆。",
    PILE_B,
    highlight=[PILE_A[0], "bin_n"],
    tip="四条斜棱两两互吸 —— 矿锥自锁成环。",
)
b.step(
    "摆月岩 x3, 立信标旗 —— 太空淘金开工!",
    ["rock_a", "rock_b", "rock_c", "bea_pole", "bea_flag"],
    highlight=["gd_0_1", "gd_0_3"],
    tip="岩石与旗面重心正压拼缝铰链, 力矩为零。",
)

b.finalize(
    model_id="asteroid_mining_01",
    name="小行星采矿站",
    name_en="Asteroid Mining Outpost 01",
    description=(
        "全库第一座地外采矿站: 紫色小行星岩面上, 龙门钻机门式"
        "刚架 (双节立柱托两片桥面, 地-柱-桥-柱-地锁成大环) 正对"
        "矿脉开钻 —— 倒垂等腰钻杆底边吸桥面南沿 (受拉悬垂 30g"
        " << strict 预算 84g, 力矩 0), 钻尖恰好触地拉压双保险;"
        " 储矿仓仓口四坡矿堆冒尖, 青色输送坡道顶铰链+坡尾接地"
        "俯冲落地; 黄色居住舱气闸朝钻机、舷窗朝北, 长板舱顶双端"
        "如桥; 两座矿锥、月岩与信标旗散布场区 —— 太空淘金开工!"
    ),
    difficulty=3,
    tags=["航天", "小行星", "采矿", "科学探索", "进阶"],
    min_pieces=64,
    min_steps=14,
)
