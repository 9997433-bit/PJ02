#!/usr/bin/env python3
"""生成模型 data/models/mini_bus_01.json (迷你小巴)。

内容批 L 模型 2/4: 陆地交通主题首个 D1 载具 —— 全库第一辆
孩子能独立完成的"车": 结构签名是"双轴迷你小巴", 四片车轮底座
平行立在车道拼缝上, 两片黄色底盘长板长边压轮顶锁成门式框架,
2x1 蓝色箱体 (窗格方挡风 + 门框方侧门) 压顶封箱, 前后三角
灯与线路牌点睛 —— 不附街景, 只搭车就能开!

结构总览 (世界单位: 1.0 = 正方形磁力片边长, 车头朝东):
  - 车道 (x [0,4], y [0,2]): 五片灰色方板 + 一片长板             6 片
  - 车轮底座 x4 (前轴 + 后轴, y=0.5 / y=1.5)                    4 片
  - 底盘长板 x2 (z=1, 长边压轮顶)                                2 片
  - 车身箱体 (z 1..2): 前后壁 x2 + 侧窗 x2 + 车顶 x2             6 片
  - 灯与牌: 前灯/尾灯三角 x2 + 线路牌窗格方 + 后视镜三角           4 片
  - 前后保险杠长板 x2 + 侧面彩条长板 x1                          3 片
  - 乘客贴纸三角 x1                                              1 片
  合计 26 片, 8 个教程步骤, 6 种磁力片形状 (全部 CORE-9 之内)。

物理规则要点 (validate 常规 + strict 双档零警告):
  - 车轮底座底边 (长 2) 整边吸车道长板拼缝, 前后轴严格对齐;
  - 底盘双长板长边压四轮顶、短边在 x=2 缝互吸 —— 门式框架;
  - 车身前后壁踩底盘短边与拼缝, 侧窗竖边吸进角缝, 车顶压成环;
  - 三角灯底边整边吸沿口, 重心正压铰链零力矩。

用法: python3 tools/generate_mini_bus_01.py  (在 magtile-studio 目录下运行)
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from magtile_gen import ModelBuilder  # noqa: E402

b = ModelBuilder()

ROAD = "gray"       # 车道
BODY = "blue"       # 车身
CHASSIS = "yellow"  # 底盘
GLASS = "clear"     # 玻璃
WHEEL = "gray"      # 车轮
LIGHT_F = "yellow"  # 前灯
LIGHT_R = "red"     # 尾灯
SIGN = "green"      # 线路牌

# =================================================================
# 1. 车道 (x [0,4], y [0,2])
# =================================================================
b.flat("rd_0_0", 0, 0, 0.0, ROAD)
b.flat_rect("rd_1", 1, 0, 0.0, ROAD)
b.flat("rd_3_0", 3, 0, 0.0, ROAD)
b.flat("rd_0_1", 0, 1, 0.0, ROAD)
b.flat_rect("rd_2", 1, 1, 0.0, ROAD)
b.flat("rd_3_1", 3, 1, 0.0, ROAD)

# =================================================================
# 2. 四轴轮组 (前 x=1, 后 x=3)
# =================================================================
b.add("wh_fs", "wheel_base", (1.0, 0.5, 0.5), (90, 0, 0), WHEEL)
b.add("wh_fn", "wheel_base", (1.0, 1.5, 0.5), (90, 0, 0), WHEEL)
b.add("wh_rs", "wheel_base", (3.0, 0.5, 0.5), (90, 0, 0), WHEEL)
b.add("wh_rn", "wheel_base", (3.0, 1.5, 0.5), (90, 0, 0), WHEEL)

# =================================================================
# 3. 底盘 + 保险杠
# =================================================================
b.flat_rect("deck_w", 0, 0, 1.0, CHASSIS)
b.flat_rect("deck_e", 2, 0, 1.0, CHASSIS)
b.lintel_ew("bumper_f", 4.0, 0, 1, CHASSIS)
b.lintel_ew("bumper_r", 0.0, 0, 1, CHASSIS)

# =================================================================
# 4. 车身箱体 (z 1..2)
# =================================================================
b.add("cab_front", "window_square", (4.0, 0.5, 1.5), (90, 0, 90), GLASS)
b.wall_ew("cab_rear", 0.0, 0, 1, BODY)
b.add("door_s", "door_frame", (1.5, 0.0, 1.5), (90, 0, 0), BODY)
b.add("win_n", "window_square", (2.5, 2.0, 1.5), (90, 0, 0), GLASS)
b.flat("roof_w", 1, 0, 2.0, BODY)
b.flat("roof_e", 2, 0, 2.0, BODY)

# =================================================================
# 5. 灯、牌、彩条、贴纸
# =================================================================
b.crest_ew("headlight", 4.0, 0, 1.0, LIGHT_F)
b.crest_ew("taillight", 0.0, 1, 1.0, LIGHT_R)
b.add("route_sign", "window_square", (2.5, 0.0, 2.5), (90, 0, 0), SIGN)
b.crest_ns("mirror", 2, 2.0, 1.0, GLASS)
b.lintel_ns("stripe", 1, 0.0, 1, CHASSIS)
b.crest_ew("sticker", 2.0, 1, 1.0, LIGHT_F)

# =================================================================
# 教程步骤 (8 步)
# =================================================================
b.step(
    "铺车道: 两片长板拼缝在 x=2 与 x=3, 前后轴都靠这行格线。",
    ["rd_0_0", "rd_1", "rd_3_0", "rd_0_1", "rd_2", "rd_3_1"],
    tip="车轮底座底边长 2 —— 轮位必须是长板长边, 等长才吸得住。",
)
b.step(
    "立四轮: 前轴 x=1、后轴 x=3, 南北各一对平行立起。",
    ["wh_fs", "wh_fn", "wh_rs", "wh_rn"],
    highlight=["rd_1", "rd_2"],
    tip="四片 wheel_base 严格对齐 —— 迷你小巴的底盘骨架就位。",
)
b.step(
    "架底盘: 两片黄色长板长边压四轮顶, 在 x=2 缝彼此互吸。",
    ["deck_w", "deck_e"],
    highlight=["wh_fs", "wh_rn"],
    tip="门式框架 —— 剪断任一条铰链, 另一条路径仍托住车体。",
)
b.step(
    "装前后保险杠: 两片长板短边吸住底盘东西端。",
    ["bumper_f", "bumper_r"],
    highlight=["deck_w", "deck_e"],
    tip="保险杠把底盘封成一块整板 —— 车头车尾有了轮廓。",
)
b.step(
    "立车身: 窗格方挡风朝东, 后壁与门框方侧门封住箱体。",
    ["cab_front", "cab_rear", "door_s", "win_n"],
    highlight=["deck_e", "deck_w"],
    tip="前后壁踩底盘短边与拼缝 —— 箱形车身长高到二层。",
)
b.step(
    "盖车顶: 两片蓝色方板四边压窗顶, 箱体合龙。",
    ["roof_w", "roof_e"],
    highlight=["cab_front", "door_s"],
    tip="车顶把侧窗与前后壁锁成环 —— 越压越紧。",
)
b.step(
    "贴侧面彩条与乘客贴纸: 长板侧饰 + 三角贴纸告诉路人'这是巴士'。",
    ["stripe", "sticker"],
    highlight=["door_s"],
    tip="彩条底边整边吸车身 —— 迷你小巴有了专属涂装。",
)
b.step(
    "装前后灯、线路牌与后视镜 —— 迷你小巴发车!",
    ["headlight", "taillight", "route_sign", "mirror"],
    highlight=["roof_w", "bumper_f"],
    tip="线路牌立在车顶前沿 —— 全库第一辆 D1 载具, 开走吧!",
)

b.finalize(
    model_id="mini_bus_01",
    name="迷你小巴",
    name_en="Mini Bus 01",
    description=(
        "陆地交通首个 D1 载具, 全库第一辆孩子能独立完成的'车': "
        "四片 wheel_base 前后双轴平行立在车道拼缝上, 两片黄色底盘"
        "长板长边压轮顶锁成门式框架; 2x1 蓝色箱体以窗格方挡风、"
        "门框方侧门与北窗围合, 黄色车顶压成环; 前后三角灯、绿色"
        "线路牌与后视镜点睛, 侧面彩条与贴纸宣告'这是巴士' —— "
        "不附街景, 只搭车就能开!"
    ),
    difficulty=1,
    tags=["陆地交通", "巴士", "载具", "wheel_base", "入门"],
    min_pieces=26,
    min_steps=8,
    series="land_transport",
)
