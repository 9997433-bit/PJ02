#!/usr/bin/env python3
"""生成模型 data/models/rhombus_patchwork_01.json (菱形拼布屏风)。

几何艺术 T18 密铺变奏的菱形篇 (批 P / P4): 三角密铺屏风 (tessellation_
screen_01) 用正倒三角互咬, 本作换成 60 度菱形的**人字纹密铺** —— 每排
菱形整排同向倾斜, 上下排倾向一排一换, 排与排之间上底/下底整边互吸,
排内斜边两两互咬, 像织毯的经纬一样密不透风。按 J4 规则密铺必须立起来:
28 片菱形竖砌成 U 形三扇屏, 站在步道上当隔断屏风。

结构总览 (世界单位: 1.0 = 正方形磁力片边长; h = 菱形高 0.866025):
  - U 形步道地台: 南段 3 片 + 两角 2 片 + 西翼/东翼各 2 片      9 片
  - 中屏 (y=1 立面, x [1,4]): 3 列 x 4 排人字纹菱形,
    红/橙相间的哈里昆菱格 —— 拼布地毯的招牌花样               12 片
  - 西翼屏 (x=1 立面, y [1,3]): 2 列 x 4 排, 蓝/青拼布          8 片
  - 东翼屏 (x=4 立面, y [1,3]): 2 列 x 4 排, 绿/黄拼布,
    与西翼严格镜像 (T11), 两翼垂直咬住中屏形成 U 形自稳         8 片
  - 门旗 x2: 紫色菱形立在两角步道南沿, 朝步道口相向而倾         2 片
  合计 39 片, 10 个教程步骤; 最高点 4h = 3.4641 < R8 红线 4.0。

招牌技法: 菱形人字纹密铺竖砌成屏 —— 每排整排换一次倾向, 三扇屏
三套双色拼布 (红橙 / 蓝青 / 绿黄), 屏缘天然锯齿如织毯毛边;
两翼与中屏成直角站位, 密铺花毯自己站成了隔断屏风。

物理规则要点 (validate 常规 + strict 双档零警告):
  - 每片菱形下底整边吸住下一排 (或步道拼缝), 排内斜边整边互咬,
    连接图环路密布, R8 单点失效与无冗余警告天然消失;
  - 三扇屏各自整条底边落在步道拼缝上, 屏面全部竖直共面 ——
    任何水平铰链线剪断后, 上方子结构重心仍在铰链正上方,
    R5 悬挂 / R6 悬臂力矩均为零 (纯压传力);
  - U 形站位: 两翼立面与中屏立面正交, 接地凸包为 [0,5]x[0,3]
    矩形, 整体重心 (2.57, 1.49) 深居其中, R4 裕量充足;
  - 门旗单片吸角砖南沿, 剪断只失联 1 片 (< 3), 不触发单点失效。

用法: python3 tools/generate_rhombus_patchwork_01.py  (在 magtile-studio 目录下运行)
"""

import json
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from magtile_gen import ModelBuilder  # noqa: E402

b = ModelBuilder()

H = math.sqrt(3) / 2        # 菱形高 0.866025 (60 度菱形, 边长 1)
UP = (0.0, 0.0, 1.0)        # 竖直立面放置的内侧提示 (指向形状内部 = 正上)
ROWS = 4                    # 每扇屏 4 排, 最高点 4h = 3.4641 < 4.0

FLOOR_A, FLOOR_B = "gray", "clear"          # 步道灰/清相间
PANEL_COLORS = {                            # 三扇屏各一套双色拼布
    "c": ("red", "orange"),                 # 中屏: 红橙
    "w": ("blue", "cyan"),                  # 西翼: 蓝青
    "e": ("green", "yellow"),               # 东翼: 绿黄
}
BANNER = "purple"                           # 门旗


def chevron_panel(prefix, axis, plane, start, cols):
    """竖直平面上的人字纹菱形密铺屏: 每排整排同向倾斜, 逐排换向。

    axis="x": 屏面为 y=plane 立面, 底边沿 x 从 start 起铺 cols 列;
    axis="y": 屏面为 x=plane 立面, 底边沿 y 铺。偶数排向 +轴 倾,
    奇数排向 -轴 倾 (place_edge 的边方向即倾向); 相邻排上底/下底
    1:1 整边互吸, 排内相邻菱形斜边整边互咬。返回按排分组的 id。
    """
    color_a, color_b = PANEL_COLORS[prefix]
    rows = []
    for r in range(ROWS):
        z = r * H
        row_ids = []
        for k in range(cols):
            if r % 2 == 0:      # 向 +轴 倾: 下底 [start+k, start+k+1]
                a0, a1 = start + k, start + k + 1
            else:               # 向 -轴 倾: 下底 [start+k+0.5, start+k+1.5]
                a0, a1 = start + k + 1.5, start + k + 0.5
            if axis == "x":
                w_from, w_to = (a0, plane, z), (a1, plane, z)
            else:
                w_from, w_to = (plane, a0, z), (plane, a1, z)
            tid = f"{prefix}_{r}_{k}"
            color = color_a if (r + k) % 2 == 0 else color_b
            b.place_edge(tid, "rhombus", 0, w_from, w_to, UP, color)
            row_ids.append(tid)
        rows.append(row_ids)
    return rows


# =================================================================
# 1. U 形步道地台: 南段 [1,4]x[0,1] + 两角 + 西翼/东翼各两片
# =================================================================
b.flat("f_sw", 0, 0, 0.0, FLOOR_B)          # 西南角砖 (门旗座)
for i in range(3):
    b.flat(f"f_c{i}", 1 + i, 0, 0.0, FLOOR_A if i % 2 == 0 else FLOOR_B)
b.flat("f_se", 4, 0, 0.0, FLOOR_B)          # 东南角砖 (门旗座)
b.flat("f_w0", 0, 1, 0.0, FLOOR_A)          # 西翼步道
b.flat("f_w1", 0, 2, 0.0, FLOOR_B)
b.flat("f_e0", 4, 1, 0.0, FLOOR_A)          # 东翼步道
b.flat("f_e1", 4, 2, 0.0, FLOOR_B)

# =================================================================
# 2. 中屏 (y=1 立面, x [1,4]): 3 列 x 4 排红橙哈里昆菱格
# =================================================================
C_ROWS = chevron_panel("c", "x", 1.0, 1.0, 3)

# =================================================================
# 3. 西翼屏 (x=1 立面) 与东翼屏 (x=4 立面): 2 列 x 4 排, 严格镜像
# =================================================================
W_ROWS = chevron_panel("w", "y", 1.0, 1.0, 2)
E_ROWS = chevron_panel("e", "y", 4.0, 1.0, 2)

# =================================================================
# 4. 门旗 x2: 紫菱形立在两角砖南沿 (y=0 立面), 相向而倾
# =================================================================
b.place_edge("bn_w", "rhombus", 0, (0.0, 0.0, 0.0), (1.0, 0.0, 0.0), UP, BANNER)
b.place_edge("bn_e", "rhombus", 0, (5.0, 0.0, 0.0), (4.0, 0.0, 0.0), UP, BANNER)

# =================================================================
# 教程步骤 (10 步)
# =================================================================
b.step(
    "铺步道南段: 五片方板沿南边一字排开 —— 两端清色角砖是门旗座, 中间三片灰清相间。",
    ["f_sw", "f_c0", "f_c1", "f_c2", "f_se"],
    tip="这条步道是屏风的\"毯边\", 拼缝对齐, 后面整扇屏都要踩在缝上。",
)
b.step(
    "铺两翼步道: 西翼与东翼各两片方板向北延伸, 步道围成一个 U 字。",
    ["f_w0", "f_w1", "f_e0", "f_e1"],
    highlight=["f_sw", "f_se"],
    tip="左右各铺两片, 和角砖整边吸牢 —— U 形的怀抱就是屏风的地基。",
)
b.step(
    "立中屏底排: 三片菱形踩上步道北缝, 整排向东倾, 红橙红相间。",
    ["c_0_0", "c_0_1", "c_0_2"],
    highlight=["f_c0", "f_c1", "f_c2"],
    tip="菱形下底吸步道拼缝, 相邻斜边互咬 —— 整排同向倾是人字纹的第一笔。",
)
b.step(
    "砌中屏第二排: 三片菱形整排换向西倾, 下底一对一骑上底排的上底。",
    ["c_1_0", "c_1_1", "c_1_2"],
    highlight=["c_0_0", "c_0_1", "c_0_2"],
    tip="倾向一排一换, 两排咬合出人字纹 —— 织毯的经纬就是这样交错的。",
)
b.step(
    "砌中屏三四排封顶: 第三排回东倾, 第四排再西倾, 红橙菱格一格不错。",
    ["c_2_0", "c_2_1", "c_2_2", "c_3_0", "c_3_1", "c_3_2"],
    highlight=["c_1_0", "c_1_1", "c_1_2"],
    tip="顶排上底连成一条直线, 屏缘的锯齿像织毯毛边 —— 中屏完工!",
)
b.step(
    "立西翼下半: 两片菱形踩西翼步道缝向北倾, 第二排换向南倾骑上去, 蓝青拼布。",
    ["w_0_0", "w_0_1", "w_1_0", "w_1_1"],
    highlight=["f_w0", "f_w1"],
    tip="西翼立面和中屏成直角 —— 翼墙一立, 整面屏风就不怕前后推了。",
)
b.step(
    "立东翼下半: 与西翼镜像, 两排绿黄菱形踩东翼步道缝咬合。",
    ["e_0_0", "e_0_1", "e_1_0", "e_1_1"],
    highlight=["f_e0", "f_e1"],
    tip="左右两翼对称推进, U 形怀抱两边同时合拢, 站得最稳。",
)
b.step(
    "砌西翼上半: 第三第四排继续人字纹, 蓝青拼布到顶。",
    ["w_2_0", "w_2_1", "w_3_0", "w_3_1"],
    highlight=["w_1_0", "w_1_1"],
    tip="每一片下底都要整边骑在下一排上底上, 咔哒吸牢再放手。",
)
b.step(
    "砌东翼上半: 镜像收尾, 三扇屏同高, U 形屏风合体。",
    ["e_2_0", "e_2_1", "e_3_0", "e_3_1"],
    highlight=["e_1_0", "e_1_1"],
    tip="从上往下看, 三扇屏是一个端正的 U —— 密铺花毯自己站起来了。",
)
b.step(
    "插门旗: 两片紫菱形立在两角砖南沿, 朝步道口相向而倾, 像掀起的毯角。",
    ["bn_w", "bn_e"],
    highlight=["f_sw", "f_se"],
    tip="门旗下底吸住角砖边缘 —— 迎着台灯摆好, 六色菱格影子会铺满桌面!",
)

model = b.finalize(
    model_id="rhombus_patchwork_01",
    name="菱形拼布屏风",
    name_en="Rhombus Patchwork Screen 01",
    description=(
        "几何艺术菱形篇: 28 片 60 度菱形以人字纹密铺竖砌成 U 形三扇屏 —— "
        "每排菱形整排同向倾斜, 上下排倾向一排一换, 排间上底下底整边互吸, "
        "排内斜边两两互咬; 中屏红橙、西翼蓝青、东翼绿黄, 三套双色拼布像三块"
        "花毯拼成的隔断, 屏缘锯齿如织毯毛边, 两角紫色门旗相向而倾。两翼与"
        "中屏成直角站位, 密铺花毯自己站成了屏风。"
    ),
    difficulty=2,
    tags=["几何艺术", "密铺", "拼布", "屏风", "对称"],
    min_pieces=39,
    min_steps=10,
    series="geometric_art",
)

meta = model["content_meta"]
meta["build_paradigm"] = "bottom_up"
meta["technique_tags"] = {
    "primary": "T18_tessellation_art",
    "secondary": ["T11_mirror_symmetry"],
}
meta["signature_statement"] = (
    "菱形人字纹密铺一排一换向, 六色拼布竖砌成 U 形三扇屏。"
)
meta["structural_signature"]["silhouette_class"] = "folding_screen"
meta["structural_signature"]["height_layers"] = ROWS

out = Path(__file__).resolve().parent.parent / "data/models/rhombus_patchwork_01.json"
out.write_text(json.dumps(model, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(f"已回写含技法标注的 {out}")
