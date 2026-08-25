#!/usr/bin/env python3
"""生成模型 data/models/panda_bamboo_01.json (竹林大熊猫)。

全库第一只大熊猫: 与猫头鹰 (2x2 图腾柱) 和大象 (长鼻四柱) 的
结构语言都不同 —— 本作是"矮宽坐姿箱体动物": 4x2 身体墙环只有
一层, 上面骑一颗 2x2 脑袋, 灰色耳朵/眼罩/手臂/脚掌全部用等边
三角骑沿口表达黑白配色 (灰代黑, 清代白); 身后两丛真正的竹子
用"L 形互咬双层墙"站立 (两片墙竖边直角互咬, 天生抗侧), 竹梢
等边叶片、竹笋瘦高尖 —— 全库唯一的"坐姿熊猫 + L 形竹丛"组合。

结构总览 (世界单位: 1.0 = 正方形磁力片边长, 熊猫面朝南):
  - 竹林地面 (x [0,6], y [0,4]): 方板 6 + 长板 9               15 片
  - 身体 (x [1,5], y [1,3], z 0..1): 墙环 12 + 长板背脊 4      16 片
  - 头部 (x [2,4], y [1,3], z 1..2): 墙环 8 + 长板头顶 2       10 片
  - 耳朵 x2 + 眼罩 x2 + 手臂 x2 + 脚掌 x2 (等边骑沿口)           8 片
  - 竹丛 x2 (L 形互咬双层墙 4 + 竹叶 2)                        12 片
  - 竹笋 x2 (瘦高尖) + 岩石 x1 + 山花 x1                        4 片
  合计 65 片, 13 个教程步骤, 4 种磁力片形状 (全部 CORE-9 之内)。

物理规则要点 (validate 常规 + strict 双档零警告):
  - 身体墙环墙脚全部踩地面拼缝, 四角竖边互咬闭环;
  - 背脊长板四片边边入扣墙顶并互吸, 头部墙环墙脚压背脊拼缝,
    荷载沿墙面层层直下;
  - 竹丛两片墙竖边直角互咬 (L 形), 第二层同位叠放, 互咬棱
    一通到顶 —— 薄墙的抗侧刚度来自直角折边而不是斜撑;
  - 耳/眼/臂/掌等边三角底边整边吸沿口, 剪断任何一条装饰连接
    最多失联 1 片 (< 3), R8 单点失效通过。

用法: python3 tools/generate_panda_bamboo_01.py  (在 magtile-studio 目录下运行)
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from magtile_gen import ModelBuilder  # noqa: E402

b = ModelBuilder()

GROUND_A = "green"    # 竹林草地
GROUND_B = "yellow"   # 落叶泥地
FUR_W = "clear"       # 白毛 (清色)
FUR_B = "gray"        # 黑毛 (灰色)
BAMBOO = "green"      # 竹竿与竹叶
SHOOT = "green"       # 竹笋
ROCK = "gray"         # 岩石
FLOWER = "red"        # 山花

# =================================================================
# 1. 竹林地面 (x [0,6], y [0,4]): 草地与泥地拼出斑驳林下光影
# =================================================================
b.flat_rect("ground_0_0", 0, 0, 0.0, GROUND_A)
b.flat_rect("ground_2_0", 2, 0, 0.0, GROUND_B)
b.flat_rect("ground_4_0", 4, 0, 0.0, GROUND_A)
b.flat("ground_0_1", 0, 1, 0.0, GROUND_B)
b.flat_rect("ground_1_1", 1, 1, 0.0, GROUND_A)
b.flat_rect("ground_3_1", 3, 1, 0.0, GROUND_B)
b.flat("ground_5_1", 5, 1, 0.0, GROUND_A)
b.flat("ground_0_2", 0, 2, 0.0, GROUND_A)
b.flat_rect("ground_1_2", 1, 2, 0.0, GROUND_B)
b.flat_rect("ground_3_2", 3, 2, 0.0, GROUND_A)
b.flat("ground_5_2", 5, 2, 0.0, GROUND_B)
b.flat_rect("ground_0_3", 0, 3, 0.0, GROUND_B)
b.flat_rect("ground_2_3", 2, 3, 0.0, GROUND_A)
b.flat("ground_4_3", 4, 3, 0.0, GROUND_B)
b.flat("ground_5_3", 5, 3, 0.0, GROUND_A)

# =================================================================
# 2. 身体 (x [1,5], y [1,3], z 0..1): 4x2 墙环, 灰色四角是四肢
# =================================================================
b.wall_ns("body_s_0", 1, 1.0, 0, FUR_B)   # 左前肢
b.wall_ns("body_s_1", 2, 1.0, 0, FUR_W)   # 白肚皮
b.wall_ns("body_s_2", 3, 1.0, 0, FUR_W)
b.wall_ns("body_s_3", 4, 1.0, 0, FUR_B)   # 右前肢
b.wall_ns("body_n_0", 1, 3.0, 0, FUR_B)   # 左后肢
b.wall_ns("body_n_1", 2, 3.0, 0, FUR_W)
b.wall_ns("body_n_2", 3, 3.0, 0, FUR_W)
b.wall_ns("body_n_3", 4, 3.0, 0, FUR_B)   # 右后肢
b.wall_ew("body_w_s", 1.0, 1, 0, FUR_B)   # 左肩
b.wall_ew("body_w_n", 1.0, 2, 0, FUR_B)
b.wall_ew("body_e_s", 5.0, 1, 0, FUR_B)   # 右肩
b.wall_ew("body_e_n", 5.0, 2, 0, FUR_B)

# 背脊 (z=1): 四条长板边边入扣墙顶
b.flat_rect("back_1", 1, 1, 1.0, FUR_W, axis="y")
b.flat_rect("back_2", 2, 1, 1.0, FUR_W, axis="y")
b.flat_rect("back_3", 3, 1, 1.0, FUR_W, axis="y")
b.flat_rect("back_4", 4, 1, 1.0, FUR_W, axis="y")

# =================================================================
# 3. 头部 (x [2,4], y [1,3], z 1..2): 2x2 墙环骑在背脊正中
# =================================================================
b.wall_ns("head_s_w", 2, 1.0, 1, FUR_W)   # 脸
b.wall_ns("head_s_e", 3, 1.0, 1, FUR_W)
b.wall_ns("head_n_w", 2, 3.0, 1, FUR_W)
b.wall_ns("head_n_e", 3, 3.0, 1, FUR_W)
b.wall_ew("head_w_s", 2.0, 1, 1, FUR_W)
b.wall_ew("head_w_n", 2.0, 2, 1, FUR_W)
b.wall_ew("head_e_s", 4.0, 1, 1, FUR_W)
b.wall_ew("head_e_n", 4.0, 2, 1, FUR_W)
b.flat_rect("head_top_w", 2, 1, 2.0, FUR_W, axis="y")
b.flat_rect("head_top_e", 3, 1, 2.0, FUR_W, axis="y")

# 耳朵 (骑头顶东西侧沿) + 眼罩 (骑头顶南沿, 立在脸正上方)
b.crest_ew("ear_w", 2.0, 2, 2.0, FUR_B)
b.crest_ew("ear_e", 4.0, 2, 2.0, FUR_B)
b.crest_ns("eye_w", 2, 1.0, 2.0, FUR_B)
b.crest_ns("eye_e", 3, 1.0, 2.0, FUR_B)

# 手臂 (骑背脊南沿, 分列脑袋两侧) + 脚掌 (踩地, 分列身体两侧)
b.crest_ns("arm_w", 1, 1.0, 1.0, FUR_B)
b.crest_ns("arm_e", 4, 1.0, 1.0, FUR_B)
b.crest_ns("paw_w", 0, 1.0, 0.0, FUR_B)
b.crest_ns("paw_e", 5, 1.0, 0.0, FUR_B)

# =================================================================
# 4. 竹丛 x2: L 形互咬双层墙 + 竹叶 (熊猫身后, 东西各一丛)
# =================================================================
b.wall_ns("bamboo_a1", 5, 4.0, 0, BAMBOO)
b.wall_ew("bamboo_a2", 5.0, 3, 0, BAMBOO)
b.wall_ns("bamboo_a3", 5, 4.0, 1, BAMBOO)
b.wall_ew("bamboo_a4", 5.0, 3, 1, BAMBOO)
b.crest_ns("leaf_a1", 5, 4.0, 2.0, BAMBOO)
b.crest_ew("leaf_a2", 5.0, 3, 2.0, BAMBOO)

b.wall_ns("bamboo_b1", 0, 4.0, 0, BAMBOO)
b.wall_ew("bamboo_b2", 0.0, 3, 0, BAMBOO)
b.wall_ns("bamboo_b3", 0, 4.0, 1, BAMBOO)
b.wall_ew("bamboo_b4", 0.0, 3, 1, BAMBOO)
b.crest_ns("leaf_b1", 0, 4.0, 2.0, BAMBOO)
b.crest_ew("leaf_b2", 0.0, 3, 2.0, BAMBOO)

# =================================================================
# 5. 竹笋 x2 + 岩石 + 山花
# =================================================================
b.spire_ns("shoot_a", 0, 2.0, 0.0, SHOOT)
b.spire_ns("shoot_b", 5, 2.0, 0.0, SHOOT)
b.crest_ew("rock", 0.0, 0, 0.0, ROCK)
b.crest_ew("flower", 6.0, 1, 0.0, FLOWER)

# =================================================================
# 教程步骤 (13 步)
# =================================================================
b.step(
    "铺竹林南行: 三条长板边边互吸。",
    ["ground_0_0", "ground_2_0", "ground_4_0"],
    tip="山谷里的竹林刚下过雨 —— 先铺出这片林下空地。",
)
b.step(
    "铺竹林中段两行: 方板与长板拼出斑驳的林下光影。",
    ["ground_0_1", "ground_1_1", "ground_3_1", "ground_5_1",
     "ground_0_2", "ground_1_2", "ground_3_2", "ground_5_2"],
    highlight=["ground_0_0"],
    tip="行行等边互吸 —— 熊猫的墙脚要踩这些拼缝。",
)
b.step(
    "铺竹林北行: 空地铺满, 留出身后的竹丛角。",
    ["ground_0_3", "ground_2_3", "ground_4_3", "ground_5_3"],
    highlight=["ground_1_2"],
    tip="东西两个角落待会儿要长出真正的竹子。",
)
b.step(
    "立身体南墙与左肩: 灰色的是前肢, 清色的是白肚皮。",
    ["body_s_0", "body_s_1", "body_s_2", "body_s_3",
     "body_w_s", "body_w_n"],
    highlight=["ground_1_1"],
    tip="大熊猫坐着的身体是 4x2 的墙环 —— 墙脚踩住拼缝才稳。",
)
b.step(
    "合身体北墙与右肩: 十二片墙环四角竖边互咬闭环。",
    ["body_n_0", "body_n_1", "body_n_2", "body_n_3",
     "body_e_s", "body_e_n"],
    highlight=["body_s_0"],
    tip="墙环合拢 —— 圆滚滚的身体有了。",
)
b.step(
    "铺背脊: 四条白长板边边入扣墙顶, 板板互吸。",
    ["back_1", "back_2", "back_3", "back_4"],
    highlight=["body_s_1"],
    tip="每条长板两端都咬住墙顶 —— 脑袋要骑在这些拼缝上。",
)
b.step(
    "起头部墙环: 2x2 的脑袋骑在背脊正中。",
    ["head_s_w", "head_s_e", "head_n_w", "head_n_e",
     "head_w_s", "head_w_n", "head_e_s", "head_e_n"],
    highlight=["back_2"],
    tip="墙脚压住背脊拼缝, 荷载沿墙面一路传到地面。",
)
b.step(
    "盖头顶, 竖起圆耳朵: 灰色等边三角骑住头顶东西沿。",
    ["head_top_w", "head_top_e", "ear_w", "ear_e"],
    highlight=["head_s_w"],
    tip="两片头顶板互吸封口, 耳朵一左一右 —— 有熊猫样了!",
)
b.step(
    "贴眼罩与手臂: 招牌黑眼圈立在脸正上方, 手臂扶着竹子。",
    ["eye_w", "eye_e", "arm_w", "arm_e"],
    highlight=["head_top_w"],
    tip="大熊猫的眼圈其实是毛色 —— 灰色三角一挂, 表情就有了。",
)
b.step(
    "放脚掌、岩石与山花: 坐姿熊猫完工。",
    ["paw_w", "paw_e", "rock", "flower"],
    highlight=["body_s_0"],
    tip="两只大脚掌摊在身前 —— 这是熊猫最舒服的坐姿。",
)
b.step(
    "种右侧竹丛: 两片绿墙竖边直角互咬, 再同位叠高一层。",
    ["bamboo_a1", "bamboo_a2", "bamboo_a3", "bamboo_a4",
     "leaf_a1", "leaf_a2"],
    highlight=["ground_4_3"],
    tip="L 形折边就是竹竿的靠山 —— 薄墙互咬直角, 天生抗侧。",
)
b.step(
    "种左侧竹丛: 同样的 L 形互咬双层墙, 竹梢挂叶。",
    ["bamboo_b1", "bamboo_b2", "bamboo_b3", "bamboo_b4",
     "leaf_b1", "leaf_b2"],
    highlight=["ground_0_3"],
    tip="两丛竹子一东一西, 正好把熊猫围在中间。",
)
b.step(
    "冒出两根竹笋: 竹林早餐开饭!",
    ["shoot_a", "shoot_b"],
    highlight=["paw_w", "eye_w"],
    tip="瘦高尖是刚冒头的春笋 —— 大熊猫一天要吃几十斤竹子呢。",
)

b.finalize(
    model_id="panda_bamboo_01",
    name="竹林大熊猫",
    name_en="Bamboo Grove Panda 01",
    description=(
        "只用核心九片型的国宝首秀: 与图腾柱猫头鹰和四柱大象都不同, "
        "大熊猫是一只'矮宽坐姿箱体动物' —— 4x2 单层身体墙环上骑一颗 "
        "2x2 脑袋, 灰色四角就是四肢, 耳朵/眼罩/手臂/脚掌全部用等边"
        "三角骑沿口点出黑白配色; 身后两丛竹子用 L 形互咬双层墙站立, "
        "直角折边就是薄墙的抗侧靠山, 竹梢挂叶、脚边冒笋 —— 山谷雨后, "
        "圆滚滚的干饭熊上桌了!"
    ),
    difficulty=3,
    tags=["自然", "动物世界", "大熊猫", "竹林", "国宝", "进阶"],
    min_pieces=65,
    min_steps=13,
)
