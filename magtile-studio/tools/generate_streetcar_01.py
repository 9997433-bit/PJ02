#!/usr/bin/env python3
"""生成模型 data/models/streetcar_01.json (有轨电车).

内容批 P 模型 P7/10: 陆地交通 D2 —— 双转向架 wheel_base 底盘 +
3 段红色裙边 T09 车辆底盘 + 绿色长箱车厢, 与 mini_bus_01 的
2 格短箱蓝色小巴刻意区分: 本作结构签名是 "埋轨床 + 前后双转向架
四轮 + 北窗带南乘客门 + 车顶受电弓"。

结构总览 (世界单位: 1.0 = 正方形磁力片边长, 车头朝东):
  - 轨床 (x [0,6], y [0,1]): 灰床 + 长板拼缝给转向架            8 片
  - 转向架: wheel_base x4 (前 x=1, 后 x=4)                       4 片
  - 底盘: 红色长板 x3 长边压轮顶锁门式框架                       3 片
  - 箱体: 前后透明端壁 x2 + 北窗格方 x3 + 南墙/门/窗 x3          8 片
  - 车顶: 绿色方板 x4 + 灰色受电弓 x1                            5 片
  - 点睛: 前后三角灯 x2 + 线路牌窗格方 x1 + 轨端 x1             4 片
  合计 32 片, 8 个教程步骤, 6 种磁力片形状 (全部 CORE-9 之内)。

物理规则要点 (validate 常规 + strict 双档零警告):
  - 转向架 wheel_base 平行立在 y=0/y=1 拼缝, 底边 (长 2) 整边
    吸轨床长板; 三片底盘长板长边压四轮顶, 剪断任一条铰链力绕行;
  - 箱体墙踩底盘短边/拼缝, 北窗带 lintel 短边吸后壁顶, 四角竖边
    互咬; 车顶方板压墙顶锁成连续箱环;
  - 受电弓/前后灯/线路牌重心正压铰链线, 力矩为零。

用法: python3 tools/generate_streetcar_01.py  (在 magtile-studio 目录下运行)
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from magtile_gen import ModelBuilder  # noqa: E402

b = ModelBuilder()

TRACK = "gray"
RAIL = "yellow"
BODY = "green"
SKIRT = "red"
GLASS = "clear"
WHEEL = "gray"
PANTO = "gray"
LIGHT_F = "yellow"
LIGHT_R = "red"
SIGN = "green"

# =================================================================
# 1. 轨床 (x [0,6], y [0,1]): 拼缝纪律 —— 转向架踩在 x=1 / x=4
# =================================================================
b.flat("rd_0_0", 0, 0, 0.0, TRACK)
b.flat_rect("rd_1_0", 1, 0, 0.0, TRACK)
b.flat_rect("rd_3_0", 3, 0, 0.0, RAIL)
b.flat("rd_5_0", 5, 0, 0.0, TRACK)
b.flat("rd_0_1", 0, 1, 0.0, TRACK)
b.flat_rect("rd_1_1", 1, 1, 0.0, TRACK)
b.flat_rect("rd_3_1", 3, 1, 0.0, RAIL)
b.flat("rd_5_1", 5, 1, 0.0, TRACK)

# =================================================================
# 2. 双转向架: 前后各一对 wheel_base (x=1 前, x=5 后)
# =================================================================
b.add("wh_fs", "wheel_base", (1.0, 0.0, 0.5), (90, 0, 0), WHEEL)
b.add("wh_fn", "wheel_base", (1.0, 1.0, 0.5), (90, 0, 0), WHEEL)
b.add("wh_rs", "wheel_base", (5.0, 0.0, 0.5), (90, 0, 0), WHEEL)
b.add("wh_rn", "wheel_base", (5.0, 1.0, 0.5), (90, 0, 0), WHEEL)

# =================================================================
# 3. T09 车辆底盘: 三片红色长板长边压轮顶, 低重心门式框架
# =================================================================
b.flat_rect("deck_w", 0, 0, 1.0, SKIRT)
b.flat_rect("deck_m", 2, 0, 1.0, SKIRT)
b.flat_rect("deck_e", 4, 0, 1.0, SKIRT)

# =================================================================
# 4. 车厢箱体: 透明端壁 + 北整排窗 + 南乘客门与侧窗
# =================================================================
b.wall_ew("cab_rear", 0.0, 0, 1, GLASS)
b.wall_ew("cab_front", 6.0, 0, 1, GLASS)
b.wall_ns("wall_s0", 0, 0.0, 1, BODY)
b.add("door_s", "door_frame", (1.5, 0.0, 1.5), (90, 0, 0), BODY)
b.wall_ns("wall_s2", 2, 0.0, 1, BODY)
b.wall_ns("wall_s3", 3, 0.0, 1, BODY)
for x in (0, 1, 2, 3):
    b.add(f"win_n{x}", "window_square", (x + 0.5, 1.0, 1.5), (90, 0, 0), GLASS)
b.add("win_s4", "window_square", (4.5, 0.0, 1.5), (90, 0, 0), GLASS)

# =================================================================
# 5. 车顶: 五片绿色方板 + 受电弓
# =================================================================
for x in (0, 1, 2, 3, 4):
    b.flat(f"roof_{x}", x, 0, 2.0, BODY)
b.crest_ew("panto", 2.0, 0, 2.0, PANTO)

# =================================================================
# 6. 前后灯、线路牌、轨端延长
# =================================================================
b.crest_ew("headlight", 6.0, 0, 2.0, LIGHT_F)
b.crest_ew("taillight", 0.0, 0, 2.0, LIGHT_R)
b.add("route_sign", "window_square", (3.5, 0.0, 2.5), (90, 0, 0), SIGN)
b.flat("rd_6_0", 6, 0, 0.0, TRACK)

# =================================================================
# 教程步骤 (8 步)
# =================================================================
b.step(
    "铺轨床南行: 长板拼缝在 x=2 与 x=4, 前后转向架都靠这行格线。",
    ["rd_0_0", "rd_1_0", "rd_3_0", "rd_5_0"],
    tip="x=3 黄色长板是轨道标记 —— 有轨电车走在轨道上!",
)
b.step(
    "铺轨床北行: 与南行对缝, y=1 转向架缝同样贯通。",
    ["rd_0_1", "rd_1_1", "rd_3_1", "rd_5_1"],
    highlight=["rd_1_0"],
    tip="双行轨床铺完 —— 转向架马上落位。",
)
b.step(
    "落双转向架: 前后各一对 wheel_base 立上拼缝, 底边整边吸长板。",
    ["wh_fs", "wh_fn", "wh_rs", "wh_rn"],
    highlight=["rd_1_0", "rd_1_1"],
    tip="四轮底边 (长 2) 与轨缝长板等长 —— 转向架一次吸牢。",
)
b.step(
    "架三段底盘: 三片红色长板长边压四轮顶, 低重心门式框架锁死。",
    ["deck_w", "deck_m", "deck_e"],
    highlight=["wh_fs", "wh_rn"],
    tip="T09 车辆底盘 —— 裙边长板是车厢的承重地板。",
)
b.step(
    "立前后端壁: 透明端壁踩住底盘西短边与东短边。",
    ["cab_rear", "cab_front"],
    highlight=["deck_w", "deck_e"],
    tip="端壁竖边咬进底盘拐角 —— 长箱轮廓比小巴多出一格。",
)
b.step(
    "砌南墙: 侧墙段 + 门框乘客门, 竖边咬进前后壁。",
    ["wall_s0", "door_s", "wall_s2", "wall_s3"],
    highlight=["cab_rear", "cab_front"],
    tip="南墙逐段合龙 —— 乘客门在中段。",
)
b.step(
    "装北窗带与南窗: 四扇北窗格方 + 南窗, 竖边吸进端壁拐角。",
    ["win_n0", "win_n1", "win_n2", "win_n3", "win_s4"],
    highlight=["wall_s2", "wall_s3"],
    tip="北整排窗 + 南乘客门 —— 有轨电车的标志性侧脸。",
)
b.step(
    "盖车顶并立受电弓: 五片绿色方板压墙顶, 灰色弓立中缝取电。",
    ["roof_0", "roof_1", "roof_2", "roof_3", "roof_4", "panto"],
    highlight=["win_n1", "door_s"],
    tip="受电弓底边骑住车顶拼缝 —— 叮, 通电!",
)
b.step(
    "装前后灯、线路牌并延长轨端 —— 有轨电车出发!",
    ["headlight", "taillight", "route_sign", "rd_6_0"],
    highlight=["roof_2", "cab_front"],
    tip="绿色线路牌挂在车顶南沿 —— 下一站到市中心!",
)

model = b.finalize(
    model_id="streetcar_01",
    name="有轨电车",
    name_en="Streetcar 01",
    description=(
        "陆地交通 D2 有轨载具: 前后双转向架四片 wheel_base 立在埋轨床拼缝上,"
        "三片红色裙边长板长边压轮顶锁成 T09 低重心门式底盘; 4 格绿色长箱"
        "北整排透明窗格、南嵌乘客门, 车顶四片方板合龙后立灰色受电弓取电,"
        "前后三角灯与绿色线路牌点睛 —— 低扁长箱剪影, 与小巴短箱完全不同!"
    ),
    difficulty=2,
    tags=["陆地交通", "有轨", "载具", "wheel_base", "进阶"],
    min_pieces=28,
    min_steps=9,
    series="land_transport",
)

# 追加主技法标注 (T09 车辆底盘)
out = Path(__file__).resolve().parent.parent / "data" / "models" / "streetcar_01.json"
data = json.loads(out.read_text(encoding="utf-8"))
data["content_meta"]["technique_tags"] = {"primary": "T09_vehicle_chassis"}
out.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print("已写入 technique_tags.primary = T09_vehicle_chassis")
