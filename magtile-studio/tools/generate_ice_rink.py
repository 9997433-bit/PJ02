#!/usr/bin/env python3
"""生成模型 data/models/ice_rink_01.json (滑冰场)。

城市生活主题: 全库首座以**大正方形冰面**为主角的运动场地 ——
6 片大正方形拼出 6x4 晶莹冰面, 四周长方形回廊压边, 回廊外沿
立起整圈长方形挡板 (南侧留 2 格宽入口), 四角挡板柱升红旗;
西侧一排悬挑坐板的看台 (背墙 + 座板, 面朝冰面), 东南角保暖小屋
(门框方朝北开门 + 等腰尖顶), 入口外一辆车轮底座磨冰车正要开进
场 —— 冰刀与冰面的沙沙声, 是冬天最好听的音乐。

结构总览 (世界单位: 1.0 = 正方形磁力片边长):
  - 冰面 [0,6]x[0,4]: 大正方形 x6                              6 片
  - 回廊压边: 长方形 x10 + 四角方板 x4                        14 片
  - 挡板: 长方形立板 x9 (南留入口) + 四角柱 x8 + 角旗 x4      21 片
  - 看台 (西侧): 台面 5 + 背墙 5 + 悬挑坐板 5                 15 片
  - 保暖小屋 [8,10]x[0,2]: 引路 2 + 地板 4 + 立墙 8 (门框方)
    + 平顶 4 + 等腰尖顶 4                                     22 片
  - 磨冰车 (入口外): 车轮底座 + 长方形侧壁 + 首尾墙 + 车顶 2   6 片
  合计 84 片, 19 个教程步骤, 7 种磁力片形状。

物理规则要点 (通过 R1~R8 全部校验):
  - 大正方形边长 2, 与相邻大正方形整边等长互吸; 回廊长方形的
    长边与大正方形边等长贴合 (2 = 2), 是冰面与外围的唯一转换件;
  - 挡板立板底边 (长 2) 整边吸回廊长方形外沿长边, 四角柱底边
    吸角方板边, 柱与立板竖边互吸锁角;
  - 看台坐板一排共线铰链合并受力: 力矩 75 <= 严格档预算 87.5;
  - 磨冰车厢壁长方形整边吸底座长边, 底座北长边整边吸回廊南沿
    (2 = 2), 首尾墙底边吸底座短边。

用法: python3 tools/generate_ice_rink.py  (在 magtile-studio 目录下运行)
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from magtile_gen import ModelBuilder  # noqa: E402

b = ModelBuilder()

ICE = "clear"       # 冰面
RIM = "cyan"        # 回廊压边
BOARD = "blue"      # 挡板
FLAG = "red"        # 角旗
STAND = "purple"    # 看台
HUT = "orange"      # 保暖小屋
HUTROOF = "gray"    # 小屋平顶
HUTHAT = "red"      # 小屋尖顶
ZAM = "green"       # 磨冰车
GLASS = "clear"     # 磨冰车驾驶窗

# =================================================================
# 1. 冰面: 6 片大正方形拼 [0,6]x[0,4]
# =================================================================
for i, (cx, cy) in enumerate([(1, 1), (3, 1), (5, 1), (1, 3), (3, 3), (5, 3)]):
    b.add(f"ice_{i}", "large_square", (float(cx), float(cy), 0.0), (0, 0, 0), ICE)

# =================================================================
# 2. 回廊压边: 长方形 x10 + 四角方板 x4
# =================================================================
for i, x0 in enumerate((0, 2, 4)):
    b.flat_rect(f"rm_s_{i}", x0, -1, 0.0, RIM, axis="x")     # 南回廊
    b.flat_rect(f"rm_n_{i}", x0, 4, 0.0, RIM, axis="x")      # 北回廊
for i, y0 in enumerate((0, 2)):
    b.flat_rect(f"rm_w_{i}", -1, y0, 0.0, RIM, axis="y")     # 西回廊
    b.flat_rect(f"rm_e_{i}", 6, y0, 0.0, RIM, axis="y")      # 东回廊
b.flat("cn_sw", -1, -1, 0.0, RIM)
b.flat("cn_se", 6, -1, 0.0, RIM)
b.flat("cn_nw", -1, 4, 0.0, RIM)
b.flat("cn_ne", 6, 4, 0.0, RIM)

# =================================================================
# 3. 挡板: 长方形立板 (南留 [2,4] 入口) + 四角柱 + 角旗
# =================================================================
b.lintel_ns("bd_s_0", 0, -1.0, 0, BOARD)                     # 南挡板西段
b.lintel_ns("bd_s_1", 4, -1.0, 0, BOARD)                     # 南挡板东段
for i, x0 in enumerate((0, 2, 4)):
    b.lintel_ns(f"bd_n_{i}", x0, 5.0, 0, BOARD)              # 北挡板
for i, y0 in enumerate((0, 2)):
    b.lintel_ew(f"bd_w_{i}", -1.0, y0, 0, BOARD)             # 西挡板
    b.lintel_ew(f"bd_e_{i}", 7.0, y0, 0, BOARD)              # 东挡板
b.wall_ns("cp_sw_s", -1, -1.0, 0, BOARD)                     # 四角柱 (L 形)
b.wall_ew("cp_sw_w", -1.0, -1, 0, BOARD)
b.wall_ns("cp_se_s", 6, -1.0, 0, BOARD)
b.wall_ew("cp_se_e", 7.0, -1, 0, BOARD)
b.wall_ns("cp_nw_n", -1, 5.0, 0, BOARD)
b.wall_ew("cp_nw_w", -1.0, 4, 0, BOARD)
b.wall_ns("cp_ne_n", 6, 5.0, 0, BOARD)
b.wall_ew("cp_ne_e", 7.0, 4, 0, BOARD)
b.crest_ns("fl_sw", -1, -1.0, 1.0, FLAG)                     # 角旗
b.crest_ns("fl_se", 6, -1.0, 1.0, FLAG)
b.crest_ns("fl_nw", -1, 5.0, 1.0, FLAG)
b.crest_ns("fl_ne", 6, 5.0, 1.0, FLAG)

# =================================================================
# 4. 看台 (西侧 [-2,-1]x[-1,4]): 台面 + 背墙 + 悬挑坐板
# =================================================================
for i, y0 in enumerate(range(-1, 4)):
    b.flat(f"st_f_{i}", -2, y0, 0.0, STAND)
for i, y0 in enumerate(range(-1, 4)):
    b.wall_ew(f"st_w_{i}", -2.0, y0, 0, STAND)
for i, y0 in enumerate(range(-1, 4)):
    b.flat(f"st_s_{i}", -2, y0, 1.0, STAND)

# =================================================================
# 5. 保暖小屋 [8,10]x[0,2]: 引路 x2 + 地板 + 立墙 (门框方朝北) + 顶
#    (小屋退离东挡板一格, 引路两片把它接进场地)
# =================================================================
b.flat("ht_path0", 7, -1, 0.0, RIM)
b.flat("ht_path1", 8, -1, 0.0, RIM)
for x in range(8, 10):
    for y in range(2):
        b.flat(f"ht_f_{x}_{y}", x, y, 0.0, HUT)
for x in range(8, 10):
    b.wall_ns(f"ht_s_{x}", x, 0.0, 0, HUT)
for y in range(2):
    b.wall_ew(f"ht_w_{y}", 8.0, y, 0, HUT)
    b.wall_ew(f"ht_e_{y}", 10.0, y, 0, HUT)
b.add("ht_door", "door_frame", (8.5, 2.0, 0.5), (90, 0, 0), HUT)
b.wall_ns("ht_n_9", 9, 2.0, 0, HUT)
for x in range(8, 10):
    for y in range(2):
        b.flat(f"ht_r_{x}_{y}", x, y, 1.0, HUTROOF)
HUT_HAT = b.hat4("ht_hat", 9, 1, 1.0, HUTHAT)

# =================================================================
# 6. 磨冰车 (入口外 [2,4]x[-2,-1]): 底座 + 侧壁 + 首尾 + 车顶
# =================================================================
b.add("zb_ch", "wheel_base", (3.0, -1.5, 0.0), (0, 0, 0), ZAM)
b.lintel_ns("zb_s", 2, -2.0, 0, ZAM)                         # 南侧壁
b.wall_ew("zb_w", 2.0, -2, 0, ZAM)                           # 车尾
b.wall_ew("zb_e", 4.0, -2, 0, GLASS)                         # 驾驶窗
b.flat("zb_r0", 2, -2, 1.0, ZAM)                             # 车顶
b.flat("zb_r1", 3, -2, 1.0, ZAM)

# =================================================================
# 教程步骤 (19 步)
# =================================================================
b.step(
    "铺设冰面南排: 3 片透明大正方形整边互吸。",
    ["ice_0", "ice_1", "ice_2"],
    tip="大正方形边长 2, 一片顶四片 —— 冰面要大才滑得开。",
)
b.step(
    "铺设冰面北排: 再 3 片, 6x4 大冰面合拢。",
    ["ice_3", "ice_4", "ice_5"],
    highlight=["ice_0"],
    tip="6 片大正方形缝缝相吸, 冰面晶莹平整。",
)
b.step(
    "压边南回廊与两角: 3 片青色长方形长边整边吸冰面南沿, "
    "西南/东南角各补 1 片方板。",
    ["rm_s_0", "rm_s_1", "rm_s_2", "cn_sw", "cn_se"],
    highlight=["ice_0", "ice_2"],
    tip="长方形长边与大正方形边等长 (2 = 2), 是冰面的转换压边。",
)
b.step(
    "压边北回廊与两角: 再 3 片长方形 + 2 片角板。",
    ["rm_n_0", "rm_n_1", "rm_n_2", "cn_nw", "cn_ne"],
    highlight=["ice_3", "ice_5"],
    tip="北回廊与南回廊对称, 角板锁住四角。",
)
b.step(
    "压边东西回廊: 各 2 片竖放长方形, 回廊成环。",
    ["rm_w_0", "rm_w_1", "rm_e_0", "rm_e_1"],
    highlight=["cn_sw", "cn_nw"],
    tip="回廊环一合拢, 整个场地连成一个刚性大环。",
)
b.step(
    "立南挡板与南角柱: 2 片长方形立板底边吸回廊外沿 (中间留 2 格"
    "入口), 西南/东南角柱 L 形锁角。",
    ["bd_s_0", "bd_s_1", "cp_sw_s", "cp_sw_w", "cp_se_s", "cp_se_e"],
    highlight=["rm_s_0", "rm_s_2"],
    tip="挡板底边 (长 2) 与回廊长方形外沿整边等长互吸。",
)
b.step(
    "立北挡板与北角柱: 3 片立板 + 4 片角柱, 北线合拢。",
    ["bd_n_0", "bd_n_1", "bd_n_2", "cp_nw_n", "cp_nw_w", "cp_ne_n", "cp_ne_e"],
    highlight=["rm_n_0", "rm_n_2"],
    tip="角柱竖边与挡板竖边互吸 —— 拐角是挡板圈最结实的地方。",
)
b.step(
    "立东西挡板: 各 2 片, 挡板圈只留南入口。",
    ["bd_w_0", "bd_w_1", "bd_e_0", "bd_e_1"],
    highlight=["cp_sw_w", "cp_ne_e"],
    tip="冰球飞不出去, 小朋友也扶得稳 —— 这就是挡板的使命。",
)
b.step(
    "升四面角旗: 红色等边三角立上四角柱顶边。",
    ["fl_sw", "fl_se", "fl_nw", "fl_ne"],
    highlight=["cp_sw_s", "cp_ne_n"],
    tip="角旗立在角柱顶的铰链线上, 重心正压。",
)
b.step(
    "铺看台台面: 西侧一列 5 片紫色方板, 与西南角板相接。",
    [f"st_f_{i}" for i in range(5)],
    highlight=["cn_sw"],
    tip="看台在挡板外一步之遥 —— 视野正对冰面。",
)
b.step(
    "竖看台背墙: 5 片方墙立在台面西沿。",
    [f"st_w_{i}" for i in range(5)],
    highlight=["st_f_0", "st_f_4"],
    tip="背墙底边吸台面板边, 竖边互吸成整面。",
)
b.step(
    "搭看台坐板: 5 片坐板压背墙顶边、向冰面悬挑。",
    [f"st_s_{i}" for i in range(5)],
    highlight=["st_w_0", "st_w_4"],
    tip="一整排坐板共线铰链合并受力 (力矩 75 <= 预算 87.5)。",
)
b.step(
    "铺保暖小屋引路与地板: 引路 2 片 + 地板 4 片 (东南角外一格)。",
    ["ht_path0", "ht_path1"]
    + [f"ht_f_{x}_{y}" for x in range(8, 10) for y in range(2)],
    highlight=["cn_se"],
    tip="引路板把小屋和场地连成一个连通整体, 小屋退离挡板一格。",
)
b.step(
    "竖小屋南墙与西墙: 橙色方墙各 2 片。",
    ["ht_s_8", "ht_s_9", "ht_w_0", "ht_w_1"],
    highlight=["ht_f_8_0"],
    tip="墙底边吸地板边, 拐角竖边互吸。",
)
b.step(
    "竖小屋东墙与北墙: 门框方大门朝北 (背风开门)。",
    ["ht_e_0", "ht_e_1", "ht_door", "ht_n_9"],
    highlight=["ht_w_1"],
    tip="门框方外框照常整边吸合 —— 推门进屋喝热可可。",
)
b.step(
    "盖小屋平顶: 4 片灰色顶板压住四面墙顶边。",
    [f"ht_r_{x}_{y}" for x in range(8, 10) for y in range(2)],
    highlight=["ht_door"],
    tip="盖上顶板, 小屋变成闭合的箱形筒。",
)
b.step(
    "合拢小屋尖顶: 4 片红色等腰三角斜棱两两互吸、锥尖自锁。",
    HUT_HAT,
    highlight=["ht_r_9_1"],
    tip="尖顶是滑冰场的地标 —— 远远就能看见。",
)
b.step(
    "拼装磨冰车: 车轮底座停在入口外, 北长边整边吸回廊南沿; "
    "长方形侧壁吸底座长边, 车尾与驾驶窗合拢。",
    ["zb_ch", "zb_s", "zb_w", "zb_e"],
    highlight=["rm_s_1"],
    tip="底座长边与回廊长方形长边等长互吸 (2 = 2)。",
)
b.step(
    "盖磨冰车车顶: 2 片绿色顶板, 两端吸车尾与驾驶窗顶边 —— "
    "滑冰场开门迎客!",
    ["zb_r0", "zb_r1"],
    highlight=["zb_w", "zb_e"],
    tip="磨冰车缓缓开过, 冰面焕然如镜。",
)

b.finalize(
    model_id="ice_rink_01",
    name="滑冰场",
    name_en="Ice Rink",
    description=(
        "晶莹滑冰场: 6 片大正方形拼出 6x4 透明冰面, 青色长方形回廊压边, "
        "外沿立起整圈长方形挡板 (南留入口), 四角柱升红旗; 西侧看台背墙"
        "托一排悬挑坐板面朝冰面, 东南角保暖小屋门框方朝北开门、头戴红色"
        "等腰尖顶, 入口外车轮底座磨冰车正要进场 —— 冰刀与冰面的沙沙声, "
        "是冬天最好听的音乐。"
    ),
    difficulty=4,
    tags=["城市", "运动", "冬季", "车辆", "进阶"],
    min_pieces=84,
    min_steps=19,
)
