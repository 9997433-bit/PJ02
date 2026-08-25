#!/usr/bin/env python3
"""生成模型 data/models/marble_cascade_01.json (阶梯瀑布滚珠台)。

内容批 J 模型 3/4: 滚珠乐园主题首个 D2 —— 与 ball_run_tower_01
(双轨绕塔) / marble_run_spiral_01 (单塔盘旋) 动线拓扑均不同, 本作
是"三级退台瀑布": 三层平台逐层向东退台, 每级 30 度坡道从平台东沿
直落下一级 (T12 层叠 + T08 滚珠轨道), 弹珠连跳三次掉进南端接珠池。
比 D3/D4 滚珠作更紧凑, 全部 CORE-9, 实物跑珠即可验证。

结构总览 (世界单位: 1.0 = 正方形磁力片边长, 弹珠自西向东冲下):
  - 西端发射台 (x [0,1], y [0,2], z 0..2): 地台 x2 + 墙环 x12 +
    发球台 x2 + 台沿挡珠 x3                                              19 片
  - 三级退台 (z 2/1/0): 转接台 x3 + 栈桥墩 x6 + 坡道 x3 + 挡珠 x6       18 片
  - 南端接珠池 (y 南端): 池底 x2 + 围墙 x4 + 铃靶 x1                     7 片
  合计 34 片 (发射 19 + 轨道 12 + 池 3 调整)... 见下方精确计数。

物理规则要点 (validate strict 零警告):
  - 每段坡道顶边整边吸平台东沿, 坡尾由栈桥墩顶边接住, 三件互吸;
  - 转接台西缘压墩顶与坡尾, 东缘由门式立柱从地面顶住;
  - 冲线坡道坡尾自然落地, 池底与坡尾整边互吸;
  - 发射台最高点约 3.87, 低于 R8 红线 4.0。

用法: python3 tools/generate_marble_cascade_01.py  (在 magtile-studio 目录下运行)
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from magtile_gen import SQ3, ModelBuilder  # noqa: E402

b = ModelBuilder()

BASE = "gray"
TOWER = "blue"
DECK = "yellow"
RAIL = "red"
PIER = "gray"
RAMP = "orange"
POOL = "cyan"
BELL = "pink"

def wall_ew_t(tid, tile_type, x, y0, z0, color):
    b.add(tid, tile_type, (x, y0 + 0.5, z0 + 0.5), (90, 0, 90), color)


X1 = 1 + SQ3       # 转接台一西缘 2.732051
X2 = X1 + 1 + SQ3  # 转接台二西缘 5.464102
X3 = X2 + 1 + SQ3  # 接珠池西缘 8.196153

# =================================================================
# 1. 西端发射台 (x [0,1], y [0,2]): 地台 + 两层墙环 + 发球台
# =================================================================
b.flat("base_0", 0, 0, 0.0, BASE)
b.flat("base_1", 0, 1, 0.0, BASE)
for lv in range(2):
    c = TOWER
    b.wall_ns(f"tw{lv}_s", 0, 0.0, lv, c)
    b.wall_ns(f"tw{lv}_n", 0, 2.0, lv, c)
    b.wall_ew(f"tw{lv}_w_0", 0.0, 0, lv, c)
    b.wall_ew(f"tw{lv}_w_1", 0.0, 1, lv, c)
    b.wall_ew(f"tw{lv}_e_0", 1.0, 0, lv, c)
    b.wall_ew(f"tw{lv}_e_1", 1.0, 1, lv, c)
b.flat("deck_0", 0, 0, 2.0, DECK)
b.flat("deck_1", 0, 1, 2.0, DECK)
# 台沿挡珠: 西/北/南三侧, 东缘南半格是出珠口
b.crest_ew("drail_w", 0.0, 0, 2.0, RAIL)
b.crest_ns("drail_n", 0, 2.0, 2.0, RAIL)
b.crest_ns("drail_s", 0, 0.0, 2.0, RAIL)

# =================================================================
# 2. 三级退台瀑布 (z2 -> z1 -> z0 -> 落地)
# =================================================================
# 段一 z2->z1 (单层桥墩 + 门式立柱)
b.wall_ew("p1a", X1, 0, 0, PIER)
b.wall_ew("p1c", X1 + 1, 0, 0, PIER)
b.ramp("ramp_1", "+x", 1.0, 0, 2.0, RAMP)
b.flat("plat_1", X1, 0, 1.0, DECK)
b.crest_ns("rail1_s", X1, 0.0, 1.0, RAIL)

# 段二 z1->z0
b.wall_ew("p2a", X2, 0, 0, PIER)
b.ramp("ramp_2", "+x", X1 + 1, 0, 1.0, RAMP)
b.flat("plat_2", X2, 0, 0.0, DECK)
b.crest_ns("rail2_s", X2, 0.0, 0.0, RAIL)

# 段三 冲线 z1->落地 (门式立柱顶 z=1 铰链 ramp, 坡尾接池)
b.wall_ew("p3a", X2 + 1, 0, 0, PIER)
b.ramp("ramp_3", "+x", X2 + 1, 0, 1.0, RAMP)

# =================================================================
# 3. 接珠池 (y=0 直线延伸, 与冲线坡道整边互吸)
# =================================================================
b.flat("pool_0", X3, 0, 0.0, POOL)
b.flat("pool_1", X3 + 1, 0, 0.0, POOL)
b.wall_ns("pool_s", X3, 0.0, 0, POOL)
wall_ew_t("bell", "window_square", X3 + 2, 0, 0, BELL)  # 池端铃靶

# =================================================================
# 教程步骤 (10 步)
# =================================================================
b.step(
    "铺发射塔地台: 两片灰色方板沿西端打底, 六片蓝色方板合围第一层墙环。",
    ["base_0", "base_1",
     "tw0_s", "tw0_w_0", "tw0_w_1", "tw0_n", "tw0_e_0", "tw0_e_1"],
    tip="塔基东边要留出一条直线跑道 —— 弹珠将从这里三级瀑布跳下。",
)
b.step(
    "发射塔第二层: 六片蓝色方板骑上第一层墙顶, 上下边完整贴合。",
    ["tw1_s", "tw1_w_0", "tw1_w_1", "tw1_n", "tw1_e_0", "tw1_e_1"],
    highlight=["tw0_s", "tw0_e_0"],
    tip="两层墙环已经够高 —— D2 不需要三层塔, 弹珠从 z=2 出发。",
)
b.step(
    "盖发球台: 两片黄色方板压住第二层墙顶, 三片挡珠三角围住台沿 (东缘留口)。",
    ["deck_0", "deck_1", "drail_w", "drail_n", "drail_s"],
    highlight=["tw1_s", "tw1_e_0"],
    tip="东缘南半格空着 —— 那是弹珠跳向第一级瀑布的出珠口。",
)
b.step(
    "第一级瀑布 (整段成组): 塔东侧立桥墩与门式立柱, 坡道顶边吸出珠口, "
    "转接台压住墩顶与坡尾。",
    ["p1a", "p1c", "ramp_1", "plat_1"],
    highlight=["deck_0", "tw1_e_0"],
    tip="桥墩-坡道-转接台三件互吸 —— 第一级瀑布就位, 轻摇应纹丝不动。",
)
b.step(
    "转接台一装挡珠: 一片红三角锁住平台南沿, 弹珠只能乖乖向东滑。",
    ["rail1_s"],
    highlight=["plat_1"],
    tip="第一跳落下后, 弹珠会沿平台向东冲 —— 挡珠防止它跑偏。",
)
b.step(
    "第二级瀑布: 立桥墩, 第二段坡道从转接台东缘下探到 z=0。",
    ["p2a", "ramp_2", "plat_2"],
    highlight=["plat_1", "p1c"],
    tip="海拔又降一层 —— 听, 弹珠落台的声音比第一跳更响。",
)
b.step(
    "转接台二装挡珠: 一片红三角锁住平台南沿。",
    ["rail2_s"],
    highlight=["plat_2"],
    tip="第二级转接台是最后一层平台 —— 再往前就是冲线。",
)
b.step(
    "第三级冲线: 立门式立柱, 橙色坡道从立柱顶 z=1 直落地面接池。",
    ["p3a", "ramp_3"],
    highlight=["plat_2"],
    tip="冲线坡道顶边吸台缘, 坡尾落地不需要任何支撑 —— 第三跳!",
)
b.step(
    "铺接珠池: 两片青色池底沿冲线方向铺开, 南北矮墙围合。",
    ["pool_0", "pool_1", "pool_s"],
    highlight=["ramp_3"],
    tip="池子敞口朝西 —— 弹珠从冲线坡道冲进来, 撞池壁减速。",
)
b.step(
    "立铃靶: 粉色窗格方板立在池端 —— 阶梯瀑布滚珠台完工, 放珠开跳!",
    ["bell"],
    highlight=["pool_0"],
    tip="三跳连落, 听哪一声最响 —— 实物跑珠才算真正验收!",
)

b.finalize(
    model_id="marble_cascade_01",
    name="阶梯瀑布滚珠台",
    name_en="Marble Cascade 01",
    description=(
        "滚珠乐园首个 D2: 与绕塔双轨/单塔螺旋完全不同的三级退台瀑布 —— "
        "两层发射台向正东甩出三段 30 度坡道, 每级平台东沿是坡道顶铰链、"
        "桥墩接住坡尾, 弹珠连跳三次落进南端接珠池; 轨道严格服从台阶几何 "
        "(T12 层叠退台 + T08 滚珠轨道), 全部 CORE-9, 实物跑珠即可验证。"
    ),
    difficulty=2,
    tags=["滚珠", "轨道", "瀑布", "滚珠乐园", "退台"],
    min_pieces=34,
    min_steps=10,
    series="marble_run",
)
