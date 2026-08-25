#!/usr/bin/env python3
"""生成模型 data/models/mini_bus_01.json (迷你小巴).

用法: python3 tools/generate_mini_bus_01.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from magtile_gen import ModelBuilder  # noqa: E402

b = ModelBuilder()

ROAD = "gray"
BODY = "blue"
CHASSIS = "yellow"
GLASS = "clear"
WHEEL = "gray"
LIGHT_F = "yellow"
LIGHT_R = "red"
SIGN = "green"

b.flat("rd_0_0", 0, 0, 0.0, ROAD)
b.flat_rect("rd_1_0", 1, 0, 0.0, ROAD)
b.flat("rd_3_0", 3, 0, 0.0, ROAD)
b.flat("rd_0_1", 0, 1, 0.0, ROAD)
b.flat_rect("rd_1_1", 1, 1, 0.0, ROAD)
b.flat("rd_3_1", 3, 1, 0.0, ROAD)
b.flat("rd_4_0", 4, 0, 0.0, ROAD)

b.add("wh_fs", "wheel_base", (1.0, 0.0, 0.5), (90, 0, 0), WHEEL)
b.add("wh_fn", "wheel_base", (1.0, 1.0, 0.5), (90, 0, 0), WHEEL)
b.add("wh_rs", "wheel_base", (3.0, 0.0, 0.5), (90, 0, 0), WHEEL)
b.add("wh_rn", "wheel_base", (3.0, 1.0, 0.5), (90, 0, 0), WHEEL)
b.flat_rect("deck_w", 0, 0, 1.0, CHASSIS)
b.flat_rect("deck_e", 2, 0, 1.0, CHASSIS)

b.wall_ew("cab_rear", 0.0, 0, 1, BODY)
b.wall_ew("cab_front", 4.0, 0, 1, GLASS)
b.lintel_ns("wall_n", 0, 1.0, 1, GLASS)
b.wall_ns("wall_s0", 0, 0.0, 1, BODY)
b.add("door_s", "door_frame", (1.5, 0.0, 1.5), (90, 0, 0), BODY)
b.wall_ns("wall_s2", 2, 0.0, 1, BODY)
b.flat("roof_w", 1, 0, 2.0, BODY)
b.flat("roof_e", 2, 0, 2.0, BODY)

b.crest_ew("headlight", 4.0, 0, 2.0, LIGHT_F)
b.crest_ew("taillight", 0.0, 0, 2.0, LIGHT_R)
b.add("route_sign", "window_square", (2.5, 0.0, 2.5), (90, 0, 0), SIGN)
b.crest_ns("mirror", 1, 1.0, 2.0, GLASS)
b.crest_ns("badge", 1, 0.0, 2.0, CHASSIS)

b.step(
    "铺车道: 长板拼缝在 x=2, 前后轴都靠这行格线。",
    ["rd_0_0", "rd_1_0", "rd_3_0", "rd_0_1", "rd_1_1", "rd_3_1"],
)
b.step(
    "立四轮并架底盘: 前后双轴 wheel_base 立上拼缝, 两片黄色长板长边压轮顶。",
    ["wh_fs", "wh_fn", "wh_rs", "wh_rn", "deck_w", "deck_e"],
    highlight=["rd_1_0", "rd_1_1"],
)
b.step(
    "立前后壁与北窗带: 后壁蓝、前挡风透明, 北墙长板短边吸后壁顶。",
    ["cab_rear", "cab_front", "wall_n"],
    highlight=["deck_w", "deck_e"],
)
b.step(
    "砌南墙: 侧墙段 + 门框方侧门, 竖边咬进前后壁拐角。",
    ["wall_s0", "door_s", "wall_s2"],
    highlight=["cab_rear", "cab_front"],
)
b.step(
    "盖车顶: 两片蓝色方板四边压墙顶, 箱体合龙。",
    ["roof_w", "roof_e"],
    highlight=["door_s", "wall_n"],
)
b.step(
    "贴车顶徽标: 三角饰钉在车顶南沿 —— 一眼认出迷你小巴。",
    ["badge"],
    highlight=["roof_w"],
)
b.step(
    "装前后灯、线路牌、后视镜并延长路面 —— 迷你小巴发车!",
    ["headlight", "taillight", "route_sign", "mirror", "rd_4_0"],
    highlight=["roof_w", "cab_front"],
)

b.finalize(
    model_id="mini_bus_01",
    name="迷你小巴",
    name_en="Mini Bus 01",
    description=(
        "陆地交通首个 D1 载具: 四片 wheel_base 前后双轴立在车道拼缝上,"
        "两片黄色底盘长板长边压轮顶锁成门式框架; 2x1 蓝色箱体围合,"
        "前后三角灯与绿色线路牌点睛 —— 不附街景, 只搭车就能开!"
    ),
    difficulty=1,
    tags=["陆地交通", "巴士", "载具", "wheel_base", "入门"],
    min_pieces=26,
    min_steps=7,
    series="land_transport",
)
