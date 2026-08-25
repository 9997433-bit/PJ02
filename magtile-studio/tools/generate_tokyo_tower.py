#!/usr/bin/env python3
"""生成模型 data/models/tokyo_tower_01.json (东京塔)。

第三批模型: 世界地标主题 —— 与埃菲尔铁塔的四柱直腿完全不同:
东京塔的裙座是 4 片梯形从 2x2 底口对倾收分到 1x1 (无压顶洞口
上盖压顶板), 塔身骑在压顶板上直上两级; 主展望台四面各外挑一片
观景板, 特别展望台再收一级, 塔尖以等腰四坡锥收顶 —— 红白涂装。
塔前红色牌楼门 (鸟居意象)、纪念品商店、绿篱与园灯组成塔下公园。

结构总览 (世界单位: 1.0 = 正方形磁力片边长):
  - 塔基环道 (4 长方形 + 4 角板) + 外圈广场 16                    24 片
  - 梯形裙座 4 + 压顶板 1                                          5 片
  - 塔身两级 (每级 4 墙) + 主展望台 (楼板 + 4 观景板)             13 片
  - 特别展望台一级 (4 墙 + 顶板) + 等腰四坡塔尖 4                  9 片
  - 牌楼门 (双柱 x2 + 门楣 + 双尖) + 纪念品商店 (4 墙 + 顶)       12 片
  - 绿篱 4 + 园灯 2                                                6 片
  合计 69 片, 17 个教程步骤, 5 种磁力片形状。

物理要点 (通过 R1~R8 全部校验):
  - 裙座梯形下底 (长 2) 整边吸环道长方形长边, 上底围成 1x1 由
    压顶板封住 —— 塔身荷载经四条斜面分散到环道;
  - 主展望台观景板单片外挑 0.5 力臂 (弯矩 15 < 20), 且每片同时
    吸楼板边与上级塔墙底边, 剪断一条铰链线仍有第二条路径;
  - 塔尖四片等腰斜棱两两互吸自锁成环。

坐标约定与 C++ 端一致: 旋转为欧拉角 (度), R = Rz * Ry * Rx。
用法: python3 tools/generate_tokyo_tower.py  (在 magtile-studio 目录下运行)
"""

from magtile_gen import EQ_APEX, ModelBuilder

mb = ModelBuilder()

RIM = EQ_APEX                  # 裙座压顶高度 0.707107
L1 = RIM + 1.0                 # 塔身一级顶 1.707107
DECK = RIM + 2.0               # 主展望台 2.707107
TOP = DECK + 1.0               # 特别展望台顶 3.707107

TOWER = "red"      # 塔身国际橙红
WHITE = "clear"    # 白色涂装段
PLAZA = "green"
RING = "gray"

# =================================================================
# 1. 塔基环道 (围绕裙座底口 [2,4]x[2,4]) + 外圈广场
# =================================================================
mb.flat_rect("rg_s", 2, 1, 0.0, RING)              # [2,4]x[1,2]
mb.flat_rect("rg_n", 2, 4, 0.0, RING)              # [2,4]x[4,5]
mb.flat_rect("rg_w", 1, 2, 0.0, RING, axis="y")    # [1,2]x[2,4]
mb.flat_rect("rg_e", 4, 2, 0.0, RING, axis="y")    # [4,5]x[2,4]
mb.flat("rg_sw", 1, 1, 0.0, RING)
mb.flat("rg_se", 4, 1, 0.0, RING)
mb.flat("rg_nw", 1, 4, 0.0, RING)
mb.flat("rg_ne", 4, 4, 0.0, RING)
for i in range(4):
    mb.flat(f"pz_s{i}", 1 + i, 0, 0.0, PLAZA)      # 南排 [1,5]x[0,1]
for i in range(4):
    mb.flat(f"pz_n{i}", 1 + i, 5, 0.0, PLAZA)      # 北排 [1,5]x[5,6]
for j in range(4):
    mb.flat(f"pz_w{j}", 0, 1 + j, 0.0, PLAZA)      # 西列 [0,1]x[1,5]
for j in range(4):
    mb.flat(f"pz_e{j}", 5, 1 + j, 0.0, PLAZA)      # 东列 [5,6]x[1,5]

# =================================================================
# 2. 梯形裙座 (2x2 -> 1x1 收分) + 压顶板
# =================================================================
skirt_ids, skirt_cap = mb.hip_roof2("skirt", 2, 2, 0.0, TOWER,
                                    cap_color=RING)

# =================================================================
# 3. 塔身两级 ([2.5,3.5] 见方) + 主展望台
# =================================================================
for lv, (z0, col) in enumerate(((RIM, TOWER), (RIM + 1.0, WHITE))):
    mb.wall_ns(f"s{lv}_s", 2.5, 2.5, z0, col)
    mb.wall_ns(f"s{lv}_n", 2.5, 3.5, z0, col)
    mb.wall_ew(f"s{lv}_w", 2.5, 2.5, z0, col)
    mb.wall_ew(f"s{lv}_e", 3.5, 2.5, z0, col)
mb.flat("md_c", 2.5, 2.5, DECK, "yellow")          # 主展望台楼板
mb.flat("md_s", 2.5, 1.5, DECK, "yellow")          # 四面观景板
mb.flat("md_n", 2.5, 3.5, DECK, "yellow")
mb.flat("md_w", 1.5, 2.5, DECK, "yellow")
mb.flat("md_e", 3.5, 2.5, DECK, "yellow")

# =================================================================
# 4. 特别展望台 + 等腰四坡塔尖
# =================================================================
mb.wall_ns("t_s", 2.5, 2.5, DECK, TOWER)
mb.wall_ns("t_n", 2.5, 3.5, DECK, TOWER)
mb.wall_ew("t_w", 2.5, 2.5, DECK, TOWER)
mb.wall_ew("t_e", 3.5, 2.5, DECK, TOWER)
mb.flat("t_cap", 2.5, 2.5, TOP, RING)              # 特别展望台顶板
mb.hat4("spire", 2.5, 2.5, TOP, TOWER)             # 塔尖 (等腰四坡)

# =================================================================
# 5. 牌楼门 (平面 y=0) + 纪念品商店 ([0,1]x[2,3])
# =================================================================
mb.wall_ns("gt_w0", 1, 0.0, 0, TOWER)
mb.wall_ns("gt_w1", 1, 0.0, 1, TOWER)
mb.wall_ns("gt_e0", 4, 0.0, 0, TOWER)
mb.wall_ns("gt_e1", 4, 0.0, 1, TOWER)
mb.lintel_ns("gt_beam", 2, 0.0, 1, TOWER)          # 门楣 x [2,4], z [1,2]
mb.spire_ns("gt_tip_w", 1, 0.0, 2.0, "yellow")
mb.spire_ns("gt_tip_e", 4, 0.0, 2.0, "yellow")

mb.wall_ns("sh_s", 0, 2.0, 0, "orange")
mb.wall_ns("sh_n", 0, 3.0, 0, "orange")
mb.wall_ew("sh_w", 0.0, 2, 0, "orange")
mb.wall_ew("sh_e", 1.0, 2, 0, "orange")
mb.flat("sh_roof", 0, 2, 1.0, "orange")

# =================================================================
# 6. 绿篱 + 园灯
# =================================================================
mb.crest_ns("hg_nw", 1, 6.0, 0.0, PLAZA)
mb.crest_ns("hg_ne", 4, 6.0, 0.0, PLAZA)
mb.crest_ew("hg_e0", 6.0, 2, 0.0, PLAZA)
mb.crest_ew("hg_e1", 6.0, 4, 0.0, PLAZA)
mb.spire_ew("lamp_w", 0.0, 4, 0.0, "yellow")
mb.spire_ew("lamp_e", 6.0, 1, 0.0, "yellow")

# =================================================================
# 教程步骤 (17 步)
# =================================================================
mb.step(
    "塔基环道: 4 片灰色长方形围出 [2,4]x[2,4] 底口 —— 长边留给"
    "裙座梯形的下底。",
    ["rg_s", "rg_e", "rg_n", "rg_w"],
    tip="底口正中空着 —— 东京塔的裙座直接跨在环道上。",
)
mb.step(
    "环道角板: 4 片方板补齐四角, 环道成回字。",
    ["rg_sw", "rg_se", "rg_nw", "rg_ne"],
    highlight=["rg_s", "rg_w"],
)
mb.step(
    "广场南排: 塔前铺 4 片绿色园地。",
    ["pz_s0", "pz_s1", "pz_s2", "pz_s3"],
    highlight=["rg_sw", "rg_se"],
)
mb.step(
    "广场北排: 塔后再铺 4 片。",
    ["pz_n0", "pz_n1", "pz_n2", "pz_n3"],
    highlight=["rg_nw", "rg_ne"],
)
mb.step(
    "广场西列: 4 片园地沿西侧铺开。",
    ["pz_w0", "pz_w1", "pz_w2", "pz_w3"],
    highlight=["rg_sw", "rg_nw"],
)
mb.step(
    "广场东列: 4 片合拢, 塔下公园成形。",
    ["pz_e0", "pz_e1", "pz_e2", "pz_e3"],
    highlight=["rg_se", "rg_ne"],
)
mb.step(
    "梯形裙座: 4 片红色梯形下底整边吸环道长边, 对倾收分到 1x1 "
    "洞口, 腰边两两互吸 —— 东京塔标志性的喇叭裙脚。",
    ["skirt_s", "skirt_e", "skirt_n", "skirt_w"],
    highlight=["rg_s", "rg_e"],
    tip="按南-东-北-西顺序放, 每片腰边都能吸住前一片。",
)
mb.step(
    "裙座压顶: 灰色压顶板封住 1x1 洞口 (z=0.707) —— 塔身的基座。",
    [skirt_cap],
    highlight=["skirt_s", "skirt_n"],
)
mb.step(
    "塔身一级: 压顶板四缘立 4 面红色方墙。",
    ["s0_s", "s0_n", "s0_w", "s0_e"],
    highlight=[skirt_cap],
)
mb.step(
    "塔身二级: 白色涂装段再上一级 —— 红白相间开始显形。",
    ["s1_s", "s1_n", "s1_w", "s1_e"],
    highlight=["s0_s"],
)
mb.step(
    "主展望台: 楼板压墙顶, 四面各外挑 1 片黄色观景板 (力臂 0.5, "
    "弯矩 15 在预算内)。",
    ["md_c", "md_s", "md_n", "md_w", "md_e"],
    highlight=["s1_s", "s1_n"],
)
mb.step(
    "特别展望台: 楼板中央再围 4 面红墙 —— 每面墙底同时压楼板边"
    "与观景板内边, 给观景板补上第二条传力路径。",
    ["t_s", "t_n", "t_w", "t_e"],
    highlight=["md_c", "md_s"],
)
mb.step(
    "顶板与塔尖: 灰色顶板封口, 4 片等腰三角对锥合拢成塔尖 "
    "(尖顶 z=4.57), 斜棱两两互吸自锁。",
    ["t_cap", "spire_s", "spire_e", "spire_n", "spire_w"],
    highlight=["t_s", "t_n"],
)
mb.step(
    "牌楼门双柱: 塔前广场南沿立两条 2 层红柱, 门洞留在中间。",
    ["gt_w0", "gt_w1", "gt_e0", "gt_e1"],
    highlight=["pz_s0", "pz_s3"],
)
mb.step(
    "门楣与门尖: 红色长方形门楣横跨双柱 (竖直短边互吸), 柱顶"
    "各插 1 根黄色门尖 —— 塔前牌楼落成。",
    ["gt_beam", "gt_tip_w", "gt_tip_e"],
    highlight=["gt_w1", "gt_e1"],
)
mb.step(
    "纪念品商店: 广场西侧拼 1 间橙色小屋 (4 墙 + 顶)。",
    ["sh_s", "sh_n", "sh_w", "sh_e", "sh_roof"],
    highlight=["pz_w1"],
)
mb.step(
    "绿篱与园灯: 北沿与东沿立 4 片绿篱, 西北与东南各点 1 盏园灯 "
    "—— 华灯初上, 铁塔点亮。",
    ["hg_nw", "hg_ne", "hg_e0", "hg_e1", "lamp_w", "lamp_e"],
    highlight=["pz_n0", "pz_e3"],
)

mb.finalize(
    model_id="tokyo_tower_01",
    name="东京塔",
    name_en="Tokyo Tower 01",
    description=(
        "红白涂装的电波塔: 与四柱直腿的铁塔不同, 东京塔的裙座是 "
        "4 片梯形从 2x2 底口对倾收分到 1x1 再以压顶板封口 —— 塔身"
        "荷载经四条斜面分散到环道; 红白两级塔身直上, 主展望台四面"
        "各外挑一片观景板 (上级塔墙压住板内边, 双路径传力), 特别"
        "展望台再收一级, 等腰四坡塔尖自锁收顶。塔前红色牌楼门、"
        "纪念品商店、绿篱园灯围成塔下公园。"
    ),
    difficulty=3,
    tags=["东京塔", "世界地标", "电波塔", "梯形收分", "红白涂装"],
    min_pieces=65,
    min_steps=17,
)
