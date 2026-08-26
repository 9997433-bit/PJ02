#!/usr/bin/env python3
"""生成模型 data/models/napkin_holder_01.json (拱门餐巾架)。

D1 补员批 2 模型 4/4 (难度配额解冻线 D1 >= 20, 路径 B1): 入门档
实用功能选题 —— 餐桌上的拱门餐巾架。结构签名是"双墙门式框架":
门框方一排与窗格方一排面对面立在相邻拼缝上, 顶板把两道墙锁成
门式框架, 一格宽的槽腔正好插一沓餐巾; 两角粉色'餐巾角'高高
翘起, 两侧牙签盒与调料盒借用框架墙各省一面墙 —— 与手机摇篮
(单墙靠背 + 坡道)、杯垫台 (闭合箱体)、笔筒 (开顶双筒) 的结构
逻辑均不相同。

结构总览 (世界单位: 1.0 = 正方形磁力片边长):
  - 餐垫 6 片方板棋盘 (x [0,2], y [0,3])                 6 片
  - 南墙 2 片门框方 (y=1 拼缝, 透出餐巾图案)             2 片
  - 北墙 2 片窗格方 (y=2 拼缝, 与南墙面对面)             2 片
  - 顶板 2 片方板 (z=1, 南北边分别整边锁两道墙顶)        2 片
  - 牙签盒 (左前角, 借南墙作第四面)                      3 片
  - 调料盒 (右后角, 借北墙作第四面)                      3 片
  - 侧沿小旗 x2 (等边三角骑顶板短边)                     2 片
  - 餐巾角 x2 (等腰三角立南墙顶沿, 像餐巾翘起的两角)     2 片
  合计 22 片, 7 个教程步骤, 6 种磁力片形状 (全部 CORE-9 之内)。

物理规则要点 (validate 常规 + strict 双档零警告):
  - 门式框架: 两道墙 + 顶板围成闭合传力环, 剪断任何一条
    铰链线都还有另一条路兜底, 无单点失效;
  - 门框方/窗格方外框与正方形完全一致, 物理按实心方板校验
    (docs/TILE_SET.md), 镂空只是看得见餐巾的造型语义;
  - 小旗/餐巾角重心正压铰链线, 力矩为零; 全程受压零悬挑;
  - 两只小盒各借框架墙作第四面 —— 内墙用竖棱角缝互锁,
    与框架墙同平面不同区段, 共面 SAT 重叠深度为零 (R3)。

用法: python3 tools/generate_napkin_holder_01.py  (在 magtile-studio 目录下运行)
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from magtile_gen import ModelBuilder  # noqa: E402

b = ModelBuilder()

MAT_A = "green"     # 餐垫方板 (深)
MAT_B = "yellow"    # 餐垫方板 (浅)
ARCH = "red"        # 门框方 / 窗格方框架墙
ROOF = "gray"       # 顶板
BOX = "cyan"        # 牙签盒 / 调料盒
FLAG = "green"      # 侧沿小旗
CORNER = "pink"     # 餐巾角


def wall_ns_t(tile_id, tile_type, x0, y, z0, color):
    """南北朝向立墙 (自定义片型: 门框方/窗格方外框同正方形)。"""
    b.add(tile_id, tile_type, (x0 + 0.5, y, z0 + 0.5), (90, 0, 0), color)


# =================================================================
# 1. 餐垫: 六片方板棋盘 (x [0,2], y [0,3])
# =================================================================
for gx in range(2):
    for gy in range(3):
        color = MAT_A if (gx + gy) % 2 == 0 else MAT_B
        b.flat(f"mat_{gx}_{gy}", gx, gy, 0.0, color)

# =================================================================
# 2. 门式框架: 南墙门框方 (y=1) + 北墙窗格方 (y=2) + 顶板 (z=1)
# =================================================================
wall_ns_t("arch_s_w", "door_frame", 0, 1.0, 0, ARCH)
wall_ns_t("arch_s_e", "door_frame", 1, 1.0, 0, ARCH)
wall_ns_t("arch_n_w", "window_square", 0, 2.0, 0, ARCH)
wall_ns_t("arch_n_e", "window_square", 1, 2.0, 0, ARCH)
b.flat("roof_w", 0, 1, 1.0, ROOF)
b.flat("roof_e", 1, 1, 1.0, ROOF)

# =================================================================
# 3. 牙签盒 (左前角格 [0,1]x[0,1], 南墙 arch_s_w 作第四面)
# =================================================================
b.wall_ns("pick_s", 0, 0.0, 0, BOX)
b.wall_ew("pick_w", 0.0, 0, 0, BOX)
b.wall_ew("pick_e", 1.0, 0, 0, BOX)

# =================================================================
# 4. 调料盒 (右后角格 [1,2]x[2,3], 北墙 arch_n_e 作第四面)
# =================================================================
b.wall_ns("spice_n", 1, 3.0, 0, BOX)
b.wall_ew("spice_w", 1.0, 2, 0, BOX)
b.wall_ew("spice_e", 2.0, 2, 0, BOX)

# =================================================================
# 5. 侧沿小旗 (骑顶板短边) + 餐巾角 (立南墙顶沿)
# =================================================================
b.crest_ew("flag_w", 0.0, 1, 1.0, FLAG)
b.crest_ew("flag_e", 2.0, 1, 1.0, FLAG)
b.spire_ns("corner_w", 0, 1.0, 1.0, CORNER)
b.spire_ns("corner_e", 1, 1.0, 1.0, CORNER)

# =================================================================
# 教程步骤 (7 步)
# =================================================================
b.step(
    "铺餐垫: 六片绿黄棋盘方板逐片整边互吸, 铺成 2x3 的野餐格。",
    ["mat_0_0", "mat_0_1", "mat_0_2", "mat_1_0", "mat_1_1", "mat_1_2"],
    tip="餐垫拼缝就是墙脚线 —— 铺齐了后面才好立墙。",
)
b.step(
    "立南墙: 两片红色门框方踩住 y=1 拼缝并肩而立, 门洞里将透出餐巾。",
    ["arch_s_w", "arch_s_e"],
    highlight=["mat_0_0", "mat_1_0"],
    tip="门框方外框和方板一模一样, 吸法完全相同。",
)
b.step(
    "立北墙: 两片红色窗格方踩住 y=2 拼缝, 与南墙面对面留出一格餐巾槽。",
    ["arch_n_w", "arch_n_e"],
    highlight=["arch_s_w"],
)
b.step(
    "盖顶板锁框架: 两片灰色方板南北边分别整边吸住两道墙顶, 门式框架合龙!",
    ["roof_w", "roof_e"],
    highlight=["arch_s_w", "arch_n_w"],
    tip="顶板一盖, 两道墙互相拉住 —— 推哪边都不倒。",
)
b.step(
    "围牙签盒: 左前角三片青墙合围, 南墙自己当第四面, 省一片是一片。",
    ["pick_s", "pick_w", "pick_e"],
    highlight=["mat_0_0"],
)
b.step(
    "围调料盒: 右后角同样三片合围, 北墙作第四面, 前后正好对角呼应。",
    ["spice_n", "spice_w", "spice_e"],
    highlight=["mat_1_2"],
)
b.step(
    "升小旗、翘餐巾角: 两面绿旗骑上顶板短边, 两片粉色等腰三角立上南墙顶沿 —— 餐巾架开饭!",
    ["flag_w", "flag_e", "corner_w", "corner_e"],
    highlight=["roof_w", "roof_e"],
    tip="餐巾角重心正压沿口, 翘得高也站得稳。",
)

model = b.finalize(
    model_id="napkin_holder_01",
    name="拱门餐巾架",
    name_en="Napkin Holder 01",
    description=(
        "入门档实用功能: 餐桌上的拱门餐巾架, 结构签名是'双墙门式"
        "框架' —— 两片门框方与两片窗格方面对面立在相邻拼缝上, "
        "灰色顶板南北边整边锁住两道墙顶围成闭合传力环, 一格宽的"
        "槽腔正好插一沓餐巾, 门洞窗格里都看得见; 左前牙签盒与右后"
        "调料盒各借一道框架墙当第四面, 对角呼应; 顶板短边两面绿旗, "
        "南墙顶沿两片粉色'餐巾角'高高翘起。22 片受压闭环零悬挑, "
        "搭完就能开饭。"
    ),
    difficulty=1,
    tags=["实用功能", "餐巾架", "餐桌", "厨房", "入门"],
    min_pieces=22,
    min_steps=7,
)

# ---- series 归类落盘 (CONTENT_STRATEGY.md 4.3 节: 入库必填) --------
out = Path(__file__).resolve().parent.parent / "data" / "models" / "napkin_holder_01.json"
model["content_meta"] = {
    "series": "practical_utility",
    "structural_signature": model["content_meta"]["structural_signature"],
}
out.write_text(json.dumps(model, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print("已写入 series=practical_utility")
