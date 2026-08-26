#!/usr/bin/env python3
"""生成模型 data/models/strait_rainbow_bridge_01.json (海峡之虹悬索桥)。

内容策略 §6 简报 ①: 桥梁工程 D5 旗舰悬索桥。
用法: python3 tools/generate_strait_rainbow_bridge_01.py
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from magtile_gen import ModelBuilder  # noqa: E402

b = ModelBuilder()

DECK_Z = 1.0
TOWER_W = 5
TOWER_E = 9
PIER_W = 4
PIER_E = 10
RIM_S = 1.0
RIM_N = 3.0
LEG_S = 1
LEG_N = 2
ROW_S = 1
ROW_N = 2

BANK = "green"
STONE = "gray"
TOWER = "orange"
DECK = "gray"
CABLE = "clear"
STAY = "orange"
RAMP = "gray"

# 北幅 / 南幅各 6 段 (4 跨中 + 2 锚跨); 南幅无 stay 故可与北幅同 x 位
MAIN_SPAN = ((3, +1), (5, -1), (6, +1), (8, -1))
MAIN_ANCHOR = ((2, +1), (9, -1))


def deck_cable(tile_id, x0, y, lean, color=CABLE):
    if lean > 0:
        w_from, w_to = (float(x0), y, DECK_Z), (float(x0 + 1), y, DECK_Z)
    else:
        w_from, w_to = (float(x0 + 1), y, DECK_Z), (float(x0), y, DECK_Z)
    b.place_edge(tile_id, "rhombus", 0, w_from, w_to, (0, 0, 1), color)


def deck_cross(tile_id, x, y_lo, color=CABLE):
    b.place_edge(tile_id, "rhombus", 0,
                 (float(x), y_lo, DECK_Z), (float(x), y_lo + 1, DECK_Z),
                 (float(x) + 0.5, y_lo + 0.5, DECK_Z + 0.35), color)


def span_cable(tile_id, x0, x1, y, color=CABLE):
    b.place_edge(tile_id, "rhombus", 0,
                 (float(x0), y, DECK_Z), (float(x1), y, DECK_Z),
                 (float(x0) + 0.5, y + 0.35, DECK_Z + 0.35), color)


def west_tower_hanger(prefix, tx, south, color=CABLE):
    if south:
        y_t, y_r = RIM_S, RIM_S
        b.place_edge(f"{prefix}_a", "rhombus", 0,
                     (float(tx), y_t, 1.0), (float(tx + 1), y_r, 1.0),
                     (float(tx), y_t, 2.0), color)
    else:
        y_t, y_r = RIM_N, float(LEG_N)
        b.place_edge(f"{prefix}_a", "rhombus", 0,
                     (float(tx), y_r, 1.0), (float(tx + 1), y_r, 1.0),
                     (float(tx), y_t, 2.0), color)


def east_tower_hanger(prefix, tx, south, color=CABLE):
    if south:
        y_t, y_r = RIM_S, RIM_S
        b.place_edge(f"{prefix}_a", "rhombus", 0,
                     (float(tx), y_t, 1.0), (float(tx - 1), y_r, 1.0),
                     (float(tx), y_t, 2.0), color)
    else:
        y_t, y_r = RIM_N, float(LEG_N)
        b.place_edge(f"{prefix}_a", "rhombus", 0,
                     (float(tx), y_r, 1.0), (float(tx - 1), y_r, 1.0),
                     (float(tx), y_t, 2.0), color)


def west_hangers(prefix, south, color=CABLE):
    y = RIM_S if south else RIM_N
    row = ROW_S if south else ROW_N
    west_tower_hanger(prefix, TOWER_W, south, color)
    for i, x in enumerate((3, 4, 5, 6)):
        deck_cross(f"{prefix}_c{i}", x, row, color)
    for i, (x0, x1) in enumerate(((2, 3), (3, 4), (4, 5), (5, 6))):
        span_cable(f"{prefix}_s{i}", x0, x1, y, color)


def east_hangers(prefix, south, color=CABLE):
    y = RIM_S if south else RIM_N
    row = ROW_S if south else ROW_N
    east_tower_hanger(prefix, TOWER_E, south, color)
    for i, x in enumerate((7, 8, 9, 10)):
        deck_cross(f"{prefix}_c{i}", x, row, color)
    for i, (x0, x1) in enumerate(((7, 8), (8, 9), (9, 10), (10, 11))):
        span_cable(f"{prefix}_s{i}", x0, x1, y, color)


# ---- 1. 锚台 + 桥台 ----
for row in (ROW_S, ROW_N):
    b.flat(f"aw_{row}a", 2, row, 0.0, BANK)
    if row == ROW_S:
        b.flat(f"aw_{row}b", 3, row, 0.0, BANK)
    b.flat(f"ae_{row}a", 10, row, 0.0, BANK)
    if row == ROW_S:
        b.flat(f"ae_{row}b", 11, row, 0.0, BANK)
    b.wall_ew(f"pw_{row}", float(PIER_W), row, 0, STONE)
    b.wall_ew(f"pe_{row}", float(PIER_E), row, 0, STONE)

# ---- 2. 双塔 ----
for tag, tx in (("tw", TOWER_W), ("te", TOWER_E)):
    for lv in range(2):
        b.wall_ew(f"{tag}_s_{lv}", float(tx), LEG_S, lv, TOWER)
        b.wall_ew(f"{tag}_n_{lv}", float(tx), LEG_N, lv, TOWER)

# ---- 3. 斜撑 x20 ----
for tag, tx in (("tw", TOWER_W), ("te", TOWER_E)):
    b.brace(f"{tag}_g1_s", (float(tx), float(LEG_S), 0.0), "+x", STAY)
    b.brace(f"{tag}_g2_s", (float(tx), float(LEG_S), 0.0), "-x", STAY)
    b.brace(f"{tag}_g1_n", (float(tx), float(LEG_N), 0.0), "+x", STAY)
    b.brace(f"{tag}_g2_n", (float(tx), float(LEG_N), 0.0), "-x", STAY)

b.brace("awb_s", (float(PIER_W), float(ROW_S), 0.0), "-x", STAY)
b.brace("awb_n", (float(PIER_W), float(ROW_N), 0.0), "-x", STAY)
b.brace("aeb_s", (float(PIER_E), float(ROW_S), 0.0), "+x", STAY)
b.brace("aeb_n", (float(PIER_E), float(ROW_N), 0.0), "+x", STAY)
b.brace("anc_w", (2.0, float(ROW_S), 0.0), "+y", STAY)
b.brace("anc_n", (2.0, float(ROW_N), 0.0), "+y", STAY)
b.brace("dj4", (4.0, float(ROW_N), DECK_Z), "+x", STAY)
b.brace("dj6", (6.0, float(ROW_N), DECK_Z), "+x", STAY)
b.brace("dj8", (8.0, float(ROW_N), DECK_Z), "-x", STAY)
b.brace("tw_stay_n", (float(TOWER_W), float(ROW_N), DECK_Z), "+x", STAY)
b.brace("te_stay_n", (float(TOWER_E), float(ROW_N), DECK_Z), "-x", STAY)
b.brace("eb_tie", (11.0, float(ROW_S), 0.0), "+x", STAY)

# ---- 4. 桥面 + 引桥 ----
for x0 in range(3, 10):
    for row in (ROW_S, ROW_N):
        b.flat(f"d_{x0}_{row}", x0, row, DECK_Z, DECK)

b.wall_ew("pm_1", 6.0, ROW_S, 0, STONE)
b.wall_ew("pm_2", 6.0, ROW_N, 0, STONE)

for name, side, x, rows in (
    ("w0", "-x", 3.0, (ROW_S, ROW_N)), ("w1", "-x", 4.0, (ROW_S, ROW_N)),
    ("e0", "+x", 10.0, (ROW_S, ROW_N)), ("e1", "+x", 9.0, (ROW_S, ROW_N)),
):
    for i, row in enumerate(rows):
        b.ramp(f"ramp_{name}_{i}", side, x, row, DECK_Z, RAMP)

# ---- 5. 主缆 + 吊索 ----
for x0, lean in MAIN_SPAN:
    deck_cable(f"mc_s_{x0}", x0, RIM_S, lean)
    deck_cable(f"mc_n_{x0}", x0, RIM_N, lean)
for x0, lean in MAIN_ANCHOR:
    deck_cable(f"mc_s_{x0}", x0, RIM_S, lean)
    deck_cable(f"mc_n_{x0}", x0, RIM_N, lean)

west_hangers("hgw_s", south=True)
west_hangers("hgw_n", south=False)
east_hangers("hge_s", south=True)
east_hangers("hge_n", south=False)

# ---- 25 步教程 (西向东连续合龙, 零分组断连) ----
b.step("西岸锚台: 铺 3 片绿色岸台, 整边互吸成锚碇子结构。",
       ["aw_1a", "aw_1b", "aw_2a"],
       tip="锚碇是悬索桥荷载最终入地点 —— 西岸子结构一次成形。")
b.step("西桥台墙: 2 片灰色桥台墙吸住岸台东缘。",
       ["pw_1", "pw_2"], highlight=["aw_1a"],
       tip="桥台墙底接地、顶边将托住桥面 x=3。")
b.step("桥面西端: x=3 两排方板压上西桥台。",
       ["d_3_1", "d_3_2"], highlight=["pw_1"],
       tip="桥面先压稳桥台 —— 引桥坡道留待全桥合龙后再挂。")
b.step("桥面西进: 悬挑 1 排 (x=4), 自桥台向东推进一格。",
       ["d_4_1", "d_4_2"], highlight=["d_3_1"],
       tip="单格悬挑在磁吸力矩预算内 —— 先别急着再挑第二排!")
b.step("西段锁缝撑: 1 根斜撑锁定 x=4 悬挑段。",
       ["dj4"], highlight=["d_4_1"],
       tip="悬挑下一格前必须先装斜撑 —— 真实悬索桥的架设节奏。")
b.step("西主塔 L1 + 桥面 x=5: 塔腿、塔脚撑与北排 stay 合龙。",
       ["d_5_1", "d_5_2", "tw_s_0", "tw_n_0", "tw_g1_s", "tw_stay_n"],
       highlight=["d_4_1"],
       tip="塔腿侧向整边贴桥面 —— tw_stay_n 水平边吸桥面北沿。")
b.step("西塔 L2 + 主跨西段: 二层塔腿、中墩与 x=6 桥面及 dj6 合龙。",
       ["tw_s_1", "tw_n_1", "tw_g2_s", "d_6_1", "d_6_2", "dj6", "pm_1", "pm_2"],
       highlight=["tw_s_0", "d_5_1"],
       tip="x=6 中墩与 dj6 同步 —— 悬挑力矩在预算内。")
b.step("主跨东段 + 东塔 L1: x=7-9 与 dj7、dj8、东塔一次合龙。",
       ["d_7_1", "d_7_2", "d_8_1", "d_8_2", "d_9_1", "d_9_2",
        "dj8", "te_s_0", "te_n_0", "te_g1_s", "te_stay_n"],
       highlight=["d_6_1"],
       tip="三排桥面与东塔同步 —— 无中间长悬臂步。")
b.step("东桥台墙: 2 片灰色桥台墙吸住桥面东缘。",
       ["pe_1", "pe_2"], highlight=["d_9_1"],
       tip="桥面 x=9 已压稳 —— 桥台墙底接地。")
b.step("东塔 L2: 二层塔腿与塔脚斜撑封顶。",
       ["te_s_1", "te_n_1", "te_g2_s"],
       highlight=["te_s_0", "d_9_1"],
       tip="东塔封顶 —— 北腿整边吸桥面北排。")
b.step("东岸锚台 (南排): 2 片绿色岸台吸住东桥台南缘。",
       ["ae_1a", "ae_1b"], highlight=["pe_1", "d_9_1"],
       tip="南岸台先合龙 —— 北岸随后整边互吸。")
b.step("东岸锚台 (北排): 1 片绿色岸台 —— 全桥单一连通组!",
       ["ae_2a"], highlight=["ae_1a", "pe_2"],
       tip="东岸锚台整边吸桥台 —— 无分组断连。")
b.step("主跨侧撑: 2 根斜撑锁牢双塔北侧塔脚。",
       ["tw_g2_n", "te_g2_n"], highlight=["d_6_1"],
       tip="合龙后立即锁塔脚 —— 主跨不再颤。")
b.step("塔脚与岸台侧撑: 4 根斜撑锁双塔脚与桥台 (T14)。",
       ["tw_g1_n", "te_g1_n", "awb_s", "aeb_s"],
       highlight=["tw_s_1", "te_s_1"],
       tip="塔脚四向斜撑在 z=0 锁塔腿 —— 双路径传力入地。")
b.step("岸台互锁: 3 根斜撑完成双岸桥台互锁。",
       ["awb_n", "aeb_n", "eb_tie"],
       highlight=["awb_s", "pe_1"],
       tip="斜撑全部就位 —— 双岸锚台与桥台墙成一体。")
b.step("锚碇角撑: 2 根斜撑加固东西岸锚台外角。",
       ["anc_w", "anc_n"], highlight=["awb_s"],
       tip="锚碇外角加撑 —— 重车制动不松。")
b.step("西引桥: 4 条坡道落地, 顶边整边吸桥面西缘。",
       ["ramp_w0_0", "ramp_w0_1", "ramp_w1_0", "ramp_w1_1"],
       highlight=["d_3_1"],
       tip="坡道顶边整边吸桥面西缘, 坡尾自然落地 —— 西引桥自成稳定三点支撑。")
b.step("东引桥: 4 条坡道落地, 顶边整边吸桥面东缘。",
       ["ramp_e0_0", "ramp_e0_1", "ramp_e1_0", "ramp_e1_1"],
       highlight=["d_9_1", "ae_1a"],
       tip="东引桥 ae 侧坡道与锚台整边互吸 —— 全桥单一连通组。")
b.step("东锚主缆: x=9 锚跨透明菱形落地。",
       ["mc_s_9", "mc_n_9"],
       highlight=["d_9_1"],
       tip="锚跨主缆底边吸桥面东缘与锚台侧外缘。")
b.step("主缆·南幅: 锚跨 + 4 段跨中透明菱形 (十二段之半幅)。",
       ["mc_s_3", "mc_s_2", "mc_s_5", "mc_s_6", "mc_s_8"],
       highlight=["d_3_1"],
       tip="先接桥面端 x=3 再接锚跨 x=2 —— 底边整边吸桥面沿口。")
b.step("主缆·北幅: 锚跨 + 4 段跨中菱形 —— 十二段主缆就位。",
       ["mc_n_3", "mc_n_2", "mc_n_5", "mc_n_6", "mc_n_8"],
       highlight=["mc_s_8"],
       tip="十二段主缆 × 南北两幅 —— 海峡之虹的受压曲线。")
b.step("西半跨南吊索: 9 段菱形 (x2-6 区)。",
       ["hgw_s_a", "hgw_s_c0", "hgw_s_c1", "hgw_s_c2", "hgw_s_c3",
        "hgw_s_s0", "hgw_s_s1", "hgw_s_s2", "hgw_s_s3"],
       highlight=["tw_s_1", "d_5_1"],
       tip="沿口 span 链只用桥面 x 位 —— 零 tile_overlap。")
b.step("西半跨北吊索: 9 段, 与南幅镜像。",
       ["hgw_n_a", "hgw_n_c0", "hgw_n_c1", "hgw_n_c2", "hgw_n_c3",
        "hgw_n_s0", "hgw_n_s1", "hgw_n_s2", "hgw_n_s3"],
       highlight=["tw_n_1"],
       tip="四路吊索锁牢双塔 —— 竖向彩虹。")
b.step("东半跨南吊索: 9 段 (x7-11 区)。",
       ["hge_s_a", "hge_s_c0", "hge_s_c1", "hge_s_c2", "hge_s_c3",
        "hge_s_s0", "hge_s_s1", "hge_s_s2", "hge_s_s3"],
       highlight=["te_s_1", "d_9_1"],
       tip="东半跨吊索向西吸桥面 —— 与西塔镜像。")
b.step("东半跨北吊索: 9 段 —— 海峡之虹悬索桥合龙通车!",
       ["hge_n_a", "hge_n_c0", "hge_n_c1", "hge_n_c2", "hge_n_c3",
        "hge_n_s0", "hge_n_s1", "hge_n_s2", "hge_n_s3"],
       highlight=["hge_s_a", "mc_n_8"],
       tip="通桥仪式: 双塔、双幅主缆、四路吊索 —— 彩虹悬索桥落成!")

model = b.finalize(
    model_id="strait_rainbow_bridge_01",
    name="海峡之虹悬索桥",
    name_en="Strait Rainbow Suspension Bridge 01",
    description=(
        "桥梁工程 D5 悬索旗舰: 结构签名是'十二段菱形链从双塔垂向桥面' —— "
        "先立双塔桁架芯与斜撑 (T02+T14), 再铺桥面连续梁, 最后由跨中向两塔"
        "对称挂透明菱形主缆与吊索, 用受压链条再现悬索桥的受拉曲线; 与 D3 "
        "海湾悬索桥 (单格悬挑合龙) 和 D4 石拱桥 (拱洞负空间) 传力叙事均不同。"
    ),
    difficulty=5,
    tags=["桥梁", "悬索桥", "工程", "桁架", "大师", "需要扩展装"],
    min_pieces=110,
    min_steps=25,
    series="bridge_engineering",
)

meta = model["content_meta"]
meta["build_paradigm"] = "skeleton_first"
meta["technique_tags"] = {
    "primary": "T15_suspension_sim",
    "secondary": ["T02_triangular_truss", "T14_diagonal_bracing"],
}
meta["signature_statement"] = (
    "十二段菱形链从双塔垂向桥面, 用受压链条再现悬索桥的受拉曲线。"
)
meta["physical_risk_notes"] = [
    {"step": 7, "risk": "主塔封顶前为单柱悬臂, 桌面震动可致倾倒",
     "mitigation": "该步 tip 提示: 一手扶塔身再放片"},
    {"step": 20, "risk": "首段菱形链仅单边吸合时最易脱落",
     "mitigation": "教程要求先接桥面端再接塔端"},
]
meta["structural_signature"]["silhouette_class"] = "twin_tower_span"
meta["structural_signature"]["height_layers"] = 7

out = Path(__file__).resolve().parent.parent / "data/models/strait_rainbow_bridge_01.json"
out.write_text(json.dumps(model, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

from collections import Counter
hist = Counter(t["type"] for t in model["final_assembly"])
print("目标核对:", dict(hist))
print(f"已生成 {out} ({len(model['final_assembly'])} 片, {len(model['steps'])} 步)")
