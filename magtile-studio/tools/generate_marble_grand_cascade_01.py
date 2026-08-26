#!/usr/bin/env python3
"""生成模型 data/models/marble_grand_cascade_01.json (瀑布双道滚珠梯台)。

滚珠乐园 D5 旗舰: 双道并行直落瀑布 (T08) —— 2x2 三层发球塔向东
甩出两条并排赛道, 经两级门式梯台 (栈桥墩 + 门柱 + 台板三件互吸)
三段 30 度坡道直落地面接珠池; 全程黄三角中央分道堤隔开双珠,
池尾六边形靶标 + 竖长方形冲线旗门。与 D4 螺旋滚珠塔 (绕塔盘旋)
的动线拓扑完全不同: 不转向, 比直线加速。
用法: python3 tools/generate_marble_grand_cascade_01.py
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from magtile_gen import ModelBuilder, HEX_APOTHEM, SQ3  # noqa: E402

b = ModelBuilder()

TOWER = "blue"       # 发球塔
PAD = "green"        # 塔基
DECK = "yellow"      # 发球台
RAMP = "orange"      # 坡道
PIER = "gray"        # 栈桥墩 / 门柱
PLAT = "cyan"        # 梯台台板
RAIL = "red"         # 挡珠围栏
DIV = "yellow"       # 中央分道堤
BASIN = "blue"       # 接珠池
FLAG = "pink"        # 冲线旗门
BRACE = "purple"     # 塔内斜撑

# 梯台 x 坐标 (坡道水平投影 sqrt(3), 全部落在非整数网格线上)
T1 = 2 + SQ3                 # 3.732051  一级梯台西缘
T1E = T1 + 2                 # 5.732051  一级梯台东缘
T2 = T1E + SQ3               # 7.464102  二级梯台西缘
T2E = T2 + 1                 # 8.464102  二级梯台东缘
BX = T2E + SQ3               # 10.196153 接珠池西缘

# ---- 1. 发球塔: 2x2 塔基 + 三层环圈 + 塔内斜撑 + 发球台 ------------
for j in range(2):
    for i in range(2):
        b.flat(f"pad_{i}_{j}", i, j, 0.0, PAD if (i + j) % 2 == 0 else "cyan")
for lv in range(3):
    c = TOWER if lv % 2 == 0 else "cyan"
    for i in range(2):
        b.wall_ns(f"tw{lv}_s_{i}", i, 0.0, lv, c)
        b.wall_ns(f"tw{lv}_n_{i}", i, 2.0, lv, c)
    for j in range(2):
        b.wall_ew(f"tw{lv}_w_{j}", 0.0, j, lv, c)
        b.wall_ew(f"tw{lv}_e_{j}", 2.0, j, lv, c)
b.brace("tw_br_s", (1.0, 0.0, 0.0), "+y", BRACE)
b.brace("tw_br_n", (1.0, 2.0, 0.0), "-y", BRACE)
for j in range(2):
    for i in range(2):
        b.flat(f"deck_{i}_{j}", i, j, 3.0, DECK)
# 发球台围栏: 南北黄三角 + 西缘双等腰高塔柱 (东缘全开 —— 双道出珠口)
b.crest_ns("dk_rail_s0", 0, 0.0, 3.0, RAIL)
b.crest_ns("dk_rail_s1", 1, 0.0, 3.0, RAIL)
b.crest_ns("dk_rail_n0", 0, 2.0, 3.0, RAIL)
b.crest_ns("dk_rail_n1", 1, 2.0, 3.0, RAIL)
b.spire_ew("dk_mast_0", 0.0, 0, 3.0, "purple")
b.spire_ew("dk_mast_1", 0.0, 1, 3.0, "purple")

# ---- 2. 第一落差 (z3 -> z2): 双坡道 + 双层栈桥墩/门柱 + 2x2 梯台 ---
for lane in (0, 1):
    b.wall_ew(f"p1_{lane}_a", T1, lane, 0, PIER)     # 栈桥墩下层
    b.wall_ew(f"p1_{lane}_b", T1, lane, 1, PIER)     # 栈桥墩上层, 顶边接坡尾
    b.wall_ew(f"c1_{lane}_a", T1E, lane, 0, PIER)    # 东门柱下层
    b.wall_ew(f"c1_{lane}_b", T1E, lane, 1, PIER)    # 东门柱上层, 顶边接台板东缘
    b.ramp(f"r1_{lane}", "+x", 2.0, lane, 3.0, RAMP)
    b.flat(f"t1w_{lane}", T1, lane, 2.0, PLAT)       # 台板西列
    b.flat(f"t1e_{lane}", T1 + 1, lane, 2.0, PLAT)   # 台板东列
# 一级梯台围栏: 南北挡珠 + 中央分道堤
b.crest_ns("t1_rail_s0", T1, 0.0, 2.0, RAIL)
b.crest_ns("t1_rail_s1", T1 + 1, 0.0, 2.0, RAIL)
b.crest_ns("t1_rail_n0", T1, 2.0, 2.0, RAIL)
b.crest_ns("t1_rail_n1", T1 + 1, 2.0, 2.0, RAIL)
b.crest_ns("t1_div_0", T1, 1.0, 2.0, DIV)
b.crest_ns("t1_div_1", T1 + 1, 1.0, 2.0, DIV)

# ---- 3. 第二落差 (z2 -> z1): 双坡道 + 单层墩/柱 + 1x2 梯台 ---------
for lane in (0, 1):
    b.wall_ew(f"p2_{lane}", T2, lane, 0, PIER)
    b.wall_ew(f"c2_{lane}", T2E, lane, 0, PIER)
    b.ramp(f"r2_{lane}", "+x", T1E, lane, 2.0, RAMP)
    b.flat(f"t2_{lane}", T2, lane, 1.0, PLAT)
b.crest_ns("t2_rail_s", T2, 0.0, 1.0, RAIL)
b.crest_ns("t2_rail_n", T2, 2.0, 1.0, RAIL)
b.crest_ns("t2_div", T2, 1.0, 1.0, DIV)

# ---- 4. 冲线坡道 (z1 -> 落地) + 接珠池 -----------------------------
for lane in (0, 1):
    b.ramp(f"r3_{lane}", "+x", T2E, lane, 1.0, RAMP)
for j in range(2):
    b.flat(f"bs_w_{j}", BX, j, 0.0, BASIN)
    b.flat(f"bs_e_{j}", BX + 1, j, 0.0, BASIN if j == 0 else "cyan")
b.wall_ns("bw_s0", BX, 0.0, 0, BASIN)
b.wall_ns("bw_s1", BX + 1, 0.0, 0, BASIN)
b.wall_ns("bw_n0", BX, 2.0, 0, BASIN)
b.wall_ns("bw_n1", BX + 1, 2.0, 0, BASIN)
b.wall_ew("bw_e0", BX + 2, 0, 0, BASIN)
b.wall_ew("bw_e1", BX + 2, 1, 0, BASIN)
# 六边形靶标: 南北墙顶各立一面, 隔池相对 (双珠各撞各的锣)
b.add("hex_0", "hexagon", (BX + 0.5, 0.0, 1 + HEX_APOTHEM), (90, 0, 0), DECK)
b.add("hex_1", "hexagon", (BX + 0.5, 2.0, 1 + HEX_APOTHEM), (90, 0, 0), DECK)
# 双冲线旗门: 竖长方形并肩立在东墙顶, 中缝竖边整边互吸
b.place_edge("flag_0", "rectangle", 1,
             (BX + 2, 0.0, 1.0), (BX + 2, 1.0, 1.0), (0, 0, 1), FLAG)
b.place_edge("flag_1", "rectangle", 1,
             (BX + 2, 1.0, 1.0), (BX + 2, 2.0, 1.0), (0, 0, 1), FLAG)

# ---- 教程步骤 (25 步) ----------------------------------------------
b.step("铺发球塔塔基: 2x2 共 4 片方板整边互吸。",
       [f"pad_{i}_{j}" for j in range(2) for i in range(2)],
       tip="赛道向东直落约 12 格 —— 塔基靠桌面西端摆放。")
b.step("塔身一层·南墙与西墙 (4 片)。",
       ["tw0_s_0", "tw0_s_1", "tw0_w_0", "tw0_w_1"],
       highlight=["pad_0_0"],
       tip="2x2 塔身四角竖缝两两互吸, 环圈自锁。")
b.step("塔身一层·北墙与东墙合圈 (4 片)。",
       ["tw0_n_0", "tw0_n_1", "tw0_e_0", "tw0_e_1"],
       highlight=["tw0_w_0"])
b.step("塔内斜撑 2 根: 直角边分吸塔基缝与墙角竖缝。",
       ["tw_br_s", "tw_br_n"], highlight=["tw0_s_0"],
       tip="斜撑要趁塔顶未封先装 —— 装完手就伸不进去了。")
b.step("塔身二层·南墙与西墙 (4 片)。",
       ["tw1_s_0", "tw1_s_1", "tw1_w_0", "tw1_w_1"],
       highlight=["tw0_s_0"])
b.step("塔身二层·北墙与东墙合圈 (4 片)。",
       ["tw1_n_0", "tw1_n_1", "tw1_e_0", "tw1_e_1"],
       highlight=["tw1_w_0"])
b.step("塔身三层·南墙与西墙 (4 片)。",
       ["tw2_s_0", "tw2_s_1", "tw2_w_0", "tw2_w_1"],
       highlight=["tw1_s_0"])
b.step("塔身三层·北墙与东墙合圈 (4 片)。",
       ["tw2_n_0", "tw2_n_1", "tw2_e_0", "tw2_e_1"],
       highlight=["tw2_w_0"])
b.step("发球台: 4 片黄方板压顶 (z=3)。",
       [f"deck_{i}_{j}" for j in range(2) for i in range(2)],
       highlight=["tw2_s_0"],
       tip="台面四边坐满墙顶 —— 剪断任何一条铰链仍有正交支撑。")
b.step("发球台南北围栏 4 片红三角 (东缘全开 —— 双道出珠口)。",
       ["dk_rail_s0", "dk_rail_s1", "dk_rail_n0", "dk_rail_n1"],
       highlight=["deck_0_0"])
b.step("西缘双紫色等腰高塔柱 (塔尖 z≈5) —— 全场地标。",
       ["dk_mast_0", "dk_mast_1"], highlight=["deck_0_0"],
       tip="高塔柱底边整边吸台面西沿, 轻拿轻放。")
b.step("南道第一落差: 双层栈桥墩 + 双层门柱 + 坡道 + 台板西/东列 "
       "三件互吸成门式梯台。",
       ["p1_0_a", "p1_0_b", "c1_0_a", "c1_0_b", "r1_0", "t1w_0", "t1e_0"],
       highlight=["tw2_e_0", "deck_1_0"],
       tip="坡道顶边整边吸台面东沿, 坡尾由墩顶接住, 台板再压墩顶与柱顶。")
b.step("北道第一落差: 与南道并排同法安装 (7 片)。",
       ["p1_1_a", "p1_1_b", "c1_1_a", "c1_1_b", "r1_1", "t1w_1", "t1e_1"],
       highlight=["p1_0_a", "r1_0"])
b.step("一级梯台南北挡珠 4 片红三角。",
       ["t1_rail_s0", "t1_rail_s1", "t1_rail_n0", "t1_rail_n1"],
       highlight=["t1w_0"])
b.step("一级梯台中央分道堤 2 片黄三角 —— 双珠各行其道。",
       ["t1_div_0", "t1_div_1"], highlight=["t1w_0", "t1w_1"],
       tip="分道堤立在两列台板的共享缝上, 底边同时吸住两侧台板。")
b.step("第二落差: 单层墩/柱 + 双坡道 + 1x2 梯台一次成组 (8 片)。",
       ["p2_0", "p2_1", "c2_0", "c2_1", "r2_0", "r2_1", "t2_0", "t2_1"],
       highlight=["t1e_0", "c1_0_b"],
       tip="坡道顶边吸一级梯台东沿与门柱顶 —— 三件互吸零悬挑。")
b.step("二级梯台挡珠与分道堤 (3 片)。",
       ["t2_rail_s", "t2_rail_n", "t2_div"], highlight=["t2_0"])
b.step("双冲线坡道: 顶边吸二级梯台东沿, 坡尾直接落地。",
       ["r3_0", "r3_1"], highlight=["t2_0", "c2_0"],
       tip="坡尾自身接地 —— 弹珠由此冲进接珠池。")
b.step("接珠池地台西列 2 片, 西缘整边吸双坡尾。",
       ["bs_w_0", "bs_w_1"], highlight=["r3_0"])
b.step("接珠池地台东列 2 片。",
       ["bs_e_0", "bs_e_1"], highlight=["bs_w_0"])
b.step("接珠池南墙 2 片。",
       ["bw_s0", "bw_s1"], highlight=["bs_w_0"])
b.step("接珠池北墙 2 片。",
       ["bw_n0", "bw_n1"], highlight=["bs_w_1"])
b.step("接珠池东墙 2 片 —— 三面围合, 迎珠面敞开。",
       ["bw_e0", "bw_e1"], highlight=["bs_e_0"])
b.step("双六边形靶标: 南北墙顶各立一面, 隔池相对。",
       ["hex_0", "hex_1"], highlight=["bw_s0", "bw_n0"])
b.step("东墙顶并肩立 2 面粉色冲线旗门 (中缝竖边互吸) —— "
       "瀑布双道滚珠梯台完工!",
       ["flag_0", "flag_1"], highlight=["bw_e0", "bw_e1"],
       tip="双珠同时从发球台放手, 听哪面旗门先被撞响 —— 直线加速赛开始!")

if __name__ == "__main__":
    model = b.finalize(
        model_id="marble_grand_cascade_01",
        name="瀑布双道滚珠梯台",
        name_en="Marble Grand Cascade 01",
        description=(
            "滚珠乐园 D5 旗舰: 结构签名是'双道并行三段直落瀑布' —— "
            "三层发球塔向东甩出两条并排赛道, 每级落差由 30 度坡道 + "
            "栈桥墩 + 门柱 + 台板三件互吸构成门式梯台 (2x2 与 1x2 两级"
            "递减), 全程黄三角分道堤隔开双珠直线竞速, 冲线坡道落地滚入"
            "三面围合接珠池, 池尾六边形靶标与竖长方形旗门计分; 与 D4 "
            "螺旋滚珠塔 (绕塔盘旋转向) 的动线拓扑完全不同 —— 不转向, "
            "拼直线加速。"
        ),
        difficulty=5,
        tags=["滚珠", "滚珠乐园", "竞速", "梯台", "大师", "旗舰"],
        min_pieces=85,
        min_steps=25,
        series="marble_run",
    )

    meta = model["content_meta"]
    meta["build_paradigm"] = "module_dock"
    meta["technique_tags"] = {
        "primary": "T08_ball_run",
        "secondary": ["T11_mirror_build", "T12_layered_platform"],
    }
    meta["signature_statement"] = (
        "双道并行三段直落瀑布: 门式梯台逐级递减, 双珠直线竞速不转向。"
    )
    meta["physical_risk_notes"] = [
        {"step": 12, "risk": "台板压上墩顶前, 坡道仅靠顶边单线吸合最易脱落",
         "mitigation": "教程按 墩->柱->坡道->台板 顺序成组安装, 三件互吸后自锁"},
        {"step": 18, "risk": "冲线坡道坡尾落地瞬间若未对准, 珠道错缝卡珠",
         "mitigation": "tip 提示坡尾自身接地, 接珠池西列地台随后整边锁缝"},
    ]
    meta["structural_signature"]["silhouette_class"] = "cascade_race"
    meta["structural_signature"]["height_layers"] = 6

    out = Path(__file__).resolve().parent.parent / \
        "data/models/marble_grand_cascade_01.json"
    out.write_text(json.dumps(model, ensure_ascii=False, indent=2) + "\n",
                   encoding="utf-8")
    print(f"已重写 {out} (含旗舰元数据)")
