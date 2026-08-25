#!/usr/bin/env python3
"""生成模型 data/models/apiary_01.json (蜜语蜂场)。

田园主题的第一座授粉农场: 主角是三座"双层箱塔 + 四坡箱盖"的
可堆叠蜂箱 —— 与鸡舍 (架高台座 + 人字坡屋) 和羊场 (石圈 + 绵羊)
的结构语言完全不同: 蜂箱是标准化的封闭箱塔, 一层繁殖箱、一层
蜜脾箱, 顶上等边四坡箱盖斜棱互咬自锁; 南侧一整行花田开满粉黄
两色, 三只黄色小蜜蜂骑在花田拼缝上排队回巢; 北侧摇蜜坊门框
朝着蜂箱, 屋脊上一面瘦高蜂场旗 —— 全库唯一的"蜂箱阵 + 采蜜动线"。

结构总览 (世界单位: 1.0 = 正方形磁力片边长, 花田在南, 摇蜜坊在北):
  - 草场 (x [0,6], y [0,4]): 花田/蜂箱/坊舍三行单位方板 x18 +
    中央过道行长板 x3                                            21 片
  - 蜂箱 x3 (1x1, z 0..2 + 箱盖): 每座两层墙环 8 + 等边四坡盖 4  36 片
  - 小蜜蜂 x3: 黄色等边三角骑花田拼缝                             3 片
  - 摇蜜坊 (x [0,2], y [3,4], z 0..1): 六墙 (含门框方) + 长板
    平顶 (短边入扣东西墙顶) + 门楣蜂场旗 (瘦高等腰, 顶尖 3.0)     8 片
  - 围栏 x2 (y=4) + 科普牌窗格方 x1 (y=0)                         3 片
  合计 71 片, 15 个教程步骤, 7 种磁力片形状 (全部 CORE-9 之内)。

物理规则要点 (validate 常规 + strict 双档零警告):
  - 蜂箱两层墙环四角竖边互咬闭环, 上层墙脚整边压下层墙顶;
    箱盖四片等边三角斜棱两两互吸自锁成环, 底边各吸一道墙顶;
    蜂箱北墙脚吸蜂箱行方板的北沿 (过道行为长板, 拼缝取南侧);
  - 摇蜜坊六墙合环, 长板平顶两条短边整边入扣东西墙顶; 蜂场旗
    底边整边吸南墙墙顶 (门楣沿口);
  - 蜜蜂/围栏/科普牌底边整边吸草场拼缝, 剪断任何一条装饰连接
    最多失联 1 片 (< 3), R8 单点失效通过;
  - 拼缝纪律: 立墙墙脚线处处有等长拼缝可吸 (单位方板行供缝),
    行行等边互吸全场连通。

用法: python3 tools/generate_apiary_01.py  (在 magtile-studio 目录下运行)
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from magtile_gen import ModelBuilder  # noqa: E402

b = ModelBuilder()

FLOWER_A = "pink"     # 花田
FLOWER_B = "yellow"
GRASS = "green"       # 草场
BEE = "yellow"        # 小蜜蜂
HIVE_LOW = "orange"   # 蜂箱下层 (繁殖箱)
HIVE_UP = "yellow"    # 蜂箱上层 (蜜脾箱)
HIVE_CAP = "clear"    # 箱盖
HOUSE = "clear"       # 摇蜜坊墙
DOOR = "orange"       # 摇蜜坊门
ROOF = "red"          # 摇蜜坊平顶
FLAG = "red"          # 屋脊蜂场旗
FENCE = "clear"       # 围栏
SIGN = "cyan"         # 科普牌


def wall_ns_t(tid, tile_type, x0, y, z0, color):
    b.add(tid, tile_type, (x0 + 0.5, y, z0 + 0.5), (90, 0, 0), color)


# =================================================================
# 1. 草场四行 (y [0,4]): 花田/蜂箱/坊舍行为单位方板 (供墙脚拼缝),
#    中央过道行为三条长板
# =================================================================
for x0 in range(6):
    color = FLOWER_A if x0 % 2 == 0 else FLOWER_B
    b.flat(f"field_{x0}_0", x0, 0, 0.0, color)            # 花田行
for x0 in range(6):
    b.flat(f"field_{x0}_1", x0, 1, 0.0, GRASS)            # 蜂箱行
b.flat_rect("aisle_0", 0, 2, 0.0, GRASS)                  # 过道行 (长板)
b.flat_rect("aisle_2", 2, 2, 0.0, GRASS)
b.flat_rect("aisle_4", 4, 2, 0.0, GRASS)
for x0 in range(6):
    b.flat(f"field_{x0}_3", x0, 3, 0.0, GRASS)            # 坊舍行

# =================================================================
# 2. 蜂箱 x3 (x [1,2] / [3,4] / [5,6], y [1,2]):
#    两层墙环 + 等边四坡箱盖
# =================================================================
HIVE_CAPS = {}
for i, x0 in enumerate((1, 3, 5), start=1):
    for z0, color, tag in ((0, HIVE_LOW, "low"), (1, HIVE_UP, "up")):
        b.wall_ns(f"hive{i}_{tag}_s", x0, 1.0, z0, color)
        b.wall_ns(f"hive{i}_{tag}_n", x0, 2.0, z0, color)
        b.wall_ew(f"hive{i}_{tag}_w", float(x0), 1, z0, color)
        b.wall_ew(f"hive{i}_{tag}_e", float(x0 + 1), 1, z0, color)
    HIVE_CAPS[i] = b.hat4(f"hive{i}_cap", x0, 1, 2.0, HIVE_CAP,
                          shape="equilateral_triangle")   # 盖尖 2.71

# =================================================================
# 3. 小蜜蜂 x3: 骑在花田与草场之间的拼缝上 (y=1)
# =================================================================
b.crest_ns("bee_a", 0, 1.0, 0.0, BEE)
b.crest_ns("bee_b", 2, 1.0, 0.0, BEE)
b.crest_ns("bee_c", 4, 1.0, 0.0, BEE)

# =================================================================
# 4. 摇蜜坊 (x [0,2], y [3,4], z 0..1): 六墙 + 双板平顶 + 屋脊旗
# =================================================================
b.wall_ns("house_s_w", 0, 3.0, 0, HOUSE)
wall_ns_t("house_door", "door_frame", 1, 3.0, 0, DOOR)    # 门朝蜂箱
b.wall_ns("house_n_w", 0, 4.0, 0, HOUSE)
b.wall_ns("house_n_e", 1, 4.0, 0, HOUSE)
b.wall_ew("house_w", 0.0, 3, 0, HOUSE)
b.wall_ew("house_e", 2.0, 3, 0, HOUSE)
b.flat_rect("house_roof", 0, 3, 1.0, ROOF)                # 短边入扣东西墙顶
b.spire_ns("house_flag", 0, 3.0, 1.0, FLAG)               # 门楣旗, 顶尖 3.0

# =================================================================
# 5. 围栏 x2 (y=4) + 科普牌 (y=0 花田南沿)
# =================================================================
b.wall_ns("fence_3", 3, 4.0, 0, FENCE)
b.wall_ns("fence_5", 5, 4.0, 0, FENCE)
wall_ns_t("sign", "window_square", 4, 0.0, 0, SIGN)       # 科普牌

# =================================================================
# 教程步骤 (15 步)
# =================================================================
b.step(
    "铺南侧花田: 粉黄相间六片方板, 边边互吸连成一行。",
    [f"field_{x0}_0" for x0 in range(6)],
    tip="蜜蜂的一天从花田开始 —— 花越多, 蜂蜜越香。",
)
b.step(
    "铺蜂箱行草场: 绿色方板六片, 与花田行行互吸。",
    [f"field_{x0}_1" for x0 in range(6)],
    highlight=["field_0_0"],
    tip="草场连成一整张网, 后面的蜂箱都要踩它的拼缝。",
)
b.step(
    "铺中央过道: 三条绿色长板首尾互吸, 留给养蜂人巡场。",
    ["aisle_0", "aisle_2", "aisle_4"],
    highlight=["field_0_1"],
    tip="养蜂人每天沿着长板过道巡视, 看看哪箱蜜先满。",
)
b.step(
    "铺北侧坊舍行草场: 摇蜜坊和围栏都盖在这一行上。",
    [f"field_{x0}_3" for x0 in range(6)],
    highlight=["aisle_0"],
    tip="四行方板铺完, 蜂场的地盘就圈好了。",
)
b.step(
    "立第一座蜂箱的繁殖箱: 四面橙色墙合环, 四角竖边互咬。",
    ["hive1_low_s", "hive1_low_n", "hive1_low_w", "hive1_low_e"],
    highlight=["field_1_1"],
    tip="墙脚要踩住草场拼缝 —— 繁殖箱里住着蜂后和小幼虫。",
)
b.step(
    "叠上第一座蜂箱的蜜脾箱: 黄色墙环整边压住下层墙顶。",
    ["hive1_up_s", "hive1_up_n", "hive1_up_w", "hive1_up_e"],
    highlight=["hive1_low_s"],
    tip="上箱装蜜, 下箱育儿 —— 真蜂场就是这样一层层叠起来的。",
)
b.step(
    "盖第一座蜂箱的箱盖: 四片等边三角斜棱互咬, 收成小尖顶。",
    HIVE_CAPS[1],
    highlight=["hive1_up_s"],
    tip="四条斜棱两两互吸自锁成环 —— 盖尖 2.71, 雨水顺坡流走。",
)
b.step(
    "立第二座蜂箱的两层箱塔: 先橙色繁殖箱, 再黄色蜜脾箱。",
    ["hive2_low_s", "hive2_low_n", "hive2_low_w", "hive2_low_e",
     "hive2_up_s", "hive2_up_n", "hive2_up_w", "hive2_up_e"],
    highlight=["hive1_cap_s"],
    tip="这次一口气叠两层 —— 记得每层四角都要咬紧再往上叠。",
)
b.step(
    "盖第二座蜂箱的箱盖: 手法和第一座一样。",
    HIVE_CAPS[2],
    highlight=["hive2_up_s"],
    tip="三座蜂箱排成一列, 间隔一格 —— 蜜蜂认得自家门口。",
)
b.step(
    "立第三座蜂箱的两层箱塔: 蜂场东端最后一座。",
    ["hive3_low_s", "hive3_low_n", "hive3_low_w", "hive3_low_e",
     "hive3_up_s", "hive3_up_n", "hive3_up_w", "hive3_up_e"],
    highlight=["hive2_cap_s"],
    tip="东端的墙脚踩在草场最外沿的拼缝上, 一样咬得牢。",
)
b.step(
    "盖第三座蜂箱的箱盖: 蜂箱阵完工!",
    HIVE_CAPS[3],
    highlight=["hive3_up_s"],
    tip="三顶小尖盖一字排开 —— 远看像三座小金字塔。",
)
b.step(
    "三只小蜜蜂骑上花田拼缝: 排队飞回自家蜂箱。",
    ["bee_a", "bee_b", "bee_c"],
    highlight=["field_0_0", "hive1_low_s"],
    tip="蜜蜂底边整边吸住拼缝 —— 嗡嗡嗡, 满载花蜜回巢喽!",
)
b.step(
    "搭摇蜜坊: 六面墙合环, 门框方正对蜂箱阵。",
    ["house_s_w", "house_door", "house_n_w", "house_n_e",
     "house_w", "house_e"],
    highlight=["field_0_3"],
    tip="养蜂人抱着蜜脾从这扇门进坊, 摇蜜机就在屋里。",
)
b.step(
    "盖摇蜜坊长板平顶, 门楣上立起蜂场旗: 瘦高三角直指天空。",
    ["house_roof", "house_flag"],
    highlight=["house_s_w"],
    tip="长板两条短边整边入扣东西墙顶, 旗子底边吸住门楣沿口 —— 顶尖 3.0!",
)
b.step(
    "装北侧围栏和花田科普牌: 蜂场开张!",
    ["fence_3", "fence_5", "sign"],
    highlight=["house_flag", "bee_a"],
    tip="牌上写着: 轻轻走慢慢看, 别挡住蜜蜂的回家路。",
)

b.finalize(
    model_id="apiary_01",
    name="蜜语蜂场",
    name_en="Honeybee Apiary 01",
    description=(
        "只用核心九片型的授粉农场: 与鸡舍的架高台座和羊场的石圈"
        "都不同, 主角是三座标准化蜂箱 —— 每座都是'双层箱塔 + "
        "四坡箱盖'的可堆叠单元: 橙色繁殖箱住蜂后, 黄色蜜脾箱装"
        "蜂蜜, 等边四坡箱盖斜棱互咬自锁; 南侧粉黄花田开成一行, "
        "三只黄色小蜜蜂骑着拼缝排队回巢; 北侧摇蜜坊门框朝箱、"
        "门楣蜂场旗直指天空 —— 嘘, 听, 整座蜂场都在嗡嗡唱歌!"
    ),
    difficulty=3,
    tags=["田园", "农场", "蜜蜂", "蜂箱", "自然", "进阶"],
    min_pieces=71,
    min_steps=15,
)
