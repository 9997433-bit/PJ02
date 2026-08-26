#!/usr/bin/env python3
"""生成模型 data/models/plaza_canopy_01.json (广场遮阳亭)。

内容批 P 模型 1/10 (P1): 扩展主打片型 large_square 引流 D1 —— 重写版。
招牌是"六片大正方形门式刚架": 两片大正方形平拼 4x2 广场地台, 两片
大正方形整片立起当东西山墙, 两片大正方形在 z=2 平拼成顶棚 —— 地台边、
山墙顶、顶棚边全部是 2.0 长的整边等长互吸, 一片顶四片小方板的体量感
就是 large_square 的卖点。棚下沿地台拼缝立一条双面靠背长椅, 棚顶再立
一块长方形招牌; 南侧铺售卖步道, 北侧与东西侧点缀花箱盆栽。

与旧版 (方板 L 形抱角柱 x16 + 柜台 + 三角彩旗) 完全不同的结构逻辑:
柱子消失了 —— 大正方形山墙本身就是承重构件, 连接图是
地台-山墙-顶棚-顶棚-山墙-地台 的门式闭环。

结构总览 (世界单位: 1.0 = 正方形磁力片边长, 亭子朝南):
  - 广场地台: 大正方形 x2 平拼 4x2                              2 片
  - 南侧步道: 方板 x4 (灰黄相间)                                4 片
  - 双面长椅: 靠背方墙 x2 (骑地台拼缝) + 座面方板 x4            6 片
  - 东西山墙: 大正方形 x2 整片立起                              2 片
  - 遮阳顶棚: 大正方形 x2 平拼 4x2 (z=2)                        2 片
  - 顶棚招牌: 长方形 x1 立在顶棚拼缝上 (z 2..3)                 1 片
  - 花箱盆栽: 北侧花圃方板 x2 + 东西花箱方板 x2 + 三角花 x4     8 片
  合计 25 片, 7 个教程步骤, 4 种磁力片形状 (含 large_square x6)。

物理规则要点 (validate 常规 + strict 双档零警告):
  - 门式闭环: 山墙底边与地台外沿边、顶棚边与山墙顶边、两片顶棚
    拼缝均为 2.0 整边等长互吸; 剪断任一条铰链线, 顶棚仍有经由
    另一侧山墙的独立接地路径 (R6/R8 冗余);
  - 座面方板短边与靠背墙顶边等长互吸, 剪断靠背顶铰链后单侧两片
    座面力矩 30g·单位 < 预算 35g·单位 (strict 0.7 系数);
  - 招牌底边与顶棚拼缝两侧各成一条整边连接, 最高点 3.0 触发 R8,
    门式闭环提供环状加固, 无单点失效损失 >= 3 片。

用法: python3 tools/generate_plaza_canopy_01.py  (在 magtile-studio 目录下运行)
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from magtile_gen import ModelBuilder  # noqa: E402

b = ModelBuilder()

PLAZA = "gray"       # 广场地台 (大正方形)
WALK_A = "gray"      # 南侧步道 (灰黄相间)
WALK_B = "yellow"
BENCH_BACK = "blue"  # 长椅靠背
BENCH_SEAT = "yellow"  # 长椅座面
GABLE = "blue"       # 东西山墙 (大正方形)
CANOPY = "green"     # 遮阳顶棚 (大正方形)
SIGN = "red"         # 顶棚招牌
PLANTER = "orange"   # 花箱/花圃
FLOWERS = {"nw": "red", "ne": "purple", "w": "pink", "e": "yellow"}

# ---- 1. 广场地台: 两片大正方形平拼 4x2 -----------------------------
b.add("plaza_w", "large_square", (1.0, 1.0, 0.0), (0, 0, 0), PLAZA)
b.add("plaza_e", "large_square", (3.0, 1.0, 0.0), (0, 0, 0), PLAZA)

# ---- 2. 南侧步道: 四片方板灰黄相间 ---------------------------------
for i in range(4):
    b.flat(f"walk_{i}", i, -1, 0.0, WALK_A if i % 2 == 0 else WALK_B)

# ---- 3. 双面长椅: 靠背骑地台拼缝 (x=2), 座面两侧对称 ---------------
b.wall_ew("bench_back_s", 2.0, 0, 0, BENCH_BACK)
b.wall_ew("bench_back_n", 2.0, 1, 0, BENCH_BACK)
b.flat("seat_sw", 1, 0, 1.0, BENCH_SEAT)
b.flat("seat_nw", 1, 1, 1.0, BENCH_SEAT)
b.flat("seat_se", 2, 0, 1.0, BENCH_SEAT)
b.flat("seat_ne", 2, 1, 1.0, BENCH_SEAT)

# ---- 4. 东西山墙: 大正方形整片立起 (平面 x=0 / x=4) ----------------
b.add("gable_w", "large_square", (0.0, 1.0, 1.0), (90, 0, 90), GABLE)
b.add("gable_e", "large_square", (4.0, 1.0, 1.0), (90, 0, 90), GABLE)

# ---- 5. 遮阳顶棚: 两片大正方形平拼 4x2 (z=2) -----------------------
b.add("canopy_w", "large_square", (1.0, 1.0, 2.0), (0, 0, 0), CANOPY)
b.add("canopy_e", "large_square", (3.0, 1.0, 2.0), (0, 0, 0), CANOPY)

# ---- 6. 花圃与花箱: 北侧两片 + 东西各一片, 沿口三角花 --------------
b.flat("bed_nw", 0, 2, 0.0, PLANTER)
b.flat("bed_ne", 3, 2, 0.0, PLANTER)
b.crest_ns("flower_nw", 0, 3.0, 0.0, FLOWERS["nw"])
b.crest_ns("flower_ne", 3, 3.0, 0.0, FLOWERS["ne"])
b.flat("box_w", -1, 0, 0.0, PLANTER)
b.flat("box_e", 4, 0, 0.0, PLANTER)
b.crest_ew("flower_w", -1.0, 0, 0.0, FLOWERS["w"])
b.crest_ew("flower_e", 5.0, 0, 0.0, FLOWERS["e"])

# ---- 7. 顶棚招牌: 长方形立在顶棚拼缝上 (z 2..3) --------------------
b.lintel_ew("sign", 2.0, 0, 2, SIGN)

# ---- 教程步骤 (7 步) ------------------------------------------------
b.step(
    "铺广场地台: 两片灰色大正方形整边互吸, 平拼出 4x2 的小广场。",
    ["plaza_w", "plaza_e"],
    tip="大正方形边长 2.0, 一片顶四片小方板 —— 拼缝落在 x=2, 长椅就骑在这条缝上。",
)
b.step(
    "铺南侧步道: 四片方板灰黄相间贴住地台南沿。",
    ["walk_0", "walk_1", "walk_2", "walk_3"],
    highlight=["plaza_w", "plaza_e"],
    tip="步道彼此整边互吸连成一排 —— 灰黄相间就是亭子的迎宾地毯。",
)
b.step(
    "立双面长椅: 两片蓝色方墙骑上地台拼缝当靠背, 四片黄色座面"
    "短边吸住靠背顶沿, 两侧对称摊开。",
    ["bench_back_s", "bench_back_n",
     "seat_sw", "seat_nw", "seat_se", "seat_ne"],
    highlight=["plaza_w", "plaza_e"],
    tip="先立靠背再放座面 —— 座面左右两两互吸, 东西两边都能坐。",
)
b.step(
    "立东西山墙: 两片蓝色大正方形整片立起, 底边与地台外沿 2.0 整边"
    "一次吸合。",
    ["gable_w", "gable_e"],
    highlight=["plaza_w", "plaza_e"],
    tip="大正方形立墙不用一片片砌 —— 一片就是一整面山墙, 稳稳站住。",
)
b.step(
    "盖遮阳顶棚: 两片绿色大正方形平放到 z=2, 边与两侧山墙顶沿等长"
    "互吸, 中缝合拢成门式刚架。",
    ["canopy_w", "canopy_e"],
    highlight=["gable_w", "gable_e"],
    tip="先盖西半再盖东半 —— 地台、山墙、顶棚连成闭环, 亭子从此不怕碰。",
)
b.step(
    "布置花箱花圃: 北侧两片花圃、东西各一片花箱, 四株彩色三角花"
    "骑上外沿口。",
    ["bed_nw", "bed_ne", "flower_nw", "flower_ne",
     "box_w", "box_e", "flower_w", "flower_e"],
    highlight=["plaza_w", "plaza_e"],
    tip="花箱贴着地台与山墙脚, 三角花底边与花箱沿口等长互吸。",
)
b.step(
    "挂顶棚招牌: 一片红色长方形立在顶棚拼缝上 —— 广场遮阳亭开张啦!",
    ["sign"],
    highlight=["canopy_w", "canopy_e"],
    tip="招牌底边同时吸住两片顶棚的拼缝边 —— 远远就能看见亭子在哪。",
)

b.finalize(
    model_id="plaza_canopy_01",
    name="广场遮阳亭",
    name_en="Plaza Canopy 01",
    description=(
        "扩展主打片型 large_square 引流 D1: 六片大正方形拼出门式刚架"
        "遮阳亭 —— 两片平拼地台、两片整片立起当东西山墙、两片在 z=2"
        "合拢成顶棚, 全程 2.0 整边等长互吸; 棚下地台拼缝上骑一条双面"
        "靠背长椅, 顶棚拼缝再立一块红色招牌, 南步道、北花圃、东西花箱"
        "点缀四色三角花 —— 一片大正方形顶四片小方板, 体量感立现。"
    ),
    difficulty=1,
    tags=["实用功能", "遮阳亭", "长椅", "大正方形", "入门"],
    min_pieces=25,
    min_steps=7,
    series="practical_utility",
)
