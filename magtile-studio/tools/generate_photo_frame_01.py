#!/usr/bin/env python3
"""生成模型 data/models/photo_frame_01.json (自立相框画架).

用法: python3 tools/generate_photo_frame_01.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from magtile_gen import ModelBuilder  # noqa: E402

b = ModelBuilder()

WOOD_A = "orange"
WOOD_B = "yellow"
FRAME = "pink"
TRIM = "red"
BRACE = "gray"


def wall_ns_t(tid, tile_type, x0, y, z0, color):
    b.add(tid, tile_type, (x0 + 0.5, y, z0 + 0.5), (90, 0, 0), color)


for j in range(2):
    for i in range(3):
        b.flat(f"base_{i}_{j}", i, j, 0.0, WOOD_A if (i + j) % 2 else WOOD_B)

b.wall_ns("slot_w0", 0, 0.0, 0, WOOD_A)
b.wall_ns("slot_w1", 0, 1.0, 0, WOOD_B)
b.wall_ns("slot_e0", 2, 0.0, 0, WOOD_B)
b.wall_ns("slot_e1", 2, 1.0, 0, WOOD_A)
b.wall_ns("slot_back", 1, 1.0, 0, WOOD_A)

wall_ns_t("frame", "window_square", 1, 0.0, 0, FRAME)
b.flat("frame_top", 1, 0, 1.0, FRAME)
b.crest_ns("frame_flower", 1, 0.0, 1.0, TRIM)

b.flat("foot_l", 0, 2, 0.0, WOOD_B)
b.flat("foot_r", 2, 2, 0.0, WOOD_A)
b.wall_ns("back_l", 0, 2.0, 0, WOOD_A)
b.wall_ns("back_r", 2, 2.0, 0, WOOD_B)
b.brace("easel", (2.0, 2.0, 0.0), "-x", BRACE)
b.crest_ns("crown_w", 0, 1.0, 1.0, TRIM)
b.crest_ns("crown_e", 2, 1.0, 1.0, TRIM)

b.step(
    "铺底层地台: 六片黄橙相间的方板拼成 3x2 底板, 相邻边整边互吸。",
    [f"base_{i}_{j}" for j in range(2) for i in range(3)],
)
b.step(
    "立槽侧墙: 四片方板沿左右两列踩住底板拼缝, 围出中间插纸缝。",
    ["slot_w0", "slot_w1", "slot_e0", "slot_e1"],
    highlight=["base_0_0", "base_2_1"],
)
b.step(
    "封槽北沿: 中间一片侧墙挡住槽口北缘, 插缝仍从上方进入。",
    ["slot_back"],
    highlight=["slot_w0", "slot_e0"],
)
b.step(
    "立相框: 粉色窗格框踩在底板上, 顶板骑在框顶, 红花冠点在顶沿。",
    ["frame", "frame_top", "frame_flower"],
    highlight=["base_1_0"],
)
b.step(
    "铺后脚: 两片方板沿底板北缘向东延伸, 给画架一个更大的后脚。",
    ["foot_l", "foot_r"],
    highlight=["base_0_1", "base_2_1"],
)
b.step(
    "立后墙: 两片方板沿后脚北沿竖起, 为斜撑准备竖向吸附面。",
    ["back_l", "back_r"],
    highlight=["foot_l", "foot_r"],
)
b.step(
    "装后撑三角: 灰色直角三角竖边吸后墙、横边吸后脚拼缝, 锁成三角框。",
    ["easel"],
    highlight=["back_r", "foot_r"],
)
b.step(
    "侧冠收尾: 两片红色三角骑在槽侧墙顶沿 —— 自立相框画架完工!",
    ["crown_w", "crown_e"],
    highlight=["slot_w1", "slot_e1"],
)

b.finalize(
    model_id="photo_frame_01",
    name="自立相框画架",
    name_en="Photo Frame Easel 01",
    description=(
        "实用功能 D1 引流作: 3x2 黄橙双层地台留出一道竖缝即插纸槽,"
        "粉色窗格框立在台前, 灰色直角三角从框背斜撑到地台后缘,"
        "照片从槽顶一插就展示, 相框自己站住。"
    ),
    difficulty=1,
    tags=["实用功能", "相框", "画架", "照片", "桌面"],
    min_pieces=21,
    min_steps=8,
    series="practical_utility",
)
