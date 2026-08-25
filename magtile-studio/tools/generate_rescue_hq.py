#!/usr/bin/env python3
"""生成旗舰模型 data/models/rescue_hq_01.json (救援行动总部)。

内容策略 2.4 节"反幼稚规则"的标杆样板之一 (简报 ⑪):
不是几片拼个形状, 而是一座孩子会反复玩的三段式救援基地。

结构总览 (世界单位: 1.0 = 正方形磁力片边长, 场地 6 x 3):
  - 6x3 场地地台 (z = 0)                                     18 片
  - 左翼车库 (x 0..3): 北/西/隔墙 + 桁架护角 + 屋顶甲板       20 片
  - 出动坡道: 长方形 30 度斜坡, 顶边吸甲板西缘, 坡尾落地       1 片
  - 甲板护栏: 直角三角形一对 (甲板南缘)                        2 片
  - 右翼指挥塔 (x 3..6): 三层塔身 + 二三层楼板                45 片
    (一层门洞、二三层瞭望窗为负空间; 东立面为整高长方形幕墙柱)
  - 停机坪 (z = 3 整层) + 北缘警示三角冠                      12 片
  - 信号塔天线 (车库屋顶北缘, 双层方柱 + 等腰三角尖)            3 片
  合计 101 片, 18 个教程步骤。

物理规则要点 (通过 R1~R8 全部校验):
  - 坡道顶边与甲板边/墙顶边整边吸合, 坡尾直接落地 -> 无悬挑力矩;
  - 各层楼板四周全部坐在墙顶边上, 任何单条铰链线剪断后仍有正交支撑;
  - 塔身转角竖边互吸 (盒式框架), 连接图多环路, 满足高层结构冗余。

坐标约定与 C++ 端一致 (include/magtile/core/tile_instance.hpp):
  旋转为欧拉角 (度), 施加顺序 R = Rz * Ry * Rx。
  平铺片 rot = (0,0,0); 南北向立片 rot = (90,0,0); 东西向立片 rot = (90,0,90)。

用法: python3 tools/generate_rescue_hq.py  (在 magtile-studio 目录下运行)
"""

import json
import math
from pathlib import Path

TRI_CENTROID = round(math.sqrt(3) / 6, 6)   # 等边三角形质心到底边距离 0.288675
ISO_CENTROID = 0.666667                     # 等腰三角形质心到底边距离 (底 1 高 2)
COS30 = round(math.cos(math.radians(30)), 6)  # 0.866025
SIN30 = 0.5

tiles = []


def add(tile_id, tile_type, pos, rot, color):
    tiles.append({
        "id": tile_id,
        "type": tile_type,
        "position": [round(v, 6) for v in pos],
        "rotation": [round(v, 6) for v in rot],
        "color": color,
    })


def flat(tile_id, x0, y0, z, color):
    """平铺正方形, 覆盖 [x0,x0+1] x [y0,y0+1], 顶点落在高度 z。"""
    add(tile_id, "square", (x0 + 0.5, y0 + 0.5, z), (0, 0, 0), color)


def wall_ns(tile_id, x0, y, z0, color):
    """南北朝向立墙 (平面 y=y), 覆盖 x [x0,x0+1], z [z0,z0+1]。"""
    add(tile_id, "square", (x0 + 0.5, y, z0 + 0.5), (90, 0, 0), color)


def wall_ew(tile_id, x, y0, z0, color):
    """东西朝向立墙 (平面 x=x), 覆盖 y [y0,y0+1], z [z0,z0+1]。"""
    add(tile_id, "square", (x, y0 + 0.5, z0 + 0.5), (90, 0, 90), color)


# =================================================================
# 1. 场地地台: 6x3, 车库区暖灰 / 塔区蓝青棋盘
# =================================================================
for j in range(3):
    for i in range(6):
        if i < 3:
            color = "gray" if (i + j) % 2 == 0 else "cyan"
        else:
            color = "blue" if (i + j) % 2 == 0 else "cyan"
        flat(f"g_{i}_{j}", i, j, 0.0, color)

# =================================================================
# 2. 车库 (x 0..3, y 0..3, 高 1): 北墙 + 西墙 + 与塔楼共用的隔墙
#    南面整面敞开 = 双车位车库门
# =================================================================
for i in range(3):
    wall_ns(f"gar_n_{i}", i, 3.0, 0, "red")        # 北墙 y=3
for j in range(3):
    wall_ew(f"gar_w_{j}", 0.0, j, 0, "red")        # 西墙 x=0
for j in range(3):
    wall_ew(f"gar_d_{j}", 3.0, j, 0, "orange")     # 车库/塔楼隔墙 x=3

# 车库门两侧桁架护角: 直角三角形, 底边吸地台南缘, 竖边吸墙角竖边
# 西侧: 竖边贴西墙 (x=0); rot (90,0,0) 时本地 x -> 世界 x, 竖直边在左端
add("gar_tr_w", "right_triangle", (1 / 3, 0.0, 1 / 3), (90, 0, 0), "yellow")
# 东侧: 镜像 (rot z 加 180), 竖直边在右端贴隔墙 (x=3)
add("gar_tr_e", "right_triangle", (3 - 1 / 3, 0.0, 1 / 3), (90, 0, 180), "yellow")

# 车库屋顶 = 出动甲板 (z=1, 3x3)
for j in range(3):
    for i in range(3):
        flat(f"deck_{i}_{j}", i, j, 1.0, "gray" if (i + j) % 2 == 0 else "orange")

# =================================================================
# 3. 出动坡道: 长方形 (2x1) 绕 y 轴 -30 度, 顶边整边吸甲板西缘
#    (0,1,1)-(0,2,1), 坡尾落地于 x = -1.732 -> 自身接地, 零悬挑
# =================================================================
add("ramp_deploy", "rectangle", (-COS30, 1.5, SIN30), (0, -30, 0), "orange")

# 甲板南缘护栏: 直角三角形一对, 底边吸屋顶南缘, 竖边朝外
add("deck_tr_w", "right_triangle", (1 / 3, 0.0, 1 + 1 / 3), (90, 0, 0), "yellow")
add("deck_tr_e", "right_triangle", (3 - 1 / 3, 0.0, 1 + 1 / 3), (90, 0, 180), "yellow")

# =================================================================
# 4. 指挥塔一层 (z 0..1): 南墙留门洞 (x 4..5), 东立面用长方形幕墙柱
# =================================================================
wall_ns("t1_s_w", 3, 0.0, 0, "blue")
wall_ns("t1_s_e", 5, 0.0, 0, "blue")
for i in range(3):
    wall_ns(f"t1_n_{i}", 3 + i, 3.0, 0, "blue")

# 东立面: 3 根竖置长方形 (z 0..2 整高), 本地长轴转向世界 z
for j in range(3):
    add(f"t_e_col_{j}", "rectangle", (6.0, j + 0.5, 1.0), (0, -90, 0), "cyan")

# 二层楼板 (z=1, x 3..6)
for j in range(3):
    for i in range(3):
        flat(f"f2_{i}_{j}", 3 + i, j, 1.0, "cyan" if (i + j) % 2 == 0 else "blue")

# =================================================================
# 5. 指挥塔二层 (z 1..2): 西墙(骑在车库隔墙上) + 南墙留瞭望窗 + 北墙
# =================================================================
for j in range(3):
    wall_ew(f"t2_w_{j}", 3.0, j, 1, "blue")
wall_ns("t2_s_w", 3, 0.0, 1, "purple")
wall_ns("t2_s_e", 5, 0.0, 1, "purple")
for i in range(3):
    wall_ns(f"t2_n_{i}", 3 + i, 3.0, 1, "purple")

# 三层楼板 (z=2)
for j in range(3):
    for i in range(3):
        flat(f"f3_{i}_{j}", 3 + i, j, 2.0, "cyan" if (i + j) % 2 == 0 else "blue")

# =================================================================
# 6. 指挥塔三层 (z 2..3): 四面墙, 南面留瞭望窗 (x 4..5)
# =================================================================
wall_ns("t3_s_w", 3, 0.0, 2, "blue")
wall_ns("t3_s_e", 5, 0.0, 2, "blue")
for j in range(3):
    wall_ew(f"t3_w_{j}", 3.0, j, 2, "blue")
for j in range(3):
    wall_ew(f"t3_e_{j}", 6.0, j, 2, "blue")
for i in range(3):
    wall_ns(f"t3_n_{i}", 3 + i, 3.0, 2, "blue")

# =================================================================
# 7. 停机坪 (z=3 整层): 中心橙色着陆标记, 北缘警示三角冠
# =================================================================
for j in range(3):
    for i in range(3):
        color = "orange" if (i == 1 and j == 1) else "gray"
        flat(f"pad_{i}_{j}", 3 + i, j, 3.0, color)

for i in range(3):
    add(f"crest_{i}", "equilateral_triangle",
        (3 + i + 0.5, 3.0, 3.0 + TRI_CENTROID), (90, 0, 0), "yellow")

# =================================================================
# 8. 信号塔天线: 车库屋顶北缘双层方柱 + 等腰三角尖 (总高到 z=4)
# =================================================================
wall_ns("mast_1", 1, 3.0, 1, "purple")
wall_ns("mast_2", 1, 3.0, 2, "purple")
add("mast_tip", "isosceles_triangle", (1.5, 3.0, 3.0 + ISO_CENTROID), (90, 0, 0), "red")

# =================================================================
# 教程步骤 (18 步)
# 步骤内 tiles_to_add 的顺序即真人放片顺序: 每片放下时必须接地或
# 能吸到已放置的片 (装配可达规则 R7)。
# =================================================================
steps = []


def step(description, tiles_to_add, highlight=(), tip=""):
    steps.append({
        "step_number": len(steps) + 1,
        "description": description,
        "tip": tip,
        "tiles_to_add": list(tiles_to_add),
        "highlight_tiles": list(highlight),
    })


step(
    "铺设车库区地台: 在平整桌面左侧平放 3x3 共 9 片正方形, 相邻边逐一对齐吸合。",
    [f"g_{i}_{j}" for j in range(3) for i in range(3)],
    tip="第一排沿桌面边缘摆直, 后续每片先对准一条边再松手, 听到轻磁吸声即到位。",
)
step(
    "向右延伸塔楼区地台: 再铺 3x3 共 9 片, 与车库区地台连成 6x3 的总部场地。",
    [f"g_{i}_{j}" for j in range(3) for i in range(3, 6)],
    highlight=[f"g_2_{j}" for j in range(3)],
    tip="新片的左边要与车库区地台完全贴合, 整块场地中间不能留缝。",
)
step(
    "竖起车库北墙与西墙: 沿地台边缘各立 3 片红色正方形, 底边吸地台边, 相邻竖边互吸。",
    [f"gar_w_{j}" for j in range(3)] + [f"gar_n_{i}" for i in range(3)],
    highlight=[f"g_0_{j}" for j in range(3)] + [f"g_{i}_2" for i in range(3)],
    tip="先立西墙再立北墙, 西北角两片互相吸住后墙体会明显变稳。",
)
step(
    "立起车库与塔楼之间的橙色隔墙 (3 片), 再给车库大门两侧装上黄色桁架护角: "
    "直角三角形底边吸地台南缘, 竖直边贴住墙角。",
    [f"gar_d_{j}" for j in range(3)] + ["gar_tr_w", "gar_tr_e"],
    highlight=[f"g_2_{j}" for j in range(3)] + ["gar_w_0"],
    tip="护角三角形要两条边同时吸住: 底边贴地台, 竖边贴墙角, 车库门就不会晃。",
)
step(
    "盖上车库屋顶 (3x3 共 9 片): 这层既是屋顶也是二楼出动甲板, "
    "每片边缘都要吸住墙顶边或相邻屋顶片。",
    [f"deck_{i}_{j}" for i in range(3) for j in range(3)],
    highlight=[f"gar_w_{j}" for j in range(3)] + [f"gar_d_{j}" for j in range(3)],
    tip="从贴西墙的一列开始铺, 一列一列向东推进, 每片至少吸住一条已有的边。",
)
step(
    "安装出动坡道: 一片长方形斜靠在甲板西缘, 顶边与甲板边整边吸合, 坡尾自然落地。"
    "救援车将从这里冲出总部!",
    ["ramp_deploy"],
    highlight=["deck_0_1", "gar_w_1"],
    tip="先把坡道顶边完整贴上甲板边缘再松手, 坡尾要平稳落在桌面上。",
)
step(
    "给出动甲板南缘装上黄色护栏三角: 一对直角三角形底边吸在屋顶南缘, 竖直边朝外。",
    ["deck_tr_w", "deck_tr_e"],
    highlight=["deck_0_0", "deck_2_0"],
    tip="护栏挡住甲板边缘, 停在甲板上的直升机和小车就不会滑下去。",
)
step(
    "指挥塔一层起墙: 南面立 2 片蓝色正方形, 中间留出一个门洞; 北面立 3 片。",
    ["t1_s_w", "t1_s_e"] + [f"t1_n_{i}" for i in range(3)],
    highlight=[f"g_{i}_0" for i in range(3, 6)] + [f"g_{i}_2" for i in range(3, 6)],
    tip="门洞正对场地南侧, 是救援队员进出总部的大门。",
)
step(
    "竖起东立面幕墙柱: 3 根长方形竖直立在地台东缘, 一根就有两层楼高, "
    "相邻长边互相吸住连成整面玻璃幕墙。",
    [f"t_e_col_{j}" for j in range(3)],
    highlight=[f"g_5_{j}" for j in range(3)],
    tip="长方形要完全竖直, 底边先吸住地台东缘, 再让相邻两根的长边贴合。",
)
step(
    "铺设二层楼板 (3x3 共 9 片): 楼板四周分别坐在隔墙、南北墙的顶边上。",
    [f"f2_{i}_{j}" for i in range(3) for j in range(3)],
    highlight=[f"gar_d_{j}" for j in range(3)] + ["t1_s_w", "t1_n_0"],
    tip="从贴隔墙的一列开始铺, 每片都要压实墙顶边, 楼板才能整体受力。",
)
step(
    "指挥塔二层西墙: 3 片蓝色正方形骑在车库隔墙顶上继续向上生长。",
    [f"t2_w_{j}" for j in range(3)],
    highlight=[f"gar_d_{j}" for j in range(3)] + [f"f2_0_{j}" for j in range(3)],
    tip="这面墙同时吸住楼板边和下层墙顶边, 双重吸合最结实。",
)
step(
    "二层南墙与北墙: 南面 2 片紫色正方形留出瞭望窗, 北面 3 片。",
    ["t2_s_w", "t2_s_e"] + [f"t2_n_{i}" for i in range(3)],
    highlight=[f"f2_{i}_0" for i in range(3)],
    tip="瞭望窗正对车库甲板方向, 指挥员从这里注视每一次出动。",
)
step(
    "铺设三层楼板 (3x3 共 9 片): 与二层楼板做法相同, 幕墙柱顶边也会吸住楼板东缘。",
    [f"f3_{i}_{j}" for i in range(3) for j in range(3)],
    highlight=[f"t2_w_{j}" for j in range(3)] + ["t2_s_w", "t2_n_1"],
    tip="铺到东侧一列时留意: 楼板东缘应恰好落在 3 根幕墙柱的顶边上。",
)
step(
    "指挥塔三层南墙与西墙: 南面 2 片留出第二个瞭望窗, 西面立满 3 片。",
    ["t3_s_w", "t3_s_e"] + [f"t3_w_{j}" for j in range(3)],
    highlight=[f"f3_{i}_0" for i in range(3)] + [f"f3_0_{j}" for j in range(3)],
    tip="从西南角开始, 相邻墙片竖边互吸, 转角处形成直角。",
)
step(
    "三层东墙与北墙: 各立 3 片, 四面合围成顶层指挥室。",
    [f"t3_e_{j}" for j in range(3)] + [f"t3_n_{i}" for i in range(3)],
    highlight=["t3_w_2", "t3_s_e"],
    tip="最后一片放入前先检查四角: 每个转角的两片都应互相吸牢。",
)
step(
    "铺设塔顶停机坪 (3x3 共 9 片): 中央那片换成橙色, 是直升机的着陆标记。",
    [f"pad_{i}_{j}" for i in range(3) for j in range(3)],
    highlight=[f"t3_w_{j}" for j in range(3)] + ["t3_s_w", "t3_n_1"],
    tip="停机坪要铺得平整, 中央橙色片四边都吸住相邻片, 直升机才停得稳。",
)
step(
    "停机坪北缘装上 3 片黄色警示三角冠: 底边吸在停机坪北缘, 尖角朝天。",
    [f"crest_{i}" for i in range(3)],
    highlight=[f"pad_{i}_2" for i in range(3)],
    tip="警示冠只需底边吸合就能站稳, 捏住尖角轻轻放下。",
)
step(
    "最后架设信号塔: 车库屋顶北缘立起两层紫色方柱, 顶上装红色等腰三角天线尖。"
    "救援行动总部落成!",
    ["mast_1", "mast_2", "mast_tip"],
    highlight=["deck_1_2", "gar_n_1"],
    tip="方柱底边吸住屋顶北缘, 逐层向上; 完成后轻推整体检查, 结构应联动不散架。",
)

# ---- 汇总与输出 --------------------------------------------------
placed = [t for s in steps for t in s["tiles_to_add"]]
assert len(placed) == len(tiles) == len(set(placed)), "步骤必须恰好覆盖全部磁力片"
assert len(tiles) >= 80, f"救援总部片数 {len(tiles)} 低于旗舰标准 80"
assert len(steps) >= 18, f"救援总部步数 {len(steps)} 低于旗舰标准 18"

# BOM 备料清单: tests/test_model_logic.py 会核对该清单与 final_assembly 完全一致
bom: dict[str, int] = {}
for t in tiles:
    bom[t["type"]] = bom.get(t["type"], 0) + 1
bom = dict(sorted(bom.items(), key=lambda kv: (-kv[1], kv[0])))

model = {
    "schema_version": 1,
    "id": "rescue_hq_01",
    "name": "救援行动总部",
    "name_en": "Rescue Operations HQ 01",
    "description": (
        "旗舰救援基地: 左翼是敞开式双车位车库, 屋顶就是出动甲板, 长方形斜坡从甲板"
        "直插地面让救援车冲出总部; 右翼三层指挥塔层层起楼, 塔顶整层直升机停机坪。"
        "门洞、瞭望窗、桁架护角、信号塔一应俱全 —— 搭完就能开始救援行动。"
    ),
    "difficulty": 4,
    "total_pieces": len(tiles),
    "tags": ["救援", "总部", "建筑地标", "旗舰", "挑战"],
    "content_meta": {
        "structural_signature": {
            "tile_histogram": bom,
        },
    },
    "final_assembly": tiles,
    "steps": steps,
}

out = Path(__file__).resolve().parent.parent / "data" / "models" / "rescue_hq_01.json"
out.write_text(json.dumps(model, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

by_type = {}
for t in tiles:
    by_type[t["type"]] = by_type.get(t["type"], 0) + 1
print(f"已生成 {out} ({len(tiles)} 片, {len(steps)} 步)")
print("片形统计: " + ", ".join(f"{k} x {v}" for k, v in sorted(by_type.items())))
