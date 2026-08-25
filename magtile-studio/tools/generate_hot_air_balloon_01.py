#!/usr/bin/env python3
"""生成模型 data/models/hot_air_balloon_01.json (热气球起飞场)。

全库第一只热气球: 清晨的起飞场上, 球皮已经立起来充气 —— 3x3
双层墙环拼出彩虹竖条纹的球囊 (十二道竖条纹上下同色, 像真气球
的瓜瓣), 顶上八片清色方板围成回字环肩口, 中央 1x1 洞口再起
四片瘦高等腰锥顶 (球冠自锁互吸, 尖高 3.94); 吊篮在球旁系留
待挂, 门框方是登篮口, 篮沿骑一片红色燃烧器火苗; 鼓风机窗格
方对着球皮送风, 沙袋压绳, 风向袋看风 —— 全库唯一的"彩虹瓜瓣
双层大环 + 回字肩口瘦高锥球冠"组合。

结构总览 (世界单位: 1.0 = 正方形磁力片边长):
  - 起飞场 (x [0,6], y [0,5]): 方板 10 + 长板 10               20 片
  - 球囊下环 (x [0,3], y [1,4], z 0..1): 墙环 12               12 片
  - 球囊上环 (同 footprint, z 1..2): 墙环 12                   12 片
  - 回字环肩口 (z=2): 方板 x8, 中央留 1x1 洞口                  8 片
  - 球冠 (1x1 洞口四坡瘦高锥, 尖高 3.94): 等腰 x4               4 片
  - 吊篮 (x [4,5], y [1,3], z 0..1): 墙环 5 + 门框 1 + 火苗 1   7 片
  - 鼓风机窗格 1 + 沙袋 x2 + 风向袋 1 + 彩旗 x2                 6 片
  合计 69 片, 13 个教程步骤, 6 种磁力片形状 (全部 CORE-9 之内)。

物理规则要点 (validate 常规 + strict 双档零警告):
  - 球囊墙环墙脚全部踩地面拼缝, 四角竖边互咬, 双层同位叠放;
  - 肩口八片方板边边入扣墙顶并互吸, 围成回字留出 1x1 洞口;
  - 球冠四片等腰底边吸洞口沿边, 四条斜棱两两互吸自锁成环
    (摩天大楼金顶同款);
  - 吊篮墙环独立踩拼缝, 火苗/鼓风机/沙袋等装饰底边整边吸沿口,
    剪断任何一条装饰连接最多失联 1 片 (< 3), R8 通过。

用法: python3 tools/generate_hot_air_balloon_01.py  (在 magtile-studio 目录下运行)
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from magtile_gen import ModelBuilder  # noqa: E402

b = ModelBuilder()

GRASS = "green"      # 草地
PAD = "gray"         # 起飞坪
SNOWY = "clear"      # 帆布垫布
BASKET = "orange"    # 藤条吊篮
FLAME = "red"        # 燃烧器火苗
FAN = "cyan"         # 鼓风机
SANDBAG = "gray"     # 沙袋
SOCK = "yellow"      # 风向袋

# 球囊十二道竖条纹 (南3-东3-北3-西3, 顺时针彩虹)
GORE = {
    "s0": "red", "s1": "orange", "s2": "yellow",
    "e1": "green", "e2": "cyan", "e3": "blue",
    "n2": "purple", "n1": "pink", "n0": "red",
    "w3": "orange", "w2": "yellow", "w1": "green",
}


def wall_ns_t(tid, tile_type, x0, y, z0, color):
    b.add(tid, tile_type, (x0 + 0.5, y, z0 + 0.5), (90, 0, 0), color)


# =================================================================
# 1. 起飞场 (x [0,6], y [0,5]): 草地 + 灰色起飞坪 + 帆布垫布
# =================================================================
b.flat_rect("field_0_0", 0, 0, 0.0, GRASS)
b.flat_rect("field_2_0", 2, 0, 0.0, PAD)
b.flat_rect("field_4_0", 4, 0, 0.0, GRASS)
b.flat_rect("pad_0_1", 0, 1, 0.0, PAD)
b.flat("pad_2_1", 2, 1, 0.0, SNOWY)
b.flat("pad_0_2", 0, 2, 0.0, SNOWY)
b.flat_rect("pad_1_2", 1, 2, 0.0, PAD)
b.flat_rect("pad_0_3", 0, 3, 0.0, PAD)
b.flat("pad_2_3", 2, 3, 0.0, SNOWY)
b.flat("field_3_1", 3, 1, 0.0, GRASS)
b.flat("field_4_1", 4, 1, 0.0, PAD)
b.flat("field_5_1", 5, 1, 0.0, GRASS)
b.flat("field_3_2", 3, 2, 0.0, PAD)
b.flat("field_4_2", 4, 2, 0.0, GRASS)
b.flat("field_5_2", 5, 2, 0.0, PAD)
b.flat_rect("field_3_3", 3, 3, 0.0, GRASS)
b.flat("field_5_3", 5, 3, 0.0, GRASS)
b.flat_rect("field_0_4", 0, 4, 0.0, GRASS)
b.flat_rect("field_2_4", 2, 4, 0.0, GRASS)
b.flat_rect("field_4_4", 4, 4, 0.0, GRASS)

# =================================================================
# 2. 球囊下环 (x [0,3], y [1,4], z 0..1): 十二道竖条纹起步
# =================================================================
b.wall_ns("bag_lo_s0", 0, 1.0, 0, GORE["s0"])
b.wall_ns("bag_lo_s1", 1, 1.0, 0, GORE["s1"])
b.wall_ns("bag_lo_s2", 2, 1.0, 0, GORE["s2"])
b.wall_ew("bag_lo_e1", 3.0, 1, 0, GORE["e1"])
b.wall_ew("bag_lo_e2", 3.0, 2, 0, GORE["e2"])
b.wall_ew("bag_lo_e3", 3.0, 3, 0, GORE["e3"])
b.wall_ns("bag_lo_n2", 2, 4.0, 0, GORE["n2"])
b.wall_ns("bag_lo_n1", 1, 4.0, 0, GORE["n1"])
b.wall_ns("bag_lo_n0", 0, 4.0, 0, GORE["n0"])
b.wall_ew("bag_lo_w3", 0.0, 3, 0, GORE["w3"])
b.wall_ew("bag_lo_w2", 0.0, 2, 0, GORE["w2"])
b.wall_ew("bag_lo_w1", 0.0, 1, 0, GORE["w1"])

# =================================================================
# 3. 球囊上环 (z 1..2): 同位叠放, 条纹上下同色
# =================================================================
b.wall_ns("bag_hi_s0", 0, 1.0, 1, GORE["s0"])
b.wall_ns("bag_hi_s1", 1, 1.0, 1, GORE["s1"])
b.wall_ns("bag_hi_s2", 2, 1.0, 1, GORE["s2"])
b.wall_ew("bag_hi_e1", 3.0, 1, 1, GORE["e1"])
b.wall_ew("bag_hi_e2", 3.0, 2, 1, GORE["e2"])
b.wall_ew("bag_hi_e3", 3.0, 3, 1, GORE["e3"])
b.wall_ns("bag_hi_n2", 2, 4.0, 1, GORE["n2"])
b.wall_ns("bag_hi_n1", 1, 4.0, 1, GORE["n1"])
b.wall_ns("bag_hi_n0", 0, 4.0, 1, GORE["n0"])
b.wall_ew("bag_hi_w3", 0.0, 3, 1, GORE["w3"])
b.wall_ew("bag_hi_w2", 0.0, 2, 1, GORE["w2"])
b.wall_ew("bag_hi_w1", 0.0, 1, 1, GORE["w1"])

# =================================================================
# 4. 环形肩口 (z=2): 八片清色方板围成回字环, 中央留 1x1 洞口
# =================================================================
b.flat("shoulder_sw", 0, 1, 2.0, SNOWY)
b.flat("shoulder_s", 1, 1, 2.0, SNOWY)
b.flat("shoulder_se", 2, 1, 2.0, SNOWY)
b.flat("shoulder_e", 2, 2, 2.0, SNOWY)
b.flat("shoulder_ne", 2, 3, 2.0, SNOWY)
b.flat("shoulder_n", 1, 3, 2.0, SNOWY)
b.flat("shoulder_nw", 0, 3, 2.0, SNOWY)
b.flat("shoulder_w", 0, 2, 2.0, SNOWY)

# =================================================================
# 5. 球冠 (1x1 洞口 [1,2]x[2,3] 四坡瘦高锥, 尖高 3.94)
# =================================================================
crown_ids = b.hat4("crown", 1, 2, 2.0, FLAME)

# =================================================================
# 6. 吊篮 (x [4,5], y [1,3], z 0..1) + 燃烧器火苗
# =================================================================
wall_ns_t("basket_door", "door_frame", 4, 1.0, 0, BASKET)
b.wall_ns("basket_n", 4, 3.0, 0, BASKET)
b.wall_ew("basket_w_s", 4.0, 1, 0, BASKET)
b.wall_ew("basket_w_n", 4.0, 2, 0, BASKET)
b.wall_ew("basket_e_s", 5.0, 1, 0, BASKET)
b.wall_ew("basket_e_n", 5.0, 2, 0, BASKET)
b.crest_ew("burner", 4.0, 2, 1.0, FLAME)

# =================================================================
# 7. 地勤: 鼓风机 + 沙袋 x2 + 风向袋 + 彩旗 x2
# =================================================================
wall_ns_t("fan", "window_square", 3, 1.0, 0, FAN)
b.crest_ns("sandbag_a", 3, 2.0, 0.0, SANDBAG)
b.crest_ew("sandbag_b", 2.0, 0, 0.0, SANDBAG)
b.spire_ew("windsock", 6.0, 0, 0.0, SOCK)
b.crest_ew("flag_e", 6.0, 4, 0.0, "red")
b.crest_ew("flag_w", 0.0, 4, 0.0, FAN)

# =================================================================
# 教程步骤 (13 步)
# =================================================================
b.step(
    "铺起飞场南行: 三条长板边边互吸。",
    ["field_0_0", "field_2_0", "field_4_0"],
    tip="天刚蒙蒙亮, 起飞场的草还挂着露水 —— 嘉年华要开场了。",
)
b.step(
    "铺球囊展开区: 灰色起飞坪和清色帆布垫布拼在西侧。",
    ["pad_0_1", "pad_2_1", "pad_0_2", "pad_1_2", "pad_0_3", "pad_2_3",
     "field_3_1", "field_4_1", "field_5_1"],
    highlight=["field_0_0"],
    tip="球皮就摊在这块垫布上 —— 墙脚要踩住这些拼缝。",
)
b.step(
    "铺完起飞场: 吊篮位与北侧草地补齐。",
    ["field_3_2", "field_4_2", "field_5_2", "field_3_3", "field_5_3",
     "field_0_4", "field_2_4", "field_4_4"],
    highlight=["pad_1_2"],
    tip="东边留给吊篮, 球皮先立起来再挂篮。",
)
b.step(
    "立球囊下环南墙与西墙: 六道彩虹竖条纹起步。",
    ["bag_lo_s0", "bag_lo_s1", "bag_lo_s2",
     "bag_lo_w1", "bag_lo_w2", "bag_lo_w3"],
    highlight=["pad_0_1"],
    tip="鼓风机一响, 球皮从这一角先鼓起来。",
)
b.step(
    "合球囊下环北墙与东墙: 十二片墙环四角竖边互咬闭环。",
    ["bag_lo_n0", "bag_lo_n1", "bag_lo_n2",
     "bag_lo_e1", "bag_lo_e2", "bag_lo_e3"],
    highlight=["bag_lo_s0"],
    tip="3x3 的大环合拢 —— 这是全场最大的球囊。",
)
b.step(
    "叠球囊上环南墙与西墙: 条纹上下同色, 像真气球的瓜瓣。",
    ["bag_hi_s0", "bag_hi_s1", "bag_hi_s2",
     "bag_hi_w1", "bag_hi_w2", "bag_hi_w3"],
    highlight=["bag_lo_s0"],
    tip="墙脚整边压住下环墙顶, 荷载层层直下。",
)
b.step(
    "合球囊上环: 双层彩虹条纹到顶。",
    ["bag_hi_n0", "bag_hi_n1", "bag_hi_n2",
     "bag_hi_e1", "bag_hi_e2", "bag_hi_e3"],
    highlight=["bag_hi_s0"],
    tip="十二道竖条纹一通到顶 —— 越往上球皮越收拢。",
)
b.step(
    "铺环形肩口: 八片清色方板围成回字环, 中央留 1x1 洞口。",
    ["shoulder_sw", "shoulder_s", "shoulder_se", "shoulder_e",
     "shoulder_ne", "shoulder_n", "shoulder_nw", "shoulder_w"],
    highlight=["bag_hi_s0"],
    tip="每片方板边边入扣墙顶, 板板互吸围成回字 —— 球冠就骑洞口。",
)
b.step(
    "收球冠: 四片瘦高等腰吸住洞口沿边, 斜棱两两互吸自锁。",
    crown_ids,
    highlight=["shoulder_s"],
    tip="锥尖高 3.94 —— 摩天大楼金顶的同款自锁环。",
)
b.step(
    "编吊篮: 藤条墙环踩拼缝, 门框方是登篮口。",
    ["basket_door", "basket_n", "basket_w_s", "basket_w_n",
     "basket_e_s", "basket_e_n"],
    highlight=["field_4_1"],
    tip="吊篮在球旁系留待挂 —— 起飞前它们才合体。",
)
b.step(
    "点燃烧器, 架鼓风机: 火苗骑篮沿, 窗格方对着球皮送风。",
    ["burner", "fan"],
    highlight=["basket_door", "bag_lo_s2"],
    tip="呼 —— 热空气一进球皮, 彩虹条纹越鼓越圆。",
)
b.step(
    "压沙袋, 竖风向袋: 地勤就位。",
    ["sandbag_a", "sandbag_b", "windsock"],
    highlight=["bag_lo_s2"],
    tip="沙袋压住系留绳, 风向袋说: 今天是个起飞的好天气!",
)
b.step(
    "挂彩旗: 热气球嘉年华开场!",
    ["flag_e", "flag_w"],
    highlight=["windsock"],
    tip="数到三就松沙袋 —— 三, 二, 一, 飞喽!",
)

b.finalize(
    model_id="hot_air_balloon_01",
    name="热气球起飞场",
    name_en="Hot Air Balloon Field 01",
    description=(
        "只用核心九片型的全库第一只热气球: 清晨起飞场上, 球皮正在"
        "充气 —— 3x3 双层墙环拼出十二道上下同色的彩虹竖条纹瓜瓣, "
        "顶上八片清色方板围成回字环肩口, 中央 1x1 洞口再收四片"
        "瘦高等腰球冠 (斜棱自锁, 尖高 3.94); 橙色藤条吊篮在球旁"
        "系留待挂, 门框方登篮口、红色火苗骑篮沿; 鼓风机窗格送风, "
        "沙袋压绳, 风向袋看风 —— 三, 二, 一, 飞喽!"
    ),
    difficulty=3,
    tags=["热气球", "嘉年华", "飞行器", "起飞场", "清晨", "进阶"],
    min_pieces=69,
    min_steps=13,
)
