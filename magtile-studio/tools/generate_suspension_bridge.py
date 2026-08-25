#!/usr/bin/env python3
"""生成模型 data/models/suspension_bridge_01.json (海湾悬索桥 · 双塔合龙)。

技法: T15 悬索模拟 (主) + T03 悬臂外挑 + T11 拱肩镜像; 范式 symmetric_pair。
招牌技法: 桥面以"单格悬挑 -> 斜拉索锁定"的节奏从两岸对称推进,
最后在主跨正中合龙; 主缆用菱形链贴着桥面沿口起伏, 用受压链条
再现悬索桥的受拉曲线。

结构总览 (世界单位: 1.0 = 正方形磁力片边长, 桥轴沿 x):
  - 桥面: 12 格长 x 2 格宽的高架路面 (z=1), 两端 30 度引桥坡道落地   28 片
  - 锚碇: 东西两岸各 1 座双片桥墩 + 锚碇广场                          8 片
  - 主塔: x=4 与 x=8 两座门式塔架 —— 双腿三层 + 横梁 + 双塔尖,
    塔腿立在桥面两侧, 桥面从门洞中穿过                               18 片
  - 斜拉索: 每塔 4 片直角三角形拉索, 竖直边吸塔腿、水平边吸桥面,
    与塔-桥面构成三角刚性节点 (T15 的"索"按压杆校验)                 8 片
  - 主缆: 菱形链 8 片, 立在桥面南北沿口, 向塔顶方向倾斜,
    拼出主缆下垂-上扬的曲线                                          8 片
  - 观景平台: 主跨两侧向外悬挑 2 片 (T03, 力矩预算内)                 4 片
  合计 74 片, 16 个教程步骤。

物理规则要点 (通过 R1~R8 全部校验):
  - 桥面任何时刻最多向支撑点外悬挑 1 格 (单格力矩 30 g·单位 <
    双缝预算 40), 悬挑下一格前必须先装斜拉索;
  - 斜拉索两条直角边分别整边吸住塔腿竖边与桥面沿边, 剪断任一
    铰链线后桥面仍经拉索-塔腿接地 —— 这就是悬索桥的受力故事;
  - 东西两岸分组施工 (第 7~11 步东岸子结构独立接地, 属预期的
    disconnected_assembly 分组提示), 第 12 步主跨合龙后全桥连通。

坐标约定与 C++ 端一致: 旋转为欧拉角 (度), R = Rz * Ry * Rx。
用法: python3 tools/generate_suspension_bridge.py  (在 magtile-studio 目录下运行)
"""

from magtile_gen import ModelBuilder

mb = ModelBuilder()

# =================================================================
# 1. 桥面几何常量
# =================================================================
DECK_Z = 1.0          # 桥面高度
TOWER_W = 4           # 西主塔平面 x=4
TOWER_E = 8           # 东主塔平面 x=8
PIER_W = 2            # 西桥墩平面 x=2
PIER_E = 10           # 东桥墩平面 x=10

# ---- 桥面 (12 格 x 2 格, 铺设顺序由步骤控制) ----------------------
for x0 in range(12):
    for row in range(2):
        mb.flat(f"d_{x0}_{row}", x0, row, DECK_Z, "gray")

# ---- 锚碇广场 + 桥墩 ----------------------------------------------
for row in range(2):
    mb.flat(f"pzw_{row}", PIER_W - 1, row, 0.0, "green")   # 西岸广场
    mb.flat(f"pze_{row}", PIER_E, row, 0.0, "green")       # 东岸广场
    mb.wall_ew(f"pierw_{row}", float(PIER_W), row, 0, "gray")
    mb.wall_ew(f"piere_{row}", float(PIER_E), row, 0, "gray")

# ---- 引桥坡道 (30 度, 坡尾自然落地) --------------------------------
mb.ramp("rampw_0", "-x", 0.0, 0, DECK_Z, "orange")
mb.ramp("rampw_1", "-x", 0.0, 1, DECK_Z, "orange")
mb.ramp("rampe_0", "+x", 12.0, 0, DECK_Z, "orange")
mb.ramp("rampe_1", "+x", 12.0, 1, DECK_Z, "orange")

# ---- 主塔: 门式塔架 (塔腿在桥面南北两侧, 桥面从门洞穿过) ------------
for tag, tx in (("w", TOWER_W), ("e", TOWER_E)):
    for lv in range(3):
        mb.wall_ew(f"t{tag}_s_{lv}", float(tx), -1, lv, "red")   # 南腿 y -1..0
        mb.wall_ew(f"t{tag}_n_{lv}", float(tx), 2, lv, "red")    # 北腿 y 2..3
    mb.lintel_ew(f"t{tag}_beam", float(tx), 0, 2, "red")         # 横梁 z 2..3
    mb.spire_ew(f"t{tag}_spire_s", float(tx), -1, 3.0, "yellow")
    mb.spire_ew(f"t{tag}_spire_n", float(tx), 2, 3.0, "yellow")

# ---- 斜拉索: 直角三角形, 竖边吸塔腿内侧竖边, 水平边吸桥面沿边 -------
for tag, tx in (("w", TOWER_W), ("e", TOWER_E)):
    mb.brace(f"stay{tag}W_s", (float(tx), 0.0, DECK_Z), "-x", "cyan")
    mb.brace(f"stay{tag}W_n", (float(tx), 2.0, DECK_Z), "-x", "cyan")
    mb.brace(f"stay{tag}E_s", (float(tx), 0.0, DECK_Z), "+x", "cyan")
    mb.brace(f"stay{tag}E_n", (float(tx), 2.0, DECK_Z), "+x", "cyan")

# ---- 主缆菱形链: 立在桥面沿口, 顶边向主塔方向倾斜 ------------------
# (x0, 朝向: +1 顶边偏东 / -1 顶边偏西) —— 锚跨向塔上扬, 主跨中央下垂
CABLE_SEGS = ((2, +1), (5, -1), (6, +1), (9, -1))
for rim, y in (("s", 0.0), ("n", 2.0)):
    for x0, lean in CABLE_SEGS:
        if lean > 0:
            w_from, w_to = (float(x0), y, DECK_Z), (float(x0 + 1), y, DECK_Z)
        else:
            w_from, w_to = (float(x0 + 1), y, DECK_Z), (float(x0), y, DECK_Z)
        mb.place_edge(f"cable_{rim}_{x0}", "rhombus", 0, w_from, w_to,
                      (0, 0, 1), "purple")

# ---- 观景平台: 主跨两侧各悬挑 2 片 (T03, 30 g·单位 < 预算 40) ------
mb.flat("bal_s_0", 5, -1, DECK_Z, "blue")
mb.flat("bal_s_1", 6, -1, DECK_Z, "blue")
mb.flat("bal_n_0", 5, 2, DECK_Z, "blue")
mb.flat("bal_n_1", 6, 2, DECK_Z, "blue")

# =================================================================
# 教程步骤 (16 步): 两岸对称推进, 桥面"悬挑一格 -> 拉索锁定"交替前进
# =================================================================
mb.step(
    "西岸锚碇: 铺 2 片绿色锚碇广场, 广场东缘立 2 片灰色桥墩 (平面 x=2), "
    "墩底吸住广场边。",
    ["pierw_0", "pierw_1", "pzw_0", "pzw_1"],
    tip="桥轴沿东西向, 先在桌面左侧留出全长约 15 格的场地。",
)
mb.step(
    "西引桥: 桥面第 1 排 2 片压上桥墩顶, 向西再接 1 排, 桥头挂 2 片橙色"
    "坡道落地 —— 西引桥自成稳定的三点支撑。",
    ["d_1_0", "d_1_1", "d_0_0", "d_0_1", "rampw_0", "rampw_1"],
    highlight=["pierw_0", "pierw_1"],
    tip="坡道顶边整边吸桥面西缘, 坡尾自然落地, 不需要额外支撑。",
)
mb.step(
    "桥面西进: 越过桥墩向东悬挑 1 排 (x 2..3)。单格悬挑在磁吸力矩预算内, "
    "但先别急着再挑第二排!",
    ["d_2_0", "d_2_1"],
    highlight=["pierw_0"],
    tip="轻按墩顶上方的桥面再放悬挑排, 避免翘板效应。",
)
mb.step(
    "西主塔: 再悬挑 1 排桥面后立即立塔 —— 南北塔腿各 3 层立在桥面两侧 "
    "(平面 x=4), 顶部横梁跨过桥面锁住双腿, 最后 2 片青色斜拉索把悬挑桥面"
    "吊在塔腿上。",
    ["d_3_0", "d_3_1",
     "tw_s_0", "tw_s_1", "tw_s_2", "tw_n_0", "tw_n_1", "tw_n_2",
     "tw_beam", "staywW_s", "staywW_n"],
    highlight=["d_2_0", "d_2_1"],
    tip="拉索竖直边吸塔腿内侧竖边、水平边吸桥面沿边, 三件互吸成刚性三角。",
)
mb.step(
    "西塔封顶与东侧拉索: 塔腿顶插 2 根黄色塔尖, 桥面再东进 1 排, 塔东侧"
    "也挂上 2 片斜拉索。",
    ["tw_spire_s", "tw_spire_n", "d_4_0", "d_4_1", "staywE_s", "staywE_n"],
    highlight=["tw_beam"],
    tip="每前进一排就用拉索锁定 —— 这正是真实悬索桥的架设节奏。",
)
mb.step(
    "主跨西段: 从西塔拉索处再向东悬挑 1 排 (x 5..6), 主跨西半完成, "
    "在此停住等待东岸桥面。",
    ["d_5_0", "d_5_1"],
    highlight=["staywE_s", "staywE_n"],
    tip="主跨中央还差两排 —— 悬索桥要从两岸同时推进才挑得过去。",
)
mb.step(
    "东岸锚碇 (分组施工): 转到桌面右侧, 独立铺设东岸广场与桥墩 (平面 x=10), "
    "与西岸完全镜像。东岸子结构暂时与西岸不相连, 属预期分组。",
    ["piere_0", "piere_1", "pze_0", "pze_1"],
    highlight=["pierw_0"],
    tip="对照西岸检查: 广场在墩东侧, 墩顶将托住桥面 x=10 的接缝。",
)
mb.step(
    "东引桥: 桥面排 x 10..12 压上东墩, 桥头挂 2 片坡道落地, 与西引桥镜像。",
    ["d_10_0", "d_10_1", "d_11_0", "d_11_1", "rampe_0", "rampe_1"],
    highlight=["piere_0", "piere_1"],
    tip="东西引桥关于主跨中心 (x=6) 严格镜像 —— 这是 T11 对称搭建。",
)
mb.step(
    "桥面西行: 从东墩向西悬挑 1 排 (x 9..10)。",
    ["d_9_0", "d_9_1"],
    highlight=["piere_0"],
    tip="仍然只挑一排就停 —— 等东主塔的拉索。",
)
mb.step(
    "东主塔: 与西塔镜像 —— 悬挑 1 排桥面, 立南北塔腿各 3 层 (平面 x=8), "
    "架横梁, 塔东侧挂 2 片拉索锁定悬挑段。",
    ["d_8_0", "d_8_1",
     "te_s_0", "te_s_1", "te_s_2", "te_n_0", "te_n_1", "te_n_2",
     "te_beam", "stayeE_s", "stayeE_n"],
    highlight=["d_9_0", "d_9_1"],
    tip="东塔每一件都应出现在西塔的镜像位置上。",
)
mb.step(
    "东塔封顶与西侧拉索: 插 2 根塔尖, 桥面向西再进 1 排, 塔西侧挂 2 片"
    "拉索。",
    ["te_spire_s", "te_spire_n", "d_7_0", "d_7_1", "stayeW_s", "stayeW_n"],
    highlight=["te_beam"],
    tip="现在主跨只差正中一排 —— 合龙时刻到了。",
)
mb.step(
    "主跨合龙: 最后一排桥面 (x 6..7) 同时吸住东西两侧桥面接缝, 全桥连通! "
    "东西两岸从此不再是孤岛。",
    ["d_6_0", "d_6_1"],
    highlight=["d_5_0", "d_7_0"],
    tip="合龙排两边同时对缝再整体压下, 一次到位。",
)
mb.step(
    "主缆·南幅: 4 片紫色菱形立在桥面南沿口 —— 锚跨两片顶边朝主塔上扬, "
    "主跨两片从中央向两塔上扬, 拼出主缆的下垂曲线。",
    ["cable_s_2", "cable_s_5", "cable_s_6", "cable_s_9"],
    highlight=["d_2_0", "d_6_0"],
    tip="菱形底边整边吸桥面沿口; 倾斜方向看准再放, 曲线才连贯。",
)
mb.step(
    "主缆·北幅: 北沿口 4 片菱形与南幅严格镜像。",
    ["cable_n_2", "cable_n_5", "cable_n_6", "cable_n_9"],
    highlight=["cable_s_2", "cable_s_9"],
    tip="从桥头方向眯眼看过去, 南北两条主缆应完全重合。",
)
mb.step(
    "南观景台: 主跨南侧向外悬挑 2 片蓝色观景平台 (T03 悬臂, 两片互吸共享"
    "力矩预算)。",
    ["bal_s_0", "bal_s_1"],
    highlight=["cable_s_5", "cable_s_6"],
    tip="两片先在手里吸成 1x2 再整体贴上桥沿, 力矩最小。",
)
mb.step(
    "北观景台: 北侧镜像悬挑 2 片 —— 海湾悬索桥合龙通车!",
    ["bal_n_0", "bal_n_1"],
    highlight=["bal_s_0", "bal_s_1"],
    tip="从塔顶俯瞰: 双塔、双缆、双观景台全部左右对称, 这就是悬索桥的美。",
)

mb.finalize(
    model_id="suspension_bridge_01",
    name="海湾悬索桥",
    name_en="Bay Suspension Bridge 01",
    description=(
        "双塔门式悬索桥: 桥面以'单格悬挑 -> 斜拉索锁定'的节奏从东西两岸对称"
        "推进, 每片直角三角拉索的竖边吸塔腿、水平边吸桥面, 与塔身构成三角"
        "刚性节点; 主跨正中合龙后, 8 片菱形主缆沿桥面沿口拼出下垂-上扬的"
        "悬索曲线, 观景平台在主跨两侧悬挑收尾。搭的过程就是一堂桥梁工程课。"
    ),
    difficulty=3,
    tags=["桥梁", "悬索桥", "对称", "工程", "合龙"],
    min_pieces=60,
    min_steps=16,
)
