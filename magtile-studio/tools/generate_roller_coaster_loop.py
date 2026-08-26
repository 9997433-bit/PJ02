#!/usr/bin/env python3
"""生成模型 data/models/roller_coaster_loop_01.json (过山车环圈段)。

第三批模型 ⑤: 游乐园主题 —— 全库第一个"闭合环圈"结构:
6 片梯形在竖直平面内首尾互吸, 拼成一个外六边形边长 2、
内六边形边长 1 的空心大环圈 —— 中间的六边形洞就是过山车
穿越的圈心! 环圈西侧是登顶小丘 (桥墩 + 双坡道), 再往西是
带雨棚的车站与出站坡道, 环圈东侧停着两节红橙相连的过山车。

结构总览 (世界单位: 1.0 = 正方形磁力片边长):
  - 地面: 南侧游园带 + 轨道带 + 北侧游园带 (10 格长三条带)     20 片
  - 车站: 箱形站台 (圈层 4 + 台面 1) + 雨棚 (柱 2 + 顶 1)       8 片
  - 站牌与出站坡道: 扇形招牌 1 + 30 度坡道 1 + 排队栏 1          3 片
  - 登顶小丘: 箱形桥墩 (4 墙 + 顶板) + 上/下行坡道 x2            7 片
  - 大环圈: 6 片梯形拼成的空心六边环 (竖直自锁)                  6 片
  - 过山车: 两节车厢 (侧板/尾板/挡风尖)                          7 片
  - 场景: 旗杆塔 x2 (墙 + 旗) + 缓冲挡 + 起点闸门               6 片
  合计 57 片, 16 个教程步骤, 5 种磁力片形状。

几何要点:
  - 梯形下底 2 / 上底 1 / 两腰 1 / 高 0.866, 恰好是六边形环带的
    一个扇区 —— 6 片腰腰相吸即成闭环, 环圈是拓扑环, 剪断任何
    一条铰链线都还有第二条路径, 天生抗塌;
  - 环圈立在游园带与轨道带的公共拼缝上, 底片下底 (长 2) 同时
    吸住两侧长方形地砖的长边;
  - 下行坡道贴着环圈左肩俯冲而过, 与环圈平面零接触。

用法: python3 tools/generate_roller_coaster_loop.py  (在 magtile-studio 目录下运行)
"""

import math

from magtile_gen import ModelBuilder

b = ModelBuilder()

XC, YC = 6.0, 1.0          # 环圈中轴 x / 环圈所在平面 y
CZ = 1.732051              # 环心高度 (外六边形边长 2)
# 外六边形顶点 (平面 y=YC, 逆时针, 从左下角开始)
O = [(XC - 1, 0.0), (XC + 1, 0.0), (XC + 2, CZ),
     (XC + 1, 2 * CZ), (XC - 1, 2 * CZ), (XC - 2, CZ)]
# 内六边形顶点 (同心, 边长 1)
I = [(XC - 0.5, CZ / 2), (XC + 0.5, CZ / 2), (XC + 1, CZ),
     (XC + 0.5, 1.5 * CZ), (XC - 0.5, 1.5 * CZ), (XC - 1, CZ)]

# =================================================================
# 1. 地面三条带 (x 0..10): 南游园带 y0..1 / 轨道带 y1..2 / 北游园带 y2..3
# =================================================================
b.flat_rect("apron_s0", 0, 0, 0, "green")     # 站台地基
b.flat_rect("apron_s1", 2, 0, 0, "green")
b.flat("apron_s2", 4, 0, 0, "green")          # 排队栏落点 (单格)
b.flat_rect("apron_s3", 5, 0, 0, "green")     # 环圈南锚
b.flat_rect("apron_s4", 7, 0, 0, "green")
b.flat("apron_s5", 9, 0, 0, "green")
b.flat_rect("track_w", 0, 1, 0, "gray")       # 轨道带
b.flat("track_p0", 2, 1, 0, "gray")
b.flat("track_p1", 3, 1, 0, "gray")           # 桥墩基座
b.flat("track_p2", 4, 1, 0, "gray")
b.flat_rect("track_loop", 5, 1, 0, "gray")    # 环圈北锚
b.flat("track_c0", 7, 1, 0, "gray")           # 车厢停靠区
b.flat("track_c1", 8, 1, 0, "gray")
b.flat("track_end", 9, 1, 0, "gray")
b.flat_rect("apron_n0", 0, 2, 0, "green")     # 北游园带
b.flat_rect("apron_n1", 2, 2, 0, "green")
b.flat("apron_n2", 4, 2, 0, "green")          # 旗杆落点 (单格)
b.flat("apron_n3", 5, 2, 0, "green")          # 旗杆落点 (单格)
b.flat_rect("apron_n4", 6, 2, 0, "green")
b.flat_rect("apron_n5", 8, 2, 0, "green")

# =================================================================
# 2. 车站: 箱形站台 + 雨棚 + 扇形招牌 + 出站坡道 + 排队栏
# =================================================================
b.lintel_ns("st_s", 0, 0, 0, "blue")          # 站台圈层
b.lintel_ns("st_n", 0, 1, 0, "blue")
b.wall_ew("st_w", 0, 0, 0, "blue")
b.wall_ew("st_e", 2, 0, 0, "blue")
b.flat_rect("st_deck", 0, 0, 1, "yellow")     # 站台台面
b.wall_ew("st_post_w", 0, 0, 1, "clear")      # 雨棚柱
b.wall_ew("st_post_e", 2, 0, 1, "clear")
b.flat_rect("st_roof", 0, 0, 2, "blue")       # 雨棚顶
b.place_edge("st_sign", "sector", 0,
             (0.0, 1.0, 2.0), (0.0, 0.0, 2.0), (0, 0, 1), "purple")
b.ramp("st_exit", "-x", 0.0, 0, 1.0, "yellow")  # 出站坡道
b.crest_ns("queue", 4, 0, 0, "purple")        # 排队栏

# =================================================================
# 3. 登顶小丘: 箱形桥墩 ([3,4]x[1,2]) + 上行/俯冲坡道
# =================================================================
b.wall_ns("pier_s", 3, 1, 0, "gray")
b.wall_ns("pier_n", 3, 2, 0, "gray")
b.wall_ew("pier_w", 3, 1, 0, "gray")
b.wall_ew("pier_e", 4, 1, 0, "gray")
b.flat("pier_top", 3, 1, 1, "red")
b.ramp("hill_up", "-x", 3.0, 1, 1.0, "red")   # 上行坡道 (向西落地)
b.ramp("hill_dn", "+x", 4.0, 1, 1.0, "red")   # 俯冲坡道 (贴着环圈左肩)

# =================================================================
# 4. 大环圈: 6 片梯形首尾互吸成空心六边环 (竖直平面 y=YC)
# =================================================================
LOOP_COLORS = ["red", "yellow", "red", "yellow", "red", "yellow"]
for k in range(6):
    o0 = (O[k][0], YC, O[k][1])
    o1 = (O[(k + 1) % 6][0], YC, O[(k + 1) % 6][1])
    im = ((I[k][0] + I[(k + 1) % 6][0]) / 2, YC,
          (I[k][1] + I[(k + 1) % 6][1]) / 2)
    om = ((o0[0] + o1[0]) / 2, YC, (o0[2] + o1[2]) / 2)
    hint = (im[0] - om[0], 0.0, im[2] - om[2])
    b.place_edge(f"loop_{k}", "trapezoid", 0, o0, o1, hint, LOOP_COLORS[k])

# =================================================================
# 5. 过山车两节 + 缓冲挡 + 起点闸门 + 旗杆塔
# =================================================================
b.crest_ew("car1_nose", 8, 1, 0, "red")       # 车头挡风尖
b.wall_ns("car1_s", 8, 1, 0, "red")
b.wall_ns("car1_n", 8, 2, 0, "red")
b.wall_ew("car1_tail", 9, 1, 0, "red")        # 一节车尾 = 二节车头
b.wall_ns("car2_s", 9, 1, 0, "orange")
b.wall_ns("car2_n", 9, 2, 0, "orange")
b.wall_ew("car2_tail", 10, 1, 0, "orange")
b.crest_ew("finish_flag", 9, 0, 0, "purple")  # 终点冲线旗
b.crest_ew("start_gate", 0, 1, 0, "gray")     # 起点闸门
b.wall_ns("flag_w_post", 4, 3, 0, "gray")     # 北侧旗杆塔
b.crest_ns("flag_w", 4, 3, 1, "pink")
b.wall_ns("flag_e_post", 5, 3, 0, "gray")
b.crest_ns("flag_e", 5, 3, 1, "pink")

# =================================================================
# 教程步骤 (16 步)
# =================================================================
b.step(
    "铺南侧游园带: 沿 x 轴铺 6 片绿色地砖 (长-长-方-长-长-方), "
    "排队栏落点处必须是单格方板。",
    ["apron_s0", "apron_s1", "apron_s2", "apron_s3", "apron_s4", "apron_s5"],
    tip="环圈南锚那根长方形的位置最关键 —— 它的长边即将吸住环圈。",
)
b.step(
    "铺轨道带: 8 片灰色地砖铺出过山车的行车线。",
    ["track_w", "track_p0", "track_p1", "track_p2", "track_loop",
     "track_c0", "track_c1", "track_end"],
    highlight=["apron_s0", "apron_s3"],
    tip="桥墩基座与车厢停靠区用单格方板, 立墙只吸等长整边。",
)
b.step(
    "铺北侧游园带: 6 片绿色地砖合拢, 三条带连成 10x3 大地台。",
    ["apron_n0", "apron_n1", "apron_n2", "apron_n3", "apron_n4", "apron_n5"],
    highlight=["track_w"],
    tip="旗杆落点 (x=4,5) 两片必须是单格方板。",
)
b.step(
    "砌站台箱体: 2 根蓝色长方形横放立起做前后墙, 2 片蓝色正方形"
    "封住东西两端, 围成箱形站台。",
    ["st_w", "st_e", "st_s", "st_n"],
    highlight=["apron_s0", "track_w"],
    tip="长方形底边吸地砖长边, 端墙竖边与长墙竖边咬合。",
)
b.step(
    "盖站台台面并立雨棚柱: 1 根黄色长方形盖住箱口, 2 片透明"
    "正方形立在台面两端做雨棚柱。",
    ["st_deck", "st_post_w", "st_post_e"],
    highlight=["st_s", "st_n"],
    tip="台面四边同时吸住四面站台墙 —— 箱体从此自锁。",
)
b.step(
    "盖雨棚与挂招牌: 1 根蓝色长方形架上双柱做雨棚顶, 1 片紫色扇形"
    "立在棚顶西沿当招牌。",
    ["st_roof", "st_sign"],
    highlight=["st_post_w", "st_post_e"],
    tip="扇形直边吸棚顶边, 弧边朝天 —— 最拉风的过山车招牌。",
)
b.step(
    "装出站坡道与排队栏: 30 度坡道从台面西沿滑到地面, 1 片紫色"
    "等边三角形立在南带拼缝上当排队栏。",
    ["st_exit", "queue"],
    highlight=["st_deck"],
    tip="坡道顶边整边吸台面沿口, 坡尾稳稳落地。",
)
b.step(
    "砌登顶桥墩: 4 片灰色正方形在轨道带上围成箱形桥墩。",
    ["pier_s", "pier_n", "pier_w", "pier_e"],
    highlight=["track_p1"],
    tip="四片墙的竖边两两咬合, 箱形墩比单片墙结实得多。",
)
b.step(
    "盖墩顶并架双坡道: 红色顶板盖住桥墩, 上行坡道向西落地、"
    "俯冲坡道向东贴着环圈将要立起的位置俯冲。",
    ["pier_top", "hill_up", "hill_dn"],
    highlight=["pier_s", "pier_n"],
    tip="两条坡道的顶边分别吸住墩顶的东西沿口。",
)
b.step(
    "环圈起步: 底片梯形下底 (长 2) 立在南锚与轨道带的公共拼缝上, "
    "左右两片贴着它的腰向上生长, 外角落地。",
    ["loop_0", "loop_1", "loop_5"],
    highlight=["apron_s3", "track_loop"],
    tip="底片同时吸住两侧长方形地砖的长边 —— 环圈的地基。",
)
b.step(
    "环圈过肩: 左右再各接一片, 腰腰相吸, 环圈长到 3.5 格高。",
    ["loop_2", "loop_4"],
    highlight=["loop_1", "loop_5"],
    tip="竖直平面内的梯形正压在下方腰缝上, 天生零力矩。",
)
b.step(
    "环圈合龙: 最后一片梯形倒扣在最高点, 两条腰同时卡进左右肩缝 "
    "—— 空心大环圈自锁成环!",
    ["loop_3"],
    highlight=["loop_2", "loop_4"],
    tip="合龙后轻按整圈: 6 片像一个整体一样纹丝不动。",
)
b.step(
    "拼第一节车厢: 挡风尖 + 两侧板 + 尾板, 红色涂装停在环圈东侧。",
    ["car1_nose", "car1_s", "car1_n", "car1_tail"],
    highlight=["track_c1"],
    tip="挡风尖立在停靠区前缝上, 侧板夹住轨道带。",
)
b.step(
    "拼第二节车厢: 橙色涂装接在一节车尾后面, 共用一片隔板。",
    ["car2_s", "car2_n", "car2_tail"],
    highlight=["car1_tail"],
    tip="第一节的尾板就是第二节的车头 —— 两节列车连挂完成。",
)
b.step(
    "立北侧旗杆塔: 2 座 (灰墙 + 粉旗) 正对环圈两肩。",
    ["flag_w_post", "flag_w", "flag_e_post", "flag_e"],
    highlight=["apron_n2", "apron_n3"],
    tip="旗子底边吸在旗杆顶边上, 迎风招展。",
)
b.step(
    "装起点闸门与终点冲线旗: 起点立闸门, 停靠区旁插冲线旗 —— "
    "过山车环圈段正式营业!",
    ["start_gate", "finish_flag"],
    highlight=["track_w", "apron_s5"],
    tip="从侧面看: 站台-小丘-大环圈-列车连成一条完整赛道。",
)

b.finalize(
    model_id="roller_coaster_loop_01",
    name="过山车大环圈",
    name_en="Roller Coaster Loop 01",
    description=(
        "游乐园主题: 全库第一个闭合环圈 —— 6 片梯形在竖直平面内腰腰"
        "互吸, 拼成外边长 2、内边长 1 的空心六边大环, 中间的洞就是"
        "过山车穿越的圈心; 环是拓扑环, 剪断任何一条铰链线都还有第二条"
        "路径, 越按越紧。环圈西侧箱形桥墩甩出上行/俯冲双坡道, 再往西是"
        "带雨棚与扇形招牌的车站和出站坡道, 东侧停着两节连挂的列车。"
    ),
    difficulty=3,
    tags=["游乐园", "过山车", "环圈", "闭合环", "挑战"],
    min_pieces=55,
    min_steps=16,
)
