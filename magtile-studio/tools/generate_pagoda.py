#!/usr/bin/env python3
"""生成模型 data/models/pagoda_01.json (朱红五重塔)。

第二批模型 ④: 东方古建筑旗舰 —— 2x2 塔身五层通高, 前三层
塔檐向四面外挑, 顶层以四片梯形合拢成四坡大屋顶, 压顶正方形
上再起一座金色锥形宝顶, 总高 6.57 个单位。

结构总览 (世界单位: 1.0 = 正方形磁力片边长):
  - 寺院地坪: 4x4 去四角共 12 片 + 南面参道 2 片                14 片
  - 塔身: 2x2 占地五层, 每层 8 片朱红立墙                       40 片
  - 层间楼板: 第 1~4 层顶各 4 片                                16 片
  - 塔檐: 第 1~3 层顶各 8 片紫檐板向四面外挑                    24 片
  - 大屋顶: 顶层 2 片长方形楼板 + 4 片梯形四坡顶 + 压顶正方形    7 片
  - 宝顶: 压顶上 4 片金色等腰三角锥                              4 片
  合计 105 片, 23 个教程步骤, 4 种磁力片形状。

物理规则要点 (通过 R1~R8 全部校验):
  - 檐板单边外挑力矩 15 g·单位 < 20 预算, 且同侧两片互吸共担;
  - 梯形下底 (长 2) 必须与长方形楼板长边整边贴合 —— 这是顶层楼板
    改用长方形的原因; 东西梯形靠腰边与南北梯形互吸;
  - 每层楼板四边压墙顶成环, 剪断任何单条铰链线仍有正交支撑。

用法: python3 tools/generate_pagoda.py  (在 magtile-studio 目录下运行)
"""

from magtile_gen import ModelBuilder, EQ_APEX

b = ModelBuilder()

# =================================================================
# 1. 寺院地坪 (4x4 去四角) 与参道
# =================================================================
PLAZA = [(1, 0), (2, 0), (0, 1), (1, 1), (2, 1), (3, 1),
         (0, 2), (1, 2), (2, 2), (3, 2), (1, 3), (2, 3)]
for i, j in PLAZA:
    b.flat(f"pl_{i}_{j}", i, j, 0.0, "green" if (i + j) % 2 == 0 else "gray")
b.flat("path_w", 1, -1, 0.0, "gray")
b.flat("path_e", 2, -1, 0.0, "gray")

# =================================================================
# 2. 塔身五层 (占格 1..3 x 1..3) + 层间楼板 + 塔檐
# =================================================================
WALL_COLOR = {0: "red", 1: "orange", 2: "red", 3: "orange", 4: "red"}
for lv in range(5):
    c = WALL_COLOR[lv]
    b.wall_ns(f"st{lv}_s1", 1, 1.0, lv, c)
    b.wall_ns(f"st{lv}_s2", 2, 1.0, lv, c)
    b.wall_ew(f"st{lv}_e1", 3.0, 1, lv, c)
    b.wall_ew(f"st{lv}_e2", 3.0, 2, lv, c)
    b.wall_ns(f"st{lv}_n1", 1, 3.0, lv, c)
    b.wall_ns(f"st{lv}_n2", 2, 3.0, lv, c)
    b.wall_ew(f"st{lv}_w1", 1.0, 1, lv, c)
    b.wall_ew(f"st{lv}_w2", 1.0, 2, lv, c)

for lv in range(4):                      # 第 1~4 层顶楼板 (z = lv+1)
    z = lv + 1.0
    for i, j in ((1, 1), (2, 1), (1, 2), (2, 2)):
        b.flat(f"dk{lv}_{i}_{j}", i, j, z, "yellow" if (i + j) % 2 == 0 else "gray")

for lv in range(3):                      # 第 1~3 层顶塔檐 (每层 8 片)
    z = lv + 1.0
    b.flat(f"ev{lv}_s1", 1, 0, z, "purple")
    b.flat(f"ev{lv}_s2", 2, 0, z, "purple")
    b.flat(f"ev{lv}_e1", 3, 1, z, "purple")
    b.flat(f"ev{lv}_e2", 3, 2, z, "purple")
    b.flat(f"ev{lv}_n1", 1, 3, z, "purple")
    b.flat(f"ev{lv}_n2", 2, 3, z, "purple")
    b.flat(f"ev{lv}_w1", 0, 1, z, "purple")
    b.flat(f"ev{lv}_w2", 0, 2, z, "purple")

# =================================================================
# 3. 大屋顶: 顶层长方形楼板 x2 + 梯形四坡顶 + 压顶 + 宝顶
# =================================================================
b.flat_rect("dk4_a", 1, 1, 5.0, "yellow", axis="x")   # 覆盖 (1..3, 1..2)
b.flat_rect("dk4_b", 1, 2, 5.0, "yellow", axis="x")   # 覆盖 (1..3, 2..3)
roof_ids, roof_cap = b.hip_roof2("roof", 1, 1, 5.0, "purple", cap_color="yellow")
finial_ids = b.hat4("finial", 1.5, 1.5, 5.0 + EQ_APEX, "yellow")

# =================================================================
# 教程步骤 (23 步)
# =================================================================
b.step(
    "铺设寺院地坪南半部: 6 片正方形 (绿灰相间), 相邻边互相吸合。",
    [f"pl_{i}_{j}" for i, j in PLAZA[:6]],
    tip="地坪是 4x4 去掉四角的十字形 —— 南沿先铺中间两片, 再铺整排。",
)
b.step(
    "铺设地坪北半部 (6 片), 十字形地坪完工。",
    [f"pl_{i}_{j}" for i, j in PLAZA[6:]],
    highlight=["pl_0_1", "pl_3_1"],
    tip="塔身将立在地坪正中 2x2 区域的四条边线上。",
)
b.step(
    "铺设参道: 地坪南面接 2 片石板路, 通向塔门。",
    ["path_w", "path_e"],
    highlight=["pl_1_0", "pl_2_0"],
    tip="参道正对塔身南面 —— 这是进塔的必经之路。",
)
for lv in range(5):
    layer_name = ("第一", "第二", "第三", "第四", "第五")[lv]
    b.step(
        f"{layer_name}层塔身 (南墙与东墙): 沿 2x2 区域南、东两边各立 2 片朱红墙。",
        [f"st{lv}_s1", f"st{lv}_s2", f"st{lv}_e1", f"st{lv}_e2"],
        highlight=(["pl_1_1", "pl_2_1"] if lv == 0
                   else [f"dk{lv - 1}_1_1", f"dk{lv - 1}_2_2"]),
        tip="东南转角两片竖边互吸成直角 —— 每层都从这个稳固转角开始。"
            if lv == 0 else "新一层墙体与下层楼板沿口完整贴合, 保持塔身垂直。",
    )
    b.step(
        f"{layer_name}层塔身 (北墙与西墙), 本层合围。",
        [f"st{lv}_n1", f"st{lv}_n2", f"st{lv}_w1", f"st{lv}_w2"],
        highlight=[f"st{lv}_e2", f"st{lv}_s1"],
        tip="四角竖边都互相吸住后, 轻推塔身应整体联动。",
    )
    if lv < 4:
        b.step(
            f"盖{layer_name}层楼板: 4 片正方形压住四面墙顶, 本层封顶。",
            [f"dk{lv}_{i}_{j}" for i, j in ((1, 1), (2, 1), (1, 2), (2, 2))],
            highlight=[f"st{lv}_s1", f"st{lv}_n2"],
            tip="楼板四边都压在墙顶上 —— 这是塔身逐层加固的关键一环。",
        )
    if lv < 3:
        b.step(
            f"装{layer_name}层塔檐: 8 片紫色檐板从楼板四边向外挑出, 同侧两片互吸。",
            [f"ev{lv}_s1", f"ev{lv}_s2", f"ev{lv}_e1", f"ev{lv}_e2",
             f"ev{lv}_n1", f"ev{lv}_n2", f"ev{lv}_w1", f"ev{lv}_w2"],
            highlight=[f"dk{lv}_1_1", f"dk{lv}_2_2"],
            tip="檐板单边吸楼板沿口, 同侧相邻两片再互吸一次共担重量 —— "
                "外挑却纹丝不动。",
        )
b.step(
    "铺顶层楼板: 2 片长方形横跨塔顶, 短边压东西墙顶, 长边在正中互吸。",
    ["dk4_a", "dk4_b"],
    highlight=["st4_w1", "st4_e2"],
    tip="顶层特意改用长方形楼板: 它的长边正好与下一步梯形屋面的下底等长。",
)
b.step(
    "合拢四坡大屋顶: 先装南、北两片梯形 (下底整边吸长方形楼板长边), "
    "再装东、西两片 (腰边与南北梯形互吸), 最后用压顶正方形封住顶口。",
    roof_ids[:1] + roof_ids[2:3] + roof_ids[1:2] + roof_ids[3:] + [roof_cap],
    highlight=["dk4_a", "dk4_b"],
    tip="装东西两片时先对准两条腰边再松手; 压顶四边同时吸住四片梯形上底。",
)
b.step(
    "竖立金色宝顶: 4 片等腰三角形在压顶上合拢成锥, 五重塔落成!",
    finial_ids,
    highlight=[roof_cap],
    tip="按 南-东-北-西 顺序合拢, 锥尖交汇于塔顶最高点 6.57 个单位 —— "
        "全库最高的东方古塔。",
)

b.finalize(
    model_id="pagoda_01",
    name="朱红五重塔",
    name_en="Five-story Pagoda 01",
    description=(
        "东方古建筑旗舰: 2x2 塔身五层通高, 前三层塔檐向四面外挑 (单边力矩控制在"
        "预算内、同侧檐板互吸共担), 顶层以 2 片长方形楼板换取与梯形下底等长的"
        "整边贴合, 四片梯形合拢成四坡大屋顶, 压顶之上再起金色锥形宝顶 —— "
        "总高 6.57 个单位, 层层飞檐的剪影就是天际线。"
    ),
    difficulty=4,
    tags=["古建筑", "宝塔", "东方", "旗舰"],
    min_pieces=100,
    min_steps=22,
)
