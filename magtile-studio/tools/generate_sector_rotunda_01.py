#!/usr/bin/env python3
"""生成模型 data/models/sector_rotunda_01.json (四象扇心圆殿)。

内容批 P 模型 9/10 (P9) 全新重写: 建筑地标 D3 —— 全库扇形片型的
结构主角示范: 四片扇形在地面拼成一个真正的正圆殿底 (每片四分之一
圆, 半径边两两互吸), 四道十字风车墙骑在圆盘拼缝上升起, 顶上再用
四片扇形合拢成圆形殿顶 —— 圆底 + 圆顶都由扇形合圆而成, 而不是
沿直线排一排点缀。四座切向门屋从十字墙端头风车状展开, 每座门屋
外侧再贴一片竖立扇形当四分之一圆的扇面撑 (第三种扇形用法), 外圈
12 片广场砖合成回字环廊, 四角石柱与南入口甬道收束全局。

结构总览 (世界单位: 1.0 = 正方形磁力片边长, 圆心在 (3,3)):
  - 圆殿底盘: 四片扇形合圆 (z=0)                                4 片
  - 十字风车墙: 四片方墙骑圆盘拼缝 (z 0..1)                     4 片
  - 圆形殿顶: 四片扇形合圆 (z=1) + 顶缝四片三角冠饰              8 片
  - 四座切向门屋: 方墙 + 顶上三角檐饰 (风车状展开)               8 片
  - 四片竖立扇面撑: 底半径边吸广场砖、竖半径边吸门屋竖缝         4 片
  - 回字环廊: 12 片广场砖 + 四角石柱 (方墙 + 三角柱冠)          20 片
  - 南入口甬道: 2 片步道砖 + 2 片三角花饰                        4 片
  合计 52 片, 13 个教程步骤, 3 种磁力片形状 (含扩展扇形 12 片)。

物理规则要点 (validate 常规 + strict 双档零警告):
  - 扇形只有两条半径边可吸: 合圆时每片的两条半径边分别与相邻
    扇形互吸, 圆盘四条拼缝又各托一道风车墙 (墙脚同时吸两片扇形);
  - 殿顶扇形的两条半径边分别搁在两道风车墙顶, 同时与相邻顶扇
    互吸 —— 剪断任一条拼缝, 力都能沿圆顶绕行 (环状冗余);
  - 门屋竖缝吸风车墙端头竖边、墙脚吸广场砖 —— 圆殿与外环由
    四座门屋连成单一连通组;
  - 全程最高点 1.87 (冠饰尖), 不触发 R8 高层结构条款。

用法: python3 tools/generate_sector_rotunda_01.py  (在 magtile-studio 目录下运行)
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from magtile_gen import ModelBuilder  # noqa: E402

b = ModelBuilder()

CX, CY = 3.0, 3.0   # 圆心

DISC = "gray"       # 圆殿底盘扇形
WALL = "clear"      # 十字风车墙
DOME = "blue"       # 圆形殿顶扇形
CREST = "yellow"    # 冠饰 / 檐饰 / 柱冠
GATE = "green"      # 切向门屋
FAN = "orange"      # 竖立扇面撑
PLAZA_A = "cyan"    # 广场砖 (浅)
PLAZA_B = "gray"    # 广场砖 (深)
PILLAR = "clear"    # 四角石柱
PATH = "yellow"     # 入口甬道
FLOWER = "red"      # 甬道花饰

# 四个象限的扇形: (id 后缀, edge0 方向, 面内提示方向)
QUADRANTS = [
    ("ne", (1.0, 0.0), (0.0, 1.0)),
    ("nw", (0.0, 1.0), (-1.0, 0.0)),
    ("sw", (-1.0, 0.0), (0.0, -1.0)),
    ("se", (0.0, -1.0), (1.0, 0.0)),
]


def disc(prefix, z, color):
    """四片扇形合圆: 每片 edge0 沿一条轴向半径, 弧面扫过一个象限。"""
    ids = []
    for name, d, hint in QUADRANTS:
        tid = f"{prefix}_{name}"
        b.place_edge(
            tid, "sector", 0,
            (CX, CY, z), (CX + d[0], CY + d[1], z),
            (hint[0], hint[1], 0.0), color,
        )
        ids.append(tid)
    return ids


# =================================================================
# 1. 圆殿底盘: 四片扇形在 z=0 合圆
# =================================================================
floor_ids = disc("disc", 0.0, DISC)

# =================================================================
# 2. 十字风车墙: 四片方墙骑在圆盘的四条轴向拼缝上
# =================================================================
b.wall_ns("cw_e", 3, 3.0, 0, WALL)   # 东缝: x [3,4], y=3
b.wall_ew("cw_n", 3.0, 3, 0, WALL)   # 北缝: y [3,4], x=3
b.wall_ns("cw_w", 2, 3.0, 0, WALL)   # 西缝: x [2,3], y=3
b.wall_ew("cw_s", 3.0, 2, 0, WALL)   # 南缝: y [2,3], x=3
CROSS = ["cw_e", "cw_n", "cw_w", "cw_s"]

# =================================================================
# 3. 圆形殿顶: 四片扇形在 z=1 合圆 + 顶缝四片三角冠饰
# =================================================================
dome_ids = disc("dome", 1.0, DOME)
b.crest_ns("crown_e", 3, 3.0, 1.0, CREST)
b.crest_ew("crown_n", 3.0, 3, 1.0, CREST)
b.crest_ns("crown_w", 2, 3.0, 1.0, CREST)
b.crest_ew("crown_s", 3.0, 2, 1.0, CREST)
CROWN = ["crown_e", "crown_n", "crown_w", "crown_s"]

# =================================================================
# 4. 四座切向门屋: 从十字墙端头风车状展开
# =================================================================
b.wall_ew("gate_e", 4.0, 3, 0, GATE)   # 东端头: 面 x=4, y [3,4]
b.wall_ns("gate_n", 2, 4.0, 0, GATE)   # 北端头: 面 y=4, x [2,3]
b.wall_ew("gate_w", 2.0, 2, 0, GATE)   # 西端头: 面 x=2, y [2,3]
b.wall_ns("gate_s", 3, 2.0, 0, GATE)   # 南端头: 面 y=2, x [3,4]
GATES = ["gate_e", "gate_n", "gate_w", "gate_s"]

b.crest_ew("gc_e", 4.0, 3, 1.0, CREST)
b.crest_ns("gc_n", 2, 4.0, 1.0, CREST)
b.crest_ew("gc_w", 2.0, 2, 1.0, CREST)
b.crest_ns("gc_s", 3, 2.0, 1.0, CREST)
GATE_CRESTS = ["gc_e", "gc_n", "gc_w", "gc_s"]

# =================================================================
# 5. 回字环廊: 12 片广场砖 (从东门屋脚起顺时针合环)
# =================================================================
RING_CELLS = [
    (4, 3), (4, 4), (3, 4), (2, 4), (1, 4), (1, 3),
    (1, 2), (1, 1), (2, 1), (3, 1), (4, 1), (4, 2),
]
ring_ids = []
for i, (x, y) in enumerate(RING_CELLS):
    tid = f"ring_{x}{y}"
    b.flat(tid, x, y, 0.0, PLAZA_A if i % 2 else PLAZA_B)
    ring_ids.append(tid)

# =================================================================
# 6. 四片竖立扇面撑: 底半径边吸广场砖、竖半径边吸门屋外竖缝
# =================================================================
FANS = [
    ("fan_e", (4.0, 4.0), (4.0, 5.0)),   # 面 x=4, 吸 gate_e 北竖边
    ("fan_n", (2.0, 4.0), (1.0, 4.0)),   # 面 y=4, 吸 gate_n 西竖边
    ("fan_w", (2.0, 2.0), (2.0, 1.0)),   # 面 x=2, 吸 gate_w 南竖边
    ("fan_s", (4.0, 2.0), (5.0, 2.0)),   # 面 y=2, 吸 gate_s 东竖边
]
for tid, p0, p1 in FANS:
    b.place_edge(tid, "sector", 0,
                 (p0[0], p0[1], 0.0), (p1[0], p1[1], 0.0),
                 (0.0, 0.0, 1.0), FAN)

# =================================================================
# 7. 四角石柱 (方墙 + 三角柱冠) + 南入口甬道
# =================================================================
b.wall_ew("pil_sw", 1.0, 1, 0, PILLAR)
b.crest_ew("pc_sw", 1.0, 1, 1.0, CREST)
b.wall_ew("pil_se", 5.0, 1, 0, PILLAR)
b.crest_ew("pc_se", 5.0, 1, 1.0, CREST)
b.wall_ew("pil_nw", 1.0, 4, 0, PILLAR)
b.crest_ew("pc_nw", 1.0, 4, 1.0, CREST)
b.wall_ew("pil_ne", 5.0, 4, 0, PILLAR)
b.crest_ew("pc_ne", 5.0, 4, 1.0, CREST)

b.flat("path_w", 2, 0, 0.0, PATH)
b.flat("path_e", 3, 0, 0.0, PATH)
b.crest_ns("flw_w", 2, 0.0, 0.0, FLOWER)
b.crest_ns("flw_e", 3, 0.0, 0.0, FLOWER)

# =================================================================
# 教程步骤 (13 步)
# =================================================================
b.step(
    "扇形合圆铺殿底: 四片灰色扇形每片管一个象限, 半径边两两互吸拼成正圆。",
    floor_ids,
    tip="扇形只有两条半径边带磁 —— 四片合圆后每条拼缝都是双片互吸。",
)
b.step(
    "立十字风车墙: 四片透明方墙骑在圆盘的四条轴向拼缝上, 在圆心咬成十字。",
    CROSS,
    highlight=["disc_ne"],
    tip="墙脚一条边同时吸住两片扇形 —— 圆盘从此再也散不了。",
)
b.step(
    "扇形合圆盖殿顶: 四片蓝色扇形搁上墙顶再度合圆, 半径边吸墙顶又互吸。",
    dome_ids,
    highlight=["cw_e", "cw_n"],
    tip="剪断任何一条顶缝, 力还能沿圆顶绕行 —— 这就是合圆的环状冗余。",
)
b.step(
    "装顶缝冠饰: 四片金色三角骑在殿顶拼缝上, 圆顶开出四瓣金冠。",
    CROWN,
    highlight=["dome_ne"],
    tip="冠饰底边与顶缝共线 —— 一片吸三家 (两片顶扇加一道墙)。",
)
b.step(
    "展开切向门屋: 四片绿色方墙从十字墙端头风车状转出 90 度, 竖缝互咬。",
    GATES,
    highlight=["cw_e"],
    tip="门屋竖边吸风车墙端头竖边 —— 圆殿即将由它们连向外环。",
)
b.step(
    "铺回字环廊 (东北半环): 六片广场砖从东门屋脚起逆时针排到西北角。",
    ring_ids[:6],
    highlight=["gate_e"],
    tip="首块砖的西缘正咬住东门屋墙脚 —— 环廊与圆殿从这里接通。",
)
b.step(
    "铺回字环廊 (西南半环): 再六片合拢成回字环, 尾块咬回东门屋南侧。",
    ring_ids[6:],
    highlight=["ring_14"],
    tip="十二片合成闭环 —— 环廊自身也是一圈结构冗余。",
)
b.step(
    "装门屋檐饰: 四片金色三角骑上门屋墙顶, 四座门屋有了屋脊。",
    GATE_CRESTS,
    highlight=["gate_n"],
    tip="檐饰底边整边吸墙顶 —— 重心正压墙线, 稳如泰山。",
)
b.step(
    "贴竖立扇面撑: 四片橙色扇形立在门屋外侧, 底半径边吸广场砖、竖半径边吸门屋竖缝。",
    [tid for tid, _, _ in FANS],
    highlight=["gate_e", "ring_44"],
    tip="第三种扇形用法 —— 四分之一圆的扇面撑, 弧线从地面一直卷到墙顶。",
)
b.step(
    "立四角石柱: 四片透明方墙站上环廊四角砖的外缘。",
    ["pil_sw", "pil_se", "pil_nw", "pil_ne"],
    highlight=["ring_11"],
    tip="柱脚整边吸角砖边线 —— 四角一立, 广场的轮廓就画完了。",
)
b.step(
    "戴三角柱冠: 四片金色三角骑上柱顶, 与殿顶金冠遥相呼应。",
    ["pc_sw", "pc_se", "pc_nw", "pc_ne"],
    highlight=["pil_sw"],
    tip="柱冠重心正压柱顶铰链线 —— 力矩为零的收笔。",
)
b.step(
    "铺南入口甬道: 两片金色步道砖接在南环廊外侧。",
    ["path_w", "path_e"],
    highlight=["ring_21", "ring_31"],
    tip="甬道北缘与环廊拼缝共线整边互吸 —— 从这里正对南门屋进殿。",
)
b.step(
    "栽甬道花饰: 两片红三角站上步道外沿 —— 四象扇心圆殿落成!",
    ["flw_w", "flw_e"],
    highlight=["path_w"],
    tip="十二片扇形三种用法: 合圆殿底、合圆殿顶、竖立扇面撑 —— 入库前逐一实物复核。",
)

model = b.finalize(
    model_id="sector_rotunda_01",
    name="四象扇心圆殿",
    name_en="Sector Rotunda 01",
    description=(
        "建筑地标 D3 扇形示范: 四片扇形半径边两两互吸, 在地面合成正圆"
        "殿底; 十字风车墙骑缝升起, 顶上四片扇形再度合圆成殿顶, 拼缝"
        "四瓣金冠收顶; 四座切向门屋风车状展开, 外侧各贴一片竖立扇形"
        "扇面撑, 12 片广场砖合成回字环廊, 四角石柱与南入口甬道收束"
        "全局 —— 12 片扇形三种结构用法 (合圆底 / 合圆顶 / 竖撑), "
        "扇形是圆殿的结构主角而非点缀。"
    ),
    difficulty=3,
    tags=["建筑地标", "圆殿", "扇形", "风车墙", "环廊"],
    min_pieces=52,
    min_steps=13,
    series="landmark_architecture",
)

meta = model["content_meta"]
meta["technique_tags"] = {
    "primary": "T01_box_frame",
    "secondary": ["T11_mirror_symmetry", "T14_diagonal_bracing"],
}
meta["signature_statement"] = (
    "四片扇形合圆的殿底与殿顶夹住十字风车墙 —— 圆由扇形拼出, 不靠近似。"
)
meta["structural_signature"]["silhouette_class"] = "pinwheel_rotunda"
meta["structural_signature"]["height_layers"] = 2

out = Path(__file__).resolve().parent.parent / "data" / "models" / "sector_rotunda_01.json"
out.write_text(json.dumps(model, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
