#!/usr/bin/env python3
"""生成模型 data/models/pet_clinic_01.json (宠物医院)。

城市生活主题: 爱心宠物医院 —— 两层候诊主楼 (一层门框方大门,
二层三扇窗格方观察窗) 顶着红十字徽记 (双等边 + 等腰塔尖); 东翼
一层诊疗室戴等腰四坡尖顶; 北院是住院部小院, 两座带门洞的犬舍
(门框方门洞 + 等边锥顶) 排排坐 —— 汪汪喵喵, 挂号看诊。

结构总览 (世界单位: 1.0 = 正方形磁力片边长):
  - 地坪 [0,5]x[0,3]: 主楼 + 东翼共用大地坪                   15 片
  - 北院 [0,5]x[3,5]: 住院部小院地坪                          10 片
  - 门前步道: 大门正前 2 片                                     2 片
  - 候诊主楼 [0,3]x[0,3] 两层: 一层 12 (含门框方大门 1),
    二层 12 (含窗格方观察窗 3)                                 24 片
  - 主楼平顶: 3x3 方板                                          9 片
  - 红十字徽记: 前檐等边 x2 + 等腰塔尖 x1                       3 片
  - 东翼诊疗室 [3,5]x[0,3] 一层: 立墙 7 (西借主楼山墙)          7 片
  - 东翼平顶 + 等腰四坡尖顶: 6 + 4                             10 片
  - 犬舍 x2 (北院): 各 4 壁 (含门框方门洞) + 等边锥顶           16 片
  合计 96 片, 18 个教程步骤, 6 种磁力片形状。

物理规则要点 (通过 R1~R8 全部校验):
  - 门框方 / 窗格方物理上按实心正方形外框拼接 (docs/TILE_SET.md),
    门洞窗格仅为语义外观标记;
  - 东翼西侧直接借用主楼东山墙下层 (共墙不重叠, 消防站同款),
    翼顶板西沿吸主楼山墙下层顶边;
  - 红十字徽记立在主楼前檐铰链线上, 重心正压、力臂为零;
  - 犬舍等边锥顶斜棱两两互吸自锁成环。

用法: python3 tools/generate_pet_clinic.py  (在 magtile-studio 目录下运行)
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from magtile_gen import ModelBuilder  # noqa: E402

b = ModelBuilder()

SLAB = "gray"       # 地坪
YARD = "green"      # 北院
WALL = "clear"      # 主楼墙 (白色系)
DOOR = "blue"       # 门框方
WIN = "cyan"        # 窗格方
ROOF = "gray"       # 平顶
CROSS = "red"       # 红十字徽记
WING = "cyan"       # 东翼
HAT = "orange"      # 尖顶
DOG_A = "orange"    # 犬舍 A
DOG_B = "purple"    # 犬舍 B

# =================================================================
# 1. 地坪 / 北院 / 门前步道
# =================================================================
for x in range(5):
    for y in range(3):
        b.flat(f"sl_{x}_{y}", x, y, 0.0, SLAB)
for x in range(5):
    for y in range(3, 5):
        b.flat(f"yd_{x}_{y}", x, y, 0.0, YARD)
b.flat("pw_0", 1, -1, 0.0, SLAB)
b.flat("pw_1", 2, -1, 0.0, SLAB)

# =================================================================
# 2. 候诊主楼 [0,3]x[0,3] 两层 (一层大门 + 二层观察窗)
# =================================================================
# 一层: 前墙 (含门框方大门), 西/北/东墙
b.add("hd_door", "door_frame", (1.5, 0.0, 0.5), (90, 0, 0), DOOR)
b.wall_ns("h1_f_0", 0, 0.0, 0, WALL)
b.wall_ns("h1_f_2", 2, 0.0, 0, WALL)
for y in range(3):
    b.wall_ew(f"h1_w_{y}", 0.0, y, 0, WALL)
    b.wall_ew(f"h1_e_{y}", 3.0, y, 0, WALL)
for x in range(3):
    b.wall_ns(f"h1_n_{x}", x, 3.0, 0, WALL)
# 二层: 前墙 3 扇窗格方观察窗, 其余方墙
for x in range(3):
    b.add(f"h2_win_{x}", "window_square", (x + 0.5, 0.0, 1.5), (90, 0, 0), WIN)
for y in range(3):
    b.wall_ew(f"h2_w_{y}", 0.0, y, 1, WALL)
    b.wall_ew(f"h2_e_{y}", 3.0, y, 1, WALL)
for x in range(3):
    b.wall_ns(f"h2_n_{x}", x, 3.0, 1, WALL)

# 主楼平顶 (z=2): 3x3
for x in range(3):
    for y in range(3):
        b.flat(f"rf_{x}_{y}", x, y, 2.0, ROOF)

# 红十字徽记: 前檐 (y=0, z=2)
b.crest_ns("cx_w", 0, 0.0, 2.0, CROSS)
b.spire_ns("cx_c", 1, 0.0, 2.0, CROSS)
b.crest_ns("cx_e", 2, 0.0, 2.0, CROSS)

# =================================================================
# 3. 东翼诊疗室 [3,5]x[0,3] 一层 (西借主楼东山墙)
# =================================================================
for x in range(3, 5):
    b.wall_ns(f"wg_s_{x}", x, 0.0, 0, WING)
    b.wall_ns(f"wg_n_{x}", x, 3.0, 0, WING)
for y in range(3):
    b.wall_ew(f"wg_e_{y}", 5.0, y, 0, WING)
for x in range(3, 5):
    for y in range(3):
        b.flat(f"wr_{x}_{y}", x, y, 1.0, WING)
WING_HAT = b.hat4("wg_hat", 4, 1, 1.0, HAT)

# =================================================================
# 4. 犬舍 x2 (北院最北排, 门洞朝南)
# =================================================================
b.add("ka_door", "door_frame", (0.5, 4.0, 0.5), (90, 0, 0), DOG_A)
b.wall_ns("ka_n", 0, 5.0, 0, DOG_A)
b.wall_ew("ka_w", 0.0, 4, 0, DOG_A)
b.wall_ew("ka_e", 1.0, 4, 0, DOG_A)
KA_HAT = b.hat4("ka_hat", 0, 4, 1.0, DOG_A, shape="equilateral_triangle")

b.add("kb_door", "door_frame", (2.5, 4.0, 0.5), (90, 0, 0), DOG_B)
b.wall_ns("kb_n", 2, 5.0, 0, DOG_B)
b.wall_ew("kb_w", 2.0, 4, 0, DOG_B)
b.wall_ew("kb_e", 3.0, 4, 0, DOG_B)
KB_HAT = b.hat4("kb_hat", 2, 4, 1.0, DOG_B, shape="equilateral_triangle")

# =================================================================
# 教程步骤 (18 步)
# =================================================================
b.step(
    "铺设大地坪南排: 5 片灰色方板 (y 0..1)。",
    [f"sl_{x}_0" for x in range(5)],
    tip="主楼与东翼共用这块大地坪, 先铺南排定位。",
)
b.step(
    "补齐大地坪: 再铺 10 片, 5x3 地坪完工。",
    [f"sl_{x}_{y}" for x in range(5) for y in (1, 2)],
    highlight=["sl_0_0"],
    tip="15 片地坪板缝缝相吸, 铺完是严丝合缝的一整块。",
)
b.step(
    "铺设北院: 10 片绿色方板接在地坪北侧, 住院部小院成形。",
    [f"yd_{x}_{y}" for x in range(5) for y in (3, 4)],
    highlight=["sl_0_2", "sl_4_2"],
    tip="北院是小病号们晒太阳的地方。",
)
b.step(
    "安装大门与门前步道: 蓝色门框方立在前墙正中, 门前铺 2 片步道板。",
    ["pw_0", "pw_1", "hd_door"],
    highlight=["sl_1_0", "sl_2_0"],
    tip="门框方的门洞是真的能走小猫小狗 —— 外框照常整边吸合。",
)
b.step(
    "竖立主楼一层前墙与西墙: 大门两侧各 1 片白墙, 西面 3 片。",
    ["h1_f_0", "h1_f_2", "h1_w_0", "h1_w_1", "h1_w_2"],
    highlight=["hd_door"],
    tip="前墙与大门竖边互吸, 拐角处与西墙锁定。",
)
b.step(
    "竖立主楼一层北墙与东山墙: 各 3 片, 一层围合成筒。",
    ["h1_n_0", "h1_n_1", "h1_n_2", "h1_e_0", "h1_e_1", "h1_e_2"],
    highlight=["h1_w_2"],
    tip="东山墙将来还要借给东翼当西墙 —— 一墙两用。",
)
b.step(
    "二层前墙装观察窗: 3 扇青色窗格方对缝叠上前墙。",
    ["h2_win_0", "h2_win_1", "h2_win_2"],
    highlight=["h1_f_0", "hd_door"],
    tip="家长可以从观察窗看到诊疗室里的小病号。",
)
b.step(
    "二层围合: 西墙 3 + 北墙 3 + 东墙 3 对缝叠齐, 主楼到顶。",
    ["h2_w_0", "h2_w_1", "h2_w_2", "h2_n_0", "h2_n_1", "h2_n_2",
     "h2_e_0", "h2_e_1", "h2_e_2"],
    highlight=["h2_win_0"],
    tip="上下两层墙横边完全对齐 —— 错缝会让楼变弱。",
)
b.step(
    "铺设主楼平顶外圈: 8 片灰色顶板沿四沿压住墙顶边。",
    [f"rf_{x}_{y}" for x in range(3) for y in range(3)
     if not (x == 1 and y == 1)],
    highlight=["h2_n_1", "h2_win_1"],
    tip="每片顶板的外沿边都要吸牢正下方的墙顶边。",
)
b.step(
    "盖上平顶中心板: 主楼封顶。",
    ["rf_1_1"],
    highlight=["rf_0_0", "rf_2_2"],
    tip="中心板四边同时吸住四邻顶板, 平顶从此严丝合缝。",
)
b.step(
    "立起红十字徽记: 前檐正中 1 支红色等腰塔尖, 两侧各 1 片等边。",
    ["cx_w", "cx_c", "cx_e"],
    highlight=["rf_1_0"],
    tip="红十字立在前檐铰链线上, 重心正压 —— 全城都看得见。",
)
b.step(
    "竖立东翼南北墙: 青色方墙各 2 片, 西侧直接借用主楼东山墙。",
    ["wg_s_3", "wg_s_4", "wg_n_3", "wg_n_4"],
    highlight=["h1_e_0", "h1_e_2"],
    tip="共墙不重复 —— 东翼的西面就是主楼的东山墙。",
)
b.step(
    "竖立东翼东墙: 3 片, 诊疗室一层围合。",
    ["wg_e_0", "wg_e_1", "wg_e_2"],
    highlight=["wg_s_4", "wg_n_4"],
    tip="拐角竖边互吸, 诊疗室成为闭合的箱形筒。",
)
b.step(
    "铺设东翼平顶: 6 片青色顶板, 西沿吸主楼山墙下层顶边。",
    [f"wr_{x}_{y}" for x in range(3, 5) for y in range(3)],
    highlight=["wg_e_1", "h1_e_1"],
    tip="翼顶板一边搭主楼、一边搭翼墙 —— 两头受力最稳。",
)
b.step(
    "合拢东翼尖顶: 4 片橙色等腰三角斜棱两两互吸、锥尖自锁。",
    WING_HAT,
    highlight=["wr_4_1"],
    tip="尖顶戴在翼顶正中, 是宠物医院的标志性天际线。",
)
b.step(
    "搭建犬舍 A 四壁: 北院西端, 橙色门框方门洞朝南。",
    ["ka_door", "ka_n", "ka_w", "ka_e"],
    highlight=["yd_0_4"],
    tip="犬舍墙底边吸院板边, 门洞朝南晒太阳。",
)
b.step(
    "犬舍 A 戴等边锥顶, 犬舍 B 同步起壁。",
    KA_HAT + ["kb_door", "kb_n", "kb_w", "kb_e"],
    highlight=["ka_door"],
    tip="锥顶斜棱两两互吸自锁 —— 小房子也有讲究。",
)
b.step(
    "犬舍 B 戴锥顶: 宠物医院开诊!",
    KB_HAT,
    highlight=["kb_door"],
    tip="两座犬舍排排坐 —— 汪汪喵喵, 挂号看诊。",
)

b.finalize(
    model_id="pet_clinic_01",
    name="宠物医院",
    name_en="Pet Clinic",
    description=(
        "爱心宠物医院: 两层候诊主楼一层开蓝色门框方大门、二层嵌三扇窗格方"
        "观察窗, 平顶前檐立红十字徽记 (等腰塔尖 + 双等边); 东翼诊疗室借主楼"
        "山墙一墙两用, 顶戴橙色等腰尖顶; 北院住院部两座门框方门洞的犬舍"
        "戴等边锥顶排排坐 —— 汪汪喵喵, 挂号看诊。"
    ),
    difficulty=4,
    tags=["城市", "职业体验", "建筑", "进阶"],
    min_pieces=96,
    min_steps=18,
)
