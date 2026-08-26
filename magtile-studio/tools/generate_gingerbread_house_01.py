#!/usr/bin/env python3
"""生成模型 data/models/gingerbread_house_01.json (姜饼糖果屋)。

童话主题的第一个 D2 入门作: 与海滩小屋 (高脚桩柱) 和别墅小屋
(双层圈层砌法) 的结构语言都不同 —— 本作是"糖霜齿带姜饼盒":
3x2 姜饼色墙环单层落地, 清色糖霜屋面上, 屋檐南北两条等边三角
糖霜齿带整圈骑沿 (齿带既是装饰也是屋面压边), 屋脊两道粉色
糖峰骑拼缝; 红色门框方是糖果大门, 两面青色窗格糖窗对开;
院里棒棒糖瘦高尖、糖果栅栏小三角、门前糖果小径 —— 全库唯一
的"屋檐糖霜齿带 + 糖果配色"组合。

结构总览 (世界单位: 1.0 = 正方形磁力片边长, 大门朝南):
  - 雪院 (x [0,5], y [0,4]): 方板 8 + 长板 6                  14 片
  - 墙环 (x [1,4], y [1,3], z 0..1): 方墙 7 + 门框 1 + 窗格 2  10 片
  - 糖霜屋面 (z=1): 方板 x6                                    6 片
  - 屋檐糖霜齿带 x6 + 屋脊糖峰 x4 (等边骑沿口/拼缝)            10 片
  - 棒棒糖 x2 (瘦高尖) + 糖果栅栏 x3                            5 片
  合计 45 片, 9 个教程步骤, 6 种磁力片形状 (全部 CORE-9 之内)。

物理规则要点 (validate 常规 + strict 双档零警告):
  - 墙环墙脚全部踩雪院拼缝, 四角竖边互咬闭环;
  - 屋面六片方板边边入扣墙顶并互吸;
  - 齿带底边同时吸屋面沿边与墙顶边 (双边受力), 糖峰底边骑
    屋面拼缝; 棒棒糖/栅栏底边整边吸院子沿口, 剪断任何一条
    装饰连接最多失联 1 片 (< 3), R8 单点失效通过。

用法: python3 tools/generate_gingerbread_house_01.py  (在 magtile-studio 目录下运行)
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from magtile_gen import ModelBuilder  # noqa: E402

b = ModelBuilder()

SNOW = "clear"       # 雪地
PATH = "red"         # 糖果小径
GINGER = "orange"    # 姜饼墙
DOOR = "red"         # 糖果大门
WINDOW = "cyan"      # 糖窗
ICING = "clear"      # 糖霜屋面与齿带
PEAK = "pink"        # 屋脊糖峰
LOLLI_A = "pink"     # 棒棒糖
LOLLI_B = "purple"
FENCE = "red"        # 糖果栅栏


def wall_ns_t(tid, tile_type, x0, y, z0, color):
    b.add(tid, tile_type, (x0 + 0.5, y, z0 + 0.5), (90, 0, 0), color)


def wall_ew_t(tid, tile_type, x, y0, z0, color):
    b.add(tid, tile_type, (x, y0 + 0.5, z0 + 0.5), (90, 0, 90), color)


# =================================================================
# 1. 雪院 (x [0,5], y [0,4]): 雪地长板 + 姜饼院心 + 糖果小径
# =================================================================
b.flat_rect("yard_0_0", 0, 0, 0.0, SNOW)
b.flat("path", 2, 0, 0.0, PATH)
b.flat_rect("yard_3_0", 3, 0, 0.0, SNOW)
b.flat("yard_0_1", 0, 1, 0.0, SNOW)
b.flat_rect("floor_1_1", 1, 1, 0.0, GINGER)
b.flat("floor_3_1", 3, 1, 0.0, GINGER)
b.flat("yard_4_1", 4, 1, 0.0, SNOW)
b.flat("yard_0_2", 0, 2, 0.0, SNOW)
b.flat_rect("floor_1_2", 1, 2, 0.0, GINGER)
b.flat("floor_3_2", 3, 2, 0.0, GINGER)
b.flat("yard_4_2", 4, 2, 0.0, SNOW)
b.flat_rect("yard_0_3", 0, 3, 0.0, SNOW)
b.flat("yard_2_3", 2, 3, 0.0, SNOW)
b.flat_rect("yard_3_3", 3, 3, 0.0, SNOW)

# =================================================================
# 2. 墙环 (x [1,4], y [1,3], z 0..1): 姜饼墙 + 糖果门 + 糖窗
# =================================================================
b.wall_ns("wall_s_w", 1, 1.0, 0, GINGER)
wall_ns_t("door", "door_frame", 2, 1.0, 0, DOOR)
b.wall_ns("wall_s_e", 3, 1.0, 0, GINGER)
b.wall_ns("wall_n_w", 1, 3.0, 0, GINGER)
b.wall_ns("wall_n_m", 2, 3.0, 0, GINGER)
b.wall_ns("wall_n_e", 3, 3.0, 0, GINGER)
wall_ew_t("window_w", "window_square", 1.0, 1, 0, WINDOW)
b.wall_ew("wall_w_n", 1.0, 2, 0, GINGER)
b.wall_ew("wall_e_s", 4.0, 1, 0, GINGER)
wall_ew_t("window_e", "window_square", 4.0, 2, 0, WINDOW)

# =================================================================
# 3. 糖霜屋面 (z=1): 六片清色方板边边入扣墙顶
# =================================================================
b.flat("roof_w_s", 1, 1, 1.0, ICING)
b.flat("roof_m_s", 2, 1, 1.0, ICING)
b.flat("roof_e_s", 3, 1, 1.0, ICING)
b.flat("roof_w_n", 1, 2, 1.0, ICING)
b.flat("roof_m_n", 2, 2, 1.0, ICING)
b.flat("roof_e_n", 3, 2, 1.0, ICING)

# =================================================================
# 4. 屋檐糖霜齿带 (南北沿各 3) + 屋脊糖峰 (拼缝 x4)
# =================================================================
b.crest_ns("icing_s_w", 1, 1.0, 1.0, ICING)
b.crest_ns("icing_s_m", 2, 1.0, 1.0, ICING)
b.crest_ns("icing_s_e", 3, 1.0, 1.0, ICING)
b.crest_ns("icing_n_w", 1, 3.0, 1.0, ICING)
b.crest_ns("icing_n_m", 2, 3.0, 1.0, ICING)
b.crest_ns("icing_n_e", 3, 3.0, 1.0, ICING)
b.crest_ew("peak_w_s", 2.0, 1, 1.0, PEAK)
b.crest_ew("peak_w_n", 2.0, 2, 1.0, PEAK)
b.crest_ew("peak_e_s", 3.0, 1, 1.0, PEAK)
b.crest_ew("peak_e_n", 3.0, 2, 1.0, PEAK)

# =================================================================
# 5. 糖果院: 棒棒糖 x2 + 糖果栅栏 x3
# =================================================================
b.spire_ew("lolli_a", 0.0, 3, 0.0, LOLLI_A)
b.spire_ew("lolli_b", 5.0, 2, 0.0, LOLLI_B)
b.crest_ew("fence_sw", 0.0, 0, 0.0, FENCE)
b.crest_ew("fence_se", 5.0, 0, 0.0, FENCE)
b.crest_ew("fence_w", 0.0, 1, 0.0, FENCE)

# =================================================================
# 教程步骤 (9 步)
# =================================================================
b.step(
    "铺雪院南行: 两条雪地长板夹一格红色糖果小径。",
    ["yard_0_0", "path", "yard_3_0"],
    tip="森林深处飘来甜甜的香味 —— 顺着糖果小径走过去看看!",
)
b.step(
    "铺院心两行: 姜饼色的是屋内地板, 清色的是院里的雪。",
    ["yard_0_1", "floor_1_1", "floor_3_1", "yard_4_1",
     "yard_0_2", "floor_1_2", "floor_3_2", "yard_4_2"],
    highlight=["path"],
    tip="行行等边互吸 —— 墙脚要踩住这些拼缝。",
)
b.step(
    "铺雪院北行: 院子铺满。",
    ["yard_0_3", "yard_2_3", "yard_3_3"],
    highlight=["floor_1_2"],
    tip="雪把小院盖得松松软软 —— 正好衬糖果的颜色。",
)
b.step(
    "立南墙与西墙: 红色门框方是糖果大门, 青色窗格是糖窗。",
    ["wall_s_w", "door", "wall_s_e", "window_w", "wall_w_n"],
    highlight=["floor_1_1"],
    tip="大门正对糖果小径 —— 门楣上好像还挂着糖霜呢。",
)
b.step(
    "合北墙与东墙: 十片墙环四角竖边互咬闭环。",
    ["wall_n_w", "wall_n_m", "wall_n_e", "wall_e_s", "window_e"],
    highlight=["wall_s_w"],
    tip="姜饼墙合拢 —— 屋里已经暖烘烘的了。",
)
b.step(
    "盖糖霜屋面: 六片清色方板边边入扣墙顶, 板板互吸。",
    ["roof_w_s", "roof_m_s", "roof_e_s",
     "roof_w_n", "roof_m_n", "roof_e_n"],
    highlight=["wall_s_w"],
    tip="像刚淋上去的一层糖霜 —— 每片方板至少一条边咬住墙顶。",
)
b.step(
    "沿屋檐立糖霜齿带: 南北各三片等边三角, 底边双边受力。",
    ["icing_s_w", "icing_s_m", "icing_s_e",
     "icing_n_w", "icing_n_m", "icing_n_e"],
    highlight=["roof_w_s"],
    tip="齿带同时咬住屋面沿边和墙顶边 —— 好看又结实。",
)
b.step(
    "屋脊立糖峰: 四片粉色小三角骑住屋面拼缝。",
    ["peak_w_s", "peak_w_n", "peak_e_s", "peak_e_n"],
    highlight=["icing_s_w"],
    tip="像挤上去的四朵奶油花 —— 糖果屋的屋顶完工!",
)
b.step(
    "插棒棒糖, 围糖果栅栏: 糖果屋开门迎客!",
    ["lolli_a", "lolli_b", "fence_sw", "fence_se", "fence_w"],
    highlight=["door", "path"],
    tip="院里的棒棒糖一粉一紫 —— 闻得到, 也搭得出的童话。",
)

b.finalize(
    model_id="gingerbread_house_01",
    name="姜饼糖果屋",
    name_en="Gingerbread Candy House 01",
    description=(
        "只用核心九片型的童话入门作: 与高脚海滩小屋和双层别墅都"
        "不同, 这是一只'糖霜齿带姜饼盒' —— 3x2 姜饼色墙环单层落地, "
        "红色门框方糖果大门正对门前糖果小径, 两面青色窗格糖窗对开; "
        "清色糖霜屋面上, 屋檐南北两条等边三角糖霜齿带整圈骑沿 "
        "(底边同时咬住屋面沿边与墙顶边), 屋脊四朵粉色糖峰骑拼缝; "
        "院里棒棒糖一粉一紫, 糖果栅栏围出小院 —— 森林深处, "
        "甜甜的童话开门迎客!"
    ),
    difficulty=2,
    tags=["童话", "奇幻", "糖果屋", "姜饼", "雪院", "入门"],
    min_pieces=45,
    min_steps=9,
)
