#!/usr/bin/env python3
"""生成模型 data/models/streetcar_01.json (双层观光电车)。

内容批 P 模型 7/10 (P7): 陆地交通 D2, 主打片型 wheel_base —— 重写版。
招牌是"通长车轮裙板 + 敞篷上层观光台": 四片车轮底座首尾相接, 在轨床
两侧站成贯穿车长的裙板 (老式电车的连排轮罩剪影), 裙板顶架 2 格宽
车厢底盘; 下层是带乘客门与整排窗格的客舱, 上层不封顶 —— 八片方板
铺出观光台, 四周立一圈红黄相间的三角栏杆。与旧版 (1 格窄箱 + 前后
分离转向架 + 受电弓平顶) 的剪影完全不同: 本作是 2 格宽的双层敞篷
观光电车, 车轮裙板从头连到尾。

结构总览 (世界单位: 1.0 = 正方形磁力片边长, 车行东西向, 长 4):
  - 轨床 (6x2): 长方形 x4 (裙板正下方) + 方板 x4 (两端站台缘)    8 片
  - 车轮裙板: wheel_base x4 (南北两侧各 2 片首尾相接)            4 片
  - 车厢底盘 (z=1): 长方形 x4 纵铺, 长边压裙板顶                 4 片
  - 下层客舱 (z 1..2): 端壁方板 x4 + 南墙 (窗-门-窗-窗) + 北窗 x4 12 片
  - 上层观光台 (z=2): 方板 x8                                     8 片
  - 观光台栏杆: 三角 x12 (红黄相间)                              12 片
  合计 48 片, 9 个教程步骤, 6 种磁力片形状 (全部 CORE-9 之内)。

物理规则要点 (validate 常规 + strict 双档零警告):
  - 裙板底边 (长 2) 与轨床长方形横边等长互吸, 两片裙板竖直短边
    首尾互咬; 底盘长方形长边与裙板顶边等长互吸 —— 轨床-裙板-底盘
    三层全部整边等长贴合;
  - 客舱端壁底边与底盘短边等长互吸, 墙环四角竖直边互咬闭环;
    上层方板与墙顶边等长互吸且彼此拼缝成网;
  - 栏杆尖端 2.87 触发 R8: 裙板-底盘-墙环-台面多环冗余, 剪断任一
    条铰链线或单条连接, 结构均有第二条接地路径, 无单点失效损失
    >= 3 片。

用法: python3 tools/generate_streetcar_01.py  (在 magtile-studio 目录下运行)
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from magtile_gen import ModelBuilder  # noqa: E402

b = ModelBuilder()

TRACK = "gray"       # 轨床长石板
PLATFORM = "yellow"  # 两端站台缘方板
WHEEL = "gray"       # 车轮裙板 (wheel_base)
CHASSIS = "red"      # 车厢底盘
BODY = "red"         # 车身 (门)
GLASS = "clear"      # 车窗 / 端壁风挡
TOPDECK = "red"      # 上层观光台
RAIL_A = "yellow"    # 栏杆 (红黄相间)
RAIL_B = "red"

# =================================================================
# 1. 轨床 (x [0,6], y [0,2]): 长方形对准裙板, 两端方板站台缘
# =================================================================
b.flat_rect("rd_sw", 1, 0, 0.0, TRACK)
b.flat_rect("rd_se", 3, 0, 0.0, TRACK)
b.flat_rect("rd_nw", 1, 1, 0.0, TRACK)
b.flat_rect("rd_ne", 3, 1, 0.0, TRACK)
b.flat("rd_w0", 0, 0, 0.0, PLATFORM)
b.flat("rd_w1", 0, 1, 0.0, PLATFORM)
b.flat("rd_e0", 5, 0, 0.0, PLATFORM)
b.flat("rd_e1", 5, 1, 0.0, PLATFORM)

# =================================================================
# 2. 车轮裙板: 南北两侧各两片 wheel_base 首尾相接 (x [1,5])
# =================================================================
b.add("skirt_fs", "wheel_base", (2.0, 0.0, 0.5), (90, 0, 0), WHEEL)
b.add("skirt_rs", "wheel_base", (4.0, 0.0, 0.5), (90, 0, 0), WHEEL)
b.add("skirt_fn", "wheel_base", (2.0, 2.0, 0.5), (90, 0, 0), WHEEL)
b.add("skirt_rn", "wheel_base", (4.0, 2.0, 0.5), (90, 0, 0), WHEEL)

# =================================================================
# 3. 车厢底盘 (z=1): 四片长方形纵铺, 长边压裙板顶
# =================================================================
b.flat_rect("deck_sw", 1, 0, 1.0, CHASSIS)
b.flat_rect("deck_se", 3, 0, 1.0, CHASSIS)
b.flat_rect("deck_nw", 1, 1, 1.0, CHASSIS)
b.flat_rect("deck_ne", 3, 1, 1.0, CHASSIS)

# =================================================================
# 4. 下层客舱 (z 1..2): 透明端壁 x4 + 南墙窗门带 + 北整排窗
# =================================================================
b.wall_ew("end_sw", 1.0, 0, 1, GLASS)
b.wall_ew("end_nw", 1.0, 1, 1, GLASS)
b.wall_ew("end_se", 5.0, 0, 1, GLASS)
b.wall_ew("end_ne", 5.0, 1, 1, GLASS)
b.add("win_s1", "window_square", (1.5, 0.0, 1.5), (90, 0, 0), GLASS)
b.add("door_s", "door_frame", (2.5, 0.0, 1.5), (90, 0, 0), BODY)
b.add("win_s3", "window_square", (3.5, 0.0, 1.5), (90, 0, 0), GLASS)
b.add("win_s4", "window_square", (4.5, 0.0, 1.5), (90, 0, 0), GLASS)
for x in (1, 2, 3, 4):
    b.add(f"win_n{x}", "window_square", (x + 0.5, 2.0, 1.5), (90, 0, 0), GLASS)

# =================================================================
# 5. 上层观光台 (z=2): 八片方板铺满 4x2
# =================================================================
for x in (1, 2, 3, 4):
    for y in (0, 1):
        b.flat(f"top_{x}_{y}", x, y, 2.0, TOPDECK)

# =================================================================
# 6. 观光台栏杆: 一圈 12 片三角, 红黄相间
# =================================================================
for i, x in enumerate((1, 2, 3, 4)):
    b.crest_ns(f"rail_s{x}", x, 0.0, 2.0, RAIL_A if i % 2 == 0 else RAIL_B)
    b.crest_ns(f"rail_n{x}", x, 2.0, 2.0, RAIL_B if i % 2 == 0 else RAIL_A)
b.crest_ew("rail_w0", 1.0, 0, 2.0, RAIL_A)
b.crest_ew("rail_w1", 1.0, 1, 2.0, RAIL_B)
b.crest_ew("rail_e0", 5.0, 0, 2.0, RAIL_B)
b.crest_ew("rail_e1", 5.0, 1, 2.0, RAIL_A)

# =================================================================
# 教程步骤 (9 步)
# =================================================================
b.step(
    "铺轨床: 四片灰色长石板铺在车身正下方, 两端各补两片黄色站台缘。",
    ["rd_sw", "rd_se", "rd_nw", "rd_ne", "rd_w0", "rd_w1", "rd_e0", "rd_e1"],
    tip="长石板的 2 格横边正对裙板 —— 黄色方板是乘客上下车的站台缘。",
)
b.step(
    "立车轮裙板: 四片 wheel_base 在南北两侧首尾相接, 底边与长石板"
    "横边等长互吸。",
    ["skirt_fs", "skirt_rs", "skirt_fn", "skirt_rn"],
    highlight=["rd_sw", "rd_ne"],
    tip="裙板竖直短边首尾互咬 —— 车轮从头连到尾, 老电车的经典侧脸。",
)
b.step(
    "架车厢底盘: 四片红色长方形纵铺 z=1, 长边压住裙板顶边。",
    ["deck_sw", "deck_se", "deck_nw", "deck_ne"],
    highlight=["skirt_fs", "skirt_rn"],
    tip="底盘长边与裙板顶边等长一次吸合 —— 2 格宽的车底稳稳架好。",
)
b.step(
    "立四角端壁: 四片透明方板站上底盘短边, 围出车头车尾风挡。",
    ["end_sw", "end_nw", "end_se", "end_ne"],
    highlight=["deck_sw", "deck_ne"],
    tip="端壁底边与底盘短边等长互吸, 同侧两片竖直边互咬。",
)
b.step(
    "砌南墙: 窗-门-窗-窗, 红色门框方是乘客门, 竖直边咬进端壁拐角。",
    ["win_s1", "door_s", "win_s3", "win_s4"],
    highlight=["end_sw", "end_se"],
    tip="乘客门在第二格 —— 正对着站台缘的方向。",
)
b.step(
    "砌北墙: 四片窗格方连成整排观景窗。",
    ["win_n1", "win_n2", "win_n3", "win_n4"],
    highlight=["end_nw", "end_ne"],
    tip="北侧一整排玻璃 —— 下层乘客也能看街景。",
)
b.step(
    "铺上层观光台: 八片红色方板压住墙顶, 拼缝连成网。",
    [f"top_{x}_{y}" for x in (1, 2, 3, 4) for y in (0, 1)],
    highlight=["win_s1", "win_n4"],
    tip="从西南角开始铺 —— 每片至少吸一条墙顶边或邻板拼缝。",
)
b.step(
    "立南北栏杆: 八片红黄相间的三角沿观光台长边站一排。",
    ["rail_s1", "rail_n1", "rail_s2", "rail_n2",
     "rail_s3", "rail_n3", "rail_s4", "rail_n4"],
    highlight=["top_1_0", "top_4_1"],
    tip="栏杆底边与台面板边等长互吸 —— 敞篷上层要先装护栏再载客。",
)
b.step(
    "封两端栏杆: 四片三角围拢车头车尾 —— 双层观光电车发车!",
    ["rail_w0", "rail_w1", "rail_e0", "rail_e1"],
    highlight=["rail_s1", "rail_n4"],
    tip="一圈 12 片栏杆合拢 —— 叮叮, 上层看风景的电车来了!",
)

b.finalize(
    model_id="streetcar_01",
    name="双层观光电车",
    name_en="Streetcar 01",
    description=(
        "陆地交通 D2 wheel_base 主打示范: 四片车轮底座在轨床两侧首尾"
        "相接, 站成贯穿车长的连排轮罩裙板; 裙板顶纵铺四片长方形架出"
        "2 格宽底盘, 下层客舱透明端壁 + 南侧窗门带 + 北侧整排窗格,"
        "上层不封顶 —— 八片方板铺成敞篷观光台, 一圈红黄相间的三角"
        "栏杆围拢。轨床-裙板-底盘-墙环-台面层层整边等长互吸, 与窄箱"
        "平顶的老版有轨电车剪影完全不同。"
    ),
    difficulty=2,
    tags=["陆地交通", "有轨电车", "双层巴士", "载具", "进阶"],
    min_pieces=48,
    min_steps=9,
    series="land_transport",
)
