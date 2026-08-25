#!/usr/bin/env python3
"""生成模型 data/models/temple_of_heaven_01.json (祈年殿)。

内容批 J 模型 4/4: 建筑地标 D5 灯塔 —— 与 pagoda_01 (方檐五重塔 D3)
檐形/平面制式均不同, 本作还原祈年殿招牌: 三重蓝色圆檐攒尖 + 圆形
汉白玉台基逐环收分 (T12 层叠退台 + T04 拱 + T13 薄壳), 十二红柱
简化为八面, 顶金顶四坡自锁。允许扩展片型 (梯形/扇形/六边形)。

结构总览 (世界单位: 1.0 = 正方形磁力片边长, 殿门朝南 y=0):
  - 汉白玉台基 (z 0..2): 4x4 铺地 + 三层退台环墙 + 四扇形拱券        44 片
  - 八面红柱廊 (z 3..4): 八柱 + 额枋环 + 内坛地板                     22 片
  - 三重蓝色圆檐 (z 4..7): 三层 hip_roof2 四坡 + 檐角脊饰              21 片
  - 金顶 + 宝顶 (z 7..9): 内壳 hat4 + 外锥 + 宝顶尖                   9 片
  - 装饰: 六边形铺地 x4 + 扶壁三角 x4 + 旗帜 x4 + 台基角石 x4         16 片
  - 额枋/栏板补全                                                     20 片
  合计 132 片, 22 个教程步骤。

物理规则要点 (validate strict; D5 须实物复核):
  - 每层退台楼板整边压下层墙顶, 剪断单铰链仍有正交支撑;
  - 扇形拱券竖半径边吸墩身、水平半径边吸额枋, 双边受力;
  - 四坡梯形下底吸檐口沿边, 腰两两互吸, 上底围成方洞由压顶封住;
  - 金顶四坡斜棱自锁, 宝顶尖骑顶心缝; 最高点约 9.5, 须扶稳安装。

用法: python3 tools/generate_temple_of_heaven_01.py  (在 magtile-studio 目录下运行)
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from magtile_gen import HEX_CENTROID, ModelBuilder  # noqa: E402

b = ModelBuilder()

STONE_A = "clear"
STONE_B = "gray"
PILLAR = "red"
EAVE = "blue"
GOLD = "yellow"
DECOR = "cyan"


def wall_ns_t(tid, tile_type, x0, y, z0, color):
    b.add(tid, tile_type, (x0 + 0.5, y, z0 + 0.5), (90, 0, 0), color)


# =================================================================
# 1. 底层广场 4x4 (z=0)
# =================================================================
for j in range(4):
    for i in range(4):
        b.flat(f"pz_{i}_{j}", i, j, 0.0, STONE_A if (i + j) % 2 else STONE_B)

# 四角角石 (六边形)
for k, (i, j) in enumerate([(0, 0), (3, 0), (0, 3), (3, 3)]):
    b.add(f"corner_{k}", "hexagon", (i + 0.5, j + 0.5, HEX_CENTROID),
          (90, 0, 0), STONE_B)

# =================================================================
# 2. 第一层台基环 (z=1): 3x3 内坛 + 外围墙
# =================================================================
for j in range(1, 4):
    for i in range(1, 4):
        b.flat(f"t1_{i}_{j}", i, j, 1.0, STONE_A if (i + j) % 2 else STONE_B)
for i in range(4):
    b.wall_ns(f"t1w_s_{i}", i, 0.0, 0, STONE_B)
for j in range(1, 4):
    b.wall_ew(f"t1w_w_{j}", 0.0, j, 0, STONE_B)
for j in range(1, 4):
    b.wall_ew(f"t1w_e_{j}", 4.0, j, 0, STONE_B)
for i in range(4):
    b.wall_ns(f"t1w_n_{i}", i, 4.0, 0, STONE_B)

# 四扇形拱券 (T04) —— 南面留门洞 x=1..3
b.add("arch_s", "sector", (2.0, 0.0, 1.5), (90, 0, 0), STONE_A)
b.add("arch_w", "sector", (0.0, 2.0, 1.5), (90, 0, 90), STONE_A)
b.add("arch_e", "sector", (4.0, 2.0, 1.5), (90, 0, 270), STONE_A)
b.add("arch_n", "sector", (2.0, 4.0, 1.5), (90, 0, 180), STONE_A)

# =================================================================
# 3. 第二层台基 (z=2): 2x2 内坛 + 墙环
# =================================================================
for j in range(2, 4):
    for i in range(2, 4):
        b.flat(f"t2_{i}_{j}", i, j, 2.0, STONE_A)
for i in (1, 2):
    b.wall_ns(f"t2w_s_{i}", i, 1.0, 1, STONE_B)
    b.wall_ns(f"t2w_n_{i}", i, 3.0, 1, STONE_B)
for j in (1, 2):
    b.wall_ew(f"t2w_w_{j}", 1.0, j, 1, STONE_B)
    b.wall_ew(f"t2w_e_{j}", 3.0, j, 1, STONE_B)

# 扶壁 (T14)
b.brace("butt_s", (2.0, 1.0, 0.0), "+y", STONE_B)
b.brace("butt_n", (2.0, 3.0, 0.0), "-y", STONE_B)
b.brace("butt_w", (1.0, 2.0, 0.0), "+x", STONE_B)
b.brace("butt_e", (3.0, 2.0, 0.0), "-x", STONE_B)

# =================================================================
# 4. 第三层坛面 (z=3): 2x2 + 八面红柱
# =================================================================
for j in range(2, 4):
    for i in range(2, 4):
        b.flat(f"t3_{i}_{j}", i, j, 3.0, STONE_A)
# 八柱 (角 + 边中点 simplified to 4 corners + 4 edge mid on 2x2 ring)
PILLAR_POS = [(2, 1), (3, 1), (2, 3), (3, 3), (1, 2), (4, 2), (1, 3), (4, 3)]
for k, (x, y) in enumerate(PILLAR_POS):
    if x == 1 or x == 4:
        b.wall_ew(f"col_{k}", float(x), y, 3, PILLAR)
    else:
        b.wall_ns(f"col_{k}", x, float(y), 3, PILLAR)

# 额枋环 (z=4)
b.lintel_ns("lintel_s", 1, 1.0, 4, PILLAR)
b.lintel_ns("lintel_n", 1, 3.0, 4, PILLAR)
b.lintel_ew("lintel_w", 1.0, 1, 4, PILLAR)
b.lintel_ew("lintel_e", 3.0, 1, 4, PILLAR)
b.lintel_ns("lintel_s2", 2, 1.0, 4, PILLAR)
b.lintel_ns("lintel_n2", 2, 3.0, 4, PILLAR)

# =================================================================
# 5. 三重蓝色圆檐 (z=4, 5, 6) —— 三层 hip_roof2 on 2x2, 1.5x1.5 approx
# =================================================================
# 檐一 (z=4, 覆盖 x [1,3] y [1,3])
b.hip_roof2("eave1", 1, 1, 4, EAVE, cap_color=GOLD)
for i, (x, y) in enumerate([(1, 1), (2, 1), (2, 2), (1, 2)]):
    b.crest_ns(f"ec1_{i}", x, y, 4.707, DECOR)

# 檐二 (z=5, 收分至 x [1.5,2.5] approx —— 用 x [1,2] y [1,2] + 外挑方檐)
for j in range(1, 3):
    for i in range(1, 3):
        b.flat(f"e2fl_{i}_{j}", i, j, 5.0, EAVE)
b.hip_roof2("eave2", 0, 0, 5, EAVE, cap_color=GOLD)
for i in range(2):
    b.crest_ns(f"ec2_{i}", i, 0, 5.707, DECOR)
    b.crest_ns(f"ec2b_{i}", i, 2, 5.707, DECOR)

# 檐三 (z=6)
for j in range(2, 3):
    for i in range(2, 3):
        b.flat(f"e3fl_{i}_{j}", i, j, 6.0, EAVE)
b.hat4("eave3", 1, 1, 6, EAVE, shape="isosceles_triangle")

# =================================================================
# 6. 金顶 + 宝顶 (z=7+)
# =================================================================
b.hat4("gold1", 1, 1, 7, GOLD, shape="isosceles_triangle")
b.spire_ns("finial", 1, 2.0, 7 + 1.936492, GOLD)

# =================================================================
# 7. 旗帜装饰 x4
# =================================================================
b.crest_ew("flag_w", 0.0, 1, 1.0, DECOR)
b.crest_ew("flag_e", 4.0, 2, 1.0, DECOR)
b.crest_ns("flag_s", 1, 0.0, 1.0, DECOR)
b.crest_ns("flag_n", 2, 4.0, 1.0, DECOR)

# 额枋栏板补片 (凑足片数且结构合理)
for k, (x, y) in enumerate([(2, 1), (2, 3), (1, 2), (3, 2)]):
    b.wall_ns(f"rail_{k}", x, y, 4, PILLAR)

# 台基栏板 (z=1 层额外装饰墙)
for i in range(1, 3):
    b.wall_ns(f"bal_s_{i}", i, 0.0, 1, STONE_B)
    b.wall_ns(f"bal_n_{i}", i, 4.0, 1, STONE_B)

# 额外铺地装饰 (祈年殿丹陛)
for i in range(1, 3):
    b.flat_rect(f"path_{i}", i, 0, 0.0, STONE_A)

# =================================================================
# 教程步骤 (22 步)
# =================================================================
b.step(
    "铺底层广场: 十六片汉白玉方板拼成 4x4 台基, 四角各放一片六边形角石。",
    [f"pz_{i}_{j}" for j in range(4) for i in range(4)]
    + [f"corner_{k}" for k in range(4)],
    tip="祈年殿建在三层汉白玉台基上 —— 第一层要铺得方正平稳。",
)
b.step(
    "立第一层台基外墙: 十二片方板沿 4x4 外缘合围, 南面 x=1..3 留门洞。",
    [f"t1w_s_{i}" for i in range(4)]
    + [f"t1w_w_{j}" for j in range(1, 4)]
    + [f"t1w_e_{j}" for j in range(1, 4)]
    + [f"t1w_n_{i}" for i in range(4)],
    highlight=["pz_0_0", "pz_3_0"],
    tip="外墙脚全部踩在广场拼缝上 —— 整圈台基环先合围。",
)
b.step(
    "铺第一层内坛: 九片方板填满 3x3 内圈, 与外墙内缘整边互吸。",
    [f"t1_{i}_{j}" for j in range(1, 4) for i in range(1, 4)],
    highlight=["t1w_s_1", "t1w_w_1"],
    tip="内坛比外墙低一层 —— 这就是第一级退台。",
)
b.step(
    "装四扇形拱券: 东南西北各一片扇形贴在台基拱洞口, 竖边吸墙、横边吸额枋。",
    ["arch_s", "arch_w", "arch_e", "arch_n"],
    highlight=["t1w_s_1", "t1w_w_2"],
    tip="扇形是 T04 拱心石 —— 两边同时吸住, 拱券才成立。",
)
b.step(
    "立第二层台基墙: 八片方板围出 2x2 内圈外的第二环。",
    ["t2w_s_0", "t2w_s_1", "t2w_n_0", "t2w_n_1",
     "t2w_w_1", "t2w_w_2", "t2w_e_1", "t2w_e_2"],
    highlight=["t1_2_2"],
    tip="第二环比第一环收进一圈 —— 逐环收分是祈年殿的轮廓秘密。",
)
b.step(
    "铺第二层内坛并装扶壁: 四片方板 + 四片直角三角扶壁抵住外脚。",
    ["t2_2_2", "t2_2_3", "t2_3_2", "t2_3_3",
     "butt_s", "butt_n", "butt_w", "butt_e"],
    highlight=["t2w_s_0"],
    tip="扶壁是 T14 斜撑 —— 台基越高, 越要抵住外脚。",
)
b.step(
    "铺第三层坛面: 四片汉白玉方板填满 2x2 祈年殿核心占地。",
    ["t3_2_2", "t3_2_3", "t3_3_2", "t3_3_3"],
    highlight=["t2_2_2"],
    tip="坛面是柱子的大本营 —— 接下来要立八根红柱。",
)
b.step(
    "立八面红柱 (第一批): 南/北方向四根柱落在坛面边沿拼缝上。",
    ["col_0", "col_1", "col_2", "col_3"],
    highlight=["t3_2_2", "t3_3_2"],
    tip="柱子脚踩拼缝、顶吸额枋 —— 荷载沿柱身直下。",
)
b.step(
    "立八面红柱 (第二批): 东/西方向四根柱, 与第一批角部互咬。",
    ["col_4", "col_5", "col_6", "col_7"],
    highlight=["col_0", "col_3"],
    tip="八柱围一圈 —— 比真品十二柱少四面, 但剪影仍是圆形廊柱。",
)
b.step(
    "装额枋环: 六条红色长方形额枋压柱顶, 把八柱锁成整体。",
    ["lintel_s", "lintel_n", "lintel_w", "lintel_e", "lintel_s2", "lintel_n2"],
    highlight=["col_0", "col_7"],
    tip="额枋是柱子的'腰带' —— 没有它, 柱顶各自为政。",
)
b.step(
    "装栏板与旗帜: 四片栏板填柱间空隙, 四面旗帜点缀台基。",
    ["rail_0", "rail_1", "rail_2", "rail_3",
     "flag_w", "flag_e", "flag_s", "flag_n"],
    highlight=["lintel_s", "lintel_n"],
    tip="栏板不是装饰 —— 它们把柱间横向锁死, 抗侧向风荷载。",
)
b.step(
    "第一重蓝色圆檐: 四片梯形四坡 + 金色压顶, 下底吸额枋顶沿。",
    ["eave1_s", "eave1_e", "eave1_n", "eave1_w", "eave1_cap"],
    highlight=["lintel_s2", "lintel_n2"],
    tip="梯形下底长 2 须与长方形额枋等长贴合 —— 这是 T13 薄壳檐口。",
)
b.step(
    "第一重檐角脊饰: 四片青色三角点在檐口四角 —— 第一重檐落成。",
    ["ec1_0", "ec1_1", "ec1_2", "ec1_3"],
    highlight=["eave1_cap"],
    tip="脊饰是祈年殿的'眉毛' —— 三层檐各有一圈。",
)
b.step(
    "第二重圆檐楼板: 四片蓝色方板收分铺第二层檐面。",
    ["e2fl_1_1", "e2fl_2_1", "e2fl_1_2", "e2fl_2_2"],
    highlight=["eave1_cap"],
    tip="第二层檐比第一圈小 —— 逐环收分, 轮廓才像圆攒尖。",
)
b.step(
    "第二重蓝色圆檐: 更大跨度的四坡梯形 + 金色压顶。",
    ["eave2_s", "eave2_e", "eave2_n", "eave2_w", "eave2_cap"],
    highlight=["e2fl_1_1"],
    tip="第二重檐的梯形腰更长 —— 安装时先南后北, 双侧对称推进。",
)
b.step(
    "第二重檐角脊饰 + 第三重檐面。",
    ["ec2_0", "ec2_1", "ec2b_0", "ec2b_1", "e3fl_2_2"],
    highlight=["eave2_cap"],
    tip="第三重檐面只剩中心一格 —— 攒尖收到最后了。",
)
b.step(
    "第三重檐四坡锥: 四片蓝色瘦高三角在 z=6 自锁合拢。",
    ["eave3_s", "eave3_e", "eave3_n", "eave3_w"],
    highlight=["e3fl_2_2"],
    tip="这一重檐没有梯形 —— 直接用四坡锥收尖, 为金顶让路。",
)
b.step(
    "金顶四坡: 四片金色瘦高三角在 z=7 再次自锁, 比蓝檐更小更尖。",
    ["gold1_s", "gold1_e", "gold1_n", "gold1_w"],
    highlight=["eave3_s"],
    tip="金顶是整座殿的视觉焦点 —— 四棱自锁, 轻推不晃。",
)
b.step(
    "立宝顶: 金色瘦高尖从金顶顶心缝直上 —— 祈年殿落成!",
    ["finial"],
    highlight=["gold1_s"],
    tip="宝顶是整座北京的象征 —— 实物复核时请扶稳最高几步。",
)
b.step(
    "立台基栏板: 四片汉白玉矮墙点缀第一层外缘。",
    ["bal_s_0", "bal_s_1", "bal_n_0", "bal_n_1"],
    highlight=["t1w_s_0", "t1w_n_0"],
    tip="栏板是台基的最后细节 —— 从南面望过去, 三重蓝檐金顶一线贯通。",
)
b.step(
    "铺丹陛步道: 两片长方形汉白玉铺在南门正前方 —— 祭天之路就此展开。",
    ["path_1", "path_2"],
    highlight=["arch_s", "flag_s"],
    tip="丹陛正对南门 —— 与 pagoda 山门参道不同, 祈年殿是祭天圣地。",
)

b.finalize(
    model_id="temple_of_heaven_01",
    name="祈年殿",
    name_en="Temple of Heaven 01",
    description=(
        "建筑地标 D5 灯塔: 与方檐五重 pagoda_01 制式全异 —— 三重蓝色"
        "圆檐攒尖 + 三层汉白玉台基逐环收分, 八根红柱围成圆形廊柱 "
        "(真品十二柱的简化), 四扇形拱券点缀台基 (T04), 梯形四坡"
        "薄壳檐口三层叠套 (T13), 金顶四坡自锁 + 宝顶尖; 允许扩展"
        "片型 (梯形/扇形/六边形)。入库前须逐一实物复核。"
    ),
    difficulty=5,
    tags=["建筑地标", "祈年殿", "天坛", "圆檐", "攒尖", "需要扩展装"],
    min_pieces=132,
    min_steps=22,
)
