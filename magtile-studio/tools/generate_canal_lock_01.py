#!/usr/bin/env python3
"""生成模型 data/models/canal_lock_01.json (运河船闸)。

工程结构主题新作, 全库第一座通航水工建筑 —— 与水电大坝
(整面挡水墙) 和各类桥梁都不同, 本作的招牌是"两级水面的楼梯":
运河在船闸处分成下游水道 (z=0 蓝色水面) 与上游高位水道
(z=1 —— 蓝色水板铺在闸墙顶上, 整段高位水道就是一只封顶的
长箱体), 两道橙色闸门把中间的闸室夹在楼梯的踏步上; 红色小
驳船正在下游候闸, 值班房窗格方盯着闸室, 红色信号塔立在闸墙
顶提醒行船 —— 水往高处走的秘密, 一眼看懂。

结构总览 (世界单位: 1.0 = 正方形磁力片边长, 上游在东):
  - 南岸 (y [0,1]): 绿色长板 x5                                5 片
  - 北岸 (y [2,3]): 长板 x4 + 值班房地基方板 x2                6 片
  - 水道行 (y [1,2]): 下游蓝水 x4 + 红驳船 x1 + 闸室青水 x2
    + 高位水道箱底 x3                                         10 片
  - 闸室侧墙 x4 (x [5,7], z 0..1) + 红色信号塔 x1              5 片
  - 闸门 x2: 下游门 (x=5) 与上游门 (x=7) 橙色立板              2 片
  - 高位水道 (x [7,10]): 侧墙 x6 + 东端墙 x1 + 高位蓝水板 x3  10 片
  - 值班房 (x [5,6], y [2,3]): 三墙 (南墙与闸室北墙共用,
    观察窗直接盯闸室; 门朝东) + 等边四坡锥顶                   7 片
  - 驳船帆桅 x2 + 系船柱 x3 + 高位浮标 x1 + 岸边绿树 x2        8 片
  合计 53 片, 12 个教程步骤, 6 种磁力片形状 (全部 CORE-9 之内)。

物理规则要点 (validate 常规 + strict 双档零警告):
  - 高位水道是"封顶长箱": 侧墙与端墙踩水道拼缝整边吸合,
    三片高位蓝水板四边分别搭两侧墙顶/端墙顶/闸门顶并互吸
    —— 全支承零悬挑, 箱底方板先铺、封顶后不再触碰 (装配可达);
  - 两道闸门竖边咬进闸室与高位侧墙的拐角, 底边整边吸水道
    拼缝 —— 每道门三边受吸, 剪断任一连接不掉件;
  - 值班房与闸室共用一面窗格方墙 (共墙技法), 墙环踩北岸拼缝,
    等边四坡锥顶斜棱两两互吸自锁;
  - 帆桅/系船柱/浮标/绿树各自独立吸附, 剪断任何一条装饰连接
    最多失联 1 片 (< 3), R8 单点失效通过。

用法: python3 tools/generate_canal_lock_01.py  (在 magtile-studio 目录下运行)
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from magtile_gen import ModelBuilder  # noqa: E402

b = ModelBuilder()

BANK = "green"      # 河岸
WATER = "blue"      # 下游水面
CHAMBER = "cyan"    # 闸室水面
BED = "gray"        # 高位水道箱底
HIGH = "blue"       # 高位水面
WALL = "gray"       # 闸墙
GATE = "orange"     # 闸门
BOAT = "red"        # 驳船
SAIL = "clear"      # 驳船帆
CABIN = "clear"     # 值班房墙
WIN = "cyan"        # 值班房窗
DOOR = "orange"     # 值班房门
ROOF = "green"      # 值班房锥顶
BOLLARD = "yellow"  # 系船柱
BUOY = "red"        # 高位浮标
TOWER = "red"       # 信号塔
TREE = "green"      # 岸边绿树


def wall_ns_t(tid, tile_type, x0, y, z0, color):
    b.add(tid, tile_type, (x0 + 0.5, y, z0 + 0.5), (90, 0, 0), color)


def wall_ew_t(tid, tile_type, x, y0, z0, color):
    b.add(tid, tile_type, (x, y0 + 0.5, z0 + 0.5), (90, 0, 90), color)


# =================================================================
# 1. 南岸五长板 + 北岸 (值班房地基用单位方板)
# =================================================================
for i, x0 in enumerate((0, 2, 4, 6, 8)):
    b.flat_rect(f"bank_s_{i}", x0, 0, 0.0, BANK)      # 南岸 y [0,1]
b.flat_rect("bank_n_0", 0, 2, 0.0, BANK)              # 北岸 y [2,3]
b.flat_rect("bank_n_1", 2, 2, 0.0, BANK)
b.flat("bank_n_4", 4, 2, 0.0, BANK)
b.flat("bank_n_5", 5, 2, 0.0, BANK)                   # 值班房地基
b.flat_rect("bank_n_2", 6, 2, 0.0, BANK)
b.flat_rect("bank_n_3", 8, 2, 0.0, BANK)

# =================================================================
# 2. 水道行 (y [1,2]): 下游蓝水 -> 红驳船 -> 闸室青水 -> 箱底
# =================================================================
for x0 in range(10):
    if x0 == 2:
        color = BOAT                                  # 红驳船候闸
    elif x0 in (5, 6):
        color = CHAMBER                               # 闸室水面
    elif x0 >= 7:
        color = BED                                   # 高位水道箱底
    else:
        color = WATER
    b.flat(f"canal_{x0}", x0, 1, 0.0, color)

# =================================================================
# 3. 闸室侧墙 (x [5,7], z 0..1) + 信号塔
# =================================================================
b.wall_ns("lock_s1", 5, 1.0, 0, WALL)
b.wall_ns("lock_s2", 6, 1.0, 0, WALL)
wall_ns_t("lock_n1", "window_square", 5, 2.0, 0, WIN)  # 共墙: 兼作值班房观察窗
b.wall_ns("lock_n2", 6, 2.0, 0, WALL)
b.spire_ns("signal_tower", 5, 1.0, 1.0, TOWER)        # 信号塔骑闸墙顶

# =================================================================
# 4. 闸门 x2: 下游门 (x=5) 与上游门 (x=7)
# =================================================================
b.wall_ew("gate_low", 5.0, 1, 0, GATE)                # 下游闸门
b.wall_ew("gate_high", 7.0, 1, 0, GATE)               # 上游闸门

# =================================================================
# 5. 高位水道 (x [7,10]): 侧墙 + 东端墙 + 高位蓝水板 (z=1)
# =================================================================
for x0 in (7, 8, 9):
    b.wall_ns(f"high_s_{x0}", x0, 1.0, 0, WALL)
    b.wall_ns(f"high_n_{x0}", x0, 2.0, 0, WALL)
b.wall_ew("high_end", 10.0, 1, 0, WALL)               # 东端墙
for x0 in (7, 8, 9):
    b.flat(f"high_water_{x0}", x0, 1, 1.0, HIGH)      # 高位水面

# =================================================================
# 6. 值班房 (x [5,6], y [2,3]): 南墙与闸室北墙共用 (共墙技法),
#    观察窗直接盯着闸室, 门朝东
# =================================================================
b.wall_ns("keeper_n", 5, 3.0, 0, CABIN)
b.wall_ew("keeper_w", 5.0, 2, 0, CABIN)
wall_ew_t("keeper_e", "door_frame", 6.0, 2, 0, DOOR)  # 门朝东
KEEPER_ROOF = b.hat4("keeper_roof", 5, 2, 1.0, ROOF,
                     shape="equilateral_triangle")    # 锥尖 1.71

# =================================================================
# 7. 驳船帆桅 + 系船柱 x3 + 高位浮标 + 岸边绿树 x2
# =================================================================
b.crest_ew("boat_bow", 2.0, 1, 0.0, BOAT)             # 船头三角
b.spire_ew("boat_sail", 3.0, 1, 0.0, SAIL)            # 瘦高帆桅
b.crest_ns("bollard_a", 0, 1.0, 0.0, BOLLARD)         # 南岸系船柱
b.crest_ns("bollard_b", 3, 2.0, 0.0, BOLLARD)         # 北岸系船柱
b.crest_ns("bollard_c", 4, 1.0, 0.0, BOLLARD)         # 闸前系船柱
b.crest_ew("high_buoy", 8.0, 1, 1.0, BUOY)            # 高位浮标
b.spire_ew("tree_w", 2.0, 0, 0.0, TREE)               # 南岸绿树
b.spire_ew("tree_e", 8.0, 0, 0.0, TREE)

# =================================================================
# 教程步骤 (12 步)
# =================================================================
b.step(
    "铺南岸: 五片绿色长板短边互吸连成河岸。",
    [f"bank_s_{i}" for i in range(5)],
    tip="运河从西向东流 —— 上游在东边, 比下游高整整一层。",
)
b.step(
    "铺水道行: 下游蓝水、红驳船、闸室青水、高位箱底一字排开。",
    [f"canal_{x0}" for x0 in range(10)],
    highlight=["bank_s_0"],
    tip="灰色的三格是高位水道的箱底 —— 待会儿要被封进箱子里。",
)
b.step(
    "铺北岸: 值班房的地基用两片单位方板留好拼缝。",
    ["bank_n_0", "bank_n_1", "bank_n_4", "bank_n_5", "bank_n_2", "bank_n_3"],
    highlight=["canal_0"],
    tip="方板四条边都是墙脚的吸合缝 —— 值班房就盖在这里。",
)
b.step(
    "立闸室侧墙并竖信号塔: 北墙用窗格方 —— 它就是值班房的观察窗。",
    ["lock_s1", "lock_s2", "lock_n1", "lock_n2", "signal_tower"],
    highlight=["canal_5", "canal_6"],
    tip="共墙技法: 一片墙同时属于闸室和值班房; 红灯亮请在闸外等候。",
)
b.step(
    "装两道闸门: 橙色立板竖边咬进闸墙拐角, 底边整边吸拼缝。",
    ["gate_low", "gate_high"],
    highlight=["lock_s1", "lock_n2"],
    tip="下游门放船进闸, 上游门挡住高位水 —— 一次只开一道。",
)
b.step(
    "立高位水道侧墙: 六片灰墙沿水道两侧排到东头。",
    ["high_s_7", "high_n_7", "high_s_8", "high_n_8", "high_s_9", "high_n_9"],
    highlight=["gate_high"],
    tip="墙脚踩拼缝竖边互咬 —— 高位水道的箱壁越砌越长。",
)
b.step(
    "封东端墙、铺高位水面: 三片蓝水板搭墙顶互吸, 水在一层楼高!",
    ["high_end", "high_water_7", "high_water_8", "high_water_9"],
    highlight=["high_s_9", "high_n_9"],
    tip="水板四边搭两侧墙顶/端墙顶/闸门顶 —— 全支承零悬挑。",
)
b.step(
    "合值班房墙环: 北墙与东西墙咬进观察窗拐角, 门框方朝东。",
    ["keeper_n", "keeper_w", "keeper_e"],
    highlight=["bank_n_4", "bank_n_5"],
    tip="闸门什么时候开, 值班员说了算。",
)
b.step(
    "盖值班房锥顶: 四片绿色等边三角斜棱互咬自锁。",
    KEEPER_ROOF,
    highlight=["keeper_n"],
    tip="锥尖 1.71 —— 对角顺序合拢, 最后一片同时吸双棱。",
)
b.step(
    "装红驳船的船头与帆桅: 两片立在船身两条拼缝上。",
    ["boat_bow", "boat_sail"],
    highlight=["canal_2"],
    tip="小驳船在下游候闸 —— 它马上要坐一次水的电梯。",
)
b.step(
    "钉系船柱、放浮标: 三根黄柱骑岸缝, 红浮标漂在高位水面。",
    ["bollard_a", "bollard_b", "bollard_c", "high_buoy"],
    highlight=["canal_0", "high_water_8"],
    tip="过闸的船先系缆再等门 —— 浮标标出高位航道的中线。",
)
b.step(
    "种岸边绿树收尾: 两棵瘦高绿树骑上南岸拼缝, 通航!",
    ["tree_w", "tree_e"],
    highlight=["bank_s_1", "bank_s_4"],
    tip="信号塔换绿灯 —— 下游门缓缓打开, 请驳船进闸!",
)

b.finalize(
    model_id="canal_lock_01",
    name="运河船闸",
    name_en="Canal Lock 01",
    description=(
        "只用核心九片型的通航水工建筑: 招牌是\"两级水面的楼梯\" —— "
        "下游蓝色水面贴地, 上游高位水道是一只封顶长箱 (侧墙踩拼缝"
        "互咬, 三片蓝色水板四边搭墙顶全支承), 水面硬是比下游高出"
        "一整层; 两道橙色闸门竖边咬进闸墙拐角把闸室夹在踏步上, "
        "红色信号塔骑在闸墙顶指挥行船; 红驳船立着帆桅在下游候闸, "
        "值班房与闸室共用一面窗格方墙 (共墙技法) 直接盯着闸室、"
        "绿锥顶斜棱自锁 —— 信号塔换绿灯, 船要坐水的电梯上楼啦!"
    ),
    difficulty=3,
    tags=["工程", "运河", "船闸", "水利", "海洋"],
    min_pieces=53,
    min_steps=12,
)
