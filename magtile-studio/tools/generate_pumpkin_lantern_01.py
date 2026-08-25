#!/usr/bin/env python3
"""生成模型 data/models/pumpkin_lantern_01.json (南瓜灯小屋)。

内容批 H 模型 1/4: 全库第一个万圣节主题模型, 补上节日主题矩阵里
一直空着的万圣节席位。与姜饼糖果屋 (糖霜齿带姜饼盒) 和雪人
(三比一突变收分) 的结构语言都不同 —— 本作的结构签名是
"脸就砌在墙上, 瓜棱骑在缝上": 二层墙环的南立面直接用片型拼出
南瓜灯的脸 —— 两扇黄色窗格方是发光的眼睛, 一扇黄色门框方是
咧开的嘴巴 (兼作小屋大门); 瓜顶四条橙色瓜棱等边三角骑满两条
盖板拼缝, 绿色瓜蒂瘦高尖从顶心拼缝直上 —— 远远看去就是一只
点了蜡烛的大南瓜。

结构总览 (世界单位: 1.0 = 正方形磁力片边长, 南瓜脸朝南):
  - 暮色瓜田 (x [0,6], y [0,4]): 方板 13 + 长板 6            19 片
  - 一层墙环 (x [1,4], y [1,3], z 0..1): 方墙 9 + 门框嘴 1    10 片
  - 二层墙环 (z 1..2): 方墙 8 + 窗格眼睛 2                    10 片
  - 瓜顶盖板 (z=2): 方板 x6                                    6 片
  - 瓜棱 x4 (等边骑拼缝) + 瓜蒂 x1 (瘦高尖骑顶心缝)            5 片
  - 小南瓜 x2 (等边四坡锥, 四棱自锁)                            8 片
  - 篱笆 x3 + 小灰猫 x1 (等边骑沿口)                            4 片
  合计 62 片, 12 个教程步骤, 6 种磁力片形状 (全部 CORE-9 之内)。

物理规则要点 (validate 常规 + strict 双档零警告 + jitter 全绿):
  - 墙环墙脚全部踩瓜田拼缝 (墙脚下全单位方板), 四角竖边互咬闭环;
  - 二层墙环底边与一层墙顶整边共线吸合, 窗格/门框物理上按实心
    正方形处理;
  - 瓜顶六片盖板边边入扣墙顶并互吸; 瓜棱底边同时吸两侧盖板
    拼缝 (双边受力), 瓜蒂骑顶心缝;
  - 小南瓜等边四坡锥四棱自锁, 底边整边吸脚下单位方板;
  - 篱笆/小猫等边三角底边整边吸沿口, 剪断任何一条装饰连接
    最多失联 1 片 (< 3), R8 单点失效通过。

用法: python3 tools/generate_pumpkin_lantern_01.py  (在 magtile-studio 目录下运行)
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from magtile_gen import ModelBuilder  # noqa: E402

b = ModelBuilder()

LAWN = "green"       # 暮色草地
DUSK = "purple"      # 暮色花圃
PATH = "gray"        # 石板小径
GLOW = "yellow"      # 烛光地板 / 眼睛 / 嘴巴
RIND = "orange"      # 南瓜皮
STEM = "green"       # 瓜蒂
MINI = "orange"      # 小南瓜
FENCE = "gray"       # 木篱笆
CAT = "gray"         # 小灰猫


def wall_ns_t(tid, tile_type, x0, y, z0, color):
    b.add(tid, tile_type, (x0 + 0.5, y, z0 + 0.5), (90, 0, 0), color)


# =================================================================
# 1. 暮色瓜田 (x [0,6], y [0,4]): 草地 + 花圃 + 石板小径
# =================================================================
# 南行 (y [0,1]): 小径正对大门, 小南瓜 A 的底格是单位方板
b.flat_rect("field_0_0", 0, 0, 0.0, LAWN)
b.flat("path", 2, 0, 0.0, PATH)
b.flat("field_3_0", 3, 0, 0.0, DUSK)
b.flat("field_4_0", 4, 0, 0.0, LAWN)
b.flat("field_5_0", 5, 0, 0.0, DUSK)
# 中段两行 (y [1,3]): 屋内烛光地板全单位方板, 墙脚踩拼缝
b.flat("field_0_1", 0, 1, 0.0, DUSK)
b.flat("floor_1_1", 1, 1, 0.0, GLOW)
b.flat("floor_2_1", 2, 1, 0.0, GLOW)
b.flat("floor_3_1", 3, 1, 0.0, GLOW)
b.flat_rect("field_4_1", 4, 1, 0.0, LAWN)
b.flat("field_0_2", 0, 2, 0.0, LAWN)
b.flat("floor_1_2", 1, 2, 0.0, GLOW)
b.flat("floor_2_2", 2, 2, 0.0, GLOW)
b.flat("floor_3_2", 3, 2, 0.0, GLOW)
b.flat_rect("field_4_2", 4, 2, 0.0, DUSK)
# 北行 (y [3,4]): 小南瓜 B 的底格是单位方板
b.flat_rect("field_0_3", 0, 3, 0.0, DUSK)
b.flat_rect("field_2_3", 2, 3, 0.0, LAWN)
b.flat("field_4_3", 4, 3, 0.0, LAWN)
b.flat("field_5_3", 5, 3, 0.0, DUSK)

# =================================================================
# 2. 一层墙环 (x [1,4], y [1,3], z 0..1): 门框方就是咧开的嘴巴
# =================================================================
b.wall_ns("w1_s_w", 1, 1.0, 0, RIND)
wall_ns_t("mouth", "door_frame", 2, 1.0, 0, GLOW)   # 嘴巴兼大门
b.wall_ns("w1_s_e", 3, 1.0, 0, RIND)
b.wall_ns("w1_n_w", 1, 3.0, 0, RIND)
b.wall_ns("w1_n_m", 2, 3.0, 0, RIND)
b.wall_ns("w1_n_e", 3, 3.0, 0, RIND)
b.wall_ew("w1_w_s", 1.0, 1, 0, RIND)
b.wall_ew("w1_w_n", 1.0, 2, 0, RIND)
b.wall_ew("w1_e_s", 4.0, 1, 0, RIND)
b.wall_ew("w1_e_n", 4.0, 2, 0, RIND)

# =================================================================
# 3. 二层墙环 (z 1..2): 两扇黄窗格是发光的眼睛
# =================================================================
wall_ns_t("eye_w", "window_square", 1, 1.0, 1, GLOW)
b.wall_ns("w2_s_m", 2, 1.0, 1, RIND)
wall_ns_t("eye_e", "window_square", 3, 1.0, 1, GLOW)
b.wall_ns("w2_n_w", 1, 3.0, 1, RIND)
b.wall_ns("w2_n_m", 2, 3.0, 1, RIND)
b.wall_ns("w2_n_e", 3, 3.0, 1, RIND)
b.wall_ew("w2_w_s", 1.0, 1, 1, RIND)
b.wall_ew("w2_w_n", 1.0, 2, 1, RIND)
b.wall_ew("w2_e_s", 4.0, 1, 1, RIND)
b.wall_ew("w2_e_n", 4.0, 2, 1, RIND)

# =================================================================
# 4. 瓜顶盖板 (z=2): 六片橙色方板边边入扣墙顶
# =================================================================
b.flat("cap_w_s", 1, 1, 2.0, RIND)
b.flat("cap_m_s", 2, 1, 2.0, RIND)
b.flat("cap_e_s", 3, 1, 2.0, RIND)
b.flat("cap_w_n", 1, 2, 2.0, RIND)
b.flat("cap_m_n", 2, 2, 2.0, RIND)
b.flat("cap_e_n", 3, 2, 2.0, RIND)

# =================================================================
# 5. 瓜棱 x4 (骑盖板拼缝) + 瓜蒂 (瘦高尖骑顶心缝)
# =================================================================
b.crest_ew("ridge_w_s", 2.0, 1, 2.0, RIND)
b.crest_ew("ridge_w_n", 2.0, 2, 2.0, RIND)
b.crest_ew("ridge_e_s", 3.0, 1, 2.0, RIND)
b.crest_ew("ridge_e_n", 3.0, 2, 2.0, RIND)
b.spire_ns("stem", 2, 2.0, 2.0, STEM)   # 顶心缝直上, 尖 3.94 全场制高

# =================================================================
# 6. 小南瓜 x2 (等边四坡锥四棱自锁) + 篱笆 x3 + 小灰猫
# =================================================================
b.hat4("mini_a", 4, 0, 0.0, MINI, shape="equilateral_triangle")
b.hat4("mini_b", 5, 3, 0.0, MINI, shape="equilateral_triangle")
b.crest_ew("fence_sw", 0.0, 0, 0.0, FENCE)
b.crest_ew("fence_nw", 0.0, 3, 0.0, FENCE)
b.crest_ew("fence_e", 6.0, 1, 0.0, FENCE)
b.crest_ns("cat", 3, 0.0, 0.0, CAT)     # 蹲在小径旁看灯

# =================================================================
# 教程步骤 (12 步)
# =================================================================
b.step(
    "铺瓜田南行: 石板小径正对将来的大门, 东边留出小南瓜的底格。",
    ["field_0_0", "path", "field_3_0", "field_4_0", "field_5_0"],
    tip="秋收之夜, 瓜田里要点起一盏大灯笼 —— 先把小院铺平整。",
)
b.step(
    "铺中段两行: 黄色的是屋里的烛光地板, 墙脚要踩住这些拼缝。",
    ["field_0_1", "floor_1_1", "floor_2_1", "floor_3_1", "field_4_1",
     "field_0_2", "floor_1_2", "floor_2_2", "floor_3_2", "field_4_2"],
    highlight=["path"],
    tip="行行等边互吸 —— 屋里先铺一层暖暖的烛光色。",
)
b.step(
    "铺瓜田北行: 西边紫色花圃, 东边再留一格小南瓜底格。",
    ["field_0_3", "field_2_3", "field_4_3", "field_5_3"],
    highlight=["floor_1_2"],
    tip="单位方板的四条边都能整边吸合 —— 小南瓜就要种在那格上。",
)
b.step(
    "立一层南墙与西墙: 黄色门框方是南瓜灯咧开的嘴巴, 也是大门。",
    ["w1_s_w", "mouth", "w1_s_e", "w1_w_s", "w1_w_n"],
    highlight=["floor_1_1"],
    tip="嘴巴先上墙 —— 从小径走过来, 正好走进南瓜的笑容里。",
)
b.step(
    "合一层北墙与东墙: 十片墙环四角竖边互咬闭环。",
    ["w1_n_w", "w1_n_m", "w1_n_e", "w1_e_s", "w1_e_n"],
    highlight=["w1_s_w"],
    tip="闭环墙才站得稳 —— 每个拐角都有两条竖边互相咬住。",
)
b.step(
    "摞二层南墙与西墙: 两扇黄窗格一左一右, 是南瓜灯发光的眼睛。",
    ["eye_w", "w2_s_m", "eye_e", "w2_w_s", "w2_w_n"],
    highlight=["w1_s_w"],
    tip="底边与一层墙顶整边共线吸合 —— 眼睛亮起来啦!",
)
b.step(
    "合二层北墙与东墙: 南瓜的脸砌完整。",
    ["w2_n_w", "w2_n_m", "w2_n_e", "w2_e_s", "w2_e_n"],
    highlight=["eye_w"],
    tip="两层墙环层层互压 —— 荷载沿墙面一路传到瓜田里。",
)
b.step(
    "盖瓜顶: 六片橙色盖板边边入扣墙顶, 板板互吸。",
    ["cap_w_s", "cap_m_s", "cap_e_s", "cap_w_n", "cap_m_n", "cap_e_n"],
    highlight=["w2_s_m"],
    tip="每片盖板至少一条边咬住墙顶 —— 圆滚滚的瓜顶合拢。",
)
b.step(
    "立瓜棱插瓜蒂: 四片等边三角骑住盖板拼缝, 绿色瓜蒂从顶心直上。",
    ["ridge_w_s", "ridge_w_n", "ridge_e_s", "ridge_e_n", "stem"],
    highlight=["cap_m_s"],
    tip="瓜棱底边同时咬住两侧盖板 —— 这才像一只饱满的大南瓜。",
)
b.step(
    "种东南角小南瓜: 四片等边三角斜棱互吸, 自锁成锥。",
    ["mini_a_s", "mini_a_e", "mini_a_n", "mini_a_w"],
    highlight=["field_4_0"],
    tip="四条底边都要整边吸住脚下的方板 —— 丰收的第一只小南瓜。",
)
b.step(
    "种东北角小南瓜: 同样的四坡锥, 瓜田更热闹了。",
    ["mini_b_s", "mini_b_e", "mini_b_n", "mini_b_w"],
    highlight=["field_5_3"],
    tip="大瓜带小瓜 —— 谁提走一只当灯笼?",
)
b.step(
    "围篱笆, 请小灰猫入座: 南瓜灯小屋点灯迎客!",
    ["fence_sw", "fence_nw", "fence_e", "cat"],
    highlight=["mouth", "path"],
    tip="小灰猫蹲在小径旁 —— 提着小灯笼的朋友们, 快来讨糖果吧!",
)

b.finalize(
    model_id="pumpkin_lantern_01",
    name="南瓜灯小屋",
    name_en="Pumpkin Lantern House 01",
    description=(
        "只用核心九片型的万圣节首秀: 与姜饼糖果屋和雪人的结构语言"
        "都不同, 这座小屋的脸就砌在墙上 —— 二层墙环的南立面用片型"
        "直接拼出南瓜灯的表情: 两扇黄色窗格方是发光的眼睛, 黄色"
        "门框方是咧开的嘴巴, 也是从石板小径走进来的大门; 瓜顶四条"
        "橙色瓜棱等边三角骑满盖板拼缝, 绿色瓜蒂瘦高尖从顶心直上; "
        "瓜田东南东北各结一只四棱自锁的小南瓜, 小灰猫蹲在小径旁 —— "
        "秋收之夜, 提着小灯笼来讨糖果吧!"
    ),
    difficulty=3,
    tags=["节日", "万圣节", "南瓜灯", "小屋", "秋收", "进阶"],
    min_pieces=62,
    min_steps=12,
)
