#!/usr/bin/env python3
"""生成模型 data/models/plaza_canopy_01.json (广场遮阳售卖亭)。

内容批 P 模型 1/10: 主打片型 large_square 引流 D1 —— 两片大正方形
平拼 4x2 广场地台, 两片大正方形在 z=2 平拼 4x2 遮阳顶棚 (招牌);
下层四角方墙 + 两侧栏板墙围出亭身, 南面嵌一座带台面的售卖柜台,
上层四根角柱托两根整跨檐口横梁, 顶棚四角再立红黄三角旗收尾。

结构要点 (梁柱式, 与旧版横楣叠柱 + 盒式展框 + 直角斜撑方案不同):
  - 下层墙体: 四角前后墙与两侧栏板墙在角点竖直边互吸, 底边整边
    踩在大正方形地台沿边上 (短边含于长边即吸合), 落地自稳;
  - 檐口横梁 (2 长) 两端竖直边吸住角柱, 底边压两侧栏板墙顶沿,
    梁顶整边与大正方形顶棚 2 长的沿边等长贴合 —— 顶棚每片同时
    吸住同侧横梁、前后两根角柱与另一片顶棚, 任意剪断一条铰链线
    仍有多条独立支撑路径;
  - 柜台台面三条边同时吸柜台立面顶沿与两侧方墙顶沿;
  - 四角三角旗底边与角柱顶沿等长互吸 (最高点 2.87 触发 R8),
    连接图多环冗余, 单点失效损失均 < 3 片, 满足 strict 零警告。

用法: python3 tools/generate_plaza_canopy_01.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from magtile_gen import ModelBuilder  # noqa: E402

b = ModelBuilder()

PLAZA = "gray"          # 广场地台
FRAME = "blue"          # 亭身墙体 / 角柱 / 檐口横梁
COUNTER = "orange"      # 柜台立面与侧墙
COUNTER_TOP = "yellow"  # 柜台台面
CANOPY = "green"        # 遮阳顶棚
FLAG_A = "red"          # 三角旗 (红黄相间)
FLAG_B = "yellow"

# ---- 第 1 步: 广场地台 (两片大正方形平拼 4x2) ----------------------
b.add("lg_base_w", "large_square", (1.0, 1.0, 0.0), (0, 0, 0), PLAZA)
b.add("lg_base_e", "large_square", (3.0, 1.0, 0.0), (0, 0, 0), PLAZA)

# ---- 第 2 步: 下层亭身 (四角前后墙 + 两侧栏板墙, z 0..1) -----------
b.wall_ns("col_sw_s", 0, 0.0, 0, FRAME)   # 前墙西角: x 0..1 @y=0
b.wall_ns("col_se_s", 3, 0.0, 0, FRAME)   # 前墙东角: x 3..4 @y=0
b.wall_ns("col_nw_n", 0, 2.0, 0, FRAME)   # 后墙西角: x 0..1 @y=2
b.wall_ns("col_ne_n", 3, 2.0, 0, FRAME)   # 后墙东角: x 3..4 @y=2
b.wall_ew("side_w_s", 0.0, 0, 0, FRAME)   # 西侧栏板: y 0..1 @x=0
b.wall_ew("side_w_n", 0.0, 1, 0, FRAME)   # 西侧栏板: y 1..2 @x=0
b.wall_ew("side_e_s", 4.0, 0, 0, FRAME)   # 东侧栏板: y 0..1 @x=4
b.wall_ew("side_e_n", 4.0, 1, 0, FRAME)   # 东侧栏板: y 1..2 @x=4

# ---- 第 3 步: 南面售卖柜台 (立面 + 两侧墙 + 台面, 三线支撑) --------
b.lintel_ns("ctr_front", 1, 0.0, 0, COUNTER)    # 柜台立面: x 1..3, z 0..1
b.wall_ew("ctr_side_w", 1.0, 0, 0, COUNTER)     # 柜台西侧墙 @x=1
b.wall_ew("ctr_side_e", 3.0, 0, 0, COUNTER)     # 柜台东侧墙 @x=3
b.flat_rect("ctr_top", 1, 0, 1.0, COUNTER_TOP)  # 台面: [1,3]x[0,1] @z=1

# ---- 第 4 步: 上层四根角柱 (z 1..2) --------------------------------
b.wall_ns("post_sw", 0, 0.0, 1, FRAME)
b.wall_ns("post_se", 3, 0.0, 1, FRAME)
b.wall_ns("post_nw", 0, 2.0, 1, FRAME)
b.wall_ns("post_ne", 3, 2.0, 1, FRAME)

# ---- 第 5 步: 两根檐口横梁 (整跨 2 长, 兜住同侧一对角柱) -----------
b.lintel_ew("beam_w", 0.0, 0, 1, FRAME)   # x=0, y 0..2, z 1..2
b.lintel_ew("beam_e", 4.0, 0, 1, FRAME)   # x=4, y 0..2, z 1..2

# ---- 第 6 步: 遮阳顶棚 (两片大正方形平拼 4x2 @z=2) -----------------
b.add("canopy_w", "large_square", (1.0, 1.0, 2.0), (0, 0, 0), CANOPY)
b.add("canopy_e", "large_square", (3.0, 1.0, 2.0), (0, 0, 0), CANOPY)

# ---- 第 7 步: 顶棚四角三角旗 (红黄相间) ----------------------------
b.crest_ns("flag_sw", 0, 0.0, 2.0, FLAG_A)
b.crest_ns("flag_se", 3, 0.0, 2.0, FLAG_B)
b.crest_ns("flag_nw", 0, 2.0, 2.0, FLAG_B)
b.crest_ns("flag_ne", 3, 2.0, 2.0, FLAG_A)

# ---- 教程步骤 ------------------------------------------------------
b.step(
    "铺广场地台: 两片灰色大正方形整边互吸, 平拼出 4x2 的小广场。",
    ["lg_base_w", "lg_base_e"],
    tip="大正方形边长 2.0, 一片顶四片小方板 —— 拼缝对齐才好立墙。",
)
b.step(
    "立下层亭身: 前后各两片蓝色方墙踩住地台四角, 两侧各两片方墙"
    "连成栏板 —— 角点竖直边互相吸住, 围出亭身。",
    ["col_sw_s", "side_w_s", "side_w_n", "col_nw_n",
     "col_se_s", "side_e_s", "side_e_n", "col_ne_n"],
    highlight=["lg_base_w", "lg_base_e"],
    tip="每片墙底边都要整边踩上地台沿边, 转角处竖边咔哒一声吸牢。",
)
b.step(
    "嵌售卖柜台: 橙色横楣立在前墙两角之间当柜台立面, 两片橙色方墙"
    "关住左右, 黄色横楣平放上去当台面 —— 台面三条边一次吸住。",
    ["ctr_front", "ctr_side_w", "ctr_side_e", "ctr_top"],
    highlight=["col_sw_s", "col_se_s"],
    tip="先立好三面再放台面, 前沿与左右顶沿同时吸合才算到位。",
)
b.step(
    "立上层角柱: 四片蓝色方墙对准四角, 底边吸住下层墙顶沿,"
    "把亭子拔高到两层。",
    ["post_sw", "post_se", "post_nw", "post_ne"],
    highlight=["col_sw_s", "col_ne_n"],
    tip="上下两层对齐叠放, 柱子才又高又直。",
)
b.step(
    "架檐口横梁: 两根蓝色横楣横跨两侧, 两端竖直边吸住角柱,"
    "底边压住栏板墙顶沿 —— 梁柱框架成型。",
    ["beam_w", "beam_e"],
    highlight=["post_sw", "post_nw"],
    tip="横梁两头同时吸住前后角柱, 像门框一样兜住整个侧面。",
)
b.step(
    "盖遮阳顶棚: 两片绿色大正方形依次平放到 z=2, 沿边吸住横梁顶沿"
    "与角柱顶沿, 再整边互吸合拢成 4x2 顶棚。",
    ["canopy_w", "canopy_e"],
    highlight=["beam_w", "beam_e"],
    tip="先盖西半再盖东半, 每片都要先吸住同侧横梁再对拼缝。",
)
b.step(
    "插角旗收尾: 四片红黄相间的三角旗立上顶棚四角 —— 广场遮阳"
    "售卖亭开张啦!",
    ["flag_sw", "flag_se", "flag_nw", "flag_ne"],
    highlight=["canopy_w", "canopy_e"],
    tip="三角旗底边与角柱顶沿等长, 对准顶棚角上一按就吸住。",
)

b.finalize(
    model_id="plaza_canopy_01",
    name="广场遮阳售卖亭",
    name_en="Plaza Canopy 01",
    description=(
        "主打片型 large_square 引流 D1: 两片大正方形平拼 4x2 广场"
        "地台, 下层四角方墙加两侧栏板围出亭身, 南面嵌一座带黄色"
        "台面的售卖柜台; 上层四根角柱托两根整跨檐口横梁, 顶上两片"
        "大正方形平拼 4x2 绿色遮阳顶棚, 四角再插红黄三角旗 ——"
        "一座能摆摊的两层小凉亭。"
    ),
    difficulty=1,
    tags=["实用功能", "遮阳棚", "售卖亭", "柜台", "大正方形", "入门"],
    min_pieces=26,
    min_steps=7,
    series="practical_utility",
)
