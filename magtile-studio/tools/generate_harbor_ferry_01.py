#!/usr/bin/env python3
"""生成模型 data/models/harbor_ferry_01.json (港湾小渡轮, D1 入门)。

D1 补员批 3 模型 3/4 (海空交通): 一艘桌面上开航的小渡轮。
结构签名是"平板甲板 + 半舱船楼": 四片长板拼成通长甲板, 船头
两片直角三角合尖破浪, 四片长楣当舷墙, 船尾半段围成带门带窗的
驾驶舱并封顶, 烟囱立在舱顶正脊上 —— 与库内渔船/消防船 (60+ 片
方板堆叠船体) 的结构逻辑完全不同: 这是长板为骨的开敞车渡。

结构总览 (世界单位 1.0 = 正方形磁力片边长, 船头朝西 -x):
  - 甲板 (x [0,4], y [0,2]): 长板 2x2 拼板               4 片
  - 船头 (x < 0): 直角三角 2 片共边合尖                  2 片
  - 舷墙 (y=0 / y=2, z 0..1): 长楣各 2 通长              4 片
  - 舱门墙 (x=2): 门框方 (登舱门) + 窗格方               2 片
  - 船尾墙 (x=4): 窗格方 2 (观景尾窗)                    2 片
  - 舱顶 (z=1): 方板 4 片, 短边吸墙顶、板板互吸          4 片
  - 烟囱: 等边三角 2 片立在舱顶正脊缝上                  2 片
  合计 20 片, 6 个教程步骤, 6 种片形 (全部 CORE-9 之内)。

物理规则要点 (validate 常规 + strict 双档零警告):
  - 舷墙长楣底边 (长 2) 与甲板长板长边等长整边贴合;
    门墙/尾墙墙脚骑甲板拼缝, 竖边与舷墙互咬锁角;
  - 舱顶方板边边有靠: 门墙顶/尾窗顶/舷墙顶/邻板四面吸;
  - 船头三角平铺接地, 直角边吸甲板短边、两片共边互咬;
  - 最高点 1.87 (烟囱尖), 低于高层结构阈值, 无 R8 拓扑告警。

用法: python3 tools/generate_harbor_ferry_01.py  (在 magtile-studio 目录下运行)
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from magtile_gen import ModelBuilder  # noqa: E402

b = ModelBuilder()

DECK = "gray"       # 甲板与船头
BULWARK = "red"     # 舷墙
DOOR = "blue"       # 登舱门
GLASS = "clear"     # 窗格
ROOF = "yellow"     # 舱顶
FUNNEL = "red"      # 烟囱


def wall_ew_t(tid, tile_type, x, y0, z0, color):
    b.add(tid, tile_type, (x, y0 + 0.5, z0 + 0.5), (90, 0, 90), color)


# =================================================================
# 1. 甲板 (x [0,4], y [0,2]): 四片灰色长板拼成通长平板
# =================================================================
b.flat_rect("deck_fw_s", 0, 0, 0.0, DECK)
b.flat_rect("deck_fw_n", 0, 1, 0.0, DECK)
b.flat_rect("deck_aft_s", 2, 0, 0.0, DECK)
b.flat_rect("deck_aft_n", 2, 1, 0.0, DECK)

# =================================================================
# 2. 船头: 两片直角三角平铺, 共边合成破浪尖
# =================================================================
b.place_tri("bow_s", "right_triangle",
            (0.0, 1.0, 0.0), (0.0, 0.0, 0.0), (-1.0, 1.0, 0.0), DECK)
b.place_tri("bow_n", "right_triangle",
            (0.0, 1.0, 0.0), (0.0, 2.0, 0.0), (-1.0, 1.0, 0.0), DECK)

# =================================================================
# 3. 舷墙 (y=0 / y=2): 红色长楣通长, 底边与甲板长边等长贴合
# =================================================================
b.lintel_ns("bulwark_s_fw", 0, 0.0, 0, BULWARK)
b.lintel_ns("bulwark_s_aft", 2, 0.0, 0, BULWARK)
b.lintel_ns("bulwark_n_fw", 0, 2.0, 0, BULWARK)
b.lintel_ns("bulwark_n_aft", 2, 2.0, 0, BULWARK)

# =================================================================
# 4. 舱门墙 (x=2) 与船尾墙 (x=4): 门框登舱, 窗格观景
# =================================================================
wall_ew_t("cabin_door", "door_frame", 2.0, 0, 0, DOOR)
wall_ew_t("cabin_window", "window_square", 2.0, 1, 0, GLASS)
wall_ew_t("stern_window_s", "window_square", 4.0, 0, 0, GLASS)
wall_ew_t("stern_window_n", "window_square", 4.0, 1, 0, GLASS)

# =================================================================
# 5. 舱顶 (z=1): 四片黄色方板, 短边吸墙顶、板板互吸
# =================================================================
b.flat("roof_sw", 2, 0, 1.0, ROOF)
b.flat("roof_nw", 2, 1, 1.0, ROOF)
b.flat("roof_se", 3, 0, 1.0, ROOF)
b.flat("roof_ne", 3, 1, 1.0, ROOF)

# =================================================================
# 6. 烟囱: 两片红色等边三角立在舱顶正脊缝上
# =================================================================
b.crest_ns("funnel_fw", 2, 1.0, 1.0, FUNNEL)
b.crest_ns("funnel_aft", 3, 1.0, 1.0, FUNNEL)

# =================================================================
# 教程步骤 (6 步)
# =================================================================
b.step(
    "拼甲板: 四片灰色长板在桌面拼成 4x2 通长平板, 这就是渡轮的船底。",
    ["deck_fw_s", "deck_fw_n", "deck_aft_s", "deck_aft_n"],
    tip="长边贴长边、短边贴短边, 拼缝对齐甲板才平整。",
)
b.step(
    "合船头: 两片直角三角在西端共边一咬, 破浪尖就冲在最前面。",
    ["bow_s", "bow_n"],
    highlight=["deck_fw_s", "deck_fw_n"],
)
b.step(
    "立舷墙: 四片红色长楣踩住甲板两条长边, 一片底边正好吸满两格。",
    ["bulwark_s_fw", "bulwark_s_aft", "bulwark_n_fw", "bulwark_n_aft"],
    highlight=["deck_fw_s", "deck_aft_n"],
    tip="长楣立起后扶一下两端, 下一步就有横墙来锁角。",
)
b.step(
    "围驾驶舱: 门框方是登舱门, 三片窗格方是舷窗 —— 墙脚骑拼缝, 竖边咬舷墙。",
    ["cabin_door", "cabin_window", "stern_window_s", "stern_window_n"],
    highlight=["bulwark_s_aft", "bulwark_n_aft"],
    tip="前半段甲板故意空着 —— 那是自行车和行李上船的车位。",
)
b.step(
    "盖舱顶: 四片黄色方板短边吸墙顶、彼此长边互吸, 驾驶舱封顶。",
    ["roof_sw", "roof_nw", "roof_se", "roof_ne"],
    highlight=["cabin_door", "stern_window_s"],
)
b.step(
    "立烟囱: 两片红色三角站上舱顶正脊, 鸣笛一声 —— 渡轮开航!",
    ["funnel_fw", "funnel_aft"],
    highlight=["roof_sw", "roof_ne"],
)

b.finalize(
    model_id="harbor_ferry_01",
    name="港湾小渡轮",
    name_en="Harbor Ferry 01",
    description=(
        "D1 入门海空交通: 桌面上开航的小渡轮 —— 四片长板拼成通长甲板, "
        "船头两片直角三角共边合尖破浪, 红色长楣舷墙底边与甲板长边等长"
        "贴合, 船尾半段用门框方登舱门加三面窗格围成驾驶舱, 黄色舱顶"
        "四面有靠, 双烟囱立上正脊。前半段甲板特意留空 —— 那是自行车"
        "上船的车位。20 片全程受压零悬挑, 搭完就能载着积木过河。"
    ),
    difficulty=1,
    tags=["海洋", "渡轮", "港口", "亲子入门"],
    min_pieces=20,
    min_steps=6,
    series="sea_air_transport",
)
