#!/usr/bin/env python3
"""生成模型 data/models/snack_tray_01.json (双格点心托盘, D1 入门)。

D1 配额解冻批第 1 号 (实用功能): 全库 D1 长期为零, 本批按
CONTENT_GAP_AUDIT.md 7.3 节的解冻线 (D1 >= 20) 补入门档。入门不等于
敷衍 (反幼稚规则 J5): 这是一只端得上桌的双格点心托盘 —— 4x3 长方板
拼出托底, 中隔墙分出咸甜两格, 两端窗格方镂空即提手孔, 孔顶各立一面
小旗当"今日招牌"。

结构总览 (世界单位 1.0 = 正方形磁力片边长, 使用者坐在南侧):
  - 托底 (x [0,4], y [0,3]): 橙黄相间长方板横铺           6 片
  - 长边围沿 (y=0 / y=3, z 0..1): 青色横楣各 2            4 片
  - 端墙 (x=0 / x=4): 绿方 + 透明窗格提手 + 绿方 各 3     6 片
  - 中隔墙 (x=2, z 0..1): 蓝色立方 3 片分出两格           3 片
  - 招牌小旗: 红色等边三角立在两端提手窗顶沿              2 片
  合计 21 片, 6 个教程步骤, 4 种片形 (全部 CORE-9 之内)。

招牌技法 (T17 负空间): 两端窗格方一物两用 —— 镂空既是提手孔又是
透气窗, 负空间直接变成功能构件, 而不是贴上去的装饰。

物理规则要点 (validate 常规 + strict 双档零警告):
  - 全部立墙墙脚踩住托底拼缝, 整边吸合; 横楣底边 (长 2) 与
    长方板长边等长贴合 (长短边搭配规则);
  - 四角与中隔墙两端竖边互咬, 围沿-端墙-隔墙锁成日字形闭环;
  - 小旗底边 (长 1) 完整落在窗格提手顶沿 (长 1) 上, 纯受压零力矩;
  - 最高点 1.87 (旗尖), 低于高层结构阈值, 无 R8 拓扑告警。

用法: python3 tools/generate_snack_tray_01.py  (在 magtile-studio 目录下运行)
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from magtile_gen import ModelBuilder  # noqa: E402

b = ModelBuilder()

BOARD_A = "orange"   # 托底棋盘格
BOARD_B = "yellow"
RIM = "cyan"         # 长边围沿
END = "green"        # 端墙
HANDLE = "clear"     # 窗格提手
DIVIDER = "blue"     # 中隔墙
FLAG = "red"         # 招牌小旗


def wall_ew_t(tid, tile_type, x, y0, z0, color):
    b.add(tid, tile_type, (x, y0 + 0.5, z0 + 0.5), (90, 0, 90), color)


# =================================================================
# 1. 托底 (x [0,4], y [0,3]): 6 片长方板横铺, 橙黄相间
# =================================================================
for j in range(3):
    for i in (0, 2):
        b.flat_rect(f"board_{i}_{j}", i, j, 0.0, BOARD_A if (i // 2 + j) % 2 == 0 else BOARD_B)

# =================================================================
# 2. 长边围沿 (y=0 / y=3): 青色横楣各 2, 底边整边吸托底长边
# =================================================================
for i in (0, 2):
    b.lintel_ns(f"rim_s_{i}", i, 0.0, 0, RIM)
    b.lintel_ns(f"rim_n_{i}", i, 3.0, 0, RIM)

# =================================================================
# 3. 端墙 (x=0 / x=4): 绿方夹透明窗格提手, 窗孔就是提手孔
# =================================================================
for x, side in ((0.0, "w"), (4.0, "e")):
    b.wall_ew(f"end_{side}_a", x, 0, 0, END)
    wall_ew_t(f"handle_{side}", "window_square", x, 1, 0, HANDLE)
    b.wall_ew(f"end_{side}_b", x, 2, 0, END)

# =================================================================
# 4. 中隔墙 (x=2): 蓝色立方 3 片, 分出咸甜两格
# =================================================================
for j in range(3):
    b.wall_ew(f"divider_{j}", 2.0, j, 0, DIVIDER)

# =================================================================
# 5. 招牌小旗: 红色等边三角立在两端提手窗顶沿
# =================================================================
b.crest_ew("flag_w", 0.0, 1, 1.0, FLAG)
b.crest_ew("flag_e", 4.0, 1, 1.0, FLAG)

# =================================================================
# 教程步骤 (6 步)
# =================================================================
b.step(
    "铺托底第一排 (靠自己这排): 两片长方板头对头吸成一条长边。",
    ["board_0_0", "board_2_0"],
    tip="长方板短边对短边吸住, 托盘的地基就有了。",
)
b.step(
    "铺完托底: 再来四片长方板, 颜色橙黄错开, 拼成 4x3 大托底。",
    ["board_0_1", "board_2_1", "board_0_2", "board_2_2"],
    highlight=["board_0_0"],
    tip="每片长边都要与上一排整边贴合 —— 托底平整, 点心才放得稳。",
)
b.step(
    "立两条长边围沿: 四片青色横楣踩住托底长边, 底边一次吸满两格。",
    ["rim_s_0", "rim_s_2", "rim_n_0", "rim_n_2"],
    highlight=["board_0_0", "board_0_2"],
    tip="横楣是长片, 立的时候扶住两端再松手。",
)
b.step(
    "装两端提手墙: 绿方夹住透明窗格, 窗孔就是提手孔, 竖边与围沿咬角。",
    ["end_w_a", "handle_w", "end_w_b", "end_e_a", "handle_e", "end_e_b"],
    highlight=["rim_s_0", "rim_n_0"],
    tip="窗格放中间高度正好 —— 大人的手指能穿过窗孔把托盘端起来。",
)
b.step(
    "立中隔墙: 三片蓝色方板沿正中拼缝排开, 托盘分成咸甜两格。",
    ["divider_0", "divider_1", "divider_2"],
    highlight=["rim_s_0", "rim_s_2"],
    tip="隔墙两端与围沿竖边互咬, 像'日'字一样锁成整体。",
)
b.step(
    "插招牌小旗: 两面红色三角旗立上提手窗顶 —— 点心托盘开张!",
    ["flag_w", "flag_e"],
    highlight=["handle_w", "handle_e"],
    tip="左格放咸的、右格放甜的, 小旗写上今日招牌。",
)

model = b.finalize(
    model_id="snack_tray_01",
    name="双格点心托盘",
    name_en="Snack Tray 01",
    description=(
        "D1 入门实用件: 端得上桌的双格点心托盘 —— 4x3 橙黄长方板托底, "
        "青色横楣围出长边, 蓝色中隔墙分出咸甜两格; 两端透明窗格方一物两用, "
        "镂空既是提手孔又是透气窗, 窗顶还立着两面红色招牌小旗。六步搭完, "
        "第一件事就是端着它去装真点心。"
    ),
    difficulty=1,
    tags=["实用功能", "托盘", "收纳", "亲子入门"],
    min_pieces=21,
    min_steps=6,
)

# ---- content_meta 补全 (CONTENT_STRATEGY.md 5.1 节 schema) ---------
meta = model["content_meta"]
model["content_meta"] = {
    "series": "practical_utility",
    "build_paradigm": "bottom_up",
    "technique_tags": {
        "primary": "T17_negative_space",
        "secondary": ["T01_box_frame"],
    },
    "signature_statement": "两端窗格方一物两用: 镂空既是提手孔又是透气窗, 负空间直接当功能件。",
    "structural_signature": meta["structural_signature"],
    "physical_risk_notes": [
        {"step": 3, "risk": "长边横楣刚立起、未与端墙咬角前, 侧碰易向内倒",
         "mitigation": "该步 tip 提示扶住两端再松手; 下一步立即用端墙锁角"},
    ],
}

out = Path(__file__).resolve().parent.parent / "data" / "models" / "snack_tray_01.json"
out.write_text(json.dumps(model, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(f"已补全 content_meta 并重写 {out}")
