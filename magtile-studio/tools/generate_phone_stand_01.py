#!/usr/bin/env python3
"""生成模型 data/models/phone_stand_01.json (双档手机支架)。

内容批 M 模型 2/4: 实用功能主题 D1 —— 策略 2.2 原文点名的"手机架"。
招牌是 T01 盒式地台 + T14 斜撑: 3x2 木纹底板上一道 U 形背靠,
左右两槽各有一片 30 度坡道 + 一片直角斜撑, 陡坡槽竖放、缓坡槽
横放 —— 换槽即换档位, 与 photo_frame_01 (相框画架) 剪影和功能
均不同。

结构总览 (世界单位: 1.0 = 正方形磁力片边长, 使用者坐在南侧 y=0):
  - 底板 (x [0,3], y [0,2]): 黄橙棋盘方板 x6                       6 片
  - 背靠 U 槽: 侧墙 x4 + 后横梁 x1                                  5 片
  - 双档坡道: 左陡坡 + 右缓坡 (30 度长方形)                         2 片
  - 双斜撑 (T14): 直角三角 x2                                       2 片
  - 前挡 x2 + 中隔 x1 + 后脚 x2 + 后墙 x2                          7 片
  合计 22 片, 8 步, 4 种片形 (CORE-9)。

用法: python3 tools/generate_phone_stand_01.py  (在 magtile-studio 目录下运行)
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from magtile_gen import ModelBuilder  # noqa: E402

b = ModelBuilder()

WOOD_A = "orange"
WOOD_B = "yellow"
BACK = "purple"
RAMP_V = "cyan"      # 竖放槽 (陡坡)
RAMP_H = "pink"      # 横放槽 (缓坡)
BRACE = "gray"

# =================================================================
# 1. 底板 3x2
# =================================================================
for j in range(2):
    for i in range(3):
        b.flat(f"base_{i}_{j}", i, j, 0.0, WOOD_A if (i + j) % 2 else WOOD_B)

# =================================================================
# 2. U 形背靠 + 中隔
# =================================================================
b.wall_ns("slot_w0", 0, 0.0, 0, WOOD_A)
b.wall_ns("slot_w1", 0, 1.0, 0, WOOD_B)
b.wall_ns("slot_div", 1, 0.0, 0, BACK)          # 中隔: 左右两槽
b.wall_ns("slot_e0", 2, 0.0, 0, WOOD_B)
b.wall_ns("slot_e1", 2, 1.0, 0, WOOD_A)
b.wall_ns("slot_back", 1, 1.0, 0, BACK)

# =================================================================
# 3. 双档坡道 + 双斜撑 (T14)
# =================================================================
b.ramp("ramp_v", "-y", 1.0, 0, 1.0, RAMP_V)      # 左槽: 顶边吸靠背上沿
b.ramp("ramp_h", "-y", 1.0, 2, 1.0, RAMP_H)      # 右槽: 平行坡道
b.brace("brace_l", (1.0, 2.0, 0.0), "+y", BRACE)
b.brace("brace_r", (3.0, 2.0, 0.0), "+y", BRACE)

# =================================================================
# 4. 前挡 + 后脚扩展 + 后墙
# =================================================================
b.flat("lip_l", 0, 0, 1.0, WOOD_B)               # 左槽前挡 (骑沿口)
b.flat("lip_r", 2, 0, 1.0, WOOD_A)               # 右槽前挡
b.flat("foot_l", 0, 2, 0.0, WOOD_B)
b.flat("foot_r", 2, 2, 0.0, WOOD_A)
b.wall_ns("back_l", 0, 2.0, 0, BACK)
b.wall_ns("back_r", 2, 2.0, 0, BACK)

# =================================================================
# 教程步骤 (8 步)
# =================================================================
b.step(
    "铺底板: 六片黄橙相间的方板拼成 3x2, 相邻边整边互吸。",
    [f"base_{i}_{j}" for j in range(2) for i in range(3)],
    tip="底板是整个支架的地基 —— 拼缝对齐了, 背靠和坡道才有得吸。",
)
b.step(
    "立 U 形侧墙: 四片侧墙 + 一片中隔围出左右两个手机槽。",
    ["slot_w0", "slot_w1", "slot_div", "slot_e0", "slot_e1"],
    highlight=["base_0_0", "base_2_1"],
    tip="中隔把底板分成两槽 —— 一槽竖放、一槽横放。",
)
b.step(
    "封槽北墙: 紫色方板挡住槽口北缘, U 形背靠成型 (T01)。",
    ["slot_back"],
    highlight=["slot_w0", "slot_e0"],
    tip="北墙把 U 形锁成盒式框架 —— 坡道等会儿吸在这道沿上。",
)
b.step(
    "铺后脚: 两片方板沿底板北缘延伸, 给支架更大的后脚。",
    ["foot_l", "foot_r"],
    highlight=["base_0_1", "base_2_1"],
    tip="后脚越宽, 支架越不容易向后翻。",
)
b.step(
    "立后墙: 两片紫色方板沿后脚北沿竖起, 为斜撑准备竖向吸附面。",
    ["back_l", "back_r"],
    highlight=["foot_l", "foot_r"],
    tip="后墙与侧墙同高 —— 斜撑等会儿要吸住它们。",
)
b.step(
    "装双斜撑: 两片灰色直角三角, 竖边吸后墙、横边吸后脚拼缝 (T14)。",
    ["brace_l", "brace_r"],
    highlight=["back_l", "back_r"],
    tip="斜撑双边吸合 —— 背靠从此推不倒。",
)
b.step(
    "搭双档坡道: 青色坡道顶边吸左槽靠背上沿, 粉色坡道吸右槽 —— 陡坡竖放、缓坡横放。",
    ["ramp_v", "ramp_h"],
    highlight=["slot_back", "slot_div"],
    tip="30 度坡道顶边整边吸背靠, 坡尾落桌板 —— 手机躺上去试试!",
)
b.step(
    "装前挡收尾: 两片前唇骑槽口沿 —— 双档手机支架完工!",
    ["lip_l", "lip_r"],
    highlight=["ramp_v", "ramp_h"],
    tip="左槽竖放刷视频, 右槽横放看地图 —— 换槽就是换档位!",
)

b.finalize(
    model_id="phone_stand_01",
    name="双档手机支架",
    name_en="Dual-Slot Phone Stand 01",
    description=(
        "实用功能 D1: 3x2 盒式地台上 U 形背靠分出左右两槽, 各配 30 度"
        "坡道 + 直角斜撑 (T14 双边吸合); 左槽陡坡竖放、右槽缓坡横放,"
        "换槽即换档位。与相框画架 (主角是框与画面) 剪影和功能均不同"
        " —— 这是策略点名的真·手机架。"
    ),
    difficulty=1,
    tags=["实用功能", "手机架", "桌面", "入门", "斜撑"],
    min_pieces=22,
    min_steps=8,
    series="practical_utility",
)
