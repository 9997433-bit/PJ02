#!/usr/bin/env python3
"""生成模型 data/models/expansion_orb_01.json (四型合璧灯球坛)。

内容批 P 模型 10/10 (P10) 全新重写: 几何艺术 D4, 菱/梯/六/扇四种
扩展片型的合璧 showcase —— 与旧版测地球壳完全不同的结构路线:
一只八角剪影的"灯球"立在 3x3 展坛中央:

  - 下碗: 四片梯形窄边朝下反扣成倒置方台斗拱, 从 1x1 坛心
    外翻收出 2x2 灯球腰环 (梯形的承重用法, 不是屋顶配角);
  - 灯身: 三层长方形横板方鼓 (中层透明透光带), 四条竖角缝上
    12 片菱形逐层腰边互咬, 爬成四条菱形藤蔓角旗;
  - 上盖: 梯形四坡收顶 + 压顶方, 顶上四片扇形风车状竖立
    合成极冠 —— 扇形半径边一条吸压顶、一条悬出弧线;
  - 坛面: 四座六边形芯八角花圃 —— 六边形整边吸坛缘, 五片
    菱形花瓣沿自由边展开且相邻花瓣彼此互咬 (六边形 + 菱形
    的平面密铺用法, 花瓣还顺手咬住坛缘与灯柱脚线);
  - 四角灯柱: 方墙 + 三角柱冠收束广场轮廓。

结构总览 (世界单位: 1.0 = 正方形磁力片边长, 坛心在 (1.5,1.5)):
  - 展坛 3x3 + 四角灯柱 (墙 + 冠)                            17 片
  - 倒扣梯形下碗 (窄边吸坛心四边)                             4 片
  - 三层长方形方鼓 (4 x 3) + 12 片菱形角藤                   24 片
  - 梯形四坡上盖 + 压顶方 + 四片扇形极冠                      9 片
  - 四座菱六花圃 (六边形 x1 + 菱形花瓣 x5)                   24 片
  合计 78 片, 18 个教程步骤, 7 种磁力片形状 (扩展片型 48 片)。

物理规则要点 (validate 常规 + strict 双档零警告):
  - 倒扣梯形腰边两两互吸成环, 窄边整边吸坛心 —— 剪任一条缝
    力都沿环绕行; 方鼓横板下边与梯形宽边 2:2 等长整边贴合,
    转角短边互咬, 连接图环路极多, R8 高层告警不会触发;
  - 菱形角藤: 每片一条边整边吸鼓身竖角缝 (竖直铰链的重力力矩
    恒为零), 相邻两层菱形腰边再互咬 —— 藤蔓自锁;
  - 扇形极冠竖立在压顶边线上, 重心正压铰链线 (力矩为零),
    每片同时吸压顶方与坡面梯形上边 (双连接冗余);
  - 花圃六边形与菱形全部平贴地面, 自身接地不吃静力预算。

用法: python3 tools/generate_expansion_orb_01.py  (在 magtile-studio 目录下运行)
"""

import json
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from magtile_gen import EQ_APEX, ModelBuilder, world_vertices  # noqa: E402

b = ModelBuilder()

PLAZA_A = "gray"     # 展坛砖 (深)
PLAZA_B = "cyan"     # 展坛砖 (浅)
BOWL = "orange"      # 倒扣梯形下碗
DRUM_1 = "blue"      # 方鼓第一层
DRUM_2 = "clear"     # 方鼓第二层 (透明透光带)
DRUM_3 = "cyan"      # 方鼓第三层
VINE_A = "purple"    # 菱形角藤 (奇数层)
VINE_B = "pink"      # 菱形角藤 (偶数层)
ROOF = "orange"      # 梯形四坡上盖
CAP = "yellow"       # 压顶方
POLAR = "red"        # 扇形极冠
HEX_BED = "green"    # 花圃六边形芯
PETAL_A = "purple"   # 花圃菱形花瓣
PETAL_B = "pink"
POST = "clear"       # 四角灯柱
POST_CAP = "yellow"  # 灯柱三角冠

Z1 = EQ_APEX             # 腰环高 0.707107
Z_L = [Z1, Z1 + 1.0, Z1 + 2.0]   # 三层方鼓的层底高
Z_TOP = Z1 + 3.0         # 鼓顶 = 上盖坡脚
Z_CAP = Z_TOP + EQ_APEX  # 压顶高 4.414214
PC = (1.5, 1.5)          # 坛心 (花瓣展开方向的参照)

# =================================================================
# 1. 展坛 3x3 (坛心 (1,1) 即灯球底板)
# =================================================================
plinth_ids = []
for y in range(3):
    for x in range(3):
        tid = f"plinth_{x}{y}"
        b.flat(tid, x, y, 0.0, PLAZA_A if (x + y) % 2 else PLAZA_B)
        plinth_ids.append(tid)

# =================================================================
# 2. 倒扣梯形下碗: 窄边 (本地边 2) 朝下吸坛心四边, 外翻收出腰环
# =================================================================
BOWL_EDGES = {
    "s": ((2.0, 1.0, 0.0), (1.0, 1.0, 0.0), (0.0, -0.5, EQ_APEX)),
    "e": ((2.0, 2.0, 0.0), (2.0, 1.0, 0.0), (0.5, 0.0, EQ_APEX)),
    "n": ((1.0, 2.0, 0.0), (2.0, 2.0, 0.0), (0.0, 0.5, EQ_APEX)),
    "w": ((1.0, 1.0, 0.0), (1.0, 2.0, 0.0), (-0.5, 0.0, EQ_APEX)),
}
bowl_ids = []
for side, (w_from, w_to, hint) in BOWL_EDGES.items():
    tid = f"bowl_{side}"
    b.place_edge(tid, "trapezoid", 2, w_from, w_to, hint, BOWL)
    bowl_ids.append(tid)

# =================================================================
# 3. 三层长方形方鼓: 腰环 [0.5,2.5]^2 每面一片横板, 转角短边互咬
# =================================================================
def drum_level(level, z0, color):
    ids = [f"drum{level}_s", f"drum{level}_e", f"drum{level}_n", f"drum{level}_w"]
    b.lintel_ns(ids[0], 0.5, 0.5, z0, color)
    b.lintel_ew(ids[1], 2.5, 0.5, z0, color)
    b.lintel_ns(ids[2], 0.5, 2.5, z0, color)
    b.lintel_ew(ids[3], 0.5, 0.5, z0, color)
    return ids


drum1_ids = drum_level(1, Z_L[0], DRUM_1)
drum2_ids = drum_level(2, Z_L[1], DRUM_2)
drum3_ids = drum_level(3, Z_L[2], DRUM_3)

# =================================================================
# 4. 菱形角藤: 四条竖角缝 x 三层, 逐层腰边互咬
# =================================================================
CORNERS = {
    "se": ((2.5, 0.5), (0.707107, -0.707107)),
    "ne": ((2.5, 2.5), (0.707107, 0.707107)),
    "nw": ((0.5, 2.5), (-0.707107, 0.707107)),
    "sw": ((0.5, 0.5), (-0.707107, -0.707107)),
}
vine_ids = {1: [], 2: [], 3: []}
for cname, ((cx, cy), diag) in CORNERS.items():
    for level, z0 in enumerate(Z_L, start=1):
        tid = f"vine{level}_{cname}"
        b.place_edge(
            tid, "rhombus", 0,
            (cx, cy, z0), (cx, cy, z0 + 1.0),
            (diag[0], diag[1], 0.0),
            VINE_A if level % 2 else VINE_B,
        )
        vine_ids[level].append(tid)

# =================================================================
# 5. 梯形四坡上盖 + 压顶方 + 四片扇形极冠 (风车状竖立)
# =================================================================
roof_ids, cap_id = b.hip_roof2("roof", 0.5, 0.5, Z_TOP, ROOF, cap_color=CAP)

POLAR_EDGES = [
    ("polar_s", (1.0, 1.0), (2.0, 1.0)),
    ("polar_e", (2.0, 1.0), (2.0, 2.0)),
    ("polar_n", (2.0, 2.0), (1.0, 2.0)),
    ("polar_w", (1.0, 2.0), (1.0, 1.0)),
]
for tid, p0, p1 in POLAR_EDGES:
    b.place_edge(tid, "sector", 0,
                 (p0[0], p0[1], Z_CAP), (p1[0], p1[1], Z_CAP),
                 (0.0, 0.0, 1.0), POLAR)

# =================================================================
# 6. 四座菱六花圃: 六边形芯整边吸坛缘, 五片菱形花瓣沿自由边展开
#    (花瓣沿远离坛心的方向倾摆, 相邻花瓣彼此互咬且不压坛面)
# =================================================================
BEDS = {
    "e": ((3.0, 1.0, 0.0), (3.0, 2.0, 0.0), (1.0, 0.0)),
    "n": ((2.0, 3.0, 0.0), (1.0, 3.0, 0.0), (0.0, 1.0)),
    "w": ((0.0, 2.0, 0.0), (0.0, 1.0, 0.0), (-1.0, 0.0)),
    "s": ((1.0, 0.0, 0.0), (2.0, 0.0, 0.0), (0.0, -1.0)),
}
bed_ids = {}
for bname, (w_from, w_to, outward) in BEDS.items():
    hex_id = f"bed_{bname}"
    b.place_edge(hex_id, "hexagon", 0, w_from, w_to,
                 (outward[0], outward[1], 0.0), HEX_BED)
    ids = [hex_id]
    # 从已放置六边形取世界顶点: 攻缘那条边贴着坛缘, 其余五条自由边
    # 各贴一片菱形花瓣; 花瓣沿"远离坛心"的切向倾摆, 避免压回坛面。
    verts = world_vertices(b.tiles[-1])
    center = (sum(v[0] for v in verts) / 6.0, sum(v[1] for v in verts) / 6.0)
    edges = []
    for i in range(6):
        a, c = verts[i], verts[(i + 1) % 6]
        mid = ((a[0] + c[0]) / 2.0, (a[1] + c[1]) / 2.0)
        d2 = (mid[0] - PC[0]) ** 2 + (mid[1] - PC[1]) ** 2
        edges.append((d2, a, c, mid))
    edges.sort(key=lambda e: -e[0])
    for k, (_, a, c, mid) in enumerate(edges[:5]):
        radial = (mid[0] - PC[0], mid[1] - PC[1])
        if (c[0] - a[0]) * radial[0] + (c[1] - a[1]) * radial[1] < -1e-9:
            a, c = c, a
        out = (mid[0] - center[0], mid[1] - center[1])
        norm = math.hypot(out[0], out[1])
        tid = f"petal_{bname}{k}"
        b.place_edge(tid, "rhombus", 0, a, c,
                     (out[0] / norm, out[1] / norm, 0.0),
                     PETAL_A if k % 2 else PETAL_B)
        ids.append(tid)
    bed_ids[bname] = ids

# =================================================================
# 7. 四角灯柱: 方墙站上坛角砖外缘 + 三角柱冠
# =================================================================
POSTS = [
    ("post_sw", 0, 0.0), ("post_se", 2, 0.0),
    ("post_nw", 0, 3.0), ("post_ne", 2, 3.0),
]
post_ids = []
for tid, x0, y in POSTS:
    b.wall_ns(tid, x0, y, 0, POST)
    b.crest_ns(f"{tid}_cap", x0, y, 1.0, POST_CAP)
    post_ids += [tid, f"{tid}_cap"]

# =================================================================
# 教程步骤 (18 步)
# =================================================================
b.step(
    "铺展坛南六片: 灰青棋盘方板逐行互吸, 坛心 (中排中间) 就是灯球的底板。",
    plinth_ids[:6],
    tip="从西南角逐行铺 —— 每片至少咬住一位邻居。",
)
b.step(
    "补展坛北三片: 3x3 展坛合拢。",
    plinth_ids[6:],
    highlight=["plinth_11"],
    tip="九片平铺互咬成一整块受力底盘。",
)
b.step(
    "倒扣梯形下碗: 四片橙色梯形窄边朝下吸坛心四边, 腰边两两互咬外翻成环。",
    bowl_ids,
    highlight=["plinth_11"],
    tip="梯形当承重斗拱 —— 剪断任何一条缝, 力都能沿环绕行。",
)
b.step(
    "立方鼓第一层: 四片蓝色横板站上腰环, 下边与梯形宽边等长贴合、转角短边互咬。",
    drum1_ids,
    highlight=["bowl_s"],
    tip="2 比 2 的整边贴合 —— 灯身的每一层都这样咬转角。",
)
b.step(
    "挂第一层菱形角藤: 四片紫色菱形一条边整边吸鼓身竖角缝, 斜着向上展开。",
    vine_ids[1],
    highlight=["drum1_s", "drum1_e"],
    tip="竖直铰链不吃重力力矩 —— 菱形角旗怎么挂都稳。",
)
b.step(
    "立透明透光带: 四片透明横板骑上第一层, 灯球的光将从这一圈漏出来。",
    drum2_ids,
    highlight=["drum1_s"],
    tip="转角短边照旧互咬 —— 透光不减一分结构。",
)
b.step(
    "挂第二层菱形角藤: 四片粉色菱形吸中层角缝, 腰边咬住下层藤蔓。",
    vine_ids[2],
    highlight=["vine1_se"],
    tip="上下两片菱形腰边正好共线互吸 —— 藤蔓自己锁自己。",
)
b.step(
    "立方鼓第三层: 四片青色横板收口, 鼓身到顶。",
    drum3_ids,
    highlight=["drum2_s"],
    tip="鼓顶四条边线就是上盖的坡脚 —— 务必对平。",
)
b.step(
    "挂第三层菱形角藤: 四片紫色菱形收尾, 四条角藤爬满三层。",
    vine_ids[3],
    highlight=["vine2_se"],
    tip="十二片菱形四条藤 —— 灯球的竖向签名。",
)
b.step(
    "盖梯形四坡上盖: 四片橙色梯形宽边吸鼓顶, 腰边互咬向内收分。",
    list(roof_ids),
    highlight=["drum3_s", "drum3_n"],
    tip="D4 关键一步: 四片坡面要一次围拢, 半拢状态不要撒手。",
)
b.step(
    "压顶: 一片金色方板盖住坡顶 1x1 洞口。",
    [cap_id],
    highlight=["roof_s"],
    tip="压顶方四边同时吸四片坡面上边 —— 上盖从此成为整体。",
)
b.step(
    "竖扇形极冠 (南/东): 两片红色扇形半径边吸压顶边线, 弧线甩向天空。",
    ["polar_s", "polar_e"],
    highlight=[cap_id],
    tip="扇形底边同时吸压顶方与坡面梯形上边 —— 一片两吸。",
)
b.step(
    "竖扇形极冠 (北/西): 再两片风车状合拢 —— 灯球封顶。",
    ["polar_n", "polar_w"],
    highlight=["polar_s"],
    tip="四片极冠风车旋向一致, 从头顶看是一朵四瓣风车花。",
)
b.step(
    "砌东花圃: 六边形芯整边吸坛缘, 五片菱形花瓣沿自由边展开、相邻互咬。",
    bed_ids["e"],
    highlight=["plinth_21"],
    tip="六边形和菱形是平面密铺搭档 —— 花瓣贴边即吸。",
)
b.step(
    "砌北花圃: 第二座八角花圃向北展开。",
    bed_ids["n"],
    highlight=["bed_e"],
    tip="花瓣沿远离坛心的方向倾摆 —— 谁也不压坛面一角。",
)
b.step(
    "砌西花圃: 第三座花圃落位, 三面见花。",
    bed_ids["w"],
    highlight=["bed_n"],
    tip="每座花圃 1 芯 5 瓣 —— 四座正好用满 24 片密铺件。",
)
b.step(
    "砌南花圃: 最后一座花圃合拢, 花瓣顺手咬住坛缘拼缝。",
    bed_ids["s"],
    highlight=["bed_w"],
    tip="南花圃两侧的花瓣与坛角砖脚线共线 —— 灯柱马上踩上来。",
)
b.step(
    "立四角灯柱戴冠: 四片透明方墙站上坛角外缘, 金色三角冠收尾 —— 四型合璧灯球坛落成!",
    post_ids,
    highlight=["plinth_00", "plinth_20"],
    tip="D4 入库前须实物复核: 抖一抖透光带、提一提上盖, 全都纹丝不动才算数。",
)

model = b.finalize(
    model_id="expansion_orb_01",
    name="四型合璧灯球坛",
    name_en="Expansion Orb Display 01",
    description=(
        "几何艺术 D4 扩展片型合璧: 四片梯形窄边朝下反扣成倒置斗拱下碗, "
        "托起三层横板方鼓灯身 (中层透明透光带), 12 片菱形沿四条竖角缝"
        "逐层腰边互咬爬成角藤; 梯形四坡收顶后, 四片扇形风车状竖立合成"
        "极冠; 坛面四座六边形芯五瓣菱形花圃环绕, 四角灯柱收束广场 —— "
        "菱 32 / 梯 8 / 六 4 / 扇 4 共 48 片扩展片型, 每种都在承重或"
        "签名位置, 是豪华套装的灯球陈列件。"
    ),
    difficulty=4,
    tags=["几何艺术", "灯球", "扩展片型", "透光带", "摆件", "挑战"],
    min_pieces=78,
    min_steps=18,
    series="geometric_art",
)

meta = model["content_meta"]
meta["technique_tags"] = {
    "primary": "T13_hollow_shell",
    "secondary": ["T18_tessellation_art", "T17_negative_space"],
}
meta["signature_statement"] = (
    "倒扣梯形斗拱托起三层透光灯身, 菱形角藤与扇形极冠合璧成灯球。"
)
meta["structural_signature"]["silhouette_class"] = "lantern_orb"
meta["structural_signature"]["height_layers"] = 6

out = Path(__file__).resolve().parent.parent / "data" / "models" / "expansion_orb_01.json"
out.write_text(json.dumps(model, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
