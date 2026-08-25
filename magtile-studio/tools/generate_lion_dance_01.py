#!/usr/bin/env python3
"""生成模型 data/models/lion_dance_01.json (新春舞狮)。

全库第一场舞狮: 民俗主题继龙舟之后的第二作, 结构主角是"游行
中的三段式狮子" —— 2x2 双层狮头昂在队首, 底层两片门框方并排
是张开的大嘴 (负空间当嘴巴), 顶盖四周等边鬃毛骑沿口, 一对
青色眼睫立在额前; 狮身是两顶"舞狮人拱顶轿" (1x2 墙环驮长板
披风), 披风上错列橙色鳞浪, 队尾瘦高尾羽上翘; 北侧红鼓 1x1
墙环鼓身 + 金色鼓面压顶, 鼓槌骑沿, 窗格方大锣立在鼓旁 ——
全库唯一的"双门框大嘴 + 分段披风狮身"组合。

结构总览 (世界单位: 1.0 = 正方形磁力片边长, 狮头朝西):
  - 长街 (x [0,7], y [0,5]): 红毯长板 7 + 街面 13              20 片
  - 狮头 (x [1,3], y [1,3], z 0..2): 双层墙环 16 + 顶盖 2      18 片
  - 眼睫 x2 + 鬃毛 x4 (等边骑顶盖沿口)                          6 片
  - 狮身前段 (x [4,5]): 墙环 6 + 披风 1 + 鳞浪 2 + 脊鳍 1      10 片
  - 狮身后段 (x [6,7]): 墙环 6 + 披风 1 + 鳞浪 2 + 尾羽 1      10 片
  - 红鼓 (x [3,4], y [3,4]): 墙环 4 + 鼓面 1 + 鼓槌 1 + 锣 1    7 片
  - 灯笼杆 x2 (瘦高) + 鞭炮串 1 + 彩旗 1                        4 片
  合计 75 片, 14 个教程步骤, 6 种磁力片形状 (全部 CORE-9 之内)。

物理规则要点 (validate 常规 + strict 双档零警告):
  - 狮头/狮身/鼓的墙环墙脚全部踩街面拼缝, 四角竖边互咬;
  - 狮头第二层墙脚整边压首层墙顶, 顶盖两条长板边边入扣;
  - 披风长板四边入扣墙顶 (南北短边+东西长边全部受力);
  - 鬃毛/鳞浪/鼓槌等边三角底边整边吸沿口, 剪断任何一条装饰
    连接最多失联 1 片 (< 3), R8 单点失效通过。

用法: python3 tools/generate_lion_dance_01.py  (在 magtile-studio 目录下运行)
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from magtile_gen import ModelBuilder  # noqa: E402

b = ModelBuilder()

CARPET = "red"       # 红毯
STREET_A = "gray"    # 青石街面
STREET_B = "green"   # 街边草饰
LION_R = "red"       # 狮头主色
LION_G = "yellow"    # 金鬃
EYE = "cyan"         # 眼睫
CLOAK = "red"        # 狮身披风
SCALE = "orange"     # 鳞浪
DRUM = "red"         # 鼓身
DRUM_TOP = "yellow"  # 鼓面
GONG = "yellow"      # 大锣
LANTERN = "red"      # 灯笼杆
CRACKER = "pink"     # 鞭炮串
FLAG = "cyan"        # 彩旗


def wall_ns_t(tid, tile_type, x0, y, z0, color):
    b.add(tid, tile_type, (x0 + 0.5, y, z0 + 0.5), (90, 0, 0), color)


def wall_ew_t(tid, tile_type, x, y0, z0, color):
    b.add(tid, tile_type, (x, y0 + 0.5, z0 + 0.5), (90, 0, 90), color)


# =================================================================
# 1. 长街 (x [0,7], y [0,5]): 中央红毯 + 两侧青石街面
# =================================================================
for i in range(7):
    b.flat_rect(f"carpet_{i}", i, 1, 0.0, CARPET, axis="y")   # y [1,3]
b.flat_rect("street_s_0", 0, 0, 0.0, STREET_A)
b.flat("street_s_2", 2, 0, 0.0, STREET_B)
b.flat_rect("street_s_3", 3, 0, 0.0, STREET_A)
b.flat_rect("street_s_5", 5, 0, 0.0, STREET_A)
b.flat_rect("street_n_0", 0, 3, 0.0, STREET_A)
b.flat("street_n_2", 2, 3, 0.0, STREET_B)
b.flat("street_n_3", 3, 3, 0.0, STREET_A)
b.flat_rect("street_n_4", 4, 3, 0.0, STREET_A)
b.flat("street_n_6", 6, 3, 0.0, STREET_B)
b.flat("street_n2_0", 0, 4, 0.0, STREET_B)
b.flat_rect("street_n2_1", 1, 4, 0.0, STREET_A)
b.flat_rect("street_n2_3", 3, 4, 0.0, STREET_A)
b.flat_rect("street_n2_5", 5, 4, 0.0, STREET_A)

# =================================================================
# 2. 狮头 (x [1,3], y [1,3], z 0..2): 首层双门框大嘴, 二层金额头
# =================================================================
wall_ew_t("mouth_s", "door_frame", 1.0, 1, 0, LION_R)
wall_ew_t("mouth_n", "door_frame", 1.0, 2, 0, LION_R)
b.wall_ew("head_e_s", 3.0, 1, 0, LION_G)
b.wall_ew("head_e_n", 3.0, 2, 0, LION_G)
b.wall_ns("head_s_w", 1, 1.0, 0, LION_R)
b.wall_ns("head_s_e", 2, 1.0, 0, LION_G)
b.wall_ns("head_n_w", 1, 3.0, 0, LION_G)
b.wall_ns("head_n_e", 2, 3.0, 0, LION_R)

b.wall_ew("brow_w_s", 1.0, 1, 1, LION_G)
b.wall_ew("brow_w_n", 1.0, 2, 1, LION_G)
b.wall_ew("head2_e_s", 3.0, 1, 1, LION_R)
b.wall_ew("head2_e_n", 3.0, 2, 1, LION_R)
b.wall_ns("head2_s_w", 1, 1.0, 1, LION_R)
b.wall_ns("head2_s_e", 2, 1.0, 1, LION_R)
b.wall_ns("head2_n_w", 1, 3.0, 1, LION_R)
b.wall_ns("head2_n_e", 2, 3.0, 1, LION_R)

b.flat_rect("head_cap_w", 1, 1, 2.0, LION_R, axis="y")
b.flat_rect("head_cap_e", 2, 1, 2.0, LION_R, axis="y")

# 眼睫 (骑顶盖西沿, 立在额前) + 鬃毛 (骑顶盖南北沿)
b.crest_ew("eye_s", 1.0, 1, 2.0, EYE)
b.crest_ew("eye_n", 1.0, 2, 2.0, EYE)
b.crest_ns("mane_s_w", 1, 1.0, 2.0, LION_G)
b.crest_ns("mane_s_e", 2, 1.0, 2.0, LION_G)
b.crest_ns("mane_n_w", 1, 3.0, 2.0, LION_G)
b.crest_ns("mane_n_e", 2, 3.0, 2.0, LION_G)

# =================================================================
# 3. 狮身前段 (x [4,5], y [1,3], z 0..1): 舞狮人拱顶轿 + 披风
# =================================================================
b.wall_ns("body1_s", 4, 1.0, 0, LION_G)
b.wall_ns("body1_n", 4, 3.0, 0, LION_G)
b.wall_ew("body1_w_s", 4.0, 1, 0, CLOAK)
b.wall_ew("body1_w_n", 4.0, 2, 0, CLOAK)
b.wall_ew("body1_e_s", 5.0, 1, 0, CLOAK)
b.wall_ew("body1_e_n", 5.0, 2, 0, CLOAK)
b.flat_rect("cloak1", 4, 1, 1.0, CLOAK, axis="y")
b.crest_ns("scale1_s", 4, 1.0, 1.0, SCALE)
b.crest_ns("scale1_n", 4, 3.0, 1.0, SCALE)
b.crest_ew("fin1", 5.0, 1, 1.0, LION_R)

# =================================================================
# 4. 狮身后段 (x [6,7], y [1,3], z 0..1) + 上翘尾羽
# =================================================================
b.wall_ns("body2_s", 6, 1.0, 0, LION_G)
b.wall_ns("body2_n", 6, 3.0, 0, LION_G)
b.wall_ew("body2_w_s", 6.0, 1, 0, CLOAK)
b.wall_ew("body2_w_n", 6.0, 2, 0, CLOAK)
b.wall_ew("body2_e_s", 7.0, 1, 0, CLOAK)
b.wall_ew("body2_e_n", 7.0, 2, 0, CLOAK)
b.flat_rect("cloak2", 6, 1, 1.0, CLOAK, axis="y")
b.crest_ns("scale2_s", 6, 1.0, 1.0, SCALE)
b.crest_ns("scale2_n", 6, 3.0, 1.0, SCALE)
b.spire_ew("tail", 7.0, 1, 1.0, SCALE)

# =================================================================
# 5. 红鼓 (x [3,4], y [3,4], z 0..1) + 鼓槌 + 大锣
# =================================================================
b.wall_ns("drum_s", 3, 3.0, 0, DRUM)
b.wall_ns("drum_n", 3, 4.0, 0, DRUM)
b.wall_ew("drum_w", 3.0, 3, 0, DRUM)
b.wall_ew("drum_e", 4.0, 3, 0, DRUM)
b.flat("drum_top", 3, 3, 1.0, DRUM_TOP)
b.crest_ns("drumstick", 3, 4.0, 1.0, SCALE)
wall_ns_t("gong", "window_square", 6, 4.0, 0, GONG)

# =================================================================
# 6. 街景: 灯笼杆 x2 + 鞭炮串 + 彩旗
# =================================================================
b.spire_ew("lantern_a", 0.0, 0, 0.0, LANTERN)
b.spire_ew("lantern_b", 5.0, 0, 0.0, LANTERN)
b.crest_ew("firecracker", 0.0, 4, 0.0, CRACKER)
b.crest_ew("flag", 7.0, 4, 0.0, FLAG)

# =================================================================
# 教程步骤 (14 步)
# =================================================================
b.step(
    "铺中央红毯: 七条红长板边边互吸, 一路铺到街尾。",
    [f"carpet_{i}" for i in range(7)],
    tip="咚咚锵! 新春的长街上, 舞狮队要从红毯上走过。",
)
b.step(
    "铺南侧街面: 青石板夹一格街边草饰。",
    ["street_s_0", "street_s_2", "street_s_3", "street_s_5"],
    highlight=["carpet_0"],
    tip="石板与红毯行行互吸 —— 狮头的墙脚要踩这些拼缝。",
)
b.step(
    "铺北侧街面: 两行石板补齐, 鼓位留在红毯边。",
    ["street_n_0", "street_n_2", "street_n_3", "street_n_4",
     "street_n_6", "street_n2_0", "street_n2_1", "street_n2_3",
     "street_n2_5"],
    highlight=["carpet_3"],
    tip="长街铺满 —— 观众都在街边等着看狮子呢。",
)
b.step(
    "立狮头首层: 队首两片门框方并排, 就是张开的大嘴!",
    ["mouth_s", "mouth_n", "head_s_w", "head_s_e",
     "head_n_w", "head_n_e", "head_e_s", "head_e_n"],
    highlight=["carpet_1"],
    tip="门洞就是嘴巴 —— 舞狮讨彩头, 大嘴要张得大大的。",
)
b.step(
    "叠狮头二层: 金色额头压在嘴巴正上方, 墙脚整边压墙顶。",
    ["brow_w_s", "brow_w_n", "head2_s_w", "head2_s_e",
     "head2_n_w", "head2_n_e", "head2_e_s", "head2_e_n"],
    highlight=["mouth_s"],
    tip="双层狮头昂起来 —— 荷载沿墙面层层传到街面。",
)
b.step(
    "盖狮头顶盖: 两条红长板边边入扣墙顶。",
    ["head_cap_w", "head_cap_e"],
    highlight=["brow_w_s"],
    tip="顶盖锁住整圈墙 —— 鬃毛和眼睫都要骑在它的沿口上。",
)
b.step(
    "立眼睫与鬃毛: 青色眼睫立在额前, 金鬃分列南北沿。",
    ["eye_s", "eye_n", "mane_s_w", "mane_s_e", "mane_n_w", "mane_n_e"],
    highlight=["head_cap_w"],
    tip="眨眨眼 —— 狮子有了精气神, 鬃毛随步子一颤一颤。",
)
b.step(
    "立狮身前段墙环: 这是第一位舞狮人的拱顶轿。",
    ["body1_s", "body1_n", "body1_w_s", "body1_w_n",
     "body1_e_s", "body1_e_n"],
    highlight=["carpet_4"],
    tip="狮身分段才能舞得起伏 —— 每段各有一位舞狮人在里面。",
)
b.step(
    "披狮身前段披风: 长板四边入扣墙顶, 鳞浪与脊鳍骑沿。",
    ["cloak1", "scale1_s", "scale1_n", "fin1"],
    highlight=["body1_s"],
    tip="披风一抖, 橙色鳞浪就跟着翻起来。",
)
b.step(
    "立狮身后段墙环: 第二位舞狮人跟上步子。",
    ["body2_s", "body2_n", "body2_w_s", "body2_w_n",
     "body2_e_s", "body2_e_n"],
    highlight=["carpet_6"],
    tip="前后两段隔一步, 狮身舞起来才有波浪的起伏。",
)
b.step(
    "披狮身后段披风, 翘起尾羽: 狮子全身完工。",
    ["cloak2", "scale2_s", "scale2_n", "tail"],
    highlight=["body2_s"],
    tip="瘦高尾羽向上一甩 —— 好一个精神的狮子摆尾!",
)
b.step(
    "架红鼓: 1x1 墙环鼓身踩拼缝, 金色鼓面压顶。",
    ["drum_s", "drum_n", "drum_w", "drum_e", "drum_top"],
    highlight=["street_n_3"],
    tip="鼓是舞狮的心跳 —— 鼓点快, 狮子跳; 鼓点慢, 狮子摇。",
)
b.step(
    "搭鼓槌与大锣: 锣鼓班子就位。",
    ["drumstick", "gong"],
    highlight=["drum_top"],
    tip="窗格方是大锣 —— 咚咚锵, 咚咚锵, 锣鼓一响年味就来了。",
)
b.step(
    "竖灯笼杆, 挂鞭炮串与彩旗: 新春长街开舞!",
    ["lantern_a", "lantern_b", "firecracker", "flag"],
    highlight=["mouth_s", "tail"],
    tip="狮子眨眨眼, 朝你一点头 —— 恭喜发财, 新年大吉!",
)

b.finalize(
    model_id="lion_dance_01",
    name="新春舞狮",
    name_en="New Year Lion Dance 01",
    description=(
        "只用核心九片型的民俗大戏: 长街红毯上, 一只三段式狮子正在"
        "游行 —— 2x2 双层狮头昂在队首, 底层两片门框方并排就是张开"
        "讨彩头的大嘴 (负空间当嘴巴), 金鬃骑顶盖沿口, 青色眼睫立在"
        "额前; 狮身是两顶'舞狮人拱顶轿', 1x2 墙环驮红披风, 橙色鳞浪"
        "错列翻滚, 队尾瘦高尾羽上翘; 北侧红鼓金面配窗格大锣, 灯笼杆"
        "鞭炮串彩旗满街 —— 咚咚锵, 恭喜发财, 新年大吉!"
    ),
    difficulty=3,
    tags=["节日", "民俗", "舞狮", "新春", "锣鼓", "进阶"],
    min_pieces=75,
    min_steps=14,
)
