#!/usr/bin/env python3
"""生成模型 data/models/owl_01.json (月夜猫头鹰)。

自然世界主题的第一只夜行动物: 与企鹅 (冰面圆胖) 和大象 (长鼻
四柱) 的结构语言都不同 —— 本作是"树桩基座 + 双层鸟身图腾柱":
2x2 树桩墙环托起锯木平台, 猫头鹰蹲在平台正中 —— 身体与头部是
两层 2x1 墙环竖叠, 一对窗格方就是它的招牌大圆眼 (负空间当
眼睛); 双耳羽等边三角骑头顶盖板侧沿, 收拢的翅膀是两片瘦高
等腰贴在身侧, 尾羽双三角骑平台北沿; 林地上红蘑菇、绿树苗
点缀 —— 全库唯一的"窗格眼睛 + 图腾柱身法"。

结构总览 (世界单位: 1.0 = 正方形磁力片边长, 猫头鹰面朝南):
  - 林地 (x [0,4], y [0,4]): 单位方板 x12 + 长板苔径 x2       14 片
  - 树桩 (x [1,3], y [1,3], z 0..1): 墙环 8 + 锯木平台 4       12 片
  - 鸟身 (x [1,3], y [1,2], z 1..2): 墙环 6                     6 片
  - 头部 (同footprint, z 2..3): 墙环 6 (南面双窗格大圆眼)       6 片
  - 头顶盖板 x2 (z=3) + 双耳羽 (等边三角骑盖板侧沿)             4 片
  - 翅膀 x2 (瘦高等腰贴身侧, 骑平台边) + 尾羽 x2 (骑平台北沿)   4 片
  - 红蘑菇 x3 + 绿树苗 x2 + 观察牌窗格方 x1                     6 片
  合计 52 片, 12 个教程步骤, 6 种磁力片形状 (全部 CORE-9 之内)。

物理规则要点 (validate 常规 + strict 双档零警告):
  - 树桩墙环四角竖边互咬, 锯木平台四片边边入扣墙顶并互吸;
  - 鸟身/头部墙环墙脚整边压平台拼缝或下层墙顶, 层层直下,
    整根图腾柱荷载沿墙面传到地面;
  - 翅膀底边整边吸平台侧沿 (西/东), 与身侧墙面错列不重叠;
    尾羽底边整边吸平台北沿; 耳羽底边整边吸盖板东西侧沿;
  - 蘑菇/树苗/观察牌底边整边吸林地拼缝, 剪断任何一条装饰连接
    最多失联 1 片 (< 3), R8 单点失效通过。

用法: python3 tools/generate_owl_01.py  (在 magtile-studio 目录下运行)
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from magtile_gen import ModelBuilder  # noqa: E402

b = ModelBuilder()

GROUND_A = "green"   # 林地棋盘格
GROUND_B = "gray"
STUMP = "orange"     # 树桩 (树皮)
PLATFORM = "yellow"  # 锯木平台 (年轮)
BODY = "purple"      # 鸟身羽毛
BELLY = "clear"      # 胸腹
HEAD = "purple"      # 头部
EYE = "cyan"         # 窗格大圆眼
CAP = "gray"         # 头顶盖板
EAR = "purple"       # 耳羽
WING = "gray"        # 翅膀
TAIL = "orange"      # 尾羽
MUSHROOM = "red"     # 蘑菇
SAPLING = "green"    # 树苗
SIGN = "cyan"        # 观察牌


def wall_ns_t(tid, tile_type, x0, y, z0, color):
    b.add(tid, tile_type, (x0 + 0.5, y, z0 + 0.5), (90, 0, 0), color)


# =================================================================
# 1. 林地 (x [0,4], y [0,4]): 深浅绿棋盘格 (西缘与北缘各嵌一条
#    长板苔径, 其余为单位方板供墙脚/点缀拼缝)
# =================================================================
for x0 in range(4):
    color = GROUND_A if x0 % 2 == 0 else GROUND_B
    b.flat(f"ground_{x0}_0", x0, 0, 0.0, color)
b.flat_rect("moss_w", 0, 1, 0.0, GROUND_A, axis="y")      # [0,1]x[1,3]
for x0 in (1, 2, 3):
    color = GROUND_B if x0 % 2 == 0 else GROUND_A
    b.flat(f"ground_{x0}_1", x0, 1, 0.0, color)
for x0 in (1, 2, 3):
    color = GROUND_A if x0 % 2 == 0 else GROUND_B
    b.flat(f"ground_{x0}_2", x0, 2, 0.0, color)
b.flat("ground_0_3", 0, 3, 0.0, GROUND_B)
b.flat_rect("moss_n", 1, 3, 0.0, GROUND_A)                # [1,3]x[3,4]
b.flat("ground_3_3", 3, 3, 0.0, GROUND_B)

# =================================================================
# 2. 树桩 (x [1,3], y [1,3], z 0..1): 墙环 + 锯木平台
# =================================================================
b.wall_ns("stump_s_w", 1, 1.0, 0, STUMP)
b.wall_ns("stump_s_e", 2, 1.0, 0, STUMP)
b.wall_ns("stump_n_w", 1, 3.0, 0, STUMP)
b.wall_ns("stump_n_e", 2, 3.0, 0, STUMP)
b.wall_ew("stump_w_s", 1.0, 1, 0, STUMP)
b.wall_ew("stump_w_n", 1.0, 2, 0, STUMP)
b.wall_ew("stump_e_s", 3.0, 1, 0, STUMP)
b.wall_ew("stump_e_n", 3.0, 2, 0, STUMP)
b.flat("platform_1_1", 1, 1, 1.0, PLATFORM)
b.flat("platform_2_1", 2, 1, 1.0, PLATFORM)
b.flat("platform_1_2", 1, 2, 1.0, PLATFORM)
b.flat("platform_2_2", 2, 2, 1.0, PLATFORM)

# =================================================================
# 3. 鸟身 (x [1,3], y [1,2], z 1..2): 墙环 (南面胸腹清色)
# =================================================================
b.wall_ns("body_s_w", 1, 1.0, 1, BELLY)
b.wall_ns("body_s_e", 2, 1.0, 1, BELLY)
b.wall_ns("body_n_w", 1, 2.0, 1, BODY)
b.wall_ns("body_n_e", 2, 2.0, 1, BODY)
b.wall_ew("body_w", 1.0, 1, 1, BODY)
b.wall_ew("body_e", 3.0, 1, 1, BODY)

# =================================================================
# 4. 头部 (z 2..3): 南面一对窗格方大圆眼
# =================================================================
wall_ns_t("eye_w", "window_square", 1, 1.0, 2, EYE)
wall_ns_t("eye_e", "window_square", 2, 1.0, 2, EYE)
b.wall_ns("head_n_w", 1, 2.0, 2, HEAD)
b.wall_ns("head_n_e", 2, 2.0, 2, HEAD)
b.wall_ew("head_w", 1.0, 1, 2, HEAD)
b.wall_ew("head_e", 3.0, 1, 2, HEAD)

# 头顶盖板 + 双耳羽
b.flat("cap_w", 1, 1, 3.0, CAP)
b.flat("cap_e", 2, 1, 3.0, CAP)
b.crest_ew("ear_w", 1.0, 1, 3.0, EAR)
b.crest_ew("ear_e", 3.0, 1, 3.0, EAR)

# =================================================================
# 5. 翅膀 (瘦高等腰骑平台西/东沿, 贴在身后侧) + 尾羽 (平台北沿)
# =================================================================
b.spire_ew("wing_w", 1.0, 2, 1.0, WING)
b.spire_ew("wing_e", 3.0, 2, 1.0, WING)
b.crest_ns("tail_w", 1, 3.0, 1.0, TAIL)
b.crest_ns("tail_e", 2, 3.0, 1.0, TAIL)

# =================================================================
# 6. 林地点缀: 蘑菇 x3 + 树苗 x2 + 观察牌
# =================================================================
b.crest_ns("mushroom_a", 0, 1.0, 0.0, MUSHROOM)
b.crest_ns("mushroom_b", 3, 4.0, 0.0, MUSHROOM)
b.crest_ew("mushroom_c", 4.0, 2, 0.0, MUSHROOM)
b.spire_ns("sapling_a", 0, 4.0, 0.0, SAPLING)
b.spire_ew("sapling_b", 4.0, 0, 0.0, SAPLING)
wall_ns_t("sign", "window_square", 2, 0.0, 0, SIGN)   # 观察牌

# =================================================================
# 教程步骤 (12 步)
# =================================================================
b.step(
    "铺林地南行: 深浅绿棋盘格四片, 边边互吸。",
    [f"ground_{x0}_0" for x0 in range(4)],
    tip="夜色刚落下, 森林安静下来 —— 先铺出这片林间空地。",
)
b.step(
    "铺林地第二、三行: 西缘竖嵌一条长板苔径, 其余方板补齐。",
    ["moss_w", "ground_1_1", "ground_2_1", "ground_3_1",
     "ground_1_2", "ground_2_2", "ground_3_2"],
    highlight=["ground_0_0"],
    tip="行行等边互吸, 林地连成一整张网 —— 树桩的墙脚要踩这些拼缝。",
)
b.step(
    "铺林地北行: 中段再嵌一条长板苔径, 空地铺满。",
    ["ground_0_3", "moss_n", "ground_3_3"],
    highlight=["ground_1_2"],
    tip="正中四格就是老树桩的家。",
)
b.step(
    "立树桩南墙与西墙: 四片橙色树皮墙踩住拼缝。",
    ["stump_s_w", "stump_s_e", "stump_w_s", "stump_w_n"],
    highlight=["ground_1_1"],
    tip="树桩是猫头鹰的瞭望台 —— 墙脚咬牢, 上面还要站鸟呢。",
)
b.step(
    "合树桩北墙与东墙: 八片墙环四角竖边互咬闭环。",
    ["stump_n_w", "stump_n_e", "stump_e_s", "stump_e_n"],
    highlight=["stump_s_w"],
    tip="2x2 的墙环围好了 —— 这是整只猫头鹰的地基。",
)
b.step(
    "铺锯木平台: 四片黄色方板边边入扣墙顶, 板板互吸。",
    ["platform_1_1", "platform_2_1", "platform_1_2", "platform_2_2"],
    highlight=["stump_s_w"],
    tip="像刚锯开的树桩年轮 —— 每片至少一条边咬住墙顶。",
)
b.step(
    "起鸟身墙环: 南面两片清色是胸腹, 墙脚压平台拼缝。",
    ["body_s_w", "body_s_e", "body_n_w", "body_n_e",
     "body_w", "body_e"],
    highlight=["platform_1_1"],
    tip="猫头鹰蹲坐的身体是 2x1 的墙环 —— 荷载沿墙面一路传到地面。",
)
b.step(
    "叠头部墙环: 南面装一对窗格方 —— 那是它的大圆眼!",
    ["eye_w", "eye_e", "head_n_w", "head_n_e", "head_w", "head_e"],
    highlight=["body_s_w"],
    tip="窗格的洞就是瞳孔 —— 猫头鹰的眼睛在夜里最亮。",
)
b.step(
    "盖头顶盖板, 竖起双耳羽: 等边三角骑住盖板东西侧沿。",
    ["cap_w", "cap_e", "ear_w", "ear_e"],
    highlight=["eye_w"],
    tip="两撮耳羽尖尖的 —— 其实那不是耳朵, 是它的羽毛角。",
)
b.step(
    "贴收拢的翅膀, 插上尾羽: 猫头鹰全身完工。",
    ["wing_w", "wing_e", "tail_w", "tail_e"],
    highlight=["body_w", "platform_1_2"],
    tip="瘦高翅膀骑平台侧沿贴在身后, 尾羽朝北 —— 起飞前的姿势。",
)
b.step(
    "林地长出红蘑菇: 三片小红三角骑在拼缝上。",
    ["mushroom_a", "mushroom_b", "mushroom_c"],
    highlight=["ground_0_0"],
    tip="夜里的蘑菇圈 —— 传说绕着它走三圈会有好运气。",
)
b.step(
    "种树苗、立观察牌: 月夜森林开园!",
    ["sapling_a", "sapling_b", "sign"],
    highlight=["mushroom_a", "eye_w"],
    tip="牌上写着: 保持安静 —— 猫头鹰工作到天亮, 白天请让它睡觉。",
)

b.finalize(
    model_id="owl_01",
    name="月夜猫头鹰",
    name_en="Night Owl 01",
    description=(
        "只用核心九片型的夜行动物: 与圆胖企鹅和四柱大象都不同, "
        "猫头鹰是一根'树桩基座 + 双层鸟身'的图腾柱 —— 2x2 橙色"
        "树桩墙环托起黄色锯木平台, 紫色身体与头部两层墙环竖叠, "
        "一对青色窗格方就是它的招牌大圆眼 (窗洞当瞳孔); 双耳羽"
        "骑头顶盖板, 灰色瘦高翅膀收在身后, 橙色尾羽指北; 林地"
        "红蘑菇圈与绿树苗点缀月夜 —— 咕, 咕, 森林守夜人上岗了!"
    ),
    difficulty=3,
    tags=["自然", "动物世界", "猫头鹰", "森林", "夜晚", "进阶"],
    min_pieces=52,
    min_steps=12,
)
