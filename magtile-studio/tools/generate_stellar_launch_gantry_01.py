#!/usr/bin/env python3
"""生成模型 data/models/stellar_launch_gantry_01.json (星港发射塔组合体)。

航天器 D5 旗舰: 发射场三模块对接 (T16) —— 2x2 三级重型火箭
(方墙环圈 x3 + 长板过渡环 + 梯形整流罩合尖) + 1x2 五层勤务塔
(顶层观测甲板 + 等腰避雷尖塔) 以 z=3 脐带桥对接, 东侧双穹顶
燃料罐区; 火箭四片直角尾翼与勤务塔斜撑均为双边吸合结构件。
用法: python3 tools/generate_stellar_launch_gantry_01.py
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from magtile_gen import ModelBuilder  # noqa: E402

b = ModelBuilder()

APRON = "gray"       # 发射场坪
CRAWL = "yellow"     # 履带运输道
ROCKET = "clear"     # 火箭箭体 (白箭涂装用透明近似)
STAGE = "red"        # 级间环
FAIR = "orange"      # 整流罩
FIN = "red"          # 尾翼
GANTRY = "blue"      # 勤务塔
DECK = "cyan"        # 观测甲板
TANK = "green"       # 燃料罐
WARN = "orange"      # 警戒标
BRACE = "purple"     # 斜撑

# ---- 1. 场坪: 履带道 (y1) + 发射坪双排 (y2/y3) ---------------------
for x in range(8):
    b.flat(f"cl_{x}", x, 1, 0.0, CRAWL if x % 2 == 0 else APRON)
for x in range(8):
    b.flat(f"ap_s_{x}", x, 2, 0.0, APRON if x % 2 == 0 else "cyan")
for x in range(8):
    b.flat(f"ap_n_{x}", x, 3, 0.0, "cyan" if x % 2 == 0 else APRON)

# ---- 2. 重型火箭 (x 1..3, y 2..4): 三级环圈 + 过渡环 + 整流罩 ------
for lv in range(3):
    c = ROCKET if lv != 1 else STAGE
    for i in (1, 2):
        b.wall_ns(f"rk{lv}_s_{i}", i, 2.0, lv, c)
        b.wall_ns(f"rk{lv}_n_{i}", i, 4.0, lv, c)
    for j in (2, 3):
        b.wall_ew(f"rk{lv}_w_{j}", 1.0, j, lv, c)
        b.wall_ew(f"rk{lv}_e_{j}", 3.0, j, lv, c)
# 肩部甲板 (z=3): 2 片 2x1 长板, 短边整边吸三级环东西墙顶,
# 长边向过渡环长板提供整边吸合基座
b.flat_rect("rk_deck_s", 1, 2, 3.0, STAGE, axis="x")
b.flat_rect("rk_deck_n", 1, 3, 3.0, STAGE, axis="x")
# 过渡环 (z 3..4): 4 片 2x1 长板立墙, 南北底边整边吸甲板长边, 四角短竖边互吸
b.lintel_ns("rk3_s", 1, 2.0, 3, STAGE)
b.lintel_ns("rk3_n", 1, 4.0, 3, STAGE)
b.lintel_ew("rk3_w", 1.0, 2, 3, STAGE)
b.lintel_ew("rk3_e", 3.0, 2, 3, STAGE)
# 整流罩: 梯形四坡合尖 + 压顶 (顶 z=4.707)
NOSE, NOSE_CAP = b.hip_roof2("nose", 1, 2, 4.0, FAIR, cap_color=CRAWL)
# 尾翼: 4 片直角三角形, 直角边分吸场坪边与箭体竖棱
b.brace("fin_sw", (1.0, 2.0, 0.0), "-x", FIN)
b.brace("fin_nw", (1.0, 4.0, 0.0), "-x", FIN)
b.brace("fin_se", (3.0, 2.0, 0.0), "+x", FIN)
b.brace("fin_ne", (3.0, 4.0, 0.0), "+x", FIN)

# ---- 3. 勤务塔 (x 4..5, y 2..4): 五层环圈 + 甲板 + 避雷尖塔 --------
for lv in range(4):
    b.wall_ns(f"gt{lv}_s", 4, 2.0, lv, GANTRY)
    b.wall_ns(f"gt{lv}_n", 4, 4.0, lv, GANTRY)
    for j in (2, 3):
        b.wall_ew(f"gt{lv}_w_{j}", 4.0, j, lv, GANTRY)
        b.wall_ew(f"gt{lv}_e_{j}", 5.0, j, lv, GANTRY)
# 塔脚斜撑 (东侧, 直角边分吸场坪边与塔身竖棱)
b.brace("gt_br_s", (5.0, 2.0, 0.0), "+x", BRACE)
b.brace("gt_br_n", (5.0, 4.0, 0.0), "+x", BRACE)
# 脐带桥 (z=3): 两片方板西吸箭体三级环顶, 东吸塔身三层顶
b.flat("bridge_s", 3, 2, 3.0, DECK)
b.flat("bridge_n", 3, 3, 3.0, DECK)
# 观测甲板 (z=4)
b.flat("deck_s", 4, 2, 4.0, DECK)
b.flat("deck_n", 4, 3, 4.0, DECK)
# 甲板围栏 + 等腰避雷尖塔 (塔尖 z≈6)
b.crest_ns("dk_rail_n", 4, 4.0, 4.0, WARN)
b.crest_ew("dk_rail_e0", 5.0, 2, 4.0, WARN)
b.crest_ew("dk_rail_e1", 5.0, 3, 4.0, WARN)
b.spire_ns("dk_mast", 4, 2.0, 4.0, "pink")

# ---- 4. 燃料罐区 (x 6..7, y 2..4): 双联罐体 + 等边穹顶 -------------
b.wall_ns("tk_s", 6, 2.0, 0, TANK)
b.wall_ns("tk_m", 6, 3.0, 0, TANK)
b.wall_ns("tk_n", 6, 4.0, 0, TANK)
for j in (2, 3):
    b.wall_ew(f"tk_w_{j}", 6.0, j, 0, TANK)
    b.wall_ew(f"tk_e_{j}", 7.0, j, 0, TANK)
TANK_A = b.hat4("tk_dome_a", 6, 2, 1.0, TANK, shape="equilateral_triangle")
TANK_B = b.hat4("tk_dome_b", 6, 3, 1.0, TANK, shape="equilateral_triangle")

# ---- 5. 履带道警戒标 (南沿 4 片三角) -------------------------------
for k, x in enumerate((0, 2, 5, 7)):
    b.crest_ns(f"warn_{k}", x, 1.0, 0.0, WARN)

# ---- 教程步骤 (27 步) ----------------------------------------------
b.step("铺履带运输道西段: 4 片黄灰相间方板。",
       [f"cl_{x}" for x in range(4)],
       tip="发射场占地 8x3 —— 桌面横向留足场地再开工。")
b.step("履带道东段合龙 (4 片)。",
       [f"cl_{x}" for x in range(4, 8)], highlight=["cl_3"])
b.step("发射坪南排西段 (4 片, 吸住履带道北沿)。",
       [f"ap_s_{x}" for x in range(4)], highlight=["cl_0"])
b.step("发射坪南排东段 (4 片)。",
       [f"ap_s_{x}" for x in range(4, 8)], highlight=["ap_s_3"])
b.step("发射坪北排西段 (4 片)。",
       [f"ap_n_{x}" for x in range(4)], highlight=["ap_s_0"])
b.step("发射坪北排东段合龙 —— 场坪成刚性大底盘。",
       [f"ap_n_{x}" for x in range(4, 8)], highlight=["ap_n_3"])
b.step("火箭一级·南墙与西墙 (4 片): 墙底整边吸场坪。",
       ["rk0_s_1", "rk0_s_2", "rk0_w_2", "rk0_w_3"],
       highlight=["ap_s_1"],
       tip="2x2 箭体四角竖缝两两互吸 —— 环圈自锁是火箭站稳的关键。")
b.step("火箭一级·北墙与东墙合圈 (4 片)。",
       ["rk0_n_1", "rk0_n_2", "rk0_e_2", "rk0_e_3"],
       highlight=["rk0_w_2"])
b.step("四片直角尾翼: 直角边分别吸场坪边与箭体竖棱。",
       ["fin_sw", "fin_nw", "fin_se", "fin_ne"],
       highlight=["rk0_s_1"],
       tip="尾翼是结构件 —— 双边吸合后一级箭体成三角刚性节点。")
b.step("火箭二级·南墙与西墙 (4 片, 红色级间环)。",
       ["rk1_s_1", "rk1_s_2", "rk1_w_2", "rk1_w_3"],
       highlight=["rk0_s_1"])
b.step("火箭二级·北墙与东墙合圈 (4 片)。",
       ["rk1_n_1", "rk1_n_2", "rk1_e_2", "rk1_e_3"],
       highlight=["rk1_w_2"])
b.step("火箭三级·南墙与西墙 (4 片)。",
       ["rk2_s_1", "rk2_s_2", "rk2_w_2", "rk2_w_3"],
       highlight=["rk1_s_1"])
b.step("火箭三级·北墙与东墙合圈 (4 片)。",
       ["rk2_n_1", "rk2_n_2", "rk2_e_2", "rk2_e_3"],
       highlight=["rk2_w_2"])
b.step("肩部甲板: 2 片 2x1 长板压顶, 短边整边吸三级环东西墙顶。",
       ["rk_deck_s", "rk_deck_n"], highlight=["rk2_w_2"],
       tip="甲板长边朝南北 —— 过渡环长板要整边吸在甲板长边上。")
b.step("过渡环: 4 片 2x1 长板立墙 (先南北后东西), 四角短竖边互吸。",
       ["rk3_s", "rk3_n", "rk3_w", "rk3_e"],
       highlight=["rk_deck_s"],
       tip="长板环是整流罩的基座 —— 梯形下底要整边吸在长板顶边上。")
b.step("整流罩四坡合尖 + 黄压顶 (顶 z≈4.7)。",
       NOSE + [NOSE_CAP], highlight=["rk3_s"],
       tip="四片梯形腰边两两互吸自锁 —— 最后压顶前先对齐四条棱。")
b.step("勤务塔一层环圈 (6 片): 1x2 占地, 六段墙合圈。",
       ["gt0_s", "gt0_n", "gt0_w_2", "gt0_w_3", "gt0_e_2", "gt0_e_3"],
       highlight=["ap_s_4"])
b.step("塔脚斜撑 2 根 (东侧)。",
       ["gt_br_s", "gt_br_n"], highlight=["gt0_e_2"])
b.step("勤务塔二层环圈 (6 片)。",
       ["gt1_s", "gt1_n", "gt1_w_2", "gt1_w_3", "gt1_e_2", "gt1_e_3"],
       highlight=["gt0_s"])
b.step("勤务塔三层环圈 (6 片)。",
       ["gt2_s", "gt2_n", "gt2_w_2", "gt2_w_3", "gt2_e_2", "gt2_e_3"],
       highlight=["gt1_s"])
b.step("脐带桥对接: 2 片方板西缘吸箭体三级环顶, 东缘吸塔身三层顶。",
       ["bridge_s", "bridge_n"], highlight=["rk2_e_2", "gt2_w_2"],
       tip="桥板两端同时受力 —— 火箭与勤务塔从此连成一体 (T16 对接)。")
b.step("勤务塔四层环圈 (6 片)。",
       ["gt3_s", "gt3_n", "gt3_w_2", "gt3_w_3", "gt3_e_2", "gt3_e_3"],
       highlight=["gt2_s"])
b.step("观测甲板 (z=4): 2 片方板压顶合圈。",
       ["deck_s", "deck_n"], highlight=["gt3_s"])
b.step("甲板围栏 3 片 + 粉色等腰避雷尖塔 (塔尖 z≈6)。",
       ["dk_rail_n", "dk_rail_e0", "dk_rail_e1", "dk_mast"],
       highlight=["deck_s"],
       tip="尖塔底边整边吸甲板南沿 —— 全场最高点, 轻拿轻放。")
b.step("燃料罐区罐体: 7 段墙围出双联罐 (共用中隔墙)。",
       ["tk_s", "tk_m", "tk_n", "tk_w_2", "tk_w_3", "tk_e_2", "tk_e_3"],
       highlight=["ap_s_6"])
b.step("南罐等边穹顶 (4 片合尖)。",
       TANK_A, highlight=["tk_s"])
b.step("北罐等边穹顶 (4 片) —— 罐区完工。",
       TANK_B, highlight=["tk_m"])
b.step("履带道南沿 4 片橙色警戒标 —— 星港发射塔组合体落成!",
       [f"warn_{k}" for k in range(4)], highlight=["cl_0"],
       tip="点火倒计时: 检查脐带桥两端吸合, 就可以想象发射了。")

if __name__ == "__main__":
    model = b.finalize(
        model_id="stellar_launch_gantry_01",
        name="星港发射塔组合体",
        name_en="Stellar Launch Gantry 01",
        description=(
            "航天器 D5 旗舰: 结构签名是'三模块对接的发射场组合体' —— "
            "2x2 三级重型火箭 (方墙环圈自锁 x3 + 2x1 长板过渡环 + 梯形"
            "整流罩合尖, 四片直角尾翼双边吸合), 1x2 五段勤务塔 (四层"
            "环圈 + 观测甲板 + 等腰避雷尖塔至 z≈6), 两者以 z=3 脐带桥"
            "刚性对接 (T16); 东侧双联燃料罐共用中隔墙, 各顶等边穹顶。"
            "与 D4 火箭发射台 (单塔) 和 D3 航天飞机 (机身叙事) 的模块"
            "化程度完全不同。"
        ),
        difficulty=5,
        tags=["航天", "火箭", "发射台", "对接", "大师", "旗舰"],
        min_pieces=110,
        min_steps=26,
        series="spacecraft",
    )

    meta = model["content_meta"]
    meta["build_paradigm"] = "module_dock"
    meta["technique_tags"] = {
        "primary": "T16_modular_docking",
        "secondary": ["T01_box_frame", "T14_diagonal_bracing"],
    }
    meta["signature_statement"] = (
        "火箭、勤务塔、燃料罐三模块分立生长, 脐带桥在 z=3 一步刚性对接。"
    )
    meta["physical_risk_notes"] = [
        {"step": 15, "risk": "整流罩四坡合尖前, 前三片梯形腰边为半开环",
         "mitigation": "tip 提示压顶前先对齐四条棱, 一次合尖"},
        {"step": 20, "risk": "脐带桥板若只吸单端, 另一端悬空易坠",
         "mitigation": "教程要求西缘先对准箭体环顶, 东缘同步压塔身顶边"},
        {"step": 23, "risk": "避雷尖塔为全场最高点, 单边吸合易被袖口带倒",
         "mitigation": "该步 tip 提示轻拿轻放, 底边整边吸合后再松手"},
    ]
    meta["structural_signature"]["silhouette_class"] = "launch_complex"
    meta["structural_signature"]["height_layers"] = 7

    out = Path(__file__).resolve().parent.parent / \
        "data/models/stellar_launch_gantry_01.json"
    out.write_text(json.dumps(model, ensure_ascii=False, indent=2) + "\n",
                   encoding="utf-8")
    print(f"已重写 {out} (含旗舰元数据)")
