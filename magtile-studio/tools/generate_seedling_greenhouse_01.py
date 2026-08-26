#!/usr/bin/env python3
"""生成模型 data/models/seedling_greenhouse_01.json (育苗小暖棚, D1 入门)。

D1 配额解冻批第 2 号 (植物花园): 一座朝南的单坡育苗暖棚 (园艺里的
"阳畦") —— 后墙是一排透明窗格"玻璃", 30 度长板斜顶从后墙顶沿一直
铺到苗床前缘, 两端直角三角形山墙锁角, 苗床前沿探出一排刚发芽的
小苗。与库内温室 (greenhouse_01 双坡骨架房 / greenhouse_dome_01
穹顶) 结构叙事完全不同: 这是"一面墙 + 一面坡"的单坡棚。

结构总览 (世界单位 1.0 = 正方形磁力片边长, 南侧朝阳):
  - 苗床 (x [0,4], y [0,2]): 橙黄棋盘格方板                8 片
  - 后墙 (y=2, z 0..1): 透明窗格方一排 4 片                 4 片
  - 山墙锁角: 直角三角形斜撑立在两端 (竖边吸后墙端缝,
    横边吸苗床拼缝)                                          2 片
  - 玻璃斜顶: 30 度透明长板 4 道并排, 顶边整边吸后墙顶沿,
    坡尾自然落地                                             4 片
  - 新芽: 等边三角立在苗床前缘 (三绿一粉, 其中一株开花)      4 片
  合计 22 片, 6 个教程步骤, 5 种片形 (全部 CORE-9 之内)。

招牌技法 (T14 斜撑加固): 30 度斜板不当滚珠道用, 翻身成暖棚玻璃顶 ——
顶边吸墙沿、坡尾自落地, 板身自身接地故剪断顶铰链也不悬挂;
两端直角三角形既是山墙造型又是双边咬合的锁角斜撑。

物理规则要点 (validate 常规 + strict 双档零警告):
  - 后墙墙脚踩苗床拼缝, 相邻竖边互咬; 山墙三角双直角边分别
    吸后墙端缝与苗床拼缝, 后墙-山墙-苗床锁成门式框架;
  - 斜顶顶边与后墙顶沿等长整边吸合, 坡尾顶点触地 (接地片),
    相邻坡板长边共面互吸 —— 无悬挂链、无悬臂力矩;
  - 新芽三角底边完整吸住苗床前缘拼缝, 纯受压;
  - 最高点 1.0 (后墙顶), 远低于高层结构阈值。

用法: python3 tools/generate_seedling_greenhouse_01.py  (在 magtile-studio 目录下运行)
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from magtile_gen import ModelBuilder  # noqa: E402

b = ModelBuilder()

BED_A = "orange"    # 苗床棋盘格 (培养土)
BED_B = "yellow"
GLASS = "clear"     # 后墙窗格与玻璃斜顶
GABLE = "gray"      # 山墙锁角三角
SPROUT = "green"    # 新芽
BLOOM = "pink"      # 开花的那一株


def glass_wall(tid, x0, y, z0, color):
    b.add(tid, "window_square", (x0 + 0.5, y, z0 + 0.5), (90, 0, 0), color)


# =================================================================
# 1. 苗床 (x [0,4], y [0,2]): 橙黄棋盘格方板
# =================================================================
for j in range(2):
    for i in range(4):
        b.flat(f"bed_{i}_{j}", i, j, 0.0, BED_A if (i + j) % 2 == 0 else BED_B)

# =================================================================
# 2. 后墙 (y=2): 透明窗格方一排, 墙脚踩苗床北缘拼缝
# =================================================================
for i in range(4):
    glass_wall(f"glass_{i}", i, 2.0, 0, GLASS)

# =================================================================
# 3. 山墙锁角: 直角三角形立在两端 (直角顶点在后墙脚)
# =================================================================
b.brace("gable_w", (0.0, 2.0, 0.0), "-y", GABLE)
b.brace("gable_e", (4.0, 2.0, 0.0), "-y", GABLE)

# =================================================================
# 4. 玻璃斜顶: 30 度长板 4 道并排, 顶边吸后墙顶沿, 坡尾落地
# =================================================================
for i in range(4):
    b.ramp(f"roof_{i}", "-y", 2.0, i, 1.0, GLASS)

# =================================================================
# 5. 新芽: 等边三角立在苗床前缘, 三绿一粉
# =================================================================
for i in range(4):
    b.crest_ns(f"sprout_{i}", i, 0.0, 0.0, BLOOM if i == 2 else SPROUT)

# =================================================================
# 教程步骤 (6 步)
# =================================================================
b.step(
    "铺苗床第一排 (靠自己这排): 四片橙黄相间的方板从左到右吸成一条。",
    [f"bed_{i}_0" for i in range(4)],
    tip="橙黄棋盘格就是培养土 —— 拼缝对齐, 后面的墙和坡才有得吸。",
)
b.step(
    "铺苗床第二排: 再来四片, 与第一排整边互吸, 4x2 苗床完工。",
    [f"bed_{i}_1" for i in range(4)],
    highlight=["bed_0_0"],
    tip="轻推苗床应整体滑动 —— 说明八片吸成了一块。",
)
b.step(
    "立后墙: 四片透明窗格方踩住苗床北缘拼缝排成一排, 相邻竖边互咬。",
    [f"glass_{i}" for i in range(4)],
    highlight=["bed_0_1", "bed_3_1"],
    tip="窗格朝南, 太阳一出来整面墙都是亮的。",
)
b.step(
    "锁两端山墙: 灰色直角三角竖边吸后墙端缝、横边吸苗床拼缝。",
    ["gable_w", "gable_e"],
    highlight=["glass_0", "glass_3"],
    tip="三角一咬上, 后墙就推不倒了 —— 这就是斜撑的本事。",
)
b.step(
    "盖玻璃斜顶: 四道透明长板顶边整边吸住后墙顶沿, 坡尾自然落地。",
    [f"roof_{i}" for i in range(4)],
    highlight=["glass_0", "glass_3"],
    tip="一道一道盖, 相邻坡板长边互吸 —— 30 度斜坡正好接住阳光。",
)
b.step(
    "种上新芽: 四株小苗立上苗床前缘 —— 有一株已经开花了!",
    [f"sprout_{i}" for i in range(4)],
    highlight=["bed_0_0", "bed_3_0"],
    tip="底边要整条吸住前缘拼缝; 明天浇水的任务就交给你了。",
)

model = b.finalize(
    model_id="seedling_greenhouse_01",
    name="育苗小暖棚",
    name_en="Seedling Greenhouse 01",
    description=(
        "D1 入门园艺件: 朝南的单坡育苗暖棚 —— 4x2 橙黄棋盘苗床上立一排"
        "透明窗格后墙, 四道 30 度透明长板从墙顶一直斜铺到床前当玻璃顶, "
        "两端灰色直角三角山墙一咬锁死整个棚架; 苗床前缘探出四株新芽, "
        "其中一株已经开出粉色的花。搭完记得把它摆到窗台最晒的位置。"
    ),
    difficulty=1,
    tags=["植物花园", "暖棚", "育苗", "亲子入门"],
    min_pieces=22,
    min_steps=6,
)

# ---- content_meta 补全 (CONTENT_STRATEGY.md 5.1 节 schema) ---------
meta = model["content_meta"]
model["content_meta"] = {
    "series": "plant_garden",
    "build_paradigm": "bottom_up",
    "technique_tags": {
        "primary": "T14_diagonal_bracing",
        "secondary": ["T01_box_frame", "T17_negative_space"],
    },
    "signature_statement": "30 度斜板翻身当暖棚玻璃顶: 顶边吸墙沿坡尾自落地, 直角三角山墙双边锁角。",
    "structural_signature": meta["structural_signature"],
    "physical_risk_notes": [
        {"step": 3, "risk": "后墙一排窗格在山墙锁角前只靠墙脚与竖边互咬, 前推易倒",
         "mitigation": "下一步立即用直角三角双边咬合锁角; 该步 tip 提示竖边互咬"},
    ],
}

out = Path(__file__).resolve().parent.parent / "data" / "models" / "seedling_greenhouse_01.json"
out.write_text(json.dumps(model, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(f"已补全 content_meta 并重写 {out}")
