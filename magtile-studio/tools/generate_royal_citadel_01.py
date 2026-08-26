#!/usr/bin/env python3
"""生成模型 data/models/royal_citadel_01.json (王城四塔要塞)。

城堡与要塞 D5 旗舰: 6x6 同心要塞 —— 四座三段式角楼 (环圈自锁 +
等边四坡锥顶) 锁定环形幕墙, 南门楼双塔夹长方形门楣, 中央主堡
双层长板环梁圈托梯形四坡大顶 (hip_roof2); 幕墙沿口雉堞冠, 庭院
内侧八根直角斜撑 (T14) 锁墙脚。
用法: python3 tools/generate_royal_citadel_01.py
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from magtile_gen import ModelBuilder  # noqa: E402

b = ModelBuilder()

STONE = "gray"       # 幕墙石
PAVE = "cyan"        # 庭院石板
TOWER = "blue"       # 角楼
ROOF = "red"         # 角楼锥顶 / 主堡大顶
KEEP = "orange"      # 主堡
CREST = "yellow"     # 雉堞
BRACE = "purple"     # 斜撑
GATE = "green"       # 门楼

# ---- 1. 地台: 6x6 环形边廊 + 门道 + 主堡台基 ----------------------
BORDER = [(i, j) for j in range(6) for i in range(6)
          if i in (0, 5) or j in (0, 5)]
for i, j in BORDER:
    b.flat(f"fl_{i}_{j}", i, j, 0.0, STONE if (i + j) % 2 == 0 else PAVE)
b.flat("path_2", 2, 1, 0.0, PAVE)
b.flat("path_3", 3, 1, 0.0, STONE)
# 主堡台基: 两片 2x1 长板 (长边朝南北, 供环梁圈整边吸合)
b.flat_rect("keep_pad_s", 2, 2, 0.0, KEEP, axis="x")
b.flat_rect("keep_pad_n", 2, 3, 0.0, KEEP, axis="x")

# ---- 2. 幕墙一层 (z 0..1, 南门洞 x 2..4 敞开) ----------------------
SOUTH_X = (0, 1, 4, 5)
for i in SOUTH_X:
    b.wall_ns(f"cw_s_{i}", i, 0.0, 0, STONE)
for i in range(6):
    b.wall_ns(f"cw_n_{i}", i, 6.0, 0, STONE)
for j in range(6):
    b.wall_ew(f"cw_w_{j}", 0.0, j, 0, STONE)
for j in range(6):
    b.wall_ew(f"cw_e_{j}", 6.0, j, 0, STONE)

# ---- 3. 南门楼 (z 1..2): 双塔夹门楣 + 雉堞 -------------------------
b.wall_ns("gh_w", 1, 0.0, 1, GATE)
b.wall_ns("gh_e", 4, 0.0, 1, GATE)
b.lintel_ns("gh_lintel", 2, 0.0, 1, GATE)
b.crest_ns("gh_crest_w", 1, 0.0, 2.0, CREST)
b.crest_ns("gh_crest_e", 4, 0.0, 2.0, CREST)

# ---- 4. 四角楼: 一层补内壁 + 二层环圈 + 等边四坡锥顶 ---------------
# (corner_x, corner_y): 角楼占格; 每座一层由两段幕墙 + 两段内壁закрыть
TOWERS = {
    "sw": (0, 0),
    "se": (5, 0),
    "nw": (0, 5),
    "ne": (5, 5),
}
for tag, (cx, cy) in TOWERS.items():
    # 一层内壁 (幕墙已给外侧两面)
    inner_y = cy + 1 if cy == 0 else cy       # 内侧南北墙所在网格线
    inner_x = cx + 1 if cx == 0 else cx       # 内侧东西墙所在网格线
    b.wall_ns(f"tw_{tag}_L1n", cx, float(inner_y), 0, TOWER)
    b.wall_ew(f"tw_{tag}_L1e", float(inner_x), cy, 0, TOWER)
    # 二层环圈 (四面闭合, 环圈自锁)
    b.wall_ns(f"tw_{tag}_L2s", cx, float(cy), 1, TOWER)
    b.wall_ns(f"tw_{tag}_L2n", cx, float(cy + 1), 1, TOWER)
    b.wall_ew(f"tw_{tag}_L2w", float(cx), cy, 1, TOWER)
    b.wall_ew(f"tw_{tag}_L2e", float(cx + 1), cy, 1, TOWER)
    # 等边四坡锥顶 (锥尖 z=2.707, 四斜棱两两互吸自锁)
    b.hat4(f"tw_{tag}_roof", cx, cy, 2.0, ROOF,
           shape="equilateral_triangle")

# ---- 5. 幕墙雉堞冠 (z=1 沿口, 避开角楼与门楼) ----------------------
for i in (1, 2, 3, 4):
    b.crest_ns(f"cr_n_{i}", i, 6.0, 1.0, CREST)
for j in (1, 2, 3, 4):
    b.crest_ew(f"cr_w_{j}", 0.0, j, 1.0, CREST)
for j in (1, 2, 3, 4):
    b.crest_ew(f"cr_e_{j}", 6.0, j, 1.0, CREST)

# ---- 6. 中央主堡: 双层长板环梁圈 + 梯形四坡大顶 --------------------
# 一层环梁圈 (z 0..1): 南北长板底边整边吸台基长边, 四角短边互吸
b.lintel_ns("kp_L1_s", 2, 2.0, 0, KEEP)
b.lintel_ns("kp_L1_n", 2, 4.0, 0, KEEP)
b.lintel_ew("kp_L1_w", 2.0, 2, 0, KEEP)
b.lintel_ew("kp_L1_e", 4.0, 2, 0, KEEP)
# 二层环梁圈 (z 1..2)
b.lintel_ns("kp_L2_s", 2, 2.0, 1, KEEP)
b.lintel_ns("kp_L2_n", 2, 4.0, 1, KEEP)
b.lintel_ew("kp_L2_w", 2.0, 2, 1, KEEP)
b.lintel_ew("kp_L2_e", 4.0, 2, 1, KEEP)
# 梯形四坡大顶 + 压顶 (压顶 z=2.707)
KP_ROOF, KP_CAP = b.hip_roof2("kp_roof", 2, 2, 2.0, ROOF, cap_color=CREST)

# ---- 7. 庭院斜撑 (T14): 直角边分吸地台边与幕墙竖缝 -----------------
b.brace("br_s_w", (2.0, 0.0, 0.0), "+y", BRACE)
b.brace("br_s_e", (4.0, 0.0, 0.0), "+y", BRACE)
b.brace("br_n_w", (2.0, 6.0, 0.0), "-y", BRACE)
b.brace("br_n_e", (4.0, 6.0, 0.0), "-y", BRACE)
b.brace("br_w_s", (0.0, 2.0, 0.0), "+x", BRACE)
b.brace("br_w_n", (0.0, 4.0, 0.0), "+x", BRACE)
b.brace("br_e_s", (6.0, 2.0, 0.0), "-x", BRACE)
b.brace("br_e_n", (6.0, 4.0, 0.0), "-x", BRACE)

# ---- 教程步骤 (27 步) ----------------------------------------------
b.step("铺南侧边廊地台: 6 片石板一字排开, 相邻整边互吸。",
       [f"fl_{i}_0" for i in range(6)],
       tip="要塞占地 6x6 —— 桌面正中先铺南廊, 四周留足场地。")
b.step("铺西侧边廊地台 (5 片, 向北延伸)。",
       [f"fl_0_{j}" for j in range(1, 6)], highlight=["fl_0_0"],
       tip="西廊每片先吸住南邻再落位, 保证整条边廊单一连通。")
b.step("铺东侧边廊地台 (5 片)。",
       [f"fl_5_{j}" for j in range(1, 6)], highlight=["fl_5_0"])
b.step("北侧边廊合龙 (4 片) —— 环形边廊闭合。",
       [f"fl_{i}_5" for i in (1, 2, 3, 4)],
       highlight=["fl_0_5", "fl_5_5"],
       tip="边廊闭环后地台成刚性回字框, 后续高墙都锚在它上面。")
b.step("门道与主堡台基: 2 片门道石板 + 2 片 2x1 长板台基。",
       ["path_2", "path_3", "keep_pad_s", "keep_pad_n"],
       highlight=["fl_2_0"],
       tip="长板台基长边朝南北 —— 主堡环梁圈要整边吸在长边上。")
b.step("南幕墙一层: 门洞两侧各立 2 段石墙 (x 2..4 留作城门)。",
       [f"cw_s_{i}" for i in SOUTH_X], highlight=["fl_1_0"],
       tip="墙底整边吸地台外沿, 门洞宽 2 格 —— 门楣稍后跨上去。")
b.step("西幕墙一层: 6 段石墙, 与南墙西端竖缝互吸。",
       [f"cw_w_{j}" for j in range(6)], highlight=["cw_s_0"])
b.step("东幕墙一层: 6 段石墙。",
       [f"cw_e_{j}" for j in range(6)], highlight=["cw_s_5"])
b.step("北幕墙一层合龙: 6 段石墙 —— 环形幕墙闭合成圈。",
       [f"cw_n_{i}" for i in range(6)],
       highlight=["cw_w_5", "cw_e_5"],
       tip="幕墙四角竖缝两两互吸, 闭环后整圈不再是自由铰链。")
b.step("庭院斜撑·南北 (4 根): 直角边分别吸地台边与幕墙竖缝。",
       ["br_s_w", "br_s_e", "br_n_w", "br_n_e"],
       highlight=["cw_s_1"],
       tip="斜撑是结构件不是装饰 —— 它把幕墙脚锁成三角刚性节点。")
b.step("庭院斜撑·东西 (4 根)。",
       ["br_w_s", "br_w_n", "br_e_s", "br_e_n"],
       highlight=["cw_w_2"])
b.step("南门楼二层: 双塔身夹 1 片长方形门楣 (先塔后楣)。",
       ["gh_w", "gh_e", "gh_lintel"], highlight=["cw_s_1"],
       tip="门楣两端短竖边分别吸左右塔身竖缝 —— 双路径受力。")
b.step("门楼雉堞: 双塔顶各立 1 片黄色三角冠。",
       ["gh_crest_w", "gh_crest_e"], highlight=["gh_lintel"])
b.step("西南角楼一层内壁 (2 段) 补全环圈。",
       ["tw_sw_L1n", "tw_sw_L1e"], highlight=["cw_s_0", "cw_w_0"],
       tip="内壁底边吸地台, 竖缝吸幕墙 —— 一层四面闭合。")
b.step("西南角楼二层环圈 (4 段, 四角竖缝自锁)。",
       ["tw_sw_L2s", "tw_sw_L2n", "tw_sw_L2w", "tw_sw_L2e"],
       highlight=["tw_sw_L1n"])
b.step("西南角楼锥顶: 4 片等边三角四坡合尖 (斜棱两两互吸)。",
       [f"tw_sw_roof_{s}" for s in ("s", "e", "n", "w")],
       highlight=["tw_sw_L2s"],
       tip="四坡锥顶自锁成环 —— 装最后一片前先把前三片棱边对准。")
b.step("东南角楼一层内壁 + 二层环圈 (6 段)。",
       ["tw_se_L1n", "tw_se_L1e", "tw_se_L2s", "tw_se_L2n",
        "tw_se_L2w", "tw_se_L2e"],
       highlight=["cw_s_5", "cw_e_0"])
b.step("东南角楼锥顶 (4 片)。",
       [f"tw_se_roof_{s}" for s in ("s", "e", "n", "w")],
       highlight=["tw_se_L2s"])
b.step("西北角楼一层内壁 + 二层环圈 (6 段)。",
       ["tw_nw_L1n", "tw_nw_L1e", "tw_nw_L2s", "tw_nw_L2n",
        "tw_nw_L2w", "tw_nw_L2e"],
       highlight=["cw_n_0", "cw_w_5"])
b.step("西北角楼锥顶 (4 片)。",
       [f"tw_nw_roof_{s}" for s in ("s", "e", "n", "w")],
       highlight=["tw_nw_L2s"])
b.step("东北角楼一层内壁 + 二层环圈 (6 段)。",
       ["tw_ne_L1n", "tw_ne_L1e", "tw_ne_L2s", "tw_ne_L2n",
        "tw_ne_L2w", "tw_ne_L2e"],
       highlight=["cw_n_5", "cw_e_5"])
b.step("东北角楼锥顶 (4 片) —— 四楼齐峰。",
       [f"tw_ne_roof_{s}" for s in ("s", "e", "n", "w")],
       highlight=["tw_ne_L2s"])
b.step("北幕墙雉堞冠 (4 片黄三角, 底边吸墙顶沿口)。",
       [f"cr_n_{i}" for i in (1, 2, 3, 4)], highlight=["cw_n_1"])
b.step("西幕墙雉堞冠 (4 片)。",
       [f"cr_w_{j}" for j in (1, 2, 3, 4)], highlight=["cw_w_1"])
b.step("东幕墙雉堞冠 (4 片)。",
       [f"cr_e_{j}" for j in (1, 2, 3, 4)], highlight=["cw_e_1"])
b.step("主堡一层环梁圈: 4 片 2x1 长板立墙, 底边整边吸台基长边, "
       "四角短竖边两两互吸。",
       ["kp_L1_s", "kp_L1_n", "kp_L1_w", "kp_L1_e"],
       highlight=["keep_pad_s"],
       tip="先南北后东西 —— 东西长板落位时两端同时吸角。")
b.step("主堡二层环梁圈 (4 片, 与一层同法叠圈)。",
       ["kp_L2_s", "kp_L2_n", "kp_L2_w", "kp_L2_e"],
       highlight=["kp_L1_s"])
b.step("主堡梯形四坡大顶 + 黄压顶 —— 王城要塞落成!",
       KP_ROOF + [KP_CAP], highlight=["kp_L2_s"],
       tip="四片梯形下底整边吸环梁圈顶, 腰边两两互吸, 压顶最后落位。")

if __name__ == "__main__":
    model = b.finalize(
        model_id="royal_citadel_01",
        name="王城四塔要塞",
        name_en="Royal Citadel 01",
        description=(
            "城堡与要塞 D5 旗舰: 结构签名是'回字形三重防线' —— 6x6 环形"
            "边廊地台锚定环形幕墙 (四角竖缝闭环 + 庭院八根斜撑锁脚), 四座"
            "三段式角楼以二层环圈自锁托等边四坡锥顶, 南门楼双塔夹长方形"
            "门楣; 中央主堡用双层 2x1 长板环梁圈叠圈, 顶上梯形四坡大顶"
            "压顶合尖 —— 与 D3 城堡塔楼 (单塔) 和 D4 城堡吊桥 (机构叙事)"
            "的防御纵深完全不同。"
        ),
        difficulty=5,
        tags=["城堡", "要塞", "角楼", "雉堞", "大师", "旗舰"],
        min_pieces=115,
        min_steps=27,
        series="castle_fortress",
    )

    meta = model["content_meta"]
    meta["build_paradigm"] = "outline_first"
    meta["technique_tags"] = {
        "primary": "T01_box_frame",
        "secondary": ["T14_diagonal_bracing", "T17_negative_space"],
    }
    meta["signature_statement"] = (
        "回字形三重防线: 环形幕墙、四座锥顶角楼与长板环梁主堡逐圈向心收拢。"
    )
    meta["physical_risk_notes"] = [
        {"step": 11, "risk": "门楣跨门洞落位时若只吸单端, 另一端悬空易坠",
         "mitigation": "教程要求先立双塔身, 门楣两端短竖边同时对准再放手"},
        {"step": 27, "risk": "梯形大顶第四片合围前, 前三片腰边为半开环",
         "mitigation": "tip 提示装最后一片前先把前三片棱边对准, 一次合尖"},
    ]
    meta["structural_signature"]["silhouette_class"] = "concentric_fortress"
    meta["structural_signature"]["height_layers"] = 5

    out = Path(__file__).resolve().parent.parent / "data/models/royal_citadel_01.json"
    out.write_text(json.dumps(model, ensure_ascii=False, indent=2) + "\n",
                   encoding="utf-8")
    print(f"已重写 {out} (含旗舰元数据)")
