#!/usr/bin/env python3
"""生成模型 data/models/canal_lock_01.json (运河船闸)。

工程结构主题的第一座通航建筑: 与水电站大坝 (阶梯重力坝挡水) 的
结构逻辑完全不同 —— 大坝把水拦住, 船闸让船"爬楼梯": 两扇整板
钢闸门插在闸墙竖边之间, 夹出中央闸室; 上游高位水面整整比下游
高一层 (蓝色水板铺在围堰墙顶, z=1), 一艘白帆小船正泊在闸室里
等水位上涨; 北岸闸控室窗格方望着闸门, 两侧检修梯斜撑贴墙而立
—— 全库唯一的"双闸门 + 两级水面"。

结构总览 (世界单位: 1.0 = 正方形磁力片边长, 水道沿 x 向, 南北两岸):
  - 南北岸步道 (y [0,1] / [3,4], x [0,7]): 方板 + 中段长板     12 片
  - 上游高位水池 (x [0,2], y [1,3]): 围堰墙 6 + 高位水板 (z=1) 4 10 片
  - 上/下游闸门: 整板长方形竖插 (x=2 / x=4, y [1,3], z [0,1])    2 片
  - 闸室 (x [2,4], y [1,3]): 闸墙 4 + 低位水板 (z=0) 4            8 片
  - 下游水道 (x [4,7], y [1,3]): 低位水板 (z=0)                   6 片
  - 闸控室 (x [2,3], y [3,4]): 三墙 (含窗格方) + 平顶 (与闸墙
    共用南墙)                                                     4 片
  - 小船 (闸室内): 白帆瘦高等腰 + 船旗等边三角, 骑水板拼缝        2 片
  - 闸口警示三角 x2 (闸墙墙顶) + 检修梯斜撑 x2 (贴闸墙竖边)       4 片
  - 缆桩 x4 (岸沿) + 上下游航标 x2 (水面拼缝)                     6 片
  合计 54 片, 13 个教程步骤, 6 种磁力片形状 (全部 CORE-9 之内)。

物理规则要点 (validate 常规 + strict 双档零警告):
  - 整板闸门两条竖直短边分别吸住两侧闸墙 (或围堰墙) 的竖边,
    底边落地 —— 一扇门同时锁住两道墙, 剪断任一边仍有支撑路径;
  - 高位水板铺在围堰墙顶: 每片至少一条边整边吸墙顶, 板板互吸
    连成整面, 荷载沿墙面直下 (罗马水道桥同款"墙顶铺板");
  - 检修梯斜撑双边吸合 (竖直角边吸闸墙竖边, 水平直角边吸岸面
    拼缝), 撑-墙-岸锁成三角刚性节点;
  - 帆/旗/航标/缆桩底边整边吸拼缝, 剪断任何一条装饰连接最多
    失联 1 片 (< 3), R8 单点失效通过。

用法: python3 tools/generate_canal_lock_01.py  (在 magtile-studio 目录下运行)
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from magtile_gen import ModelBuilder  # noqa: E402

b = ModelBuilder()

BANK = "gray"        # 两岸步道
WALL = "gray"        # 围堰墙 / 闸墙
GATE = "orange"      # 整板钢闸门
WATER_HI = "blue"    # 上游高位水面
WATER_LO = "cyan"    # 闸室与下游低位水面
CABIN = "clear"      # 闸控室
CABIN_WIN = "cyan"   # 闸控室窗
ROOF = "red"         # 闸控室平顶
SAIL = "clear"       # 小船白帆
FLAG = "red"         # 船旗
WARN = "red"         # 闸口警示三角
LADDER = "yellow"    # 检修梯斜撑
BOLLARD = "orange"   # 缆桩
BUOY = "green"       # 航标


def wall_ns_t(tid, tile_type, x0, y, z0, color):
    b.add(tid, tile_type, (x0 + 0.5, y, z0 + 0.5), (90, 0, 0), color)


# =================================================================
# 1. 南北两岸步道 (y [0,1] / [3,4]): 单位方板供墙脚/缆桩拼缝,
#    中段各嵌一条长板
# =================================================================
b.flat("bank_s_0", 0, 0, 0.0, BANK)
b.flat("bank_s_1", 1, 0, 0.0, BANK)
b.flat_rect("bank_s_mid", 2, 0, 0.0, BANK)      # x [2,4]
b.flat("bank_s_4", 4, 0, 0.0, BANK)
b.flat("bank_s_5", 5, 0, 0.0, BANK)
b.flat("bank_s_6", 6, 0, 0.0, BANK)
b.flat("bank_n_0", 0, 3, 0.0, BANK)
b.flat("bank_n_1", 1, 3, 0.0, BANK)
b.flat("bank_n_2", 2, 3, 0.0, BANK)
b.flat("bank_n_3", 3, 3, 0.0, BANK)
b.flat_rect("bank_n_mid", 4, 3, 0.0, BANK)      # x [4,6]
b.flat("bank_n_6", 6, 3, 0.0, BANK)

# =================================================================
# 2. 下游水道 (x [4,7]) 与闸室 (x [2,4]) 低位水面 (z=0)
# =================================================================
for x0 in (4, 5, 6):
    b.flat(f"water_lo_{x0}_1", x0, 1, 0.0, WATER_LO)
    b.flat(f"water_lo_{x0}_2", x0, 2, 0.0, WATER_LO)
for x0 in (2, 3):
    b.flat(f"chamber_{x0}_1", x0, 1, 0.0, WATER_LO)
    b.flat(f"chamber_{x0}_2", x0, 2, 0.0, WATER_LO)

# =================================================================
# 3. 闸墙 (闸室南北, z 0..1) 与上游围堰墙
# =================================================================
b.wall_ns("lock_s_w", 2, 1.0, 0, WALL)
b.wall_ns("lock_s_e", 3, 1.0, 0, WALL)
b.wall_ns("lock_n_w", 2, 3.0, 0, WALL)
b.wall_ns("lock_n_e", 3, 3.0, 0, WALL)

b.wall_ew("basin_w_1", 0.0, 1, 0, WALL)
b.wall_ew("basin_w_2", 0.0, 2, 0, WALL)
b.wall_ns("basin_s_0", 0, 1.0, 0, WALL)
b.wall_ns("basin_s_1", 1, 1.0, 0, WALL)
b.wall_ns("basin_n_0", 0, 3.0, 0, WALL)
b.wall_ns("basin_n_1", 1, 3.0, 0, WALL)

# =================================================================
# 4. 两扇整板钢闸门: 竖直长方形插在闸墙竖边之间
# =================================================================
b.lintel_ew("gate_up", 2.0, 1, 0, GATE)     # 上闸门 (x=2)
b.lintel_ew("gate_down", 4.0, 1, 0, GATE)   # 下闸门 (x=4)

# =================================================================
# 5. 上游高位水面 (z=1): 水板铺在围堰墙顶
# =================================================================
b.flat("water_hi_0_1", 0, 1, 1.0, WATER_HI)
b.flat("water_hi_0_2", 0, 2, 1.0, WATER_HI)
b.flat("water_hi_1_1", 1, 1, 1.0, WATER_HI)
b.flat("water_hi_1_2", 1, 2, 1.0, WATER_HI)

# =================================================================
# 6. 闸控室 (x [2,3], y [3,4]): 与闸墙 lock_n_w 共用南墙
# =================================================================
b.wall_ew("cabin_w", 2.0, 3, 0, CABIN)
b.wall_ew("cabin_e", 3.0, 3, 0, CABIN)
wall_ns_t("cabin_n", "window_square", 2, 4.0, 0, CABIN_WIN)
b.flat("cabin_roof", 2, 3, 1.0, ROOF)

# =================================================================
# 7. 小船 (闸室) + 警示三角 (闸墙顶) + 检修梯斜撑 + 缆桩 + 航标
# =================================================================
b.spire_ew("boat_sail", 3.0, 1, 0.0, SAIL)      # 白帆骑闸室水缝
b.crest_ew("boat_flag", 3.0, 2, 0.0, FLAG)      # 船旗

b.crest_ns("warn_s", 2, 1.0, 1.0, WARN)         # 南闸墙顶警示
b.crest_ns("warn_n", 3, 3.0, 1.0, WARN)         # 北闸墙顶警示

b.brace("ladder_s", (4.0, 1.0, 0.0), "-y", LADDER)   # 南岸检修梯
b.brace("ladder_n", (4.0, 3.0, 0.0), "+y", LADDER)   # 北岸检修梯

b.crest_ns("bollard_s_1", 1, 0.0, 0.0, BOLLARD)
b.crest_ns("bollard_s_5", 5, 0.0, 0.0, BOLLARD)
b.crest_ns("bollard_n_1", 1, 4.0, 0.0, BOLLARD)
b.crest_ns("bollard_n_6", 6, 4.0, 0.0, BOLLARD)

b.crest_ns("buoy_up", 0, 2.0, 1.0, BUOY)        # 上游航标 (高位水缝)
b.crest_ns("buoy_down", 5, 2.0, 0.0, BUOY)      # 下游航标 (低位水缝)

# =================================================================
# 教程步骤 (13 步)
# =================================================================
b.step(
    "铺南岸步道: 方板加中段长板边边互吸, 沿着水道一字排开。",
    ["bank_s_0", "bank_s_1", "bank_s_mid", "bank_s_4",
     "bank_s_5", "bank_s_6"],
    tip="运河边的纤道 —— 以前的船就是靠人沿着这条路拉过闸的。",
)
b.step(
    "铺下游低位水面: 六片青色水板贴着南岸北沿铺开。",
    ["water_lo_4_1", "water_lo_4_2", "water_lo_5_1",
     "water_lo_5_2", "water_lo_6_1", "water_lo_6_2"],
    highlight=["bank_s_4"],
    tip="下游的水位低 —— 记住这个高度, 一会儿和上游比一比。",
)
b.step(
    "铺闸室低位水面: 四片青色水板, 船就停在这一段。",
    ["chamber_2_1", "chamber_2_2", "chamber_3_1", "chamber_3_2"],
    highlight=["water_lo_4_1"],
    tip="闸室是船的'电梯间': 关上门, 水涨船高。",
)
b.step(
    "铺北岸步道: 贴着水面北沿再铺一排, 与南岸隔水相望。",
    ["bank_n_0", "bank_n_1", "bank_n_2", "bank_n_3",
     "bank_n_mid", "bank_n_6"],
    highlight=["chamber_2_2", "water_lo_4_2"],
    tip="两岸夹住两格宽的水道 —— 船闸的舞台搭好了。",
)
b.step(
    "立闸室南北闸墙: 四片灰墙踩住岸沿拼缝, 墙脚咬牢。",
    ["lock_s_w", "lock_s_e", "lock_n_w", "lock_n_e"],
    highlight=["chamber_2_1"],
    tip="闸墙是船闸的骨架, 一会儿两扇闸门都要靠它夹住。",
)
b.step(
    "围上游围堰: 西墙两片 + 南北墙各两片, 围出高位水池。",
    ["basin_w_1", "basin_w_2", "basin_s_0", "basin_s_1",
     "basin_n_0", "basin_n_1"],
    highlight=["lock_s_w"],
    tip="围堰墙顶就是上游水面的高度 —— 整整比下游高一层。",
)
b.step(
    "插上下两扇整板钢闸门: 竖直长方形卡进闸墙竖边之间。",
    ["gate_up", "gate_down"],
    highlight=["basin_s_1", "lock_s_e"],
    tip="一整板就是一扇门: 两条竖边同时吸住两侧墙边, 底边落地。",
)
b.step(
    "给上游铺高位水面: 四片蓝色水板压在围堰墙顶上。",
    ["water_hi_0_1", "water_hi_0_2", "water_hi_1_1", "water_hi_1_2"],
    highlight=["basin_w_1", "gate_up"],
    tip="每片水板至少一条边整边吸住墙顶, 板板互吸连成水面。",
)
b.step(
    "挂闸口警示三角, 贴检修梯斜撑: 撑-墙-岸锁成三角。",
    ["warn_s", "warn_n", "ladder_s", "ladder_n"],
    highlight=["lock_s_w", "lock_n_e"],
    tip="斜撑两条直角边都要吸牢 —— 检修工人踩着它上下闸墙。",
)
b.step(
    "搭北岸闸控室: 借用闸墙当南墙, 窗格方望着闸门。",
    ["cabin_w", "cabin_e", "cabin_n"],
    highlight=["lock_n_w"],
    tip="闸长在窗后值班: 看水位、开闸门, 全在这一间小屋里。",
)
b.step(
    "盖闸控室平顶: 红色方板四边入扣墙顶。",
    ["cabin_roof"],
    highlight=["cabin_n"],
    tip="平顶压住四面墙, 闸控室就锁成了一个结实的盒子。",
)
b.step(
    "小船进闸: 白帆骑上闸室水缝, 船旗跟在后面。",
    ["boat_sail", "boat_flag"],
    highlight=["gate_up", "gate_down"],
    tip="两扇闸门都关好了 —— 接下来只要往闸室放水, 船就升高啦。",
)
b.step(
    "系缆桩、放航标: 船闸通航!",
    ["bollard_s_1", "bollard_s_5", "bollard_n_1", "bollard_n_6",
     "buoy_up", "buoy_down"],
    highlight=["boat_sail"],
    tip="绿色航标一高一低 —— 正好指给船长看两级水面差多少。",
)

b.finalize(
    model_id="canal_lock_01",
    name="运河船闸",
    name_en="Canal Lock 01",
    description=(
        "只用核心九片型的通航水利工程: 与拦水的大坝不同, 船闸是"
        "让船'爬楼梯'的电梯间 —— 两扇橙色整板钢闸门竖插在闸墙"
        "竖边之间, 夹出中央闸室; 上游蓝色高位水面铺在围堰墙顶, "
        "整整比下游青色水面高一层, 一艘白帆小船正泊在闸室里等"
        "水位上涨; 北岸闸控室窗格方望着闸门, 黄色检修梯斜撑"
        "贴墙锁成三角, 绿色航标一高一低标出两级水面 —— 开闸, "
        "放水, 水涨船高!"
    ),
    difficulty=3,
    tags=["工程", "船闸", "运河", "水利", "航运", "进阶"],
    min_pieces=54,
    min_steps=13,
)
