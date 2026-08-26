#!/usr/bin/env python3
"""生成模型 data/models/phone_cradle_01.json (追剧手机摇篮)。

D1 补员批 2 模型 1/4 (难度配额解冻线 D1 >= 20, 路径 B1): 入门档
实用功能选题 —— 一座真能用的手机躺靠架。与书桌整理站 (D2, 五个
功能位) 刻意区分: 本作只做一件事并把它做透 —— 30 度躺靠坡道 +
门式靠背 + 耳机小盒, 20 片一步不多; 入门档降低的是操作难度,
不是成品感 (CONTENT_STRATEGY.md 2.4 节)。

结构总览 (世界单位: 1.0 = 正方形磁力片边长):
  - 桌垫底板 3 行 x 2 长板 (x [0,4], y [0,3])            6 片
  - 靠背墙 4 片方板 (y=2 拼缝上, z 0..1)                 4 片
  - 靠背两端直角三角斜撑 (南向, 咬棱压缝)                2 片
  - 30 度躺靠坡道 (顶边吸靠背顶沿, 坡尾落底板)           1 片
  - 靠背顶沿三面小旗 (等边三角, 骑整边)                  3 片
  - 耳机小盒 (右前角四面围墙, 开顶)                      4 片
  合计 20 片, 6 个教程步骤, 4 种磁力片形状 (全部 CORE-9 之内)。

物理规则要点 (validate 常规 + strict 双档零警告):
  - 坡道顶边 (短边) 整边吸靠背顶沿, 坡尾恰好落地 (z=0) ——
    自身即接地片, 剪断顶边铰链也不构成悬挑子结构;
  - 斜撑竖直角边整边咬靠背端墙竖棱, 水平直角边压底板边缝;
  - 小旗重心正压铰链线, 力矩为零; 最高点 1.87 < 2.5,
    不触发 R8 高层结构判定;
  - 耳机小盒三面墙骑板边/拼缝, 内墙 (x=3) 靠两条竖棱角缝锁定。

用法: python3 tools/generate_phone_cradle_01.py  (在 magtile-studio 目录下运行)
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from magtile_gen import ModelBuilder  # noqa: E402

b = ModelBuilder()

MAT_A = "blue"      # 桌垫长板 (深)
MAT_B = "cyan"      # 桌垫长板 (浅)
BACK = "purple"     # 靠背墙
BRACE = "gray"      # 直角三角斜撑
RAMP = "orange"     # 躺靠坡道
FLAG = "red"        # 顶沿小旗
BOX = "green"       # 耳机小盒

# =================================================================
# 1. 桌垫底板 3 行 x 2 长板 (x [0,4], y [0,3])
# =================================================================
b.flat_rect("deck_0_w", 0, 0, 0.0, MAT_A)
b.flat_rect("deck_0_e", 2, 0, 0.0, MAT_B)
b.flat_rect("deck_1_w", 0, 1, 0.0, MAT_B)
b.flat_rect("deck_1_e", 2, 1, 0.0, MAT_A)
b.flat_rect("deck_2_w", 0, 2, 0.0, MAT_A)
b.flat_rect("deck_2_e", 2, 2, 0.0, MAT_B)

# =================================================================
# 2. 靠背墙 (y=2 拼缝, z 0..1) + 两端斜撑 (南向)
# =================================================================
b.wall_ns("back_0", 0, 2.0, 0, BACK)
b.wall_ns("back_1", 1, 2.0, 0, BACK)
b.wall_ns("back_2", 2, 2.0, 0, BACK)
b.wall_ns("back_3", 3, 2.0, 0, BACK)
b.brace("brace_w", (0.0, 2.0, 0.0), "-y", BRACE)
b.brace("brace_e", (4.0, 2.0, 0.0), "-y", BRACE)

# =================================================================
# 3. 30 度躺靠坡道 (车道 x [1,2], 顶边在 y=2 / z=1, 坡尾落地)
# =================================================================
b.ramp("cradle_ramp", "-y", 2.0, 1, 1.0, RAMP)

# =================================================================
# 4. 靠背顶沿三面小旗 (跳过坡道所在的 x [1,2] 段)
# =================================================================
b.crest_ns("flag_w", 0, 2.0, 1.0, FLAG)
b.crest_ns("flag_m", 2, 2.0, 1.0, FLAG)
b.crest_ns("flag_e", 3, 2.0, 1.0, FLAG)

# =================================================================
# 5. 耳机小盒 (右前角 x [3,4], y [0,1], 开顶)
# =================================================================
b.wall_ns("box_s", 3, 0.0, 0, BOX)
b.wall_ns("box_n", 3, 1.0, 0, BOX)
b.wall_ew("box_w", 3.0, 0, 0, BOX)
b.wall_ew("box_e", 4.0, 0, 0, BOX)

# =================================================================
# 教程步骤 (6 步)
# =================================================================
b.step(
    "铺桌垫前两行: 四片蓝青相间的长板行行整边互吸, 从左到右排齐。",
    ["deck_0_w", "deck_0_e", "deck_1_w", "deck_1_e"],
    tip="长板一片顶两格, 底板铺得又快又稳。",
)
b.step(
    "补上桌垫第三行: 再来两片长板, 摇篮的地基就位。",
    ["deck_2_w", "deck_2_e"],
    highlight=["deck_1_w"],
)
b.step(
    "立靠背墙: 四片紫色方板踩住 y=2 拼缝一字排开, 墙脚整边吸牢。",
    ["back_0", "back_1", "back_2", "back_3"],
    highlight=["deck_1_w", "deck_1_e"],
    tip="靠背是手机的枕头, 四片墙互相拉手才站得直。",
)
b.step(
    "锁斜撑、搭坡道: 两片灰色直角三角咬住墙端竖棱压住板缝, 橙色长板顶边吸靠背顶沿, 坡尾自然落到底板上。",
    ["brace_w", "brace_e", "cradle_ramp"],
    highlight=["back_0", "back_3"],
    tip="30 度斜躺角正好看动画 —— 坡尾贴地, 手机再重也不怕。",
)
b.step(
    "围耳机小盒: 右前角四面绿墙合围开顶小盒, 耳机、橡皮筋都住这里。",
    ["box_s", "box_e", "box_n", "box_w"],
    highlight=["deck_0_e"],
)
b.step(
    "升三面小旗: 红色三角骑上靠背顶沿, 手机摇篮开演!",
    ["flag_w", "flag_m", "flag_e"],
    highlight=["back_0", "back_2"],
    tip="小旗重心正压沿口 —— 装饰也要站得稳。",
)

model = b.finalize(
    model_id="phone_cradle_01",
    name="追剧手机摇篮",
    name_en="Phone Cradle 01",
    description=(
        "入门档实用功能: 只做一件事并把它做透的手机躺靠架 —— "
        "四片紫色靠背墙踩住底板拼缝一字排开, 两端直角三角斜撑"
        "咬棱压缝, 橙色长板顶边整边吸住靠背顶沿搭出 30 度躺靠"
        "坡道, 坡尾恰好落回底板零悬挑; 右前角四面绿墙围出开顶"
        "耳机小盒, 靠背顶沿三面红旗迎风。20 片, 搭完的第一件事: "
        "把手机躺上去, 按下播放键。"
    ),
    difficulty=1,
    tags=["实用功能", "手机架", "书桌", "亲子", "入门"],
    min_pieces=20,
    min_steps=6,
)

# ---- series 归类落盘 (CONTENT_STRATEGY.md 4.3 节: 入库必填) --------
out = Path(__file__).resolve().parent.parent / "data" / "models" / "phone_cradle_01.json"
model["content_meta"] = {
    "series": "practical_utility",
    "structural_signature": model["content_meta"]["structural_signature"],
}
out.write_text(json.dumps(model, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print("已写入 series=practical_utility")
