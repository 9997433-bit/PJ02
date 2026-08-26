#!/usr/bin/env python3
"""生成模型 data/models/switchback_ramp_01.json (折返坡道滚珠塔)。

内容批 P 模型 8/10 (P8): 滚珠乐园 D2 —— 招牌是 T08 滚珠轨道 + T14
直角三角折返台: 两层发球塔向东甩出首段坡道, 弹珠在由两片直角三角拼成
的折返台上 180° 掉头, 沿第二段坡道折返向西, 再经第二块折返台二次掉头
冲进接珠池。≥10 片直角三角 (折返台台面 + 塔基斜撑 + 台下 T14 锁固),
与 ball_run_tower_01 (双轨镜像) / marble_run_spiral_01 (顺时针螺旋)
的动线拓扑均不同。

结构总览 (世界单位: 1.0 = 正方形磁力片边长, 弹珠自塔顶 z=2 出发):
  - 塔基 + 两层墙 + 发球台                                          10 片
  - 双段折返坡道 (T08) + 阶梯桥墩                                   2 片
  - 两块折返台 (各 2 片直角三角拼 1x1 台面) + 台下双斜撑 (T14)       6 片
  - 塔基四角斜撑 (T14)                                              4 片
  - 发球台/折返台挡珠 + 接珠池                                       12 片
  合计 36 片 (直角三角 x10 + 正方形 x17 + 长方形 x2 + 等边三角 x7)。

物理规则要点 (validate strict 零警告):
  - 每段坡道顶边整边吸平台沿口, 坡尾由桥墩顶边或折返台接住;
  - 折返台由两片直角三角对角拼合, 台下 T14 斜撑锁桥墩侧竖边;
  - 塔基四角直角三角双边吸合抗侧撞;
  - 发球台最高点 z=2, 低于 R8 红线 4.0。

用法: python3 tools/generate_switchback_ramp_01.py  (在 magtile-studio 目录下运行)
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from magtile_gen import SQ3, ModelBuilder  # noqa: E402

b = ModelBuilder()

BASE = "gray"
TOWER = "blue"
DECK = "yellow"
RAMP = "orange"
PIER = "gray"
LAND = "cyan"
RAIL = "red"
BRACE = "purple"
POOL = "blue"

XA = 1 + SQ3       # 折返台 A 西缘 = 首段坡道坡尾 x
XB = 2.0           # 折返台 B 西缘 = 第二段坡道坡尾 x

BRACES = [
    ("br_sw", (0.0, 0.0, 0.0), "-x"),
    ("br_se", (1.0, 0.0, 0.0), "-y"),
    ("br_ne", (1.0, 1.0, 0.0), "+x"),
    ("br_nw", (0.0, 1.0, 0.0), "+y"),
]


def rt_landing(prefix, x0, y0, z, color):
    """两片直角三角拼 1x1 水平折返台 (对角互吸成整面)。"""
    b.place_tri(
        f"{prefix}_lo", "right_triangle",
        (x0, y0, z), (x0 + 1, y0, z), (x0, y0 + 1, z), color,
    )
    b.place_tri(
        f"{prefix}_hi", "right_triangle",
        (x0 + 1, y0 + 1, z), (x0, y0 + 1, z), (x0 + 1, y0, z), color,
    )


# =================================================================
# 1. 塔基 1x1 + 两层墙
# =================================================================
b.flat("base_0", 0, 0, 0.0, BASE)
for lv in range(2):
    c = TOWER
    b.wall_ns(f"tw{lv}_s", 0, 0.0, lv, c)
    b.wall_ns(f"tw{lv}_n", 0, 1.0, lv, c)
    b.wall_ew(f"tw{lv}_w", 0.0, 0, lv, c)
    b.wall_ew(f"tw{lv}_e", 1.0, 0, lv, c)

for tid, corner, hdir in BRACES:
    b.brace(tid, corner, hdir, BRACE)

# =================================================================
# 2. 发球台 z=2 (东缘留出珠口)
# =================================================================
b.flat("deck_0", 0, 0, 2.0, DECK)
b.crest_ew("drail_w", 0.0, 0, 2.0, RAIL)
b.crest_ns("drail_n", 0, 1.0, 2.0, RAIL)
b.crest_ns("drail_s", 0, 0.0, 2.0, RAIL)

# =================================================================
# 3. 首段坡道 z2->z1 + 折返台 A (180° 掉头)
# =================================================================
b.wall_ew("pier_a", XA, 0, 0, PIER)
b.ramp("ramp_e", "+x", 1.0, 0, 2.0, RAMP)
rt_landing("land_a", XA, 0, 1.0, LAND)
b.place_tri(
    "brace_a_s", "right_triangle",
    (XA, 0.0, 1.0), (XA + 1, 0.0, 1.0), (XA, 0.0, 0.0), BRACE,
)
b.place_tri(
    "brace_a_n", "right_triangle",
    (XA + 1, 1.0, 1.0), (XA + 1, 1.0, 0.0), (XA + 1, 0.0, 1.0), BRACE,
)
b.crest_ns("rail_a_n", XA, 1.0, 1.0, RAIL)
b.crest_ew("rail_a_e", XA + 1, 0, 1.0, RAIL)

# =================================================================
# 4. 折返坡道 z1->z0 + 折返台 B (二次 180° 掉头, 东移避开塔身)
# =================================================================
b.ramp("ramp_w", "-x", XA + 1, 0, 1.0, RAMP)
rt_landing("land_b", XB, 0, 0.0, LAND)
b.crest_ns("rail_b_n", XB, 1.0, 0.0, RAIL)
b.crest_ew("rail_b_e", XB + 1, 0, 0.0, RAIL)

# =================================================================
# 5. 冲线短轨 + 接珠池 (东移, 与折返台 A 斜撑错开)
# =================================================================
b.flat("track_0", 3, 0, 0.0, DECK)
b.flat("pool_0", 4, 0, 0.0, POOL)
b.flat("pool_1", 5, 0, 0.0, POOL)
b.wall_ns("pool_s", 4, 0.0, 0, POOL)
b.wall_ew("pool_w", 4.0, 0, 0, POOL)
b.wall_ew("pool_e", 6.0, 0, 0, POOL)

# =================================================================
# 教程步骤 (10 步)
# =================================================================
b.step(
    "铺塔基: 一片灰色方板打底, 四片蓝色方板合围第一层墙环。",
    ["base_0", "tw0_s", "tw0_w", "tw0_n", "tw0_e"],
    tip="塔基东边要留出直线跑道 —— 弹珠将从这里折返下坡。",
)
b.step(
    "塔基四角斜撑 (T14): 四片紫色直角三角呈风车状, 竖直角边吸塔角、水平边贴地外伸。",
    [tid for tid, _, _ in BRACES],
    highlight=["tw0_s", "tw0_e"],
    tip="双边吸合的斜撑锁死塔身 —— 折返赛道反复开撞也推不倒。",
)
b.step(
    "第二层墙 + 发球台: 四片蓝色方板骑上墙顶, 一片黄色方板盖住 z=2。",
    ["tw1_s", "tw1_w", "tw1_n", "tw1_e", "deck_0"],
    highlight=["tw0_s", "tw0_e"],
    tip="两层墙环够高 —— D2 弹珠从 z=2 出发, 不必再往上叠。",
)
b.step(
    "发球台挡珠: 三片红三角围住台沿 (东缘留口), 弹珠只能向东滑出。",
    ["drail_w", "drail_n", "drail_s"],
    highlight=["deck_0"],
    tip="东缘空着 —— 那是首段折返坡道的唯一出珠口。",
)
b.step(
    "首段下坡 (整段成组): 立桥墩, 橙色坡道顶边吸发球台东缘, 两片青色直角三角"
    "拼成折返台 A 压住墩顶与坡尾, 南/北各挂一片紫色斜撑锁墩身。",
    ["pier_a", "ramp_e", "land_a_lo", "land_a_hi", "brace_a_s", "brace_a_n"],
    highlight=["deck_0", "tw1_e"],
    tip="坡道-桥墩-折返台三件互吸 —— 双斜撑给台面第二条支撑路径。",
)
b.step(
    "折返台 A 挡珠: 北缘与东缘各一片红三角, 逼弹珠折返向西。",
    ["rail_a_n", "rail_a_e"],
    highlight=["land_a_lo", "land_a_hi"],
    tip="弹珠从西边上台、向东缘拐弯 —— 第一个 180° 折返就位。",
)
b.step(
    "第二段折返坡道: 橙色坡道从折返台 A 东缘下探到 z=0, 两片青色直角三角"
    "拼成折返台 B (东移一格避开塔身), 坡尾与台面整边互吸。",
    ["ramp_w", "land_b_lo", "land_b_hi"],
    highlight=["land_a_hi", "rail_a_e"],
    tip="这一跳弹珠向西冲 —— 折返台 B 直接落地, 听落台声比首段更响。",
)
b.step(
    "折返台 B 挡珠: 北缘与东缘各一片红三角, 逼弹珠二次掉头向东冲线。",
    ["rail_b_n", "rail_b_e"],
    highlight=["land_b_lo", "land_b_hi"],
    tip="第二个 180° 折返 —— 弹珠现在朝接珠池狂奔。",
)
b.step(
    "铺冲线短轨与池底: 一片黄色方板连折返台, 两片青色方板沿东向铺开接珠池。",
    ["track_0", "pool_0", "pool_1"],
    highlight=["land_b_hi", "ramp_w"],
    tip="短轨与池底整边互吸 —— 弹珠落地不弹跳、直接滚进池子。",
)
b.step(
    "立池壁收尾: 南/西/东三面矮墙围合 —— 折返坡道滚珠塔完工, 放珠开滑!",
    ["pool_s", "pool_w", "pool_e"],
    highlight=["pool_0"],
    tip="东出 → 西折 → 东冲 —— 实物跑珠听两声折返才算验收!",
)

model = b.finalize(
    model_id="switchback_ramp_01",
    name="折返坡道滚珠塔",
    name_en="Switchback Ramp 01",
    description=(
        "滚珠乐园 D2 折返塔: 两层发球台向东甩出首段 30 度坡道, 弹珠在"
        "两片直角三角拼成的折返台上 180° 掉头, 沿第二段坡道折返向西, "
        "再经第二块折返台二次掉头冲进接珠池; 招牌是 T08 滚珠轨道 + T14 "
        "直角三角折返台 (≥10 片), 与双轨绕塔/单塔螺旋动线拓扑均不同, "
        "全部 CORE-9, 实物跑珠即可验证。"
    ),
    difficulty=2,
    tags=["滚珠", "轨道", "折返", "滚珠乐园", "直角三角"],
    min_pieces=32,
    min_steps=10,
    series="marble_run",
)

meta = model["content_meta"]
meta["technique_tags"] = {
    "primary": "T08_marble_run",
    "secondary": ["T14_diagonal_bracing"],
}
meta["signature_statement"] = (
    "两片直角三角拼成的折返台让弹珠在塔旁连续两次 180° 掉头。"
)
meta["structural_signature"]["silhouette_class"] = "switchback_tower"
meta["structural_signature"]["height_layers"] = 3

out = Path(__file__).resolve().parent.parent / "data" / "models" / "switchback_ramp_01.json"
out.write_text(json.dumps(model, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
