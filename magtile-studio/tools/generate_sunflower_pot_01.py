#!/usr/bin/env python3
"""生成模型 data/models/sunflower_pot_01.json (向日葵盆栽)。

内容批 L 模型 3/4: 植物花园主题 D2 盆栽原型。

用法: python3 tools/generate_sunflower_pot_01.py  (在 magtile-studio 目录下运行)
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from magtile_gen import ModelBuilder  # noqa: E402

b = ModelBuilder()

SAUCER = "gray"
POT = "orange"
LATTICE = "clear"
STEM = "green"
CENTER = "gray"
PETAL_S = "yellow"
PETAL_N = "orange"
LEAF = "green"
BUG = "red"

TRI_H = 0.866025


def wall_ns_t(tid, tile_type, x0, y, z0, color):
    b.add(tid, tile_type, (x0 + 0.5, y, z0 + 0.5), (90, 0, 0), color)


def petal_south(tile_id, x0, y, z, color):
    """南指花瓣: 底边在 y, 尖朝 -y。"""
    b.place_tri(tile_id, "equilateral_triangle",
                (x0, y, z), (x0 + 1.0, y, z), (x0 + 0.5, y - TRI_H, z), color)


# 1. 接水盘 (含两侧外扩台沿)
b.flat("pad_w", -1, -1, 0.0, SAUCER)
b.flat("pad_nw", -1, 0, 0.0, SAUCER)
b.flat("saucer_w", 0, -1, 0.0, SAUCER)
b.flat("saucer_c", 1, -1, 0.0, SAUCER)
b.flat("saucer_e", 2, -1, 0.0, SAUCER)
b.flat("pad_e", 3, -1, 0.0, SAUCER)
b.flat("pad_ne", 3, 0, 0.0, SAUCER)

# 2. 陶盆 (z=0 底 + 墙环, 南北窗格点缀)
b.flat("pot_00", 0, 0, 0.0, POT)
b.flat("pot_01", 0, 1, 0.0, POT)
b.flat("pot_10", 1, 0, 0.0, POT)
b.flat("pot_11", 1, 1, 0.0, POT)
wall_ns_t("pot_s", "window_square", 0, 0.0, 0, LATTICE)
wall_ns_t("pot_n", "window_square", 0, 2.0, 0, LATTICE)
b.wall_ew("pot_w", 0.0, 0, 0, POT)
b.wall_ew("pot_e", 2.0, 0, 0, POT)

# 3. 花盘心 (z=1 墙顶)
b.flat("hub_00", 0, 0, 1.0, CENTER)
b.flat("hub_01", 0, 1, 1.0, CENTER)
b.flat("hub_10", 1, 0, 1.0, CENTER)
b.flat("hub_11", 1, 1, 1.0, CENTER)

# 4. S 形茎
b.spire_ns("stem_lo", 0, 1.0, 1.0, STEM)
b.spire_ns("stem_hi", 1, 1.0, 1.0, STEM)

# 5. 八片花瓣 (z=1 沿口)
petal_south("pet_s0", 0, 0.0, 1.0, PETAL_S)
petal_south("pet_s1", 1, 0.0, 1.0, PETAL_S)
b.crest_ew("pet_w0", 0.0, 0, 1.0, PETAL_S)
b.crest_ew("pet_w1", 0.0, 1, 1.0, PETAL_S)
b.crest_ew("pet_e0", 2.0, 0, 1.0, PETAL_S)
b.crest_ew("pet_e1", 2.0, 1, 1.0, PETAL_S)
b.crest_ns("pet_n0", 0, 2.0, 1.0, PETAL_N)
b.crest_ns("pet_n1", 1, 2.0, 1.0, PETAL_N)

# 6. 四片叶子 (接水盘南沿下垂)
b.crest_ew("leaf_w", -1.0, -1, 0.0, LEAF)
b.crest_ns("leaf_cw", 0, -1, 0.0, LEAF)
b.crest_ns("leaf_ce", 2, -1, 0.0, LEAF)
b.crest_ew("leaf_e", 3.0, -1, 0.0, LEAF)

# 7. 装饰
b.crest_ns("bug", 1, -1, 0.0, BUG)

b.step(
    "铺接水盘: 七片灰色方板拼成工字形台沿, 两侧外扩托住整盆。",
    ["pad_w", "pad_nw", "saucer_w", "saucer_c", "saucer_e", "pad_e", "pad_ne"],
    tip="盆栽的第一件事 —— 接水盘接住浇多的水。",
)
b.step(
    "拼盆底: 四片陶土方板 2x2 整边互吸, 落在接水盘中央。",
    ["pot_00", "pot_01", "pot_10", "pot_11"],
    highlight=["saucer_c"],
    tip="盆底与接水盘沿整边互吸 —— 盆就不会滑。",
)
b.step(
    "围盆身: 两片窗格南北墙与两片陶土东西墙踩住盆底, 四角竖边互咬成环。",
    ["pot_s", "pot_n", "pot_w", "pot_e"],
    highlight=["pot_00", "pot_11"],
    tip="闭环盆身 —— 接下来封住墙顶做花盘。",
)
b.step(
    "拼花盘心: 四片灰色方板 2x2 整边互吸 —— 先铺三片再封口。",
    ["hub_00", "hub_01", "hub_10", "hub_11"],
    highlight=["pot_s"],
    tip="花盘心骑墙顶 —— 这是向日葵的脸。",
)
b.step(
    "立茎干: 两段绿色瘦高尖接成 S 形茎, 底边整边吸花盘。",
    ["stem_lo", "stem_hi"],
    highlight=["hub_01"],
    tip="S 形茎把重心拉回盆心 —— 接下来铺花瓣。",
)
b.step(
    "平铺南半圈花瓣: 四片黄色三角在花心南侧平铺开 (放射展开图)。",
    ["pet_s0", "pet_s1", "pet_w0", "pet_w1"],
    highlight=["hub_00", "hub_10"],
    tip="T05 平面翻折 —— 先在桌面平铺, 看清放射展开图。",
)
b.step(
    "平铺北半圈花瓣: 四片橙色三角在北侧, 与南侧镜像成对。",
    ["pet_e0", "pet_e1", "pet_n0", "pet_n1"],
    highlight=["pet_s0", "hub_11"],
    tip="T11 镜像 —— 南黄北橙, 八瓣一次向心翻折就立起来!",
)
b.step(
    "装四片叶子: 等边三角沿接水盘南沿下垂, 左右镜像成对。",
    ["leaf_w", "leaf_cw", "leaf_ce", "leaf_e"],
    highlight=["saucer_w", "saucer_e"],
    tip="叶子整边吸接水盘 —— 把重心拉回盆心下方。",
)
b.step(
    "点睛: 接水盘中央趴一只瓢虫 —— 向日葵盆栽落成!",
    ["bug"],
    highlight=["saucer_c"],
    tip="瓢虫趴在接水盘中央 —— 全库第一盆站得住的向日葵!",
)

b.finalize(
    model_id="sunflower_pot_01",
    name="向日葵盆栽",
    name_en="Sunflower Pot 01",
    description=(
        "植物花园 D2 盆栽原型: 陶土 2x2 闭环盆身托住 S 形等腰茎干, "
        "顶上一朵 2x2 灰色花盘心; 八片花瓣按放射展开图平铺后向心翻折立起; "
        "四片叶子沿接水盘南沿下垂, 窗格南北墙点缀盆身。"
    ),
    difficulty=2,
    tags=["植物花园", "向日葵", "盆栽", "翻折", "镜像"],
    min_pieces=34,
    min_steps=9,
    series="plant_garden",
)
