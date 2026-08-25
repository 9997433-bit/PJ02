#!/usr/bin/env python3
"""生成模型 data/models/snowplow_01.json (铲雪车)。

城市守护者主题新作, 全库第一台除雪作业车 —— 与救护车 (高箱方舱)、
消防车/工程车都不同, 本作的招牌是"倾斜的铲雪板": 一片长方形
30 度斜坡从底盘甲板前缘直插路面 (滚珠塔坡道的同款几何, 顶边
整边吸甲板前缘、坡尾平贴雪面零悬挑), 车身是"前驾驶室 + 后敞口
融雪剂料斗"的一体箱环; 车后的车道已铲净露出灰色路面, 车前的
车道还盖着厚雪, 路边雪堤上四堆积雪排队等着被推走 —— 雪人和
两棵小雪松在人行道上看铲雪车干活。

结构总览 (世界单位: 1.0 = 正方形磁力片边长, 车头朝东):
  - 街道 8x4: 雪堤行 x5 + 车道行 x5 + 北沿行 x5 + 人行道 x8   23 片
  - 铲雪车: 车轮底座 x2 + 底盘甲板 x1 + 箱环墙 x6 (料斗敞口
    + 车窗挡风) + 驾驶室顶 x1 + 黄警灯 x1 + 铲雪板 x1         12 片
  - 积雪堆 x4: 透明等边三角骑拼缝                              4 片
  - 雪人 (方身 + 三角头) x2 片 + 雪松 x2 + 慢行牌 x1           5 片
  合计 44 片, 10 个教程步骤, 6 种磁力片形状 (全部 CORE-9 之内)。

物理规则要点 (validate 常规 + strict 双档零警告):
  - 车轮底座底边 (长 2) 整边吸车道长板拼缝, 甲板长边整边压
    双轮顶 —— 轮组+甲板锁成门式框架 (救护车同款底盘);
  - 箱环圈层砌法: 料斗尾壁与挡风踩甲板短边, 侧壁竖边吸进
    前后壁拐角; 驾驶室顶四边压墙顶, 料斗保持敞口;
  - 铲雪板 30 度斜坡顶边整边吸甲板东缘 (与挡风共线不相交),
    坡尾自然落地 —— 悬空段零悬挑, 无悬臂力矩;
  - 积雪堆/雪人/雪松/慢行牌底边整边吸拼缝, 各自独立吸附,
    剪断任何一条装饰连接最多失联 2 片 (< 3), R8 通过。

用法: python3 tools/generate_snowplow_01.py  (在 magtile-studio 目录下运行)
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from magtile_gen import ModelBuilder  # noqa: E402

b = ModelBuilder()

SNOW = "clear"      # 积雪
ROAD = "gray"       # 铲净的路面
WALK = "cyan"       # 人行道
BODY = "orange"     # 车身
DECK = "gray"       # 底盘与车顶
WHEEL = "gray"      # 车轮
GLASS = "cyan"      # 挡风车窗
BLADE = "red"       # 铲雪板
BEACON = "yellow"   # 警灯
TREE = "green"      # 雪松
SIGN = "orange"     # 慢行牌


def wall_ns_t(tid, tile_type, x0, y, z0, color):
    b.add(tid, tile_type, (x0 + 0.5, y, z0 + 0.5), (90, 0, 0), color)


def wall_ew_t(tid, tile_type, x, y0, z0, color):
    b.add(tid, tile_type, (x, y0 + 0.5, z0 + 0.5), (90, 0, 90), color)


# =================================================================
# 1. 街道 8x4: 雪堤行 + 车道行 (车后已铲净, 车前still盖雪) + 北沿行
#    + 人行道; 轮缝长板对齐 y=1 与 y=2 线
# =================================================================
b.flat("bank_0", 0, 0, 0.0, SNOW)                     # 雪堤行 y [0,1]
b.flat_rect("bank_a", 1, 0, 0.0, SNOW)                # [1,3] 轮缝板
b.flat_rect("bank_b", 3, 0, 0.0, SNOW)
b.flat_rect("bank_c", 5, 0, 0.0, SNOW)
b.flat("bank_7", 7, 0, 0.0, SNOW)

b.flat("lane_0", 0, 1, 0.0, ROAD)                     # 车道行 y [1,2]
b.flat_rect("lane_a", 1, 1, 0.0, ROAD)                # [1,3] 车底板
b.flat("lane_3", 3, 1, 0.0, ROAD)
b.flat_rect("lane_b", 4, 1, 0.0, SNOW)                # 车前未铲的厚雪
b.flat_rect("lane_c", 6, 1, 0.0, SNOW)

b.flat("edge_0", 0, 2, 0.0, ROAD)                     # 北沿行 y [2,3]
b.flat_rect("edge_a", 1, 2, 0.0, ROAD)                # [1,3] 轮缝板
b.flat("edge_3", 3, 2, 0.0, ROAD)
b.flat_rect("edge_b", 4, 2, 0.0, SNOW)
b.flat_rect("edge_c", 6, 2, 0.0, SNOW)

for x in range(8):
    b.flat(f"walk_{x}", x, 3, 0.0, WALK)              # 人行道 y [3,4]

# =================================================================
# 2. 铲雪车底盘: 双车轮底座 + 甲板 (救护车同款门式框架)
# =================================================================
b.add("wheel_s", "wheel_base", (2.0, 1.0, 0.5), (90, 0, 0), WHEEL)
b.add("wheel_n", "wheel_base", (2.0, 2.0, 0.5), (90, 0, 0), WHEEL)
b.flat_rect("plow_deck", 1, 1, 1.0, DECK)             # 甲板 [1,3]x[1,2]

# =================================================================
# 3. 车身箱环 (z 1..2): 料斗尾壁 + 车窗挡风 + 四片侧壁
#    东半格驾驶室盖顶, 西半格融雪剂料斗保持敞口
# =================================================================
b.wall_ew("hopper_rear", 1.0, 1, 1, BODY)             # 料斗尾壁 (西)
wall_ew_t("cab_wind", "window_square", 3.0, 1, 1, GLASS)  # 挡风 (东)
b.wall_ns("side_s1", 1, 1.0, 1, BODY)                 # 南侧壁
b.wall_ns("side_s2", 2, 1.0, 1, BODY)
b.wall_ns("side_n1", 1, 2.0, 1, BODY)                 # 北侧壁
b.wall_ns("side_n2", 2, 2.0, 1, BODY)
b.flat("cab_roof", 2, 1, 2.0, DECK)                   # 驾驶室顶 [2,3]x[1,2]
b.crest_ew("beacon", 3.0, 1, 2.0, BEACON)             # 黄警灯 (车顶前沿)
b.ramp("blade", "+x", 3, 1, 1.0, BLADE)               # 铲雪板: 顶边吸甲板东缘

# =================================================================
# 4. 积雪堆 x4 (骑拼缝) + 雪人 + 雪松 x2 + 慢行牌
# =================================================================
b.crest_ew("pile_lane", 6.0, 1, 0.0, SNOW)            # 车道上的待铲雪堆
b.crest_ew("pile_a", 1.0, 0, 0.0, SNOW)               # 雪堤积雪
b.crest_ew("pile_b", 3.0, 0, 0.0, SNOW)
b.crest_ew("pile_c", 5.0, 0, 0.0, SNOW)
b.wall_ns("snowman_body", 7, 4.0, 0, SNOW)            # 雪人方身
b.crest_ns("snowman_head", 7, 4.0, 1.0, SNOW)         # 雪人三角头
b.spire_ns("pine_a", 0, 4.0, 0.0, TREE)               # 雪松
b.spire_ns("pine_b", 2, 4.0, 0.0, TREE)
wall_ns_t("slow_sign", "window_square", 5, 3.0, 0, SIGN)  # 慢行牌朝车道

# =================================================================
# 教程步骤 (10 步)
# =================================================================
b.step(
    "铺雪堤行: 长板拼缝对齐 y=1 线 —— 那是南轮的落脚缝。",
    ["bank_0", "bank_a", "bank_b", "bank_c", "bank_7"],
    tip="昨夜一场大雪, 路边的雪堤已经堆了半人高。",
)
b.step(
    "铺车道行: 车后的灰色路面已铲净, 车前还盖着厚雪。",
    ["lane_0", "lane_a", "lane_3", "lane_b", "lane_c"],
    highlight=["bank_a"],
    tip="车底长板两条长边就是南北轮的双保险吸合线。",
)
b.step(
    "铺北沿行: 五片合拢车道, 轮缝板对齐 y=2 线。",
    ["edge_0", "edge_a", "edge_3", "edge_b", "edge_c"],
    highlight=["lane_a"],
    tip="灰色与雪色的分界线, 就是铲雪车干活的进度条。",
)
b.step(
    "铺人行道: 八片青色方板沿街排开。",
    [f"walk_{x}" for x in range(8)],
    highlight=["edge_0", "edge_3"],
    tip="雪人、雪松和慢行牌都要站在人行道的拼缝上。",
)
b.step(
    "装车轮架甲板: 两片车轮底座沿拼缝立起, 甲板长边压双轮顶。",
    ["wheel_s", "wheel_n", "plow_deck"],
    highlight=["lane_a", "edge_a"],
    tip="轮组+甲板锁成门式框架 —— 铲雪车的底盘要扛得住推雪。",
)
b.step(
    "立箱环两端: 西端料斗尾壁, 东端车窗挡风正对前方。",
    ["hopper_rear", "cab_wind"],
    highlight=["plow_deck"],
    tip="端壁底边整边吸甲板短边 —— 车身骨架先立两端。",
)
b.step(
    "合箱环侧壁: 四片橙色侧壁竖边吸进前后壁拐角。",
    ["side_s1", "side_s2", "side_n1", "side_n2"],
    highlight=["hopper_rear", "cab_wind"],
    tip="圈层砌法合龙 —— 前半是驾驶室, 后半是融雪剂料斗。",
)
b.step(
    "盖驾驶室顶、装警灯、挂铲雪板: 斜坡顶边整边吸甲板东缘, 坡尾平稳落地。",
    ["cab_roof", "beacon", "blade"],
    highlight=["side_s2", "cab_wind"],
    tip="料斗保持敞口好装融雪剂; 铲雪板坡尾贴住雪面 —— 零悬挑。",
)
b.step(
    "堆积雪: 车道上一堆待铲雪, 雪堤上三堆排队等着。",
    ["pile_lane", "pile_a", "pile_b", "pile_c"],
    highlight=["blade"],
    tip="积雪底边整边吸拼缝 —— 铲雪板正对着它们一路推过去。",
)
b.step(
    "雪人雪松慢行牌收尾: 人行道上的观众就位, 开工!",
    ["snowman_body", "snowman_head", "pine_a", "pine_b", "slow_sign"],
    highlight=["walk_7", "walk_0"],
    tip="雪人方身顶三角头, 雪松站上拼缝 —— 轰隆隆, 铲雪车出发!",
)

b.finalize(
    model_id="snowplow_01",
    name="铲雪车",
    name_en="Snowplow Truck 01",
    description=(
        "只用核心九片型的除雪作业车: 招牌是一片 30 度倾斜的红色铲雪板 "
        "—— 顶边整边吸在底盘甲板前缘、坡尾平贴雪面零悬挑 (滚珠塔坡道"
        "的同款几何); 双车轮底座整边吸车道拼缝, 甲板长边压双轮顶锁成"
        "门式框架, 车身箱环前半是青窗驾驶室、后半是敞口融雪剂料斗, "
        "黄警灯立在车顶前沿; 车后车道已铲净露出灰色路面, 车前还盖着"
        "厚雪, 雪堤上四堆积雪排队等着被推走 —— 雪人和雪松在人行道上"
        "围观, 轰隆隆, 铲雪车开工!"
    ),
    difficulty=2,
    tags=["城市", "交通", "冬季", "工程车", "载具", "车轮底座"],
    min_pieces=44,
    min_steps=10,
)
