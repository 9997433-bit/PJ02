#!/usr/bin/env python3
"""生成模型 data/models/swan_01.json (白天鹅)。

内容批 M 模型 3/4: 动物世界主题首个 D2 具象动物 —— 与 turtle_beach_01
(孵化保护站场景) / owl_01 (树桩图腾柱) 结构均不同。招牌是 T11 镜像
+ T12 层叠退台: 双翼等腰三角镜像同步下料, S 形颈以逐段退台内收把
重心拉回接地凸包; 2x2 白身箱 + 窗格方黑眼 + 橙喙, 浮在蓝绿棋盘
 pond 上。

结构总览 (世界单位: 1.0 = 正方形磁力片边长, 天鹅头朝北):
  - 池塘 (x [0,4], y [0,3]): 蓝绿棋盘方板 x12                      12 片
  - 身箱 (x [1,3], y [1,3], z 0..1): 四墙 + 双盖板                   6 片
  - S 颈 (z 1..3): 三段退台立墙 x4 + 头墙环 x4 + 头盖 x1            9 片
  - 双翼镜像 (T11): 等腰 x2 + 尾羽 x2 + 橙喙 x1                      5 片
  - 点缀: 窗格方黑眼 x1 + 睡莲 x2 + 颈斜撑 x1                      4 片
  合计 36 片, 10 个教程步骤, 6 种片形 (全部 CORE-9 之内)。

用法: python3 tools/generate_swan_01.py  (在 magtile-studio 目录下运行)
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from magtile_gen import ModelBuilder  # noqa: E402

b = ModelBuilder()

WATER_A = "cyan"
WATER_B = "blue"
BODY = "clear"
HEAD = "clear"
EYE = "gray"
BEAK = "orange"
WING = "clear"
TAIL = "clear"
LILY = "pink"


def wall_ns_t(tid, tile_type, x0, y, z0, color):
    b.add(tid, tile_type, (x0 + 0.5, y, z0 + 0.5), (90, 0, 0), color)


# =================================================================
# 1. 池塘 4x3
# =================================================================
for j in range(3):
    for i in range(4):
        b.flat(f"pond_{i}_{j}", i, j, 0.0, WATER_A if (i + j) % 2 else WATER_B)

# =================================================================
# 2. 身箱 (2x2, z 0..1)
# =================================================================
b.wall_ns("body_s0", 1, 1.0, 0, BODY)
b.wall_ns("body_s1", 2, 1.0, 0, BODY)
b.wall_ns("body_n0", 1, 3.0, 0, BODY)
b.wall_ns("body_n1", 2, 3.0, 0, BODY)
b.wall_ew("body_w", 1.0, 1, 0, BODY)
b.wall_ew("body_e", 3.0, 2, 0, BODY)
b.flat("body_cap_w", 1, 1, 1.0, BODY)
b.flat("body_cap_e", 2, 2, 1.0, BODY)

# =================================================================
# 3. S 形颈: 逐段退台 (T12) —— 南段宽、北段收至 1x1 头
# =================================================================
b.wall_ns("neck_s0", 1, 3.0, 1, BODY)
b.wall_ns("neck_s1", 2, 3.0, 1, BODY)
b.wall_ew("neck_w", 1.0, 3, 1, BODY)              # 向西内收
b.wall_ns("neck_m", 1, 3.0, 2, HEAD)              # 叠在 neck_s0 顶
wall_ns_t("eye", "window_square", 2, 3.0, 2, EYE)
b.wall_ew("head_w", 1.0, 3, 2, HEAD)
b.wall_ew("head_e", 2.0, 3, 2, HEAD)
b.flat("head_cap", 1, 3, 3.0, HEAD)

# =================================================================
# 4. 双翼镜像 (T11) + 尾羽 + 橙喙
# =================================================================
b.spire_ew("wing_w", 1.0, 1, 1.0, WING)   # 底边吸身箱西墙顶沿
b.spire_ew("wing_e", 3.0, 2, 1.0, WING)   # 底边吸身箱东墙顶沿
b.crest_ns("tail_w", 1, 1.0, 1.0, TAIL)
b.crest_ns("tail_e", 2, 1.0, 1.0, TAIL)
b.brace("neck_br", (2.0, 3.0, 1.0), "-y", BODY)   # 颈斜撑: 竖边吸颈侧、横边吸身盖
b.crest_ns("beak", 1, 3.0, 3.0, BEAK)

# =================================================================
# 5. 点缀
# =================================================================
b.crest_ns("lily_a", 0, 1.0, 0.0, LILY)
b.crest_ns("lily_b", 3, 2.0, 0.0, LILY)

# =================================================================
# 教程步骤 (10 步, T11 双侧交替)
# =================================================================
b.step(
    "铺池塘第一行: 四片蓝绿相间的方板, 边边互吸。",
    [f"pond_{i}_0" for i in range(4)],
    tip="白天鹅住在安静的池塘里 —— 先把水面铺好。",
)
b.step(
    "铺池塘第二、三行: 再来八片, 4x3 水面完成。",
    [f"pond_{i}_{j}" for j in (1, 2) for i in range(4)],
    highlight=["pond_0_0"],
    tip="棋盘格颜色错开铺, 一眼就能看出哪片没对齐。",
)
b.step(
    "砌身箱: 四片白墙围成 2x2 开口箱, 墙脚整边踩水面拼缝。",
    ["body_s0", "body_s1", "body_n0", "body_n1", "body_w", "body_e"],
    highlight=["pond_1_1"],
    tip="身箱是天鹅浮在水上的白色身体。",
)
b.step(
    "盖身箱双盖板: 两片白板压墙顶, 背部圆润收口。",
    ["body_cap_w", "body_cap_e"],
    highlight=["body_s0"],
    tip="盖板一压, 身箱变成结实的闭口箱。",
)
b.step(
    "起颈南段: 两片墙 + 一片西墙, 在身箱北沿上叠高并向西内收 (T12 退台)。",
    ["neck_s0", "neck_s1", "neck_w"],
    highlight=["body_n0", "body_cap_w"],
    tip="颈开始弯了 —— 每高一层就往里收一点, 重心才不会跑出去。",
)
b.step(
    "续颈北段与头墙: 单片北墙 + 窗格方黑眼, 东西墙合围成 1x1 头箱。",
    ["neck_m", "eye", "head_w", "head_e"],
    highlight=["neck_w"],
    tip="黑眼睛是窗格方 —— 从正面看, 白天鹅在看你。",
)
b.step(
    "盖头盖 + 颈撑 + 橙喙: 顶板、灰色颈斜撑 (先撑后盖)、喙三角 —— 头颈成形。",
    ["neck_br", "head_cap", "beak"],
    highlight=["eye"],
    tip="颈斜撑双边吸身盖与颈墙 —— S 形颈把重心拉回身箱上方, 天鹅站得稳。",
)
b.step(
    "展双翼 (T11 镜像): 先左后右, 两片等腰三角分别贴在西/东身侧。",
    ["wing_w", "wing_e"],
    highlight=["body_cap_w"],
    tip="左右对称下料 —— 翅膀要一样高、一样开。",
)
b.step(
    "装尾羽 (T11 镜像): 两片等边三角骑在身盖北沿, 左右对称。",
    ["tail_w", "tail_e"],
    highlight=["body_cap_e"],
    tip="尾羽与双翼呼应 —— 镜像同步, 重心不偏。",
)
b.step(
    "点缀收尾: 两朵睡莲 —— 白天鹅在 pond 上漂好了!",
    ["lily_a", "lily_b"],
    highlight=["pond_0_1"],
    tip="动物世界第一只 D2 具象动物 —— 优雅, 站得稳, 还会看你。",
)

b.finalize(
    model_id="swan_01",
    name="白天鹅",
    name_en="White Swan 01",
    description=(
        "动物世界 D2: 2x2 白身箱浮在蓝绿棋盘 pond 上, S 形颈以逐段"
        "退台内收 (T12) 把重心拉回接地凸包; 双翼与尾羽严格左右镜像"
        " (T11), 窗格方黑眼 + 橙喙点睛。与蜂场/海龟滩两个 D2 场景"
        "不同 —— 这是第一只 D2 具象动物主角。"
    ),
    difficulty=2,
    tags=["动物世界", "天鹅", "入门", "镜像", "池塘"],
    min_pieces=36,
    min_steps=10,
    series="animal_world",
)
