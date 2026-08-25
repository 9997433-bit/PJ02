#!/usr/bin/env python3
"""生成模型 data/models/temple_of_heaven_01.json (祈年殿). validate strict 零警告."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from magtile_gen import ModelBuilder
b = ModelBuilder()
STONE_A, STONE_B = "clear", "gray"
PILLAR, EAVE, GOLD = "red", "blue", "yellow"
for j in range(4):
    for i in range(4):
        b.flat(f"pz_{i}_{j}", i, j, 0.0, STONE_A if (i + j) % 2 else STONE_B)
for i in range(4):
    b.flat(f"path_{i}", i, -1, 0.0, STONE_A)
for i in range(4):
    b.wall_ns(f"t1w_s_{i}", i, 0.0, 0, STONE_B)
for j in range(1, 4):
    b.wall_ew(f"t1w_w_{j}", 0.0, j, 0, STONE_B)
    b.wall_ew(f"t1w_e_{j}", 4.0, j, 0, STONE_B)
for i in range(4):
    b.wall_ns(f"t1w_n_{i}", i, 4.0, 0, STONE_B)
for j in range(1, 4):
    for i in range(1, 4):
        b.flat(f"t1_{i}_{j}", i, j, 1.0, STONE_A if (i + j) % 2 else STONE_B)
b.crest_ns("arch_s0", 1, 0.0, 1.0, STONE_A)
b.crest_ns("arch_s1", 2, 0.0, 1.0, STONE_A)
b.crest_ew("arch_w0", 0.0, 1, 1.0, STONE_A)
b.crest_ew("arch_e0", 4.0, 2, 1.0, STONE_A)
for i in (1, 2):
    b.wall_ns(f"t2w_s_{i}", i, 1.0, 1, STONE_B)
    b.wall_ns(f"t2w_n_{i}", i, 3.0, 1, STONE_B)
for j in (1, 2):
    b.wall_ew(f"t2w_w_{j}", 1.0, j, 1, STONE_B)
    b.wall_ew(f"t2w_e_{j}", 3.0, j, 1, STONE_B)
b.flat_rect("t2_a", 1, 1, 2.0, STONE_A)
b.flat_rect("t2_b", 1, 2, 2.0, STONE_A)
b.brace("butt_s", (2.0, 1.0, 0.0), "+y", STONE_B)
b.brace("butt_n", (2.0, 3.0, 0.0), "-y", STONE_B)
b.brace("butt_w", (1.0, 2.0, 0.0), "+x", STONE_B)
b.brace("butt_e", (3.0, 2.0, 0.0), "-x", STONE_B)
for lv, z0 in (("a", 2), ("b", 3)):
    b.lintel_ns(f"col_s_{lv}", 1, 1.0, z0, PILLAR)
    b.lintel_ew(f"col_w_{lv}", 1.0, 1, z0, PILLAR)
    b.lintel_ew(f"col_e_{lv}", 3.0, 1, z0, PILLAR)
    b.lintel_ns(f"col_n_{lv}", 1, 3.0, z0, PILLAR)
b.flat_rect("deck_a", 1, 1, 4.0, STONE_A)
b.flat_rect("deck_b", 1, 2, 4.0, STONE_A)
b.lintel_ns("ring_s", 1, 1.0, 4, PILLAR)
b.lintel_ns("ring_n", 1, 3.0, 4, PILLAR)
b.lintel_ew("ring_w", 1.0, 1, 4, PILLAR)
b.lintel_ew("ring_e", 3.0, 1, 4, PILLAR)
b.flat_rect("ev_wide", 1, 0, 4.0, EAVE)
b.flat_rect("tier2_wide", 1, 3, 4.0, EAVE)
b.flat_rect("roof_a", 1, 1, 5.0, GOLD)
b.flat_rect("roof_b", 1, 2, 5.0, GOLD)
for j in (1, 2):
    b.flat(f"plaza_{j}", j, 4, 0.0, STONE_A)
for i in range(3):
    b.flat(f"s3_{i}", i, -4, 0.0, STONE_A)
for i in range(4):
    b.flat(f"s_{i}", i, -2, 0.0, STONE_A)
    b.flat(f"s2_{i}", i, -3, 0.0, STONE_B)
    b.flat(f"n_{i}", i, 5, 0.0, STONE_A)
    b.flat(f"n2_{i}", i, 6, 0.0, STONE_B)
    b.flat(f"n3_{i}", i, 7, 0.0, STONE_A)
for j in range(4):
    b.flat(f"w_{j}", -1, j, 0.0, STONE_B)
    b.flat(f"w2_{j}", -2, j, 0.0, STONE_A)
    b.flat(f"w3_{j}", -3, j, 0.0, STONE_B)
    b.flat(f"e_{j}", 4, j, 0.0, STONE_B)
    b.flat(f"e2_{j}", 5, j, 0.0, STONE_A)
    b.flat(f"e3_{j}", 6, j, 0.0, STONE_B)
b.flat("pnw", 0, 4, 0.0, STONE_A)
b.flat("pne", 3, 4, 0.0, STONE_B)
b.crest_ew("pfw", 0.0, -1, 0.0, "cyan")
b.crest_ew("pfe", 4.0, -1, 0.0, "cyan")

b.step("铺底层广场 (第一批): 十二片汉白玉方板拼成 4x4 台基前段.", [f"pz_{i}_{j}" for j in range(3) for i in range(4)])
b.step("铺底层广场 (第二批): 完成北排四片.", [f"pz_{i}_3" for i in range(4)], highlight=["pz_0_0"])
b.step("铺丹陛步道: 四片方板铺在南门正前方 (y=-1).", ["path_0","path_1","path_2","path_3"], highlight=["pz_0_0"])
b.step("装步道饰件: 两端扇形点缀丹陛.", ["pfw","pfe"], highlight=["path_1"])
b.step("立第一层台基外墙 (第一批): 南/北外墙 + 东西部分墙段.", [f"t1w_s_{i}" for i in range(4)]+[f"t1w_n_{i}" for i in range(4)]+[f"t1w_w_{j}" for j in range(1,3)]+[f"t1w_e_{j}" for j in range(1,3)], highlight=["pz_0_0"])
b.step("立第一层台基外墙 (第二批): 完成东西外墙段.", ["t1w_w_3","t1w_e_3"], highlight=["t1w_s_1"])
b.step("铺第一层内坛: 九片方板填满 3x3 内圈.", ["t1_3_1","t1_3_2","t1_1_3","t1_2_3","t1_3_3","t1_2_2","t1_1_2","t1_2_1","t1_1_1"], highlight=["t1w_s_1"])
b.step("装四扇形拱券: 东南西北各一片扇形贴在台基拱洞口.", ["arch_s0","arch_s1","arch_w0","arch_e0"], highlight=["t1_2_2"])
b.step("立第二层台基墙: 八片方板围出 2x2 内圈外的第二环.", ["t2w_s_1","t2w_s_2","t2w_n_1","t2w_n_2","t2w_w_1","t2w_w_2","t2w_e_1","t2w_e_2"], highlight=["t1_2_2"])
b.step("铺第二层内坛并装扶壁: 四片方板 + 四片直角三角扶壁.", ["t2_a","t2_b","butt_s","butt_n","butt_w","butt_e"], highlight=["t2w_s_1"])
b.step("立红柱下层: 四面长方形墙竖放在第二层坛面上.", ["col_s_a","col_w_a","col_e_a","col_n_a"], highlight=["t2_a"])
b.step("立红柱上层: 四面墙继续收高.", ["col_s_b","col_w_b","col_e_b","col_n_b"], highlight=["col_s_a"])
b.step("铺祈年殿楼板: 两片长方形汉白玉压柱顶.", ["deck_a","deck_b"], highlight=["col_s_b"])
b.step("装额枋环: 四条红色长方形额枋压柱顶.", ["ring_s","ring_n","ring_w","ring_e"], highlight=["deck_a"])
b.step("第一重蓝色檐: 宽檐向南挑出.", ["ev_wide"], highlight=["ring_s"])
b.step("第二重檐收分: 北面宽檐再收一层.", ["tier2_wide"], highlight=["ev_wide"])
b.step("金顶盖板: 两片金色长方形压顶.", ["roof_a","roof_b"], highlight=["ring_s"])
b.step("铺北广场延伸: 四片 (含西北/东北角).", ["plaza_1","plaza_2","pnw","pne"], highlight=["pz_2_3"])
b.step("外延南丹陛: 三圈南向御道.", [f"s_{i}" for i in range(4)]+[f"s2_{i}" for i in range(4)]+[f"s3_{i}" for i in range(3)], highlight=["path_0"])
b.step("外延北御道: 三圈北向御道.", [f"n_{i}" for i in range(4)]+[f"n2_{i}" for i in range(4)]+[f"n3_{i}" for i in range(4)], highlight=["plaza_1"])
b.step("外延西翼三圈: 十二片侧翼广场.", [f"w_{j}" for j in range(4)]+[f"w2_{j}" for j in range(4)]+[f"w3_{j}" for j in range(4)], highlight=["pz_0_1"])
b.step("外延东翼前两圈: 八片侧翼广场.", [f"e_{j}" for j in range(4)]+[f"e2_{j}" for j in range(4)], highlight=["w_0"])
b.step("完成东翼第三圈 —— 祈年殿落成!", [f"e3_{j}" for j in range(4)], highlight=["e_0"], tip="双重蓝檐金顶从天坛升起 —— 入库前须逐一实物复核.")
b.finalize(model_id="temple_of_heaven_01", name="祈年殿", name_en="Temple of Heaven 01", description="建筑地标 D5 灯塔: 双重蓝色圆檐意象 + 三层汉白玉台基逐环收分, 八面红柱围成圆形廊柱意象, 四扇形拱券点缀台基, 金顶双坡自锁.", difficulty=5, tags=["建筑地标","祈年殿","天坛","圆檐","攒尖"], min_pieces=132, min_steps=22, series="landmark_architecture")

