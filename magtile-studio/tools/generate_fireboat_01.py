#!/usr/bin/env python3
"""生成模型 data/models/fireboat_01.json (消防喷水礼船)。

内容批 H 模型 4/4: 全库第一艘消防船, 给海洋航行主题的船队
(货轮/游轮/渔船/帆船/龙舟/潜艇) 补上作业船类别。与游轮
(逐级退台客舱 + 尖船艏) 和货轮 (集装箱堆场) 刻意区分, 本作的
结构签名是"双水炮齐射的进港喷水礼": 中甲板 1x1 水炮塔的顶盖
东西两沿各骑一根清色瘦高尖 —— 那是两道喷向天空的水柱, 直上
4.0 全船制高, 水柱本身就是模型的桅杆天际线; 船尾 1x2 驾驶楼
两扇青色窗格朝船头, 楼顶红色警灯骑北沿; 今天港口有新船首航,
消防船按海事传统喷水列队欢迎 —— 旁边的绿色小迎宾艇也升起了
黄帆。

结构总览 (世界单位: 1.0 = 正方形磁力片边长, 船头朝东):
  - 港口水面 (x [0,7], y [0,4]): 方板 13 + 长板 8            21 片
  - 船体墙环 (x [1,5], y [1,3], z 0..1): 红色方墙 x12        12 片
  - 主甲板 (z=1): 灰色方板 x8                                  8 片
  - 驾驶楼 (x [1,2], y [1,3], z 1..2): 方墙 4 + 窗格 2
    + 长板顶盖 1 + 警灯 1                                      8 片
  - 水炮塔 (x [3,4], y [1,2], z 1..2): 方墙 4 + 顶盖 1
    + 清色水柱瘦高尖 x2                                        7 片
  - 水带卷盘 x1 + 队旗 x1 (骑甲板沿口)                          2 片
  - 迎宾小艇 (x [6,7], y [2,3]): 方墙 4 + 黄帆 1               5 片
  合计 63 片, 12 个教程步骤, 5 种磁力片形状 (全部 CORE-9 之内)。

物理规则要点 (validate 常规 + strict 双档零警告 + jitter 全绿):
  - 船体墙环墙脚全部踩水面拼缝 (墙脚下全单位方板), 四角竖边
    互咬闭环; 主甲板八片全单位方板, 每片至少一条边直压墙顶;
  - 驾驶楼/水炮塔墙脚全部踩甲板拼缝; 驾驶楼长板顶盖南北短边
    分别吸前后墙顶, 双端受力零悬挑 (木偶剧场戏台板同款);
  - 两根水柱瘦高尖分骑水炮塔顶盖东西沿, 底边同时吸顶盖沿边
    与塔墙顶边, 双路受力;
  - 迎宾小艇四墙闭环踩单位水板, 黄帆骑艇墙顶边;
  - 警灯/卷盘/队旗/黄帆剪断任何一条装饰连接最多失联 1 片 (< 3),
    R8 单点失效通过。

用法: python3 tools/generate_fireboat_01.py  (在 magtile-studio 目录下运行)
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from magtile_gen import ModelBuilder  # noqa: E402

b = ModelBuilder()

SEA = "blue"         # 港口水面
FOAM = "cyan"        # 浪花
HULL = "red"         # 消防船船体
DECK = "gray"        # 主甲板
CABIN = "clear"      # 驾驶楼
GLASS = "cyan"       # 驾驶楼舷窗
BEACON = "red"       # 警灯
TOWER = "red"        # 水炮塔
JET = "clear"        # 水柱
HOSE = "yellow"      # 水带卷盘
FLAG = "yellow"      # 队旗
DINGHY = "green"     # 迎宾小艇
SAIL = "yellow"      # 小艇黄帆


def wall_ew_t(tid, tile_type, x, y0, z0, color):
    b.add(tid, tile_type, (x, y0 + 0.5, z0 + 0.5), (90, 0, 90), color)


# =================================================================
# 1. 港口水面 (x [0,7], y [0,4])
# =================================================================
# 南排 (y [0,1]): 三条长板 + 浪花方板
b.flat_rect("sea_0_0", 0, 0, 0.0, SEA)
b.flat_rect("sea_2_0", 2, 0, 0.0, SEA)
b.flat_rect("sea_4_0", 4, 0, 0.0, FOAM)
b.flat("sea_6_0", 6, 0, 0.0, SEA)
# 舯行 (y [1,2]): 船体内水面全单位方板
b.flat("sea_0_1", 0, 1, 0.0, FOAM)
b.flat("bilge_1_1", 1, 1, 0.0, SEA)
b.flat("bilge_2_1", 2, 1, 0.0, SEA)
b.flat("bilge_3_1", 3, 1, 0.0, SEA)
b.flat("bilge_4_1", 4, 1, 0.0, SEA)
b.flat_rect("sea_5_1", 5, 1, 0.0, SEA)
# 舯行 (y [2,3]): 小艇底格也是单位方板
b.flat("sea_0_2", 0, 2, 0.0, SEA)
b.flat("bilge_1_2", 1, 2, 0.0, SEA)
b.flat("bilge_2_2", 2, 2, 0.0, SEA)
b.flat("bilge_3_2", 3, 2, 0.0, SEA)
b.flat("bilge_4_2", 4, 2, 0.0, SEA)
b.flat("sea_5_2", 5, 2, 0.0, FOAM)
b.flat("dinghy_base", 6, 2, 0.0, SEA)
# 北排 (y [3,4])
b.flat_rect("sea_0_3", 0, 3, 0.0, FOAM)
b.flat_rect("sea_2_3", 2, 3, 0.0, SEA)
b.flat_rect("sea_4_3", 4, 3, 0.0, SEA)
b.flat("sea_6_3", 6, 3, 0.0, SEA)

# =================================================================
# 2. 船体墙环 (x [1,5], y [1,3], z 0..1): 红色消防涂装
# =================================================================
b.wall_ns("hull_s_1", 1, 1.0, 0, HULL)
b.wall_ns("hull_s_2", 2, 1.0, 0, HULL)
b.wall_ns("hull_s_3", 3, 1.0, 0, HULL)
b.wall_ns("hull_s_4", 4, 1.0, 0, HULL)
b.wall_ns("hull_n_1", 1, 3.0, 0, HULL)
b.wall_ns("hull_n_2", 2, 3.0, 0, HULL)
b.wall_ns("hull_n_3", 3, 3.0, 0, HULL)
b.wall_ns("hull_n_4", 4, 3.0, 0, HULL)
b.wall_ew("stern_s", 1.0, 1, 0, HULL)
b.wall_ew("stern_n", 1.0, 2, 0, HULL)
b.wall_ew("bow_s", 5.0, 1, 0, HULL)
b.wall_ew("bow_n", 5.0, 2, 0, HULL)

# =================================================================
# 3. 主甲板 (z=1): 八片灰色方板, 每片至少一条边直压墙顶
# =================================================================
b.flat("deck_1_1", 1, 1, 1.0, DECK)
b.flat("deck_2_1", 2, 1, 1.0, DECK)
b.flat("deck_3_1", 3, 1, 1.0, DECK)
b.flat("deck_4_1", 4, 1, 1.0, DECK)
b.flat("deck_1_2", 1, 2, 1.0, DECK)
b.flat("deck_2_2", 2, 2, 1.0, DECK)
b.flat("deck_3_2", 3, 2, 1.0, DECK)
b.flat("deck_4_2", 4, 2, 1.0, DECK)

# =================================================================
# 4. 驾驶楼 (x [1,2], y [1,3], z 1..2): 舷窗朝船头, 警灯骑北沿
# =================================================================
b.wall_ns("cabin_s", 1, 1.0, 1, CABIN)
b.wall_ns("cabin_n", 1, 3.0, 1, CABIN)
b.wall_ew("cabin_w_s", 1.0, 1, 1, CABIN)
b.wall_ew("cabin_w_n", 1.0, 2, 1, CABIN)
wall_ew_t("bridge_win_s", "window_square", 2.0, 1, 1, GLASS)
wall_ew_t("bridge_win_n", "window_square", 2.0, 2, 1, GLASS)
b.flat_rect("cabin_top", 1, 1, 2.0, CABIN, axis="y")
b.crest_ns("beacon", 1, 3.0, 2.0, BEACON)

# =================================================================
# 5. 水炮塔 (x [3,4], y [1,2], z 1..2) + 双水柱
# =================================================================
b.wall_ns("tower_s", 3, 1.0, 1, TOWER)
b.wall_ns("tower_n", 3, 2.0, 1, TOWER)
b.wall_ew("tower_w", 3.0, 1, 1, TOWER)
b.wall_ew("tower_e", 4.0, 1, 1, TOWER)
b.flat("tower_top", 3, 1, 2.0, TOWER)
b.spire_ew("jet_w", 3.0, 1, 2.0, JET)   # 骑顶盖西沿, 水柱直上 4.0
b.spire_ew("jet_e", 4.0, 1, 2.0, JET)   # 骑顶盖东沿

# =================================================================
# 6. 水带卷盘 (骑甲板东沿) + 队旗 (骑甲板南沿, 驾驶楼与水炮塔之间)
# =================================================================
b.crest_ew("hose_reel", 5.0, 1, 1.0, HOSE)
b.spire_ns("flag", 2, 1.0, 1.0, FLAG)

# =================================================================
# 7. 迎宾小艇 (x [6,7], y [2,3], z 0..1) + 黄帆
# =================================================================
b.wall_ns("dinghy_s", 6, 2.0, 0, DINGHY)
b.wall_ns("dinghy_n", 6, 3.0, 0, DINGHY)
b.wall_ew("dinghy_w", 6.0, 2, 0, DINGHY)
b.wall_ew("dinghy_e", 7.0, 2, 0, DINGHY)
b.crest_ns("sail", 6, 2.0, 1.0, SAIL)

# =================================================================
# 教程步骤 (12 步)
# =================================================================
b.step(
    "铺港口南排: 三条长板与一片方板, 青色的是船头掀起的浪花。",
    ["sea_0_0", "sea_2_0", "sea_4_0", "sea_6_0"],
    tip="今天港口有新船首航 —— 消防船要来喷水列队欢迎啦!",
)
b.step(
    "铺舯行水面: 船体里侧的水面全用单位方板, 墙脚要踩这些拼缝。",
    ["sea_0_1", "bilge_1_1", "bilge_2_1", "bilge_3_1", "bilge_4_1",
     "sea_5_1"],
    highlight=["sea_0_0"],
    tip="墙脚下必须是单位方板 —— 墙底边要和方板边等长吸合。",
)
b.step(
    "铺舯行第二行: 东端留出迎宾小艇的底格。",
    ["sea_0_2", "bilge_1_2", "bilge_2_2", "bilge_3_2", "bilge_4_2",
     "sea_5_2", "dinghy_base"],
    highlight=["bilge_1_1"],
    tip="行行等边互吸 —— 迎宾小艇待会儿就停在东边那格。",
)
b.step(
    "铺港口北排收口: 水面铺满。",
    ["sea_0_3", "sea_2_3", "sea_4_3", "sea_6_3"],
    highlight=["bilge_1_2"],
    tip="风平浪静 —— 正是列队喷水礼的好天气。",
)
b.step(
    "立船体南舷与船尾: 红色消防涂装, 墙脚踩住水面拼缝。",
    ["hull_s_1", "hull_s_2", "hull_s_3", "hull_s_4",
     "stern_s", "stern_n"],
    highlight=["bilge_1_1"],
    tip="消防船的船体是 4x2 的墙环 —— 先立南舷和船尾。",
)
b.step(
    "合北舷与船头: 十二片墙环四角竖边互咬闭环。",
    ["hull_n_1", "hull_n_2", "hull_n_3", "hull_n_4",
     "bow_s", "bow_n"],
    highlight=["hull_s_1"],
    tip="墙环合拢 —— 船体这才浮得又正又稳。",
)
b.step(
    "铺主甲板: 八片灰色方板边边入扣墙顶, 板板互吸。",
    ["deck_1_1", "deck_2_1", "deck_3_1", "deck_4_1",
     "deck_1_2", "deck_2_2", "deck_3_2", "deck_4_2"],
    highlight=["hull_s_1"],
    tip="每片甲板至少一条边直压墙顶 —— 上层建筑要踩甲板拼缝。",
)
b.step(
    "起驾驶楼: 两扇青色窗格朝船头, 那是船长的瞭望窗。",
    ["cabin_s", "cabin_n", "cabin_w_s", "cabin_w_n",
     "bridge_win_s", "bridge_win_n"],
    highlight=["deck_1_1"],
    tip="驾驶楼墙脚踩住甲板拼缝, 六片墙互咬闭环。",
)
b.step(
    "盖驾驶楼顶, 亮警灯: 长板顶盖南北短边分别吸前后墙顶。",
    ["cabin_top", "beacon"],
    highlight=["cabin_s"],
    tip="双端受力零悬挑 —— 红色警灯骑上北沿, 出航!",
)
b.step(
    "砌水炮塔并封顶: 中甲板四片红墙围塔, 顶盖四边吸墙顶。",
    ["tower_s", "tower_n", "tower_w", "tower_e", "tower_top"],
    highlight=["deck_3_1"],
    tip="水炮塔是全船的主角 —— 塔脚同样踩住甲板拼缝。",
)
b.step(
    "双水炮齐射: 两根清色瘦高尖分骑塔顶东西沿, 直上全船最高点。",
    ["jet_w", "jet_e", "hose_reel", "flag"],
    highlight=["tower_top"],
    tip="唰 —— 两道水柱喷向天空! 这就是海事传统的进港喷水礼。",
)
b.step(
    "迎宾小艇就位, 升起黄帆: 欢迎新船入港!",
    ["dinghy_s", "dinghy_n", "dinghy_w", "dinghy_e", "sail"],
    highlight=["jet_w", "dinghy_base"],
    tip="小艇也来凑热闹 —— 汽笛齐鸣, 水花如虹, 一路顺风!",
)

b.finalize(
    model_id="fireboat_01",
    name="消防喷水礼船",
    name_en="Fireboat Water Salute 01",
    description=(
        "只用核心九片型的消防船首秀, 给海洋航行船队补上作业船"
        "类别: 与逐级退台的游轮和堆集装箱的货轮都不同, 本作的"
        "结构签名是'双水炮齐射的进港喷水礼' —— 中甲板 1x1 红色"
        "水炮塔顶盖东西两沿各骑一根清色瘦高尖, 两道水柱直上全船"
        "制高, 水柱本身就是模型的桅杆天际线; 船尾驾驶楼两扇青色"
        "窗格朝船头, 长板顶盖双端受力零悬挑, 红色警灯骑北沿; "
        "黄色水带卷盘骑甲板东沿, 队旗骑甲板南沿; 东侧绿色迎宾小艇"
        "升起黄帆 —— 今天有新船首航, 消防船按海事传统喷水列队, "
        "汽笛齐鸣, 水花如虹!"
    ),
    difficulty=3,
    tags=["海洋", "消防船", "港口", "喷水礼", "职业体验", "进阶"],
    min_pieces=63,
    min_steps=12,
)
