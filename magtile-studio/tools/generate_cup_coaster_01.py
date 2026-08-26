#!/usr/bin/env python3
"""生成模型 data/models/cup_coaster_01.json (双杯位杯垫台)。

D1 补员批 2 模型 2/4 (难度配额解冻线 D1 >= 20, 路径 B1): 入门档
实用功能选题 —— 茶几上的双杯位杯垫台。结构签名是"大方地台
封顶盒": 两片大正方形地台 + 一圈单层围墙 + 中央双隔墙, 顶上
四片长板拼成整层台面 —— 台面放杯子, 盒腔收杯垫, 一物两用;
与手机摇篮 (门式靠背 + 坡道) 和笔筒 (开顶双筒塔) 的结构逻辑
完全不同, 是本批唯一的闭合箱体。

结构总览 (世界单位: 1.0 = 正方形磁力片边长):
  - 地台 2 片大正方形 (x [0,4], y [0,2])                 2 片
  - 一圈围墙 12 片方板 (z 0..1, 短边完整贴大方长边)     12 片
  - 中央双隔墙 (x=2 拼缝, 把盒腔分成两格)                2 片
  - 台面 4 片长板 (z=1, 短边吸墙顶/隔墙顶, 板板互吸)     4 片
  - 台面四角热气小旗 (等边三角, 与墙顶整边重合)          4 片
  合计 24 片, 5 个教程步骤, 4 种磁力片形状 (全部 CORE-9 之内)。

物理规则要点 (validate 常规 + strict 双档零警告):
  - 长短边完整贴合 (R2): 大正方形边长 2, 每边同时吸两片共线
    围墙墙脚; 台面长板长边完整压住两片共线墙顶 —— 环环相扣;
  - 全结构受压, 无悬挑无吊挂; 先合围后封顶,
    盒腔封闭前内部无待放片 (R7b 无包围放置);
  - 最高点 1.87 < 2.5, 不触发 R8 高层结构判定;
  - 隔墙底边骑两片大正方形的公共拼缝, 顶边吸台面板缝 ——
    盒体中央多一道受压立柱。

用法: python3 tools/generate_cup_coaster_01.py  (在 magtile-studio 目录下运行)
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from magtile_gen import ModelBuilder  # noqa: E402

b = ModelBuilder()

BASE = "yellow"     # 地台大方
RIM = "orange"      # 围墙
DIV = "orange"      # 中央隔墙
TOP = "yellow"      # 台面长板
STEAM = "pink"      # 热气小旗

# =================================================================
# 1. 地台: 两片大正方形 (x [0,2] / [2,4], y [0,2])
# =================================================================
b.add("base_w", "large_square", (1.0, 1.0, 0.0), (0, 0, 0), BASE)
b.add("base_e", "large_square", (3.0, 1.0, 0.0), (0, 0, 0), BASE)

# =================================================================
# 2. 一圈围墙 (z 0..1): 南 4 + 北 4 + 西 2 + 东 2
# =================================================================
for i in range(4):
    b.wall_ns(f"rim_s_{i}", i, 0.0, 0, RIM)
for i in range(4):
    b.wall_ns(f"rim_n_{i}", i, 2.0, 0, RIM)
for j in range(2):
    b.wall_ew(f"rim_w_{j}", 0.0, j, 0, RIM)
for j in range(2):
    b.wall_ew(f"rim_e_{j}", 4.0, j, 0, RIM)

# =================================================================
# 3. 中央双隔墙 (x=2 公共拼缝上)
# =================================================================
b.wall_ew("div_s", 2.0, 0, 0, DIV)
b.wall_ew("div_n", 2.0, 1, 0, DIV)

# =================================================================
# 4. 台面: 四片长板 (z=1), 短边吸墙顶/隔墙顶, 板板互吸
# =================================================================
b.flat_rect("top_sw", 0, 0, 1.0, TOP)
b.flat_rect("top_nw", 0, 1, 1.0, TOP)
b.flat_rect("top_se", 2, 0, 1.0, TOP)
b.flat_rect("top_ne", 2, 1, 1.0, TOP)

# =================================================================
# 5. 台面四角热气小旗 (与墙顶整边重合)
# =================================================================
b.crest_ns("steam_nw", 0, 2.0, 1.0, STEAM)
b.crest_ns("steam_ne", 3, 2.0, 1.0, STEAM)
b.crest_ns("steam_sw", 1, 0.0, 1.0, STEAM)
b.crest_ns("steam_se", 2, 0.0, 1.0, STEAM)

# =================================================================
# 教程步骤 (5 步)
# =================================================================
b.step(
    "铺地台: 两片黄色大正方形并排吸合, 一片顶四片小方, 地基一步到位。",
    ["base_w", "base_e"],
    tip="大正方形边长 2, 一条边能同时吸住两片小方 —— 记住这招。",
)
b.step(
    "围南墙与西墙: 六片橙色方板墙脚整边骑住大方板边, 逐片手拉手。",
    ["rim_s_0", "rim_s_1", "rim_s_2", "rim_s_3", "rim_w_0", "rim_w_1"],
    highlight=["base_w"],
)
b.step(
    "围北墙、东墙并立中央隔墙: 八片墙合拢一圈, 隔墙骑住两片大方的公共拼缝, 盒腔分成两格。",
    ["rim_n_0", "rim_n_1", "rim_n_2", "rim_n_3",
     "rim_e_0", "rim_e_1", "div_s", "div_n"],
    highlight=["rim_s_0", "rim_w_0"],
    tip="先合围再封顶 —— 装配顺序也是设计的一部分。",
)
b.step(
    "拼台面: 四片黄色长板盖上墙顶, 短边吸墙沿、长边压住两片共线墙顶, 板板互吸成整面。",
    ["top_sw", "top_nw", "top_se", "top_ne"],
    highlight=["rim_w_0", "div_s"],
    tip="台面放杯子, 盒腔收杯垫 —— 一物两用的秘密在这一步。",
)
b.step(
    "升热气小旗: 四片粉色三角骑上台面四角, 双杯位茶歇开张!",
    ["steam_nw", "steam_ne", "steam_sw", "steam_se"],
    highlight=["top_nw", "top_se"],
)

model = b.finalize(
    model_id="cup_coaster_01",
    name="双杯位杯垫台",
    name_en="Cup Coaster Station 01",
    description=(
        "入门档实用功能: 茶几上的双杯位杯垫台, 结构签名是'大方地台"
        "封顶盒' —— 两片大正方形地台四边各同吸两片共线围墙墙脚 "
        "(R2 长短边完整贴合), 中央双隔墙骑住公共拼缝把盒腔分成两格, "
        "顶上四片长板短边吸墙沿、长边压共线墙顶拼成整层台面, 台面"
        "放杯子、盒腔收杯垫一物两用; 四角粉色热气小旗提醒: 热饮请"
        "放杯垫上。24 片全程受压零悬挑, 4 岁小手也能一次合围成功。"
    ),
    difficulty=1,
    tags=["实用功能", "杯垫", "茶几", "收纳", "入门"],
    min_pieces=24,
    min_steps=5,
)

# ---- series 归类落盘 (CONTENT_STRATEGY.md 4.3 节: 入库必填) --------
out = Path(__file__).resolve().parent.parent / "data" / "models" / "cup_coaster_01.json"
model["content_meta"] = {
    "series": "practical_utility",
    "structural_signature": model["content_meta"]["structural_signature"],
}
out.write_text(json.dumps(model, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print("已写入 series=practical_utility")
