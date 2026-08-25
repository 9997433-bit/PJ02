#!/usr/bin/env python3
"""生成模型 data/models/drive_in_cinema_01.json (露天汽车影院)。

内容批 B 3/5: 全库第一座露天汽车影院 —— 与视力表箱塔 (双面 E 字
墙) 和各类车库/加油站刻意错开: 主角是一面 4 格宽 2 层高的巨型
银幕箱塔 —— 清色银幕面朝观众, 红色幕布收在两端, 层层箱形闭环
通过 R8 高层检查; 幕前两辆小车头朝银幕停进车位 (双轮 + 车顶板
锁成滚动门式框架, 清色挡风玻璃骑车顶北沿), 车旁青色喇叭桩插在
地缝上; 西南角放映亭二层窗格方放映窗正对银幕, 紫色放映机骑顶;
入场口双柱托横板挂红旗 —— 全库唯一的"银幕 + 车阵 + 放映亭"
夜场场景。

结构总览 (世界单位: 1.0 = 正方形磁力片边长, 银幕在北):
  - 场地 (x [0,6], y [0,4]): 方板 x20 + 车位长板 x2            22 片
  - 银幕箱塔 (x [1,5], y [3,4], z 0..2): 两层箱形墙环 x20 +
    顶面压板 x4                                                 24 片
  - 放映亭 (x [2,3], y [0,1]): 两层墙环 x8 + 压顶 + 放映机     10 片
  - 小车 x2 (x [0,1] / [4,5], y [0,2]): 双轮 + 车顶板 + 挡风    8 片
  - 喇叭桩 x2: 青色等边三角骑地缝                                2 片
  - 入场门 (x [2,4], y [2,3], z=1): 双柱 + 横板 + 门旗          4 片
  合计 70 片, 14 个教程步骤, 7 种磁力片形状 (全部 CORE-9 之内)。

物理规则要点 (validate 常规 + strict 双档零警告):
  - 银幕不是单薄的高墙, 是 4x1 足印的箱塔: 每层南北墙 + 东西
    端墙四角竖边互咬闭环, 上层墙整边骑下层墙顶, 顶面四片压板
    南北两边各压一道墙顶 (双边受力), R8 无桁架高墙检查由层层
    闭环拓扑天然通过;
  - 小车: 双片车轮底座立在车位长板的两条长边上 (一缝双吸),
    车顶板双长边压双轮顶, 轮-顶-轮-车位锁成滚动门式框架;
    挡风玻璃骑车顶北沿短边, 重心正压铰链线力矩为零;
  - 入场门横板两短边各压一根门柱顶 (双端受力零悬挑), 柱-板-
    柱-地面锁成门式刚架, 门旗底边"横板西沿 + 柱顶"一线双吸;
  - 放映亭层层墙环, 放映机骑"压顶北沿 + 塔北墙顶"一线双吸。

用法: python3 tools/generate_drive_in_cinema_01.py  (在 magtile-studio 目录下运行)
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from magtile_gen import ModelBuilder  # noqa: E402

b = ModelBuilder()

LOT = "gray"        # 场地
WALK = "purple"     # 中央步道
BAY = "clear"       # 车位长板
SCREEN = "clear"    # 银幕面 (南)
CURTAIN = "red"     # 幕布端墙
BACK = "gray"       # 银幕背墙
DECK = "gray"       # 银幕顶压板
BOOTH = "gray"      # 放映亭
PROJ_WIN = "cyan"   # 放映窗
BOOTH_DOOR = "orange"
PROJECTOR = "purple"
CAR_A = "red"       # 西车
CAR_B = "yellow"    # 东车
WHEEL = "gray"      # 车轮底座
GLASS = "clear"     # 挡风玻璃
SPEAKER = "cyan"    # 喇叭桩
GATE = "gray"       # 门柱
BEAM = "yellow"     # 门横板
FLAG = "red"        # 门旗


def wall_ns_t(tid, tile_type, x0, y, z0, color):
    b.add(tid, tile_type, (x0 + 0.5, y, z0 + 0.5), (90, 0, 0), color)


# =================================================================
# 1. 场地 (x [0,6], y [0,4]): 车位长板嵌进南两行
# =================================================================
b.flat_rect("bay_a", 0, 0, 0.0, BAY, axis="y")     # 西车位 y [0,2]
b.flat_rect("bay_b", 4, 0, 0.0, BAY, axis="y")     # 东车位 y [0,2]
for y0 in range(2):
    for x0 in (1, 2, 3, 5):
        color = WALK if x0 in (2, 3) else LOT
        b.flat(f"lot_{x0}_{y0}", x0, y0, 0.0, color)
for y0 in range(2, 4):
    for x0 in range(6):
        b.flat(f"lot_{x0}_{y0}", x0, y0, 0.0, LOT)

# =================================================================
# 2. 银幕箱塔 (x [1,5], y [3,4], z 0..2): 两层箱环 + 顶压板
# =================================================================
for lvl in range(2):
    for x0 in range(1, 5):
        b.wall_ns(f"scr{lvl}_s_{x0}", x0, 3.0, lvl, SCREEN)   # 银幕面
    for x0 in range(1, 5):
        b.wall_ns(f"scr{lvl}_n_{x0}", x0, 4.0, lvl, BACK)     # 背墙
    b.wall_ew(f"scr{lvl}_w", 1.0, 3, lvl, CURTAIN)            # 幕布端
    b.wall_ew(f"scr{lvl}_e", 5.0, 3, lvl, CURTAIN)
for x0 in range(1, 5):
    b.flat(f"scr_cap_{x0}", x0, 3, 2.0, DECK)

# =================================================================
# 3. 放映亭 (x [2,3], y [0,1]): 两层墙环 + 压顶 + 放映机
# =================================================================
wall_ns_t("bo0_s", "door_frame", 2, 0.0, 0, BOOTH_DOOR)
b.wall_ns("bo0_n", 2, 1.0, 0, BOOTH)
b.wall_ew("bo0_w", 2.0, 0, 0, BOOTH)
b.wall_ew("bo0_e", 3.0, 0, 0, BOOTH)
b.wall_ns("bo1_s", 2, 0.0, 1, BOOTH)
wall_ns_t("bo1_n", "window_square", 2, 1.0, 1, PROJ_WIN)      # 放映窗朝银幕
b.wall_ew("bo1_w", 2.0, 0, 1, BOOTH)
b.wall_ew("bo1_e", 3.0, 0, 1, BOOTH)
b.flat("bo_cap", 2, 0, 2.0, BOOTH)
b.crest_ns("bo_proj", 2, 1.0, 2.0, PROJECTOR)  # 放映机骑顶一线双吸

# =================================================================
# 4. 小车 x2 (头朝银幕): 双轮立车位长边, 车顶板压双轮顶
# =================================================================
b.add("carA_wh_w", "wheel_base", (0.0, 1.0, 0.5), (90, 0, 90), WHEEL)
b.add("carA_wh_e", "wheel_base", (1.0, 1.0, 0.5), (90, 0, 90), WHEEL)
b.flat_rect("carA_top", 0, 0, 1.0, CAR_A, axis="y")
b.crest_ns("carA_glass", 0, 2.0, 1.0, GLASS)   # 挡风玻璃朝银幕
b.add("carB_wh_w", "wheel_base", (4.0, 1.0, 0.5), (90, 0, 90), WHEEL)
b.add("carB_wh_e", "wheel_base", (5.0, 1.0, 0.5), (90, 0, 90), WHEEL)
b.flat_rect("carB_top", 4, 0, 1.0, CAR_B, axis="y")
b.crest_ns("carB_glass", 4, 2.0, 1.0, GLASS)
b.crest_ns("spk_a", 1, 2.0, 0.0, SPEAKER)      # 喇叭桩骑地缝
b.crest_ns("spk_b", 5, 2.0, 0.0, SPEAKER)

# =================================================================
# 5. 入场门 (x [2,4], y [2,3], z=1): 双柱托横板 + 门旗
#    横跨中央车道, 小车从横板下开进车位
# =================================================================
b.wall_ew("gate_w", 2.0, 2, 0, GATE)
b.wall_ew("gate_e", 4.0, 2, 0, GATE)
b.flat_rect("gate_beam", 2, 2, 1.0, BEAM)      # 横板短边压双柱顶
b.crest_ew("gate_flag", 2.0, 2, 1.0, FLAG)     # 门旗一线双吸

# =================================================================
# 教程步骤 (14 步)
# =================================================================
b.step(
    "铺场地南行: 两块清色车位长板打头, 紫色步道居中。",
    ["bay_a", "lot_1_0", "lot_2_0", "lot_3_0", "bay_b", "lot_5_0"],
    tip="车位长板竖着放 —— 它的两条长边就是待会车轮要踩的缝。",
)
b.step(
    "补场地第二行: 四片方板与车位长板拼齐。",
    ["lot_1_1", "lot_2_1", "lot_3_1", "lot_5_1"],
    highlight=["bay_a"],
    tip="车位长板一块顶两格, 这一行只需要补中间和东边。",
)
b.step(
    "铺场地第三行: 六片灰色方板横贯全场。",
    [f"lot_{x0}_2" for x0 in range(6)],
    highlight=["lot_1_1"],
    tip="这一行的北缝就是银幕的墙脚线, 对齐了再往下贴。",
)
b.step(
    "铺场地第四行: 银幕地基就位。",
    [f"lot_{x0}_3" for x0 in range(6)],
    highlight=["lot_0_2"],
    tip="行行等边互吸, 整片停车场连成一张网。",
)
b.step(
    "立银幕第一层: 四片清色银幕面朝南踩住地缝。",
    [f"scr0_s_{x0}" for x0 in range(1, 5)],
    highlight=["lot_1_3"],
    tip="银幕面要一片挨一片, 竖边互咬连成整面墙。",
)
b.step(
    "补第一层背墙与两端幕布, 箱环闭合。",
    [f"scr0_n_{x0}" for x0 in range(1, 5)] + ["scr0_w", "scr0_e"],
    highlight=["scr0_s_1"],
    tip="银幕不是一面薄墙, 是一座箱塔 —— 四角竖边互咬才站得住。",
)
b.step(
    "银幕第二层: 银幕面整边骑上第一层墙顶。",
    [f"scr1_s_{x0}" for x0 in range(1, 5)],
    highlight=["scr0_s_1"],
    tip="上层每片底边与下层墙顶整边对齐, 银幕越升越高。",
)
b.step(
    "补第二层背墙与幕布端, 上层箱环闭合。",
    [f"scr1_n_{x0}" for x0 in range(1, 5)] + ["scr1_w", "scr1_e"],
    highlight=["scr1_s_1"],
    tip="红色幕布收在银幕两端, 开场前才拉开。",
)
b.step(
    "盖银幕顶: 四片压板南北两边各压一道墙顶。",
    [f"scr_cap_{x0}" for x0 in range(1, 5)],
    highlight=["scr1_n_1"],
    tip="每片压板双边受力, 把两层箱塔锁成一个整体。",
)
b.step(
    "起放映亭一层: 橙色门朝南, 四墙合环。",
    ["bo0_s", "bo0_n", "bo0_w", "bo0_e"],
    highlight=["lot_2_0"],
    tip="放映亭站在场地正南, 和银幕正对着。",
)
b.step(
    "放映亭二层: 窗格方放映窗正对银幕, 压顶后放映机骑顶。",
    ["bo1_s", "bo1_n", "bo1_w", "bo1_e", "bo_cap", "bo_proj"],
    highlight=["bo0_s"],
    tip="放映机底边同时吸压顶北沿和北墙顶 —— 光束正好越过车顶"
        "打在银幕上。",
)
b.step(
    "西车入位: 双轮立上车位长边, 车顶板压双轮顶, 挡风朝银幕。",
    ["carA_wh_w", "carA_wh_e", "carA_top", "carA_glass", "spk_a"],
    highlight=["bay_a"],
    tip="车轮底边整边吸住长板长边, 轮-顶-轮锁成门式框架; "
        "青色喇叭桩就插在车旁地缝上。",
)
b.step(
    "东车入位: 同样的搭法, 黄色小车头朝银幕。",
    ["carB_wh_w", "carB_wh_e", "carB_top", "carB_glass", "spk_b"],
    highlight=["bay_b"],
    tip="两辆车隔着步道并排看电影, 各有各的喇叭桩。",
)
b.step(
    "搭入场门收尾: 双柱横跨中央车道托起横板, 红旗骑上西沿。",
    ["gate_w", "gate_e", "gate_beam", "gate_flag"],
    highlight=["bo_proj"],
    tip="横板两短边各压一根柱顶, 双端受力零悬挑; 小车就是从这"
        "道门下开进车位的 —— 天黑了, 电影开演!",
)

b.finalize(
    model_id="drive_in_cinema_01",
    name="露天汽车影院",
    name_en="Drive-in Cinema 01",
    description=(
        "只用核心九片型的夜场影院: 主角是 4 格宽 2 层高的巨型银幕"
        "箱塔 —— 清色银幕面朝观众, 红色幕布收在两端, 层层箱形闭环"
        "站得笔直; 幕前两辆小车头朝银幕停进车位, 双轮立上车位长板"
        "的两条长边, 车顶板压双轮顶锁成滚动门式框架, 清色挡风玻璃"
        "骑车顶北沿; 车旁青色喇叭桩插在地缝上, 西南角放映亭二层"
        "窗格方放映窗正对银幕、紫色放映机骑顶, 入场口双柱托横板"
        "挂红旗 —— 关掉车灯, 今晚放的是什么片?"
    ),
    difficulty=3,
    tags=["城市", "电影", "职业体验", "汽车", "夜晚"],
    min_pieces=70,
    min_steps=14,
)
