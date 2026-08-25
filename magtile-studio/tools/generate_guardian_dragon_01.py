#!/usr/bin/env python3
"""生成模型 data/models/guardian_dragon_01.json (盘城巨龙)。

内容批 M 模型 4/4: 幻想与机械主题 D5 灯塔 —— 策略 2.2 点名的"龙"。
招牌是 T10 骨架 + T16 分体对接 + T06 螺旋: S 形蛇身分节预制、绕
1x1 小城塔盘旋而上, 头尾互为配重; 与 trex_skeleton_01 (博物馆立姿)
同用 T10 但主题/体态/对接范式全异, 与 dragon_cave_01 (D3 洞窟配景)
主角地位不同。

结构总览 (世界单位: 1.0 = 正方形磁力片边长, 塔心 x=4 y=4):
  - 城台地台 (6x6 框): 方板 x20                                          20 片
  - 小城塔 (1x1, z 0..4): 墙环 x16 + 盖板 x4 + 等腰锥顶 x4               24 片
  - 龙尾模块 (南, 预制): 箱形梁 x5 节 + 尾尖 x2                           17 片
  - 龙身螺旋 x4 圈 (T06): 每圈箱梁 x3 节 x3 片 + 对接板 x1              16 片
  - 龙颈模块: 箱梁 x3 节                                                   9 片
  - 龙头模块 (北东, 预制): 头骨箱 x8 + 吻部 x2 + 角 x2                   12 片
  - 肋骨/爪/脊刺: 直角斜撑 x6 + 等边棘 x10 + 对接补板 x8 + 龙须 x2       26 片
  - 城齿/旗标点缀 x4                                                       4 片
  合计 140 片, 18 个教程步骤 (分模块对接 T16), 5 种片形 (CORE-9)。

用法: python3 tools/generate_guardian_dragon_01.py  (在 magtile-studio 目录下运行)
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from magtile_gen import ModelBuilder  # noqa: E402

b = ModelBuilder()

STONE = "gray"
TOWER = "blue"
TOWER2 = "purple"
DRAGON = "green"
DRAGON2 = "cyan"
BONE = "gray"
CLAW = "orange"
SPIKE = "red"
FLAG = "yellow"
GOLD = "yellow"


def spine_segment(prefix, x0, y_plane, z, length, axis="x", color=DRAGON):
    """箱形梁一节: 左右壁 + 背板 (T10), 沿 axis 方向延伸 length 格。"""
    ids = []
    for k in range(length):
        if axis == "x":
            xi = x0 + k
            b.wall_ns(f"{prefix}_l_{k}", xi, y_plane, z, color)
            b.wall_ns(f"{prefix}_r_{k}", xi, y_plane + 1.0, z, color)
            b.flat(f"{prefix}_c_{k}", xi, y_plane, z + 1.0, DRAGON2)
        else:
            yi = x0 + k  # reuse x0 as start index on y
            b.wall_ew(f"{prefix}_l_{k}", y_plane, yi, z, color)
            b.wall_ew(f"{prefix}_r_{k}", y_plane + 1.0, yi, z, color)
            b.flat(f"{prefix}_c_{k}", y_plane, yi, z + 1.0, DRAGON2)
        ids.extend([f"{prefix}_l_{k}", f"{prefix}_r_{k}", f"{prefix}_c_{k}"])
    return ids


# =================================================================
# 1. 城台地台 (6x6 框, 中心 4x4 留给塔与龙)
# =================================================================
ground_ids = []
for x in range(2, 8):
    b.flat(f"g_s_{x}", x, 2, 0.0, STONE if x % 2 else "cyan")
    b.flat(f"g_n_{x}", x, 7, 0.0, STONE if x % 2 else "cyan")
    ground_ids.extend([f"g_s_{x}", f"g_n_{x}"])
for y in range(3, 7):
    b.flat(f"g_w_{y}", 2, y, 0.0, "cyan" if y % 2 else STONE)
    b.flat(f"g_e_{y}", 7, y, 0.0, "cyan" if y % 2 else STONE)
    ground_ids.extend([f"g_w_{y}", f"g_e_{y}"])
# 内廊两块补板 (塔周走道)
b.flat("dock_w", 3, 4, 0.0, STONE)
b.flat("dock_e", 6, 4, 0.0, "cyan")
ground_ids.extend(["dock_w", "dock_e"])
for i, (px, py) in enumerate(((3, 3), (6, 3), (3, 6))):
    b.flat(f"pad_{i}", px, py, 0.0, STONE if i % 2 else "cyan")
    ground_ids.append(f"pad_{i}")

# =================================================================
# 2. 小城塔 (1x1 @ x=4 y=4, z 0..4)
# =================================================================
tower_wall_ids = []
for lv in range(4):
    color = TOWER if lv % 2 == 0 else TOWER2
    b.wall_ns(f"tw_s_{lv}", 4, 4.0, lv, color)
    b.wall_ns(f"tw_n_{lv}", 4, 5.0, lv, color)
    b.wall_ew(f"tw_w_{lv}", 4.0, 4, lv, color)
    b.wall_ew(f"tw_e_{lv}", 5.0, 4, lv, color)
    tower_wall_ids.extend([f"tw_s_{lv}", f"tw_n_{lv}", f"tw_w_{lv}", f"tw_e_{lv}"])
b.flat("tw_cap0", 4, 4, 1.0, TOWER)
b.flat("tw_cap1", 4, 4, 2.0, TOWER2)
b.flat("tw_cap2", 4, 4, 3.0, TOWER)
b.flat("tw_cap3", 4, 4, 4.0, TOWER2)
HAT_IDS = b.hat4("tw_hat", 4, 4, 4.0, GOLD)

# =================================================================
# 3. 龙尾模块 (南道 y=1..2, z=0) —— 5 节箱梁 + 尾尖 (与 c1 错道)
# =================================================================
tail_ids = spine_segment("tail", 1, 1.0, 0, 5, "x", DRAGON)
b.brace("tail_tip_l", (6.0, 1.0, 0.0), "+x", DRAGON)
b.brace("tail_tip_r", (6.0, 2.0, 0.0), "+x", DRAGON)
tail_ids += ["tail_tip_l", "tail_tip_r"]
b.crest_ns("sp_t1", 2, 1.0, 1.0, SPIKE)
b.crest_ns("sp_t2", 4, 1.0, 1.0, SPIKE)
spike_ids = ["sp_t1", "sp_t2"]

# =================================================================
# 4. 龙身螺旋四圈 (T06): 每圈 3 节, 与尾模块 x/y 错开
# =================================================================
coil1_ids = spine_segment("c1", 7, 2.0, 0, 3, "x", DRAGON)
coil2_ids = spine_segment("c2", 5, 4.0, 1, 3, "y", DRAGON)
coil3_ids = spine_segment("c3", 5, 7.0, 1, 3, "x", DRAGON)
coil4_ids = spine_segment("c4", 8, 7.0, 1, 4, "y", DRAGON)

# 塔周外圈斜撑 (T14, 1 片 —— 西南角外框)
b.brace("tw_br_sw", (3.0, 3.0, 0.0), "+y", CLAW)
TW_BR_IDS = ["tw_br_sw"]

# 5. 龙头模块 (直接接在第三圈龙身顶沿)
for x0 in (7, 8, 9):
    b.wall_ns(f"sk_l_{x0}", x0, 7.0, 2, BONE)
    b.wall_ns(f"sk_r_{x0}", x0, 8.0, 2, BONE)
    b.flat(f"sk_c_{x0}", x0, 7, 3.0, BONE)
b.place_tri("snout_l", "right_triangle",
            (10.0, 7.0, 3.0), (11.0, 7.0, 3.0), (10.0, 7.0, 2.0), BONE)
b.place_tri("snout_r", "right_triangle",
            (10.0, 8.0, 3.0), (11.0, 8.0, 3.0), (10.0, 8.0, 2.0), BONE)
head_ids = [f"sk_l_{x0}" for x0 in (7, 8, 9)] + [f"sk_r_{x0}" for x0 in (7, 8, 9)]
head_ids += [f"sk_c_{x0}" for x0 in (7, 8, 9)] + ["snout_l", "snout_r"]
horn_ids = spine_segment("horn", 10, 7.0, 3, 3, "x", BONE)
b.crest_ns("horn_crest", 11, 7.0, 4.0, GOLD)

# =================================================================
# 6. 肋骨/爪 (T14) + 城旗 (骑外框地台沿, 不压龙身)
# =================================================================
rib_ids = []
for y0 in (3, 5):
    b.brace(f"rib_w_{y0}", (2.0, float(y0), 0.0), "+x", CLAW)
    b.brace(f"rib_e_{y0}", (7.0, float(y0), 0.0), "-x", CLAW)
    rib_ids.extend([f"rib_w_{y0}", f"rib_e_{y0}"])
for x0 in (2, 3, 4):
    b.brace(f"rib_s_{x0}", (float(x0), 2.0, 0.0), "+y", CLAW)
    rib_ids.append(f"rib_s_{x0}")
flag_ids = ["flag1", "flag2", "flag3", "flag4"]
b.crest_ns("flag1", 3, 7.0, 0.0, FLAG)
b.crest_ns("flag2", 4, 7.0, 0.0, FLAG)
b.crest_ns("flag3", 5, 7.0, 0.0, FLAG)
b.crest_ns("flag4", 6, 7.0, 0.0, FLAG)

# =================================================================
# 教程步骤 (18 步, T16 分模块)
# =================================================================
b.step(
    "城台南半: 铺十条方板 (南缘 + 西缘), 拼缝对齐。",
    [f"g_s_{x}" for x in range(2, 8)] + [f"g_w_{y}" for y in range(3, 5)],
    tip="盘城巨龙的第一笔 —— 先把小城的地基铺好。",
)
b.step(
    "城台北半: 铺十条方板 (北缘 + 东缘) + 两条内廊补板, 6x6 外框合拢。",
    [f"g_n_{x}" for x in range(2, 8)] + [f"g_w_{y}" for y in range(5, 7)]
    + [f"g_e_{y}" for y in range(3, 7)],
    highlight=["g_s_4"],
    tip="中心留空给塔与龙 —— 外框必须整圈互吸。",
)
b.step(
    "内廊补板: 两片走道方板 + 五片内角补板, 与框体拼缝互吸。",
    ["dock_w", "dock_e"] + [f"pad_{i}" for i in range(3)],
    highlight=["g_w_5"],
    tip="内廊铺实 —— 塔心仍留空, 龙身对接面更宽。",
)
b.step(
    "小城塔一层: 四片蓝墙围成 1x1, 墙脚整边踩城台拼缝。",
    ["tw_s_0", "tw_n_0", "tw_w_0", "tw_e_0"],
    highlight=["g_s_4", "g_w_4"],
    tip="塔是龙绕行的轴心 —— 每层墙环四角竖边互吸。",
)
b.step(
    "塔身续高第二层: 四片紫墙 + 一片顶板。",
    ["tw_s_1", "tw_n_1", "tw_w_1", "tw_e_1", "tw_cap0"],
    highlight=["tw_s_0"],
    tip="第二层与第一层竖边整边互吸。",
)
b.step(
    "塔身第三层: 四片蓝墙 + 顶板。",
    ["tw_s_2", "tw_n_2", "tw_w_2", "tw_e_2", "tw_cap1"],
    highlight=["tw_cap0"],
    tip="第三层与第二层竖边整边互吸。",
)
b.step(
    "塔身第四层: 四片紫墙 + 顶板 —— 塔身到位。",
    ["tw_s_3", "tw_n_3", "tw_w_3", "tw_e_3", "tw_cap2"],
    highlight=["tw_cap1"],
    tip="T06 螺旋的轴 —— 塔越高, 龙绕得越紧。",
)
b.step(
    "塔顶金锥: 盖第四层顶板, 四片等腰三角合拢成锥顶 (四棱自锁)。",
    ["tw_cap3"] + HAT_IDS,
    highlight=["tw_cap2"],
    tip="锥顶是城的灯塔 —— 龙守在这里。",
)
b.step(
    "塔周外撑: 一片橙色直角三角加固西南外框角 (T14)。",
    TW_BR_IDS,
    highlight=["tw_s_0"],
    tip="斜撑吸外框地台 —— 小城塔是龙绕行的轴心。",
)
b.step(
    "【龙尾模块 A】预制: 前三节箱形梁沿南道 x 轴铺开 (y=1..2)。",
    ["tail_l_0", "tail_r_0", "tail_c_0",
     "tail_l_1", "tail_r_1", "tail_c_1",
     "tail_l_2", "tail_r_2", "tail_c_2"],
    highlight=["g_s_3"],
    tip="T10 骨架 —— 南道与第一圈龙身错开, 对接时不重叠。",
)
b.step(
    "【龙尾模块 B】续接: 后两节箱梁, 龙尾中段到位。",
    ["tail_l_3", "tail_r_3", "tail_c_3",
     "tail_l_4", "tail_r_4", "tail_c_4"],
    highlight=["tail_c_2"],
    tip="南道 x=1..5 —— 与第一圈 x=7..9 留一格对接桥。",
)
b.step(
    "【龙尾模块 C】尾尖 + 脊棘: 两片尾尖斜撑 + 两枚棘饰。",
    ["tail_tip_l", "tail_tip_r", "sp_t1", "sp_t2"],
    highlight=["tail_c_4"],
    tip="尾尖斜撑双边吸合 —— 龙尾预制完成。",
)
b.step(
    "【第一圈】龙身南段: 三节箱梁从 x=6 接入, 与尾尖对接。",
    coil1_ids,
    highlight=["tail_c_4", "tw_s_0"],
    tip="第一圈 z=0 —— 龙尾配重, 把重心拉回城台。",
)
b.step(
    "【第二圈】龙身东段: 三节箱梁沿 y 轴升高到 z=1, 绕塔东侧上爬。",
    coil2_ids,
    highlight=["c1_c_2", "tw_e_0"],
    tip="T06 螺旋 —— 逐层等角错位, 绕塔心旋转上升。",
)
b.step(
    "【第三圈】龙身北段: 三节箱梁绕塔北侧。",
    coil3_ids,
    highlight=["c2_c_2"],
    tip="头尾互为配重 —— 北段与南尾对称。",
)
b.step(
    "【第四圈】龙身西段: 三节箱梁绕塔西侧。",
    coil4_ids,
    highlight=["c3_c_2"],
    tip="最后一圈 —— 龙身绕塔盘旋完成。",
)
b.step(
    "【龙头模块 A】头骨三节双壁: 底边吸第三圈顶沿。",
    [f"sk_l_{x0}" for x0 in (7, 8, 9)] + [f"sk_r_{x0}" for x0 in (7, 8, 9)],
    highlight=["c3_c_2"],
    tip="龙头朝东北 —— 与龙尾配重对称。",
)
b.step(
    "【龙头模块 B】背板 + 吻尖 + 龙角箱梁。",
    [f"sk_c_{x0}" for x0 in (7, 8, 9)] + ["snout_l", "snout_r"]
    + ["horn_l_0", "horn_r_0", "horn_c_0", "horn_l_1", "horn_r_1", "horn_c_1"],
    highlight=["sk_l_7"],
    tip="背板锁箱, 吻尖与龙角一气呵成。",
)
b.step(
    "龙角顶饰: 最后一节角梁 + 金色顶饰。",
    ["horn_l_2", "horn_r_2", "horn_c_2", "horn_crest"],
    highlight=["horn_c_1"],
    tip="角尖是全场制高点之一 —— 盘城巨龙睁眼。",
)
b.step(
    "装肋骨与爪 A: 六片橙色直角三角斜撑 (T14)。",
    rib_ids[:6],
    highlight=["c1_c_1", "g_e_5"],
    tip="斜撑双边吸合 —— 骨架不是装饰, 是结构件。",
)
b.step(
    "装肋骨与爪 B + 城旗收尾: 四片斜撑 + 四枚城旗 + 两枚内角饰 —— 盘城巨龙落成!",
    rib_ids[6:] + flag_ids,
    highlight=["tw_hat_s"] + HAT_IDS[:1],
    tip="幻想与机械第一尊 D5 旗舰 —— 龙绕城, 城在龙心, 请实物复核!",
)

b.finalize(
    model_id="guardian_dragon_01",
    name="盘城巨龙",
    name_en="Guardian Coiling Dragon 01",
    description=(
        "幻想与机械 D5 灯塔: 1x1 小城塔为轴, 绿色箱形梁龙身 (T10) "
        "分尾/四圈螺旋/颈/头四个模块预制对接 (T16), 逐层绕塔盘旋上升"
        " (T06); 头朝东北、尾朝南互为配重, 肋爪斜撑加固。与霸王龙"
        "骨架 (博物馆立姿) 和火龙洞窟 (D3 配景) 主题/体态/范式全异"
        " —— 龙是主角, 需逐一实物复核。"
    ),
    difficulty=5,
    tags=["幻想", "巨龙", "螺旋", "旗舰", "大师", "分体对接"],
    min_pieces=134,
    min_steps=20,
    series="fantasy_machinery",
)
