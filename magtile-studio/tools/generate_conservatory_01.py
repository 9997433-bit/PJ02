#!/usr/bin/env python3
"""生成模型 data/models/conservatory_01.json (维多利亚天窗花房)。

内容批 P 模型 2/10 (重写): 植物花园主题 D2 —— 主打窗格方
(window_square)。单层通体玻璃环 (11 片窗格方, 南立面整排 4 片是
招牌) 托起绿色框架平台, 平台中央再升起一圈长方形楣带, 楣带顶沿
四片梯形合围玻璃天窗锥顶 (维多利亚温室经典的中央采光亭 lantern);
东端门框方入户, 平台东沿再挑一片梯形门廊雨檐 —— 共 5 片梯形屋檐。

与旧版 (两层盒式墙 + 平顶 + 单片南檐) 完全不同的原创结构: 本作是
"单层玻璃环 -> 框架平台 -> 中央天窗亭" 的三段式剖面, 屋顶主体
就是梯形玻璃锥, 西翼平台上立三角尖饰, 南立面外侧一排花坛。

结构总览 (世界单位: 1.0 = 正方形磁力片边长, 入户朝东):
  - 室内红灰棋盘地砖 4x2                                          8 片
  - 单层玻璃环 (z 0..1): 南窗格 x4 + 北窗格 x4 + 西窗格 x2
    + 东窗格 x1 + 东门框 x1                                       12 片
  - 框架平台 (z=1): 西翼方板 x2 + 中央长板 x2 + 东翼纵板 x1        5 片
  - 天窗亭楣带 (z 1..2): 长方形横楣四边合围                          4 片
  - 天窗玻璃锥 (z=2 沿口): 梯形四坡 + 压顶 (hip_roof2)              5 片
  - 西翼尖饰 x1 + 东门廊梯形雨檐 x1 + 入户露台长板 x1                3 片
  - 南侧花坛: 泥土方板 x4 + 三色花 x3                                7 片
  合计 44 片, 9 个教程步骤, 6 种磁力片形状 (含 1 种扩展片型)。

物理规则要点 (validate 常规 + strict 双档零警告):
  - 玻璃环墙脚整边踩地砖拼缝, 四角竖边互咬闭环 (窗格方物理同实心方);
  - 平台方板/长板整边吸墙顶沿, 楣带下底整边吸平台长板沿边;
  - 天窗四片梯形下底吸楣带顶沿 (2 格等长贴合), 腰两两互吸自锁,
    压顶方板封口 —— 与已验证的 hip_roof2 / 梯形雨棚同款;
  - 门廊雨檐下底整边吸东翼纵板 2 格长边 (单片外挑, 磁吸铰链);
  - 尖饰/花坛三角底边整边吸方板拼缝, 重心正压支承线。

用法: python3 tools/generate_conservatory_01.py  (在 magtile-studio 目录下运行)
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from magtile_gen import ModelBuilder  # noqa: E402

b = ModelBuilder()

GLASS = "clear"      # 窗格方 / 天窗梯形
FRAME = "green"      # 维多利亚式绿漆铁架: 平台 / 楣带 / 压顶 / 尖饰 / 雨檐
TILE_A = "gray"      # 室内棋盘地砖
TILE_B = "red"
DOOR = "orange"      # 木门
TERRACE = "gray"     # 入户露台
SOIL = "orange"      # 花坛泥土
BLOOMS = ["pink", "yellow", "purple"]


def glass_ns(tid, tile_type, x0, y, z0, color):
    """南北朝向立片 (平面 y=y), 覆盖 x [x0,x0+1], z [z0,z0+1]。"""
    b.add(tid, tile_type, (x0 + 0.5, y, z0 + 0.5), (90, 0, 0), color)


def glass_ew(tid, tile_type, x, y0, z0, color):
    """东西朝向立片 (平面 x=x), 覆盖 y [y0,y0+1], z [z0,z0+1]。"""
    b.add(tid, tile_type, (x, y0 + 0.5, z0 + 0.5), (90, 0, 90), color)


# =================================================================
# 1. 室内棋盘地砖 (x [0,4] x y [0,2], 红灰相间的维多利亚花砖)
# =================================================================
for x in range(4):
    for y in range(2):
        b.flat(f"floor_{x}_{y}", x, y, 0.0, TILE_A if (x + y) % 2 == 0 else TILE_B)

# =================================================================
# 2. 南侧花坛 (y [-1,0]): 四格泥土 + 三株立在拼缝上的三色花
# =================================================================
for x in range(4):
    b.flat(f"bed_{x}", x, -1, 0.0, SOIL)
for i, x in enumerate((1, 2, 3)):
    b.crest_ew(f"bloom_{x}", float(x), -1, 0.0, BLOOMS[i])

# =================================================================
# 3. 单层玻璃环 (z 0..1): 南立面整排 4 片窗格方是招牌
# =================================================================
for x in range(4):
    glass_ns(f"glass_s_{x}", "window_square", x, 0.0, 0, GLASS)
for x in range(4):
    glass_ns(f"glass_n_{x}", "window_square", x, 2.0, 0, GLASS)
glass_ew("glass_w_0", "window_square", 0.0, 0, 0, GLASS)
glass_ew("glass_w_1", "window_square", 0.0, 1, 0, GLASS)
glass_ew("door_e", "door_frame", 4.0, 0, 0, DOOR)
glass_ew("glass_e_1", "window_square", 4.0, 1, 0, GLASS)

# 入户露台: 长板短边吸地砖东沿, 与门框脚同缝
b.flat_rect("terrace", 4, 0, 0.0, TERRACE, axis="x")

# =================================================================
# 4. 框架平台 (z=1): 西翼两方板 + 中央两长板 + 东翼一纵板
#    中央长板南/北 2 格长边是楣带的落脚线, 东翼纵板 2 格东沿是雨檐铰链
# =================================================================
b.flat("deck_w_s", 0, 0, 1.0, FRAME)
b.flat("deck_w_n", 0, 1, 1.0, FRAME)
b.flat_rect("deck_c_s", 1, 0, 1.0, FRAME, axis="x")
b.flat_rect("deck_c_n", 1, 1, 1.0, FRAME, axis="x")
b.flat_rect("deck_e", 3, 0, 1.0, FRAME, axis="y")

# =================================================================
# 5. 天窗亭楣带 (z 1..2): 四片长方形横楣围出 2x2 采光井
# =================================================================
b.lintel_ns("band_s", 1, 0.0, 1, FRAME)
b.lintel_ns("band_n", 1, 2.0, 1, FRAME)
b.lintel_ew("band_w", 1.0, 0, 1, FRAME)
b.lintel_ew("band_e", 3.0, 0, 1, FRAME)

# =================================================================
# 6. 天窗玻璃锥 (z=2): 梯形四坡互锁 + 绿框压顶 (锥尖 z=2.707)
# =================================================================
lantern_ids, lantern_cap = b.hip_roof2("lantern", 1, 0, 2.0, GLASS, cap_color=FRAME)

# =================================================================
# 7. 收尾: 西翼尖饰 + 东门廊梯形雨檐
# =================================================================
b.crest_ns("finial_w", 0, 1.0, 1.0, FRAME)
b.place_edge("porch_eave", "trapezoid", 0,
             (4.0, 0.0, 1.0), (4.0, 2.0, 1.0), (0.5, 0.0, 0.707), FRAME)

# =================================================================
# 教程步骤 (9 步)
# =================================================================
b.step(
    "铺室内地砖: 八片红灰相间的方板拼成 4x2 棋盘 —— 维多利亚花砖地面。",
    [f"floor_{x}_{y}" for x in range(4) for y in range(2)],
    tip="地砖缝对整齐, 玻璃环的墙脚才有整边可吸。",
)
b.step(
    "砌南侧花坛: 四格泥土贴住地砖南沿, 粉/黄/紫三株花立在泥土拼缝上。",
    [f"bed_{x}" for x in range(4)] + [f"bloom_{x}" for x in (1, 2, 3)],
    highlight=["floor_0_0"],
    tip="花坛在玻璃墙外侧 —— 从室内透过窗格也能看到花色。",
)
b.step(
    "立南立面: 整排四片窗格方一字朝南 —— 这排玻璃就是花房的招牌。",
    [f"glass_s_{x}" for x in range(4)],
    highlight=["bed_1"],
    tip="窗格方物理上和实心方一样稳, 负空间只是造型。",
)
b.step(
    "立北立面: 四片窗格方与南排相对, 墙脚踩地砖北沿。",
    [f"glass_n_{x}" for x in range(4)],
    highlight=["glass_s_0"],
    tip="南北两排先立好, 东西短边一合就闭环。",
)
b.step(
    "合围玻璃环并铺露台: 西端两片窗格, 东端门框方入户 + 一片窗格, "
    "露台长板贴住门脚。",
    ["glass_w_0", "glass_w_1", "door_e", "glass_e_1", "terrace"],
    highlight=["glass_s_0", "glass_n_3"],
    tip="四角竖边互咬, 单层玻璃环收拢 —— 门框方留出入户负空间。",
)
b.step(
    "架框架平台: 西翼两方板、中央两长板、东翼一纵板, 整边吸住玻璃环顶沿。",
    ["deck_w_s", "deck_w_n", "deck_c_s", "deck_c_n", "deck_e"],
    highlight=["glass_s_1", "glass_n_1"],
    tip="中央长板的 2 格长边朝南北 —— 那是天窗亭楣带的落脚线。",
)
b.step(
    "升天窗亭楣带: 四片长方形横楣在平台中央围出 2x2 采光井。",
    ["band_s", "band_n", "band_w", "band_e"],
    highlight=["deck_c_s", "deck_c_n"],
    tip="南北横楣下底吸长板沿边, 东西横楣竖边与它们互咬。",
)
b.step(
    "盖玻璃天窗锥: 四片透明梯形下底吸楣带顶沿, 腰两两互锁, 绿框方板压顶。",
    lantern_ids + [lantern_cap],
    highlight=["band_s"],
    tip="梯形四坡自锁成环 —— 中央采光亭是维多利亚温室的经典剖面。",
)
b.step(
    "收尾点睛: 西翼平台立三角尖饰, 东翼沿边挑一片梯形门廊雨檐 —— 天窗花房落成!",
    ["finial_w", "porch_eave"],
    highlight=["deck_e", "door_e"],
    tip="雨檐下底整边吸东翼 2 格长边, 正好罩在入户门上方。",
)

b.finalize(
    model_id="conservatory_01",
    name="玻璃花房",
    name_en="Conservatory 01",
    description=(
        "植物花园 D2: 维多利亚天窗花房 —— 单层通体玻璃环 (11 片窗格方, "
        "南立面整排 4 片是招牌) 托起绿漆框架平台, 平台中央长方形楣带再升"
        "一圈, 顶沿四片透明梯形合围玻璃天窗锥 (中央采光亭); 东端门框方"
        "入户, 东翼再挑一片梯形门廊雨檐, 共 5 片梯形屋檐; 西翼三角尖饰, "
        "南侧四格花坛开着粉/黄/紫三色花。与 A 字斜顶 greenhouse_01、穹顶 "
        "greenhouse_dome_01 刻意区分 —— 这次的剖面是'玻璃环 + 中央天窗亭'。"
    ),
    difficulty=2,
    tags=["植物花园", "温室", "花房", "窗格", "天窗"],
    min_pieces=44,
    min_steps=9,
    series="plant_garden",
)
