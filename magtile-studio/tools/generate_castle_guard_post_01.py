#!/usr/bin/env python3
"""生成模型 data/models/castle_guard_post_01.json (城门小岗楼, D1 入门)。

D1 配额解冻批第 4 号 (城堡与要塞): 一座守在城墙缺口上的小岗楼 ——
2x2 岗房收一层平顶甲板, 四面雉堞对角错位立在甲板沿上, 南面门框方
开出士兵进出的门洞、旁边窗格方是射箭孔, 两翼短墙从岗楼两侧探出
咬住楼角, 墙顶各站一枚城齿。与库内城堡系 (castle_tower_01 高塔 /
medieval_gate_01 双塔城门 / castle_foundation_01 地基) 体量与
叙事都不同: 这是最小可驻守单元, "一间房 + 一圈垛口 + 两段翼墙"。

结构总览 (世界单位 1.0 = 正方形磁力片边长, 城门朝南):
  - 岗房地台 (x [1,3], y [0,2]): 灰色长方板 2 片            2 片
  - 南面: 紫色门框方 (门洞) + 黄色窗格方 (射箭孔)           2 片
  - 北/西/东墙: 灰色立方                                     6 片
  - 平顶甲板 (z=1): 蓝色长板 2 片压满四面墙顶                2 片
  - 雉堞: 红色等边三角 4 枚, 四面对角错位立在甲板沿          4 片
  - 两翼短墙 (y=1, x [0,1] / [3,4]): 灰色立方接地咬楼角      2 片
  - 翼墙城齿: 红色等边三角各 1 枚                            2 片
  合计 20 片, 7 个教程步骤, 5 种片形 (全部 CORE-9 之内)。

招牌技法 (T01 盒式框架): 2x2 岗房不封死 —— 平顶甲板即第二结构层,
雉堞不站墙顶而站甲板沿, 四枚对角错位形成"转圈垛口"的剪影;
两翼短墙只靠楼角竖边互咬 + 自身接地, 演示"墙咬墙"的城防延伸。

物理规则要点 (validate 常规 + strict 双档零警告):
  - 四面墙脚踩地台拼缝, 四角竖边互咬成环; 门框方/窗格方按
    实心外框参与物理 (docs/TILE_SET.md);
  - 甲板两片长板每片至少四条吸合 (南北长边压墙顶 + 短边压
    侧墙顶 + 两片互吸), 剪任何一条铰链仍有支撑路径;
  - 雉堞/城齿底边完整吸住甲板沿或翼墙顶, 纯受压零力矩;
  - 翼墙自身接地且与楼角竖边互咬, 不构成孤立组件;
  - 最高点 1.87 (雉堞尖), 低于高层结构阈值, 无 R8 拓扑告警。

用法: python3 tools/generate_castle_guard_post_01.py  (在 magtile-studio 目录下运行)
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from magtile_gen import ModelBuilder  # noqa: E402

b = ModelBuilder()

FLOOR = "gray"      # 岗房地台
WALL = "gray"       # 石墙
GATE = "purple"     # 门框方城门
ARROW = "yellow"    # 窗格方射箭孔
DECK = "blue"       # 平顶甲板
MERLON = "red"      # 雉堞与城齿
WING = "gray"       # 两翼短墙


def wall_ns_t(tid, tile_type, x0, y, z0, color):
    b.add(tid, tile_type, (x0 + 0.5, y, z0 + 0.5), (90, 0, 0), color)


# =================================================================
# 1. 岗房地台 (x [1,3], y [0,2]): 两片长方板
# =================================================================
b.flat_rect("floor_s", 1, 0, 0.0, FLOOR)
b.flat_rect("floor_n", 1, 1, 0.0, FLOOR)

# =================================================================
# 2. 南面: 门框方城门 + 窗格方射箭孔
# =================================================================
wall_ns_t("gate", "door_frame", 1, 0.0, 0, GATE)
wall_ns_t("arrow_slit", "window_square", 2, 0.0, 0, ARROW)

# =================================================================
# 3. 北墙与东西墙: 灰色立方, 墙脚踩地台拼缝
# =================================================================
b.wall_ns("wall_n_w", 1, 2.0, 0, WALL)
b.wall_ns("wall_n_e", 2, 2.0, 0, WALL)
b.wall_ew("wall_w_s", 1.0, 0, 0, WALL)
b.wall_ew("wall_w_n", 1.0, 1, 0, WALL)
b.wall_ew("wall_e_s", 3.0, 0, 0, WALL)
b.wall_ew("wall_e_n", 3.0, 1, 0, WALL)

# =================================================================
# 4. 平顶甲板 (z=1): 两片长板压满四面墙顶
# =================================================================
b.flat_rect("deck_s", 1, 0, 1.0, DECK)
b.flat_rect("deck_n", 1, 1, 1.0, DECK)

# =================================================================
# 5. 雉堞: 四枚等边三角, 四面对角错位立在甲板沿
# =================================================================
b.crest_ns("merlon_s", 1, 0.0, 1.0, MERLON)
b.crest_ew("merlon_e", 3.0, 0, 1.0, MERLON)
b.crest_ns("merlon_n", 2, 2.0, 1.0, MERLON)
b.crest_ew("merlon_w", 1.0, 1, 1.0, MERLON)

# =================================================================
# 6. 两翼短墙 (y=1): 接地立方咬住楼角 + 墙顶城齿
# =================================================================
b.wall_ns("wing_w", 0, 1.0, 0, WING)
b.wall_ns("wing_e", 3, 1.0, 0, WING)
b.crest_ns("wing_w_top", 0, 1.0, 1.0, MERLON)
b.crest_ns("wing_e_top", 3, 1.0, 1.0, MERLON)

# =================================================================
# 教程步骤 (7 步)
# =================================================================
b.step(
    "铺岗房地台: 两片灰色长方板并排吸成 2x2 的石地面。",
    ["floor_s", "floor_n"],
    tip="长边贴长边 —— 地台是岗楼的根, 拼缝要严丝合缝。",
)
b.step(
    "立南面城门墙: 紫色门框方的门洞给士兵进出, 黄色窗格方是射箭孔。",
    ["gate", "arrow_slit"],
    highlight=["floor_s"],
    tip="两片竖边互咬、墙脚踩住地台南缘 —— 门洞要正对来路。",
)
b.step(
    "立东西两面石墙: 每面两片灰方, 墙脚踩地台拼缝、与南墙咬角。",
    ["wall_w_s", "wall_w_n", "wall_e_s", "wall_e_n"],
    highlight=["gate", "arrow_slit"],
    tip="角上竖边咬住了, 墙才推不倒 —— 每放一片都捏捏角。",
)
b.step(
    "立北墙合围: 两片灰方补上最后一面, 岗房锁成一圈。",
    ["wall_n_w", "wall_n_e"],
    highlight=["wall_w_n", "wall_e_n"],
    tip="从门洞往里看一眼 —— 一间能站岗的小石屋成形了。",
)
b.step(
    "收平顶甲板: 两片蓝色长板压满四面墙顶, 岗楼有了第二层。",
    ["deck_s", "deck_n"],
    highlight=["wall_n_w", "gate"],
    tip="每片长板要同时压住三面墙顶再松手, 两片中缝互吸。",
)
b.step(
    "摆雉堞: 四枚红色三角沿甲板边转着圈站, 一面一枚对角错开。",
    ["merlon_s", "merlon_e", "merlon_n", "merlon_w"],
    highlight=["deck_s", "deck_n"],
    tip="底边整条吸住甲板沿 —— 错位站的垛口从哪边看都威风。",
)
b.step(
    "接两翼城墙: 两侧短墙咬住楼角接地立稳, 墙顶各站一枚城齿 —— 换岗!",
    ["wing_w", "wing_e", "wing_w_top", "wing_e_top"],
    highlight=["wall_w_s", "wall_e_s"],
    tip="翼墙竖边与楼角互咬、墙脚落地 —— 以后城墙就从这里往两边长。",
)

model = b.finalize(
    model_id="castle_guard_post_01",
    name="城门小岗楼",
    name_en="Castle Guard Post 01",
    description=(
        "D1 入门城防件: 最小可驻守单元 —— 2x2 石砌岗房收一层蓝色平顶"
        "甲板, 四枚红色雉堞沿甲板边对角错位转圈站岗; 南面紫色门框方开出"
        "士兵进出的门洞, 旁边黄色窗格方是射箭孔, 两翼短墙从楼角探出、"
        "墙顶各站一枚城齿。搭完从门洞塞一颗玻璃珠进去 —— 那是今晚的哨兵。"
    ),
    difficulty=1,
    tags=["城堡", "岗楼", "雉堞", "亲子入门"],
    min_pieces=20,
    min_steps=7,
)

# ---- content_meta 补全 (CONTENT_STRATEGY.md 5.1 节 schema) ---------
meta = model["content_meta"]
model["content_meta"] = {
    "series": "castle_fortress",
    "build_paradigm": "bottom_up",
    "technique_tags": {
        "primary": "T01_box_frame",
        "secondary": ["T12_layered_platform", "T17_negative_space"],
    },
    "signature_statement": "雉堞不站墙顶而站甲板沿, 四面对角错位转圈; 两翼短墙靠楼角竖边互咬延伸城防。",
    "structural_signature": meta["structural_signature"],
    "physical_risk_notes": [
        {"step": 5, "risk": "甲板长板若只压住一面墙顶就松手, 会把墙带倒",
         "mitigation": "该步 tip 强调同时压住三面墙顶再松手, 两片中缝互吸"},
    ],
}

out = Path(__file__).resolve().parent.parent / "data" / "models" / "castle_guard_post_01.json"
out.write_text(json.dumps(model, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(f"已补全 content_meta 并重写 {out}")
