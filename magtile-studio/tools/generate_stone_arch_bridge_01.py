#!/usr/bin/env python3
"""生成模型 data/models/stone_arch_bridge_01.json (三孔石拱桥)。

内容批 L 模型 4/4: 桥梁工程主题 D4 —— 补全桥梁四原型最后缺失的
"拱桥": 与 roman_aqueduct_01 (地标, 主角是输水渠) 功能叙事不同,
与 truss_bridge_01 (华伦桁架墙抗剪) 传力逻辑不同; 结构签名是
"三孔石拱桥": 四座共享桥墩撑起三孔拱洞负空间 (T17), 下层梯形
拱肩 (T04) 与上层退台行车道 (T12) 层叠压顶, 两端 30 度引桥
落地 —— 小车可以从桥上开过!

结构总览 (世界单位: 1.0 = 正方形磁力片边长, 桥沿东西向跨河):
  - 河谷 (x [0,11], y=0/2): 草岸 + 蓝色河面                   20 片
  - 石基地梁 (x [0,10]): 方基座 x4 + 连接长板 x3                 7 片
  - 下层桥墩 (z 0..2): 双壁 x4 x2 层 + 底角斜撑 x4              20 片
  - 下层拱肩 (z 0..1): 梯形拱面 x6 (T04)                          6 片
  - 下层桥面 (z=2): 墩顶方板 x4 + 跨洞长板 x3                     7 片
  - 上层矮墩 + 横楣 (z 2..3): 墙 x8 + 长楣 x6                    14 片
  - 上层行车道 (z=3): 方板 x4 + 长板 x3 + 护栏 x4                11 片
  - 引桥接板 x2 + 坡道 x4 + 游鸭 x1 + 岸灯 x2                       9 片
  合计 92 片, 16 个教程步骤, 5 种磁力片形状 (含扩展梯形)。

用法: python3 tools/generate_stone_arch_bridge_01.py  (在 magtile-studio 目录下运行)
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from magtile_gen import ModelBuilder, _sub  # noqa: E402

b = ModelBuilder()

BANK = "green"
RIVER = "blue"
STONE = "gray"
ARCH = "orange"
LINTEL = "yellow"
DECK = "gray"
RAIL = "gray"
DUCK = "yellow"
LAMP = "yellow"

PIERS = (0, 3, 6, 9)
GAPS = (1, 4, 7)
ZT = 0.866025


def arch_spandrel(prefix, x0, y, color):
    """梯形拱肩: 2 格下底在 z=0, 上底内收至 z=ZT (T04 拱券近似)。"""
    b0 = (x0, y, 0.0)
    b1 = (x0 + 2.0, y, 0.0)
    bottom_mid = (x0 + 1.0, y, 0.0)
    top_mid = (x0 + 1.0, y, ZT)
    b.place_edge(prefix, "trapezoid", 0, b0, b1, _sub(top_mid, bottom_mid), color)


def shore_row(prefix, y0):
    """南岸/北岸一行: 墩位方板 + 拱洞下河面长板 + 桥头方板, 互不重叠。"""
    b.flat(f"{prefix}_0", 0, y0, 0.0, BANK)
    b.flat_rect(f"{prefix}_rv1", 1, y0, 0.0, RIVER)
    b.flat(f"{prefix}_3", 3, y0, 0.0, BANK)
    b.flat_rect(f"{prefix}_rv4", 4, y0, 0.0, RIVER)
    b.flat(f"{prefix}_6", 6, y0, 0.0, BANK)
    b.flat_rect(f"{prefix}_rv7", 7, y0, 0.0, RIVER)
    b.flat(f"{prefix}_9", 9, y0, 0.0, BANK)
    b.flat(f"{prefix}_10", 10, y0, 0.0, BANK)
    b.flat(f"{prefix}_11", 11, y0, 0.0, BANK)


# =================================================================
# 1. 河谷 (y=0 南岸, y=2 北岸 —— y=2 与桥基地梁北沿共线互吸)
# =================================================================
shore_row("bk_s", 0)
shore_row("bk_n", 2)

# =================================================================
# 2. 石基地梁
# =================================================================
for x in PIERS:
    b.flat(f"base_{x}", x, 1, 0.0, STONE)
for x in GAPS:
    b.flat_rect(f"base_g_{x}", x, 1, 0.0, STONE)

# =================================================================
# 3. 下层桥墩 (z 0..2)
# =================================================================
for x in PIERS:
    b.wall_ns(f"p1s_{x}", x, 1.0, 0, STONE)
    b.wall_ns(f"p1n_{x}", x, 2.0, 0, STONE)
    b.wall_ns(f"p2s_{x}", x, 1.0, 1, STONE)
    b.wall_ns(f"p2n_{x}", x, 2.0, 1, STONE)
b.brace("but_ws", (0.0, 1.0, 0.0), "-x", STONE)
b.brace("but_wn", (0.0, 2.0, 0.0), "-x", STONE)
b.brace("but_es", (10.0, 1.0, 0.0), "+x", STONE)
b.brace("but_en", (10.0, 2.0, 0.0), "+x", STONE)

# =================================================================
# 4. 下层梯形拱肩 (T04)
# =================================================================
for x in GAPS:
    arch_spandrel(f"sp_s_{x}", x, 1.0, ARCH)
    arch_spandrel(f"sp_n_{x}", x, 2.0, ARCH)

# =================================================================
# 5. 下层桥面 (z=2)
# =================================================================
for x in PIERS:
    b.flat(f"d1_{x}", x, 1, 2.0, STONE)
for x in GAPS:
    b.flat_rect(f"d1g_{x}", x, 1, 2.0, STONE)

# =================================================================
# 6. 上层矮墩 + 横楣
# =================================================================
for x in PIERS:
    b.wall_ns(f"u_s_{x}", x, 1.0, 2, STONE)
    b.wall_ns(f"u_n_{x}", x, 2.0, 2, STONE)
for x in GAPS:
    b.lintel_ns(f"lin_s_{x}", x, 1.0, 2, LINTEL)
    b.lintel_ns(f"lin_n_{x}", x, 2.0, 2, LINTEL)

# =================================================================
# 7. 上层行车道 (z=3) + 护栏
# =================================================================
for x in PIERS:
    b.flat(f"d2_{x}", x, 1, 3.0, DECK)
    b.crest_ns(f"cap_{x}", x, 1.0, 3.0, RAIL)
for x in GAPS:
    b.flat_rect(f"d2g_{x}", x, 1, 3.0, DECK)

# =================================================================
# 8. 桥头牌 + 装饰 (坡道改为 z=1 桥面引桥, 与 truss_bridge 同款受力)
# =================================================================
b.flat("deck_w", 0, 1, 1.0, STONE)
b.flat("deck_e", 9, 1, 1.0, STONE)
b.ramp("ramp_w_s", "-x", 0.0, 1, 1.0, STONE)
b.ramp("ramp_w_n", "-x", 0.0, 2, 1.0, STONE)
b.ramp("ramp_e_s", "+x", 10.0, 1, 1.0, STONE)
b.ramp("ramp_e_n", "+x", 10.0, 2, 1.0, STONE)
b.crest_ew("duck_a", 4.0, 0, 0.0, DUCK)
b.crest_ew("lamp_w", 1.0, 0, 0.0, LAMP)
b.crest_ew("lamp_e", 9.0, 0, 0.0, LAMP)

# =================================================================
# 教程步骤 (16 步)
# =================================================================
b.step(
    "铺南岸: 方板与河面长板交替, 西岸路灯就位。",
    ["bk_s_0", "bk_s_rv1", "bk_s_3", "bk_s_rv4", "bk_s_6",
     "bk_s_rv7", "bk_s_9", "bk_s_10", "bk_s_11", "lamp_w"],
    tip="南岸先铺 —— 拱洞下要留净空给小鸭。",
)
b.step(
    "铺石基地梁: 方基座与长板交替, 把南岸接上桥体。",
    ["base_0", "base_g_1", "base_3", "base_g_4", "base_6", "base_g_7", "base_9"],
    highlight=["bk_s_3"],
    tip="四座方基座间距两格 —— 那就是三孔拱洞的位置。",
)
b.step(
    "铺北岸: 与地梁北沿对缝, 东岸路灯就位。",
    ["bk_n_0", "bk_n_rv1", "bk_n_3", "bk_n_rv4", "bk_n_6",
     "bk_n_rv7", "bk_n_9", "bk_n_10", "bk_n_11", "lamp_e"],
    highlight=["base_0"],
    tip="北岸 y=2 与地梁北沿共线 —— 河谷与桥体连成一体。",
)
b.step(
    "砌下层桥墩南壁: 四座石墩各立南壁两层, 底边吸地梁。",
    [f"p1s_{x}" for x in PIERS] + [f"p2s_{x}" for x in PIERS],
    highlight=["base_0"],
    tip="双壁墩箱形环 —— 拱桥推力沿墙直下。",
)
b.step(
    "砌下层桥墩北壁并铺桥头接板: 桥墩合围, 东西 z=1 接板给引桥留铰链。",
    [f"p1n_{x}" for x in PIERS] + [f"p2n_{x}" for x in PIERS] + ["deck_w", "deck_e"],
    highlight=["p1s_0"],
    tip="左右同步、整边共线 —— 桥墩直直向上; 接板长边压墙顶。",
)
b.step(
    "装底角斜撑: 东西外墩各一对直角三角防倾覆。",
    ["but_ws", "but_wn", "but_es", "but_en"],
    highlight=["p1s_0"],
    tip="分水尖 —— 桥脚更稳。",
)
b.step(
    "砌西孔拱肩: 南/北梯形拱面, 底边 2 格整边吸地梁 (T04 逐拱合龙)。",
    ["sp_s_1", "sp_n_1"],
    highlight=["p1s_0", "p1s_3"],
    tip="拱肩上底内收 —— 半拱中间态最脆弱, 一次一孔!",
)
b.step(
    "砌中孔拱肩: 第二孔南/北梯形拱面。",
    ["sp_s_4", "sp_n_4"],
    highlight=["sp_s_1"],
    tip="三孔连拱共享桥墩 —— 推力互相抵消。",
)
b.step(
    "砌东孔拱肩: 第三孔合龙, 下层拱洞全部贯通 (T17 负空间)。",
    ["sp_s_7", "sp_n_7"],
    highlight=["sp_s_4"],
    tip="拱洞净空两格 —— 小鸭 (高 0.87) 正好游过去。",
)
b.step(
    "铺下层桥面: 墩顶方板 + 跨洞长板, 把三孔拱连成整体。",
    [f"d1_{x}" for x in PIERS] + [f"d1g_{x}" for x in GAPS],
    highlight=["sp_s_4"],
    tip="长板短边整边吸拱肩顶 —— 拱上有了落脚点。",
)
b.step(
    "立上层矮墩: 四座墩再长一层, 跨洞处留空给横楣。",
    [f"u_s_{x}" for x in PIERS] + [f"u_n_{x}" for x in PIERS],
    highlight=["d1_3"],
    tip="T12 层叠退台 —— 上层比下层收分, 准备压行车道。",
)
b.step(
    "架上层横楣: 每孔南北两片黄色长板, 底边吸下层长板、竖边咬墩。",
    [f"lin_s_{x}" for x in GAPS] + [f"lin_n_{x}" for x in GAPS],
    highlight=["u_s_3"],
    tip="一片横楣三边受力 —— 退台层的传力枢纽。",
)
b.step(
    "铺上层行车道: 墩顶方板 + 跨洞长板, 小车可开的路面。",
    [f"d2_{x}" for x in PIERS] + [f"d2g_{x}" for x in GAPS],
    highlight=["lin_s_4"],
    tip="上层桥面压拱 —— 拱券从负空间变成行车道。",
)
b.step(
    "装护栏: 四座桥墩三角底边整边吸行车道沿。",
    ["cap_0", "cap_3", "cap_6", "cap_9"],
    highlight=["d2_3"],
    tip="护栏把行车道边沿锁成一线。",
)
b.step(
    "搭四条引桥: 30 度坡道顶边铰接板、坡尾落南岸。",
    ["ramp_w_s", "ramp_w_n", "ramp_e_s", "ramp_e_n"],
    highlight=["deck_w"],
    tip="引桥从接板起坡 —— 与桁架红桥同款零悬挂做法。",
)
b.step(
    "桥头游鸭入河 —— 三孔石拱桥通车!",
    ["duck_a"],
    highlight=["bk_s_rv4", "sp_s_4"],
    tip="通桥仪式 —— 桥梁四原型最后的'拱桥'归位!",
)

b.finalize(
    model_id="stone_arch_bridge_01",
    name="三孔石拱桥",
    name_en="Stone Arch Bridge 01",
    description=(
        "桥梁工程 D4 拱桥原型: 结构签名是'三孔石拱桥' —— 四座共享"
        "桥墩撑起三孔拱洞负空间 (T17), 下层六片梯形拱肩 (T04) 逐拱"
        "合龙, 上层矮墩与跨洞横楣层叠退台 (T12), 行车道压顶锁拱;"
        "四条 30 度引桥坡尾落岸, 游鸭从拱洞穿过 —— 与罗马水道桥"
        " (主角是渠) 和桁架红桥 (桁架墙抗剪) 功能叙事与传力逻辑均"
        "不同, 补全桥梁四原型最后缺失的'拱桥'!"
    ),
    difficulty=4,
    tags=["桥梁", "拱桥", "工程", "石拱", "挑战", "需要扩展装"],
    min_pieces=92,
    min_steps=15,
    series="bridge_engineering",
)
