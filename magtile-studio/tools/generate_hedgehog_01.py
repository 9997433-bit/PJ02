#!/usr/bin/env python3
"""生成模型 data/models/hedgehog_01.json (森林小刺猬)。

内容批 H 模型 2/4: 全库第一只刺猬。与竹林大熊猫 (矮宽坐姿箱体 +
头部墙环)、月夜猫头鹰 (2x2 图腾柱)、大象馆 (长鼻四柱) 的结构
语言都不同 —— 本作的结构签名是"满背芒刺骑满每一条拼缝":
3x2 伏卧箱体没有第二层、没有头部塔楼, 背甲六片盖板拼出的
全部五条拼缝与东侧沿口, 每一段都骑一片灰色等边三角 —— 拼缝
本身成为造型主角, 九根芒刺根根双边受力; 清色的脸颊墙与骑在
背甲西沿的双耳、蹲在脸前地缝上的小鼻头组成低伏的猬脸,
身旁一只红苹果四坡锥 —— 秋天的刺猬正忙着运粮呢。

结构总览 (世界单位: 1.0 = 正方形磁力片边长, 刺猬面朝西):
  - 森林地面 (x [0,6], y [0,4]): 方板 12 + 长板 6            18 片
  - 伏卧身体墙环 (x [1,4], y [1,3], z 0..1): 方墙 10          10 片
  - 背甲盖板 (z=1): 方板 x6                                    6 片
  - 背刺 x9 (等边骑拼缝/沿口)                                  9 片
  - 双耳 x2 + 小鼻头 x1 (等边骑沿口/地缝)                      3 片
  - 红苹果 x1 (等边四坡锥, 四棱自锁)                            4 片
  - 蘑菇 x2 + 落叶堆 x1 (等边骑沿口)                            3 片
  合计 53 片, 12 个教程步骤, 3 种磁力片形状 (全部 CORE-9 之内)。

物理规则要点 (validate 常规 + strict 双档零警告 + jitter 全绿):
  - 身体墙环墙脚全部踩地面拼缝 (墙脚下全单位方板), 四角竖边
    互咬闭环; 背甲六片盖板边边入扣墙顶并互吸;
  - 九根背刺底边全部同时吸两侧盖板 (拼缝) 或盖板沿边 + 墙顶边
    (沿口), 每根都是双路受力;
  - 苹果四坡锥四棱自锁, 底边整边吸脚下单位方板;
  - 耳/鼻/蘑菇/落叶等装饰剪断任何一条连接最多失联 1 片 (< 3),
    R8 单点失效通过。

用法: python3 tools/generate_hedgehog_01.py  (在 magtile-studio 目录下运行)
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from magtile_gen import ModelBuilder  # noqa: E402

b = ModelBuilder()

MOSS = "green"       # 苔藓地
LEAF = "yellow"      # 落叶地
NEST = "orange"      # 落叶窝 (屋内地板)
FUR = "orange"       # 刺猬毛色
FACE = "clear"       # 脸颊白毛
SPIKE = "gray"       # 背刺
NOSE = "gray"        # 小鼻头
APPLE = "red"        # 红苹果
SHROOM_A = "red"     # 蘑菇
SHROOM_B = "clear"
PILE = "yellow"      # 落叶堆

# =================================================================
# 1. 森林地面 (x [0,6], y [0,4]): 苔藓与落叶拼出的林间空地
# =================================================================
# 南行 (y [0,1]): 苹果底格是单位方板
b.flat("ground_0_0", 0, 0, 0.0, LEAF)
b.flat_rect("ground_1_0", 1, 0, 0.0, MOSS)
b.flat("ground_3_0", 3, 0, 0.0, LEAF)
b.flat_rect("ground_4_0", 4, 0, 0.0, MOSS)
# 中段两行 (y [1,3]): 落叶窝全单位方板, 墙脚踩拼缝
b.flat("ground_0_1", 0, 1, 0.0, MOSS)
b.flat("nest_1_1", 1, 1, 0.0, NEST)
b.flat("nest_2_1", 2, 1, 0.0, NEST)
b.flat("nest_3_1", 3, 1, 0.0, NEST)
b.flat("ground_4_1", 4, 1, 0.0, LEAF)
b.flat("ground_5_1", 5, 1, 0.0, MOSS)
b.flat("ground_0_2", 0, 2, 0.0, LEAF)
b.flat("nest_1_2", 1, 2, 0.0, NEST)
b.flat("nest_2_2", 2, 2, 0.0, NEST)
b.flat("nest_3_2", 3, 2, 0.0, NEST)
b.flat_rect("ground_4_2", 4, 2, 0.0, MOSS)
# 北行 (y [3,4])
b.flat_rect("ground_0_3", 0, 3, 0.0, MOSS)
b.flat_rect("ground_2_3", 2, 3, 0.0, LEAF)
b.flat_rect("ground_4_3", 4, 3, 0.0, MOSS)

# =================================================================
# 2. 伏卧身体墙环 (x [1,4], y [1,3], z 0..1): 清色西墙是脸颊
# =================================================================
b.wall_ns("body_s_w", 1, 1.0, 0, FUR)
b.wall_ns("body_s_m", 2, 1.0, 0, FUR)
b.wall_ns("body_s_e", 3, 1.0, 0, FUR)
b.wall_ns("body_n_w", 1, 3.0, 0, FUR)
b.wall_ns("body_n_m", 2, 3.0, 0, FUR)
b.wall_ns("body_n_e", 3, 3.0, 0, FUR)
b.wall_ew("face_s", 1.0, 1, 0, FACE)     # 脸颊白毛朝西
b.wall_ew("face_n", 1.0, 2, 0, FACE)
b.wall_ew("body_e_s", 4.0, 1, 0, FUR)
b.wall_ew("body_e_n", 4.0, 2, 0, FUR)

# =================================================================
# 3. 背甲盖板 (z=1): 六片橙色方板边边入扣墙顶
# =================================================================
b.flat("back_w_s", 1, 1, 1.0, FUR)
b.flat("back_m_s", 2, 1, 1.0, FUR)
b.flat("back_e_s", 3, 1, 1.0, FUR)
b.flat("back_w_n", 1, 2, 1.0, FUR)
b.flat("back_m_n", 2, 2, 1.0, FUR)
b.flat("back_e_n", 3, 2, 1.0, FUR)

# =================================================================
# 4. 背刺 x9: 骑满背甲的五条拼缝与东侧沿口
# =================================================================
# 中线刺 (骑 y=2 拼缝, 东西向一排 3 根)
b.crest_ns("spike_mid_w", 1, 2.0, 1.0, SPIKE)
b.crest_ns("spike_mid_m", 2, 2.0, 1.0, SPIKE)
b.crest_ns("spike_mid_e", 3, 2.0, 1.0, SPIKE)
# 双缝刺 (骑 x=2 / x=3 拼缝, 南北向各 2 根)
b.crest_ew("spike_w_s", 2.0, 1, 1.0, SPIKE)
b.crest_ew("spike_w_n", 2.0, 2, 1.0, SPIKE)
b.crest_ew("spike_e_s", 3.0, 1, 1.0, SPIKE)
b.crest_ew("spike_e_n", 3.0, 2, 1.0, SPIKE)
# 尾刺 (骑东沿口: 盖板沿边 + 墙顶边双路受力)
b.crest_ew("spike_tail_s", 4.0, 1, 1.0, SPIKE)
b.crest_ew("spike_tail_n", 4.0, 2, 1.0, SPIKE)

# =================================================================
# 5. 双耳 (骑背甲西沿) + 小鼻头 (蹲在脸前地缝上)
# =================================================================
b.crest_ew("ear_s", 1.0, 1, 1.0, FUR)
b.crest_ew("ear_n", 1.0, 2, 1.0, FUR)
b.crest_ns("nose", 0, 2.0, 0.0, NOSE)

# =================================================================
# 6. 红苹果 (四坡锥) + 蘑菇 x2 + 落叶堆
# =================================================================
b.hat4("apple", 3, 0, 0.0, APPLE, shape="equilateral_triangle")
b.crest_ew("shroom_a", 5.0, 1, 0.0, SHROOM_A)   # 骑两块单位方板拼缝
b.crest_ew("shroom_b", 6.0, 1, 0.0, SHROOM_B)   # 骑东沿口
b.crest_ns("leaf_pile", 0, 0.0, 0.0, PILE)

# =================================================================
# 教程步骤 (12 步)
# =================================================================
b.step(
    "铺林地南行: 苔藓长板与落叶方板互吸, 东边留出苹果的底格。",
    ["ground_0_0", "ground_1_0", "ground_3_0", "ground_4_0"],
    tip="秋天的森林里沙沙作响 —— 是谁在落叶堆里忙着运粮?",
)
b.step(
    "铺中段两行: 橙色的是刺猬的落叶窝, 墙脚要踩住这些拼缝。",
    ["ground_0_1", "nest_1_1", "nest_2_1", "nest_3_1", "ground_4_1",
     "ground_5_1", "ground_0_2", "nest_1_2", "nest_2_2", "nest_3_2",
     "ground_4_2"],
    highlight=["ground_1_0"],
    tip="行行等边互吸 —— 窝底铺的全是单位方板。",
)
b.step(
    "铺林地北行: 三条长板收口, 林间空地铺满。",
    ["ground_0_3", "ground_2_3", "ground_4_3"],
    highlight=["nest_1_2"],
    tip="东北角的苔藓地上, 待会儿要冒出小蘑菇。",
)
b.step(
    "立身体南墙与脸颊: 清色的两片是刺猬的白脸颊, 朝西。",
    ["body_s_w", "body_s_m", "body_s_e", "face_s", "face_n"],
    highlight=["nest_1_1"],
    tip="刺猬伏卧的身体是 3x2 的墙环 —— 墙脚踩住拼缝才稳。",
)
b.step(
    "合身体北墙与尾墙: 十片墙环四角竖边互咬闭环。",
    ["body_n_w", "body_n_m", "body_n_e", "body_e_s", "body_e_n"],
    highlight=["body_s_w"],
    tip="墙环合拢 —— 圆滚滚的小身子有了。",
)
b.step(
    "盖背甲: 六片橙色盖板边边入扣墙顶, 板板互吸。",
    ["back_w_s", "back_m_s", "back_e_s", "back_w_n", "back_m_n",
     "back_e_n"],
    highlight=["body_s_m"],
    tip="盖板拼出的每一条缝都记好位置 —— 那是背刺的家。",
)
b.step(
    "立中线刺: 三根灰刺骑住背甲正中的拼缝, 一根挨一根。",
    ["spike_mid_w", "spike_mid_m", "spike_mid_e"],
    highlight=["back_w_s"],
    tip="每根刺的底边同时咬住两侧盖板 —— 双路受力才结实。",
)
b.step(
    "立双缝刺: 四根灰刺骑住南北向的两条拼缝。",
    ["spike_w_s", "spike_w_n", "spike_e_s", "spike_e_n"],
    highlight=["spike_mid_m"],
    tip="拼缝本身就是造型主角 —— 背上的刺越来越密了。",
)
b.step(
    "立尾刺: 两根灰刺骑住东沿口, 同时咬住盖板沿边和墙顶边。",
    ["spike_tail_s", "spike_tail_n"],
    highlight=["body_e_s"],
    tip="沿口的刺也有两条受力路 —— 小刺猬从头武装到尾。",
)
b.step(
    "竖耳朵, 放鼻头: 双耳骑背甲西沿, 小鼻头蹲在脸前的地缝上。",
    ["ear_s", "ear_n", "nose"],
    highlight=["face_s"],
    tip="清色脸颊配小灰鼻 —— 嗅嗅, 苹果在哪儿?",
)
b.step(
    "结红苹果: 四片红色等边三角斜棱互吸, 自锁成锥。",
    ["apple_s", "apple_e", "apple_n", "apple_w"],
    highlight=["ground_3_0"],
    tip="四条底边都要整边吸住脚下的方板 —— 今晚的粮食找到了!",
)
b.step(
    "冒蘑菇丛, 堆落叶: 森林小刺猬完工!",
    ["shroom_a", "shroom_b", "leaf_pile"],
    highlight=["nose", "apple_s"],
    tip="传说刺猬会用背刺扎起苹果搬回家 —— 你信不信?",
)

b.finalize(
    model_id="hedgehog_01",
    name="森林小刺猬",
    name_en="Forest Hedgehog 01",
    description=(
        "只用核心九片型的刺猬首秀: 与坐姿大熊猫的头部墙环和猫头鹰"
        "的图腾柱都不同, 小刺猬是'满背芒刺骑满每一条拼缝' —— 3x2 "
        "伏卧墙环上六片背甲盖板拼出五条拼缝与东侧沿口, 每一段都骑"
        "一片灰色等边三角背刺, 九根芒刺根根双边受力, 拼缝本身成了"
        "造型主角; 清色脸颊朝西, 双耳骑背甲西沿, 小灰鼻蹲在脸前"
        "地缝上; 身旁一只四棱自锁的红苹果, 东北角冒出两朵小蘑菇 —— "
        "秋天的傍晚, 小刺猬正忙着把过冬的粮食运回落叶窝呢!"
    ),
    difficulty=3,
    tags=["自然", "动物世界", "刺猬", "森林", "秋天", "进阶"],
    min_pieces=53,
    min_steps=12,
)
