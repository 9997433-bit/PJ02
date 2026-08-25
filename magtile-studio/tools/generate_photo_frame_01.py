#!/usr/bin/env python3
"""生成模型 data/models/photo_frame_01.json (自立相框画架)。

内容批 J 模型 1/4: 实用功能主题首个 D1 引流位 —— 与 desk_organizer_01
(6x3 文具指挥站) 功能与剪影均不同, 本作只做一件事: 把照片立起来。
招牌是 T01 盒式地台 + T14 后撑三角: 双层地台留出一道竖缝即插纸槽,
粉色窗格框立在台前, 灰色直角三角从框背斜撑到地台后缘, 三边互锁成
门式框架 —— 相框自己站住, 照片从槽顶一插就展示。

结构总览 (世界单位: 1.0 = 正方形磁力片边长, 使用者坐在南侧 y=0):
  - 双层地台 (x [0,3], y [0,2]): 底层方板 x6 + 槽侧墙 x4 +
    后横梁 x1 + 前唇 x1                                        12 片
  - 相框立面 (y=0): 粉色窗格框 x1 + 顶楣 x1 + 红花冠 x1        3 片
  - 后撑与稳定 (T14): 直角斜撑 x1 + 后脚方板 x2 +
    后墙 x2 + 侧冠 x2                                           7 片
  合计 22 片, 8 个教程步骤, 4 种磁力片形状 (全部 CORE-9 之内)。

物理规则要点 (validate 常规 + strict 双档零警告):
  - 槽侧墙脚踩底层拼缝, 竖边互吸; 后横梁 lintel 两端压侧墙顶;
  - 窗格框底边吸底层拼缝, 顶楣长边吸框顶;
  - 斜撑竖边吸后墙、横边吸后脚拼缝, 与框-地台锁成三角;
  - 侧冠骑侧墙沿口, 纯装饰, 剪断最多失联 1 片。

用法: python3 tools/generate_photo_frame_01.py  (在 magtile-studio 目录下运行)
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


# =================================================================
# 1. 底层地台 (x [0,3], y [0,2], z=0): 3x2 木纹棋盘
# =================================================================
for j in range(2):
    for i in range(3):
        b.flat(f"base_{i}_{j}", i, j, 0.0, WOOD_A if (i + j) % 2 else WOOD_B)

# =================================================================
# 2. 双层槽 (z=1): 左右侧墙 + 后横梁 + 前唇 —— 中间 x=1 留缝插照片
# =================================================================
b.wall_ns("slot_w0", 0, 0.0, 0, WOOD_A)
b.wall_ns("slot_w1", 0, 1.0, 0, WOOD_B)
b.wall_ns("slot_e0", 2, 0.0, 0, WOOD_B)
b.wall_ns("slot_e1", 2, 1.0, 0, WOOD_A)
b.lintel_ns("slot_back", 0, 2.0, 0, WOOD_A)          # 后横梁 x [0,2]
b.flat("slot_lip", 1, 0, 1.0, WOOD_B)                # 前唇: 照片从后方插入

# =================================================================
# 3. 相框立面 (y=0): 窗格框 + 顶楣 + 顶花
# =================================================================
wall_ns_t("frame", "window_square", 1, 0.0, 0, FRAME)
b.flat("frame_top", 1, 0, 1.0, FRAME)                 # 顶板骑在窗格框顶沿
b.crest_ns("frame_flower", 1, 0.0, 2.0, TRIM)

# =================================================================
# 4. 后撑三角 (T14) + 后脚扩展 + 后墙 + 侧冠
# =================================================================
b.flat("foot_l", 0, 2, 0.0, WOOD_B)
b.flat("foot_r", 2, 2, 0.0, WOOD_A)
b.wall_ns("back_l", 0, 2.0, 0, WOOD_A)
b.wall_ns("back_r", 2, 2.0, 0, WOOD_B)
b.brace("easel", (2.0, 2.0, 0.0), "-x", BRACE)       # 竖边吸后墙, 横边吸后脚
b.crest_ns("crown_w", 0, 1.0, 1.0, TRIM)
b.crest_ns("crown_e", 2, 1.0, 1.0, TRIM)

# =================================================================
# 教程步骤 (8 步)
# =================================================================
b.step(
    "铺底层地台: 六片黄橙相间的方板拼成 3x2 底板, 相邻边整边互吸。",
    [f"base_{i}_{j}" for j in range(2) for i in range(3)],
    tip="底板是整个画架的地基 —— 拼缝对齐了, 上面的槽和框才有得吸。",
)
b.step(
    "立槽侧墙: 四片方板沿左右两列踩住底板拼缝, 围出中间插纸缝。",
    ["slot_w0", "slot_w1", "slot_e0", "slot_e1"],
    highlight=["base_0_0", "base_2_1"],
    tip="中间 x=1 那列空着 —— 照片卡片就从这道缝插进去。",
)
b.step(
    "封槽后梁并装前唇: 后横梁压住侧墙顶, 前唇方板骑在槽口前沿。",
    ["slot_back", "slot_lip"],
    highlight=["slot_w0", "slot_e0"],
    tip="前唇只盖半边 —— 卡片从后面滑入, 从前唇下方露出画面。",
)
b.step(
    "立相框: 粉色窗格框踩在底板上, 顶楣长边吸住框顶, 红花冠点在最高处。",
    ["frame", "frame_top", "frame_flower"],
    highlight=["base_1_0", "slot_lip"],
    tip="窗格框就是'画' —— 把最宝贝的照片卡进槽里, 从框里露出来。",
)
b.step(
    "铺后脚: 两片方板沿底板北缘向东延伸, 给画架一个更大的后脚。",
    ["foot_l", "foot_r"],
    highlight=["base_0_2", "base_2_2"],
    tip="后脚越宽, 画架越不容易向后翻 —— 这是自立的关键。",
)
b.step(
    "立后墙: 两片方板沿后脚北沿竖起, 为斜撑准备竖向吸附面。",
    ["back_l", "back_r"],
    highlight=["foot_l", "foot_r"],
    tip="后墙与侧墙在同一高度 —— 斜撑等会儿要同时吸住它们。",
)
b.step(
    "装后撑三角: 灰色直角三角竖边吸后墙、横边吸后脚拼缝, 锁成三角框。",
    ["easel"],
    highlight=["back_r", "foot_r"],
    tip="这是 T14 斜撑 —— 和整理站手机架同款, 只不过这次撑的是相框。",
)
b.step(
    "侧冠收尾: 两片红色三角骑在槽侧墙顶沿 —— 自立相框画架完工!",
    ["crown_w", "crown_e"],
    highlight=["slot_w1", "slot_e1"],
    tip="选一张最宝贝的照片卡进槽里, 摆在书桌上 —— 它自己会站好。",
)


b.finalize(
    model_id="photo_frame_01",
    name="自立相框画架",
    name_en="Photo Frame Easel 01",
    description=(
        "实用功能 D1 引流作: 不是玩具, 是真能摆照片的小画架 —— 3x2 黄橙"
        "双层地台留出一道竖缝即插纸槽, 粉色窗格框立在台前, 灰色直角"
        "三角从框背斜撑到地台后缘 (T14 双边吸合), 与后墙-后脚锁成门式"
        "框架; 照片从槽顶一插就展示, 相框自己站住。与整理站的 6x3"
        "文具站完全不同 —— 这次主角是框与画面。"
    ),
    difficulty=1,
    tags=["实用功能", "相框", "画架", "照片", "桌面"],
    min_pieces=22,
    min_steps=8,
    series="practical_utility",
)
