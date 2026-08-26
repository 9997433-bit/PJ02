#!/usr/bin/env python3
"""生成模型 data/models/marble_splitter_01.json (双轨分流滚珠台)。

内容批 P 模型 6/10 (P6): 滚珠乐园 D2, 主打片型 door_frame —— 重写版。
招牌是"门框拱廊塔 + 四柱门亭分流枢纽"的 Y 形分流动线: 发射塔首层由
四片橙色门框方立成拱廊 (T17 负空间), 弹珠自 z=2 发球台向东滑下首段
30 度坡道, 落上立在四柱门亭上的分流枢纽 (z=1), 撞上东端粉色窗格铃板
后从南/北两道门框门洞二选一穿出, 各沿一段坡道落地、穿过终点门框,
滚进分色接珠池。与 marble_cascade_01 (三级退台瀑布) / ball_run_tower_01
(双轨绕塔) / switchback_ramp_01 (折返塔) 的动线拓扑均不同。

结构总览 (世界单位: 1.0 = 正方形磁力片边长, 弹珠先向东再分南北):
  - 发射塔 (x [0,1], y [0,1]): 地台 + 门框拱廊首层 x4 + 方板二层 x4 +
    发球台 + 台沿挡珠 x3                                             13 片
  - 四柱门亭枢纽: 西桥墩 + 门框柱 x3 (东/南/北) + 枢纽台面             5 片
  - 首段坡道 + 分流室: 坡道 + 南北分流门框 x2 + 窗格铃板 + 顶饰        5 片
  - 北轨: 坡道 + 落地跑道 + 道沿挡珠 x2 + 终点门框 + 接珠池 + 池壁 x3  9 片
  - 南轨 (镜像): 同北轨                                               9 片
  合计 41 片, 9 个教程步骤; 门框方 x11, 全部片型在 CORE-9 之内。

物理规则要点 (validate strict 零警告):
  - 每段坡道顶边整边吸上一级台面沿口, 坡尾由桥墩/门框柱顶边或落地
    跑道沿边接住;
  - 枢纽台面四边均有支撑: 西桥墩 + 东/南/北三根门框柱, 分流门与铃板
    立在有柱的沿口正上方, 传力路径连续;
  - 门框方按实心墙校验, 门洞负空间 (T17) 是弹珠实际穿行的通道;
  - 全塔最高点为塔顶挡珠三角尖 z≈2.87, 低于 R8 红线 4.0。

用法: python3 tools/generate_marble_splitter_01.py  (在 magtile-studio 目录下运行)
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from magtile_gen import SQ3, ModelBuilder  # noqa: E402

b = ModelBuilder()

BASE = "gray"
GATE = "orange"     # 门框方 (拱廊 / 门亭柱 / 分流门 / 终点门, T17)
TOWER = "blue"
DECK = "yellow"
RAIL = "red"
RAMP = "orange"
PIER = "gray"
BELL = "pink"       # 窗格铃板 (弹珠分流前撞响)
POOL_N = "cyan"
POOL_S = "green"

XH = 1 + SQ3        # 枢纽台面西缘 x = 首段坡道坡尾 2.732051
XE = XH + 1         # 枢纽台面东缘 x
YN = 1 + SQ3        # 北轨落地跑道南缘 y = 北坡道坡尾
YS = -1 - SQ3       # 南轨落地跑道南缘 y (跑道北缘 -SQ3 = 南坡道坡尾)


def gate_ns(tid, x0, y, z0):
    """南北朝向门框方立墙 (平面 y=y), 覆盖 x [x0,x0+1], z [z0,z0+1]。"""
    b.add(tid, "door_frame", (x0 + 0.5, y, z0 + 0.5), (90, 0, 0), GATE)


def gate_ew(tid, x, y0, z0):
    """东西朝向门框方立墙 (平面 x=x), 覆盖 y [y0,y0+1], z [z0,z0+1]。"""
    b.add(tid, "door_frame", (x, y0 + 0.5, z0 + 0.5), (90, 0, 90), GATE)


# =================================================================
# 1. 发射塔 (x [0,1], y [0,1]): 地台 + 门框拱廊首层 + 方板二层 + 发球台
# =================================================================
b.flat("base_0", 0, 0, 0.0, BASE)
gate_ns("arc_s", 0, 0.0, 0)
gate_ns("arc_n", 0, 1.0, 0)
gate_ew("arc_w", 0.0, 0, 0)
gate_ew("arc_e", 1.0, 0, 0)
b.wall_ns("tw_s", 0, 0.0, 1, TOWER)
b.wall_ns("tw_n", 0, 1.0, 1, TOWER)
b.wall_ew("tw_w", 0.0, 0, 1, TOWER)
b.wall_ew("tw_e", 1.0, 0, 1, TOWER)
b.flat("deck_0", 0, 0, 2.0, DECK)
b.crest_ew("drail_w", 0.0, 0, 2.0, RAIL)
b.crest_ns("drail_s", 0, 0.0, 2.0, RAIL)
b.crest_ns("drail_n", 0, 1.0, 2.0, RAIL)

# =================================================================
# 2. 四柱门亭枢纽: 西桥墩 + 三根门框柱 (东/南/北) + 枢纽台面 (z=1)
# =================================================================
b.wall_ew("pier_w", XH, 0, 0, PIER)
gate_ns("pil_s", XH, 0.0, 0)
gate_ew("pil_e", XE, 0, 0)
gate_ns("pil_n", XH, 1.0, 0)
b.flat("hub", XH, 0, 1.0, DECK)

# =================================================================
# 3. 首段坡道 (z2->z1) + 分流室: 南北分流门 + 窗格铃板 + 顶饰
# =================================================================
b.ramp("ramp_e", "+x", 1.0, 0, 2.0, RAMP)
gate_ns("gate_s", XH, 0.0, 1)
gate_ns("gate_n", XH, 1.0, 1)
b.add("bell_e", "window_square", (XE, 0.5, 1.5), (90, 0, 90), BELL)
b.crest_ew("crown_e", XE, 0, 2.0, RAIL)

# =================================================================
# 4. 北轨 (z1->z0): 坡道 + 落地跑道 + 道沿挡珠 + 终点门框 + 接珠池
# =================================================================
b.ramp("ramp_n", "+y", 1.0, XH, 1.0, RAMP)
b.flat("land_n", XH, YN, 0.0, DECK)
b.crest_ew("lrail_nw", XH, YN, 0.0, RAIL)
b.crest_ew("lrail_ne", XE, YN, 0.0, RAIL)
gate_ns("fin_n", XH, YN + 1, 0)
b.flat("pool_n", XH, YN + 1, 0.0, POOL_N)
b.wall_ew("pw_n_w", XH, YN + 1, 0, POOL_N)
b.wall_ew("pw_n_e", XE, YN + 1, 0, POOL_N)
b.wall_ns("pw_n_n", XH, YN + 2, 0, POOL_N)

# =================================================================
# 5. 南轨 (镜像): 坡道 + 落地跑道 + 道沿挡珠 + 终点门框 + 接珠池
# =================================================================
b.ramp("ramp_s", "-y", 0.0, XH, 1.0, RAMP)
b.flat("land_s", XH, YS, 0.0, DECK)
b.crest_ew("lrail_sw", XH, YS, 0.0, RAIL)
b.crest_ew("lrail_se", XE, YS, 0.0, RAIL)
gate_ns("fin_s", XH, YS, 0)
b.flat("pool_s", XH, YS - 1, 0.0, POOL_S)
b.wall_ew("pw_s_w", XH, YS - 1, 0, POOL_S)
b.wall_ew("pw_s_e", XE, YS - 1, 0, POOL_S)
b.wall_ns("pw_s_s", XH, YS - 1, 0, POOL_S)

# =================================================================
# 教程步骤 (9 步)
# =================================================================
b.step(
    "铺塔基并立门框拱廊: 一片灰色方板打底, 四片橙色门框方合围首层 —— "
    "四面门洞就是本作的招牌。",
    ["base_0", "arc_s", "arc_w", "arc_n", "arc_e"],
    tip="门框方外框与正方形完全一样, 四片下边整边吸住地台即可站稳。",
)
b.step(
    "方板二层: 四片蓝色方板骑上拱廊墙顶, 上下边完整贴合。",
    ["tw_s", "tw_w", "tw_n", "tw_e"],
    highlight=["arc_s", "arc_e"],
    tip="两层塔身够高 —— D2 弹珠从 z=2 出发, 不必再往上叠。",
)
b.step(
    "盖发球台: 一片黄色方板压住二层墙顶, 三片红色挡珠三角围住台沿 "
    "(东缘留口)。",
    ["deck_0", "drail_w", "drail_s", "drail_n"],
    highlight=["tw_s", "tw_e"],
    tip="东缘空着 —— 那是弹珠冲向分流枢纽的唯一出珠口。",
)
b.step(
    "四柱门亭与首段坡道 (整段成组): 塔东侧一片灰色桥墩居西, 三片橙色"
    "门框柱站南/东/北, 枢纽台面压住四根柱顶, 橙色坡道顶边吸出珠口、"
    "坡尾搭上桥墩顶。",
    ["pier_w", "pil_s", "pil_e", "pil_n", "hub", "ramp_e"],
    highlight=["deck_0", "arc_e"],
    tip="台面四边都有柱顶整边接住, 坡道把塔与门亭连成一体 —— "
        "分流枢纽是全场受撞最多的地方。",
)
b.step(
    "布置分流室: 南北各立一道橙色分流门框, 东端粉色窗格铃板封口, "
    "顶饰三角压住铃板上沿。",
    ["gate_s", "gate_n", "bell_e", "crown_e"],
    highlight=["hub", "ramp_e"],
    tip="弹珠撞铃板弹回后从南/北门洞 (T17 负空间) 二选一穿出 —— 分流全靠它!",
)
b.step(
    "北轨下坡: 橙色坡道从北分流门下探到地面, 落地跑道接住坡尾, "
    "东西道沿各立一片红色挡珠三角。",
    ["ramp_n", "land_n", "lrail_nw", "lrail_ne"],
    highlight=["gate_n", "hub"],
    tip="坡尾与跑道南缘整边互吸 —— 弹珠穿过门洞就一路贴地向北。",
)
b.step(
    "北轨终点: 橙色终点门框立在跑道尽头, 青色池底与三面池壁围住接珠池。",
    ["fin_n", "pool_n", "pw_n_w", "pw_n_e", "pw_n_n"],
    highlight=["land_n"],
    tip="弹珠穿过终点门洞落池 —— 青色代表北轨得分!",
)
b.step(
    "南轨下坡 (镜像): 坡道从南分流门下探, 落地跑道与两片道沿挡珠对称安装。",
    ["ramp_s", "land_s", "lrail_sw", "lrail_se"],
    highlight=["gate_s", "hub"],
    tip="与北轨完全镜像 —— 对照着装, 一次就位。",
)
b.step(
    "南轨终点收尾: 终点门框 + 绿色池底与三面池壁 —— 双轨分流滚珠台完工, "
    "放珠开跑!",
    ["fin_s", "pool_s", "pw_s_w", "pw_s_e", "pw_s_s"],
    highlight=["land_s"],
    tip="轮流放珠数进池次数 —— 铃板响一声、落池哪一边, 实物跑珠才算验收!",
)

model = b.finalize(
    model_id="marble_splitter_01",
    name="双轨分流滚珠台",
    name_en="Marble Splitter 01",
    description=(
        "滚珠乐园 D2 门框方主打示范: 首层门框拱廊塔从 z=2 发球, 弹珠沿"
        "首段 30 度坡道落上四柱门亭分流枢纽, 撞响粉色窗格铃板后从南/北"
        "两道门框门洞 (T17 负空间) 二选一穿出, 各沿坡道落地、穿过终点"
        "门框滚进分色接珠池; 门框方 x11 全程既是结构柱又是弹珠通道, "
        "全部 CORE-9, 实物跑珠即可验证分流。"
    ),
    difficulty=2,
    tags=["滚珠", "轨道", "分流", "滚珠乐园", "门框"],
    min_pieces=32,
    min_steps=9,
    series="marble_run",
)

meta = model["content_meta"]
meta["technique_tags"] = {
    "primary": "T08_marble_run",
    "secondary": ["T17_negative_space", "T11_mirror_symmetry"],
}
meta["signature_statement"] = (
    "门框方既当结构柱又当弹珠通道: 四柱门亭托起分流枢纽, "
    "弹珠撞铃板后从南北门洞二选一穿出, 镜像双轨由同一座拱廊塔发球。"
)
meta["structural_signature"]["silhouette_class"] = "gate_pavilion_splitter"
meta["structural_signature"]["height_layers"] = 3

out = Path(__file__).resolve().parent.parent / "data" / "models" / "marble_splitter_01.json"
out.write_text(json.dumps(model, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
