#!/usr/bin/env python3
"""生成模型 data/models/stonehenge_01.json (太阳石门阵)。

内容批 I 模型 4/4 (旗舰): 全库第一座史前巨石阵 —— 建筑地标主题
此前的门都是"一座门"(凯旋门 / 中世纪城门), 本作的招牌是"四门
环阵": 四座三石塔石门 (两柱一梁) 对准东南西北四个方向, 围着
场地正中的日晷祭坛站成一圈 —— 远古的人们就是用它当日历的:
太阳从东门升起, 光柱穿过门洞照在祭坛的日晷尖上。每座石门的
立柱都带 L 形互咬扶壁 (两层通高), 横梁两端竖边与柱顶互咬,
黄色晨光压顶石板同时咬住柱顶与扶壁顶 —— 石门越搭越懂结构。

结构总览 (世界单位: 1.0 = 正方形磁力片边长):
  - 草原地坪 8 行 (x [0,8], y [0,8]): 单位方板梯子纪律   46 片
  - 石门 x4 (立柱 2x2 层 + L 扶壁 2x2 层 + 长方形横梁
    + 晨光压顶 x2, 每座 11 片)                          44 片
  - 日晷祭坛 (x [3,5], y [3,5]): 墙环 8 + 坛面 4
    + 日晷尖 (瘦高等腰) + 日出火苗 x2                   15 片
  合计 105 片, 18 个教程步骤, 4 种磁力片形状 (全部 CORE-9 之内)。

物理规则要点 (validate 常规 + strict 双档零警告 + jitter 全绿):
  - 立柱与扶壁竖边直角互咬且两层通高 (竹丛 L 墙同款),
    薄柱的抗侧刚度来自直角折边;
  - 横梁 (长方形) 两条短竖边分别与两根立柱二层的竖边整边
    互咬 —— 两柱一梁锁成门式刚架;
  - 压顶石板北/西两边分别整边咬柱顶与扶壁顶, 双路吸合,
    剪断任何一条仍有第二条路径, R8 单点失效通过;
  - 祭坛墙环四角竖边互咬闭环, 坛面方板四边入扣墙顶,
    日晷尖与火苗骑板缝, 单片装饰失联不超 1 片;
  - 地坪拼缝纪律: 全部石门柱脚 / 扶壁脚 / 祭坛墙脚下都是
    单位方板, 且东西两列单位方板全场纵向贯通 (梯子纪律),
    保证地坪磁力图连成一体。

用法: python3 tools/generate_stonehenge_01.py  (在 magtile-studio 目录下运行)
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from magtile_gen import ModelBuilder  # noqa: E402

b = ModelBuilder()

GRASS = "green"     # 草原
PAD = "clear"       # 石位方板 (立石脚下的单位方板)
STONE = "gray"      # 巨石立柱 / 扶壁 / 横梁
CAPSTONE = "yellow"  # 晨光压顶石板
ALTAR = "gray"      # 祭坛石墙
ALTAR_TOP = "yellow"  # 祭坛坛面
GNOMON = "red"      # 日晷尖
FLAME = "red"       # 日出火苗

# =================================================================
# 1. 草原地坪 8 行 (x [0,8], y [0,8]): 梯子纪律 —— 东西两列
#    单位方板纵向贯通, 石门与祭坛脚下全单位方板
# =================================================================
# 南行 (y [0,1]): 南门柱脚 / 扶壁脚踩 (2,0) 与 (5,0) 两块石位
b.flat("g0_0", 0, 0, 0.0, GRASS)
b.flat("g0_1", 1, 0, 0.0, GRASS)
b.flat("g0_2", 2, 0, 0.0, PAD)
b.flat_rect("g0_m", 3, 0, 0.0, GRASS)
b.flat("g0_5", 5, 0, 0.0, PAD)
b.flat("g0_6", 6, 0, 0.0, GRASS)
b.flat("g0_7", 7, 0, 0.0, GRASS)
# 行 y [1,2] / [2,3] / [5,6] / [6,7]: 两端单位方板 + 三条长板
for row, y in (("g1", 1), ("g2", 2), ("g5", 5), ("g6", 6)):
    b.flat(f"{row}_w", 0, y, 0.0, PAD if y in (2, 5) else GRASS)
    b.flat_rect(f"{row}_a", 1, y, 0.0, GRASS)
    b.flat_rect(f"{row}_b", 3, y, 0.0, GRASS)
    b.flat_rect(f"{row}_c", 5, y, 0.0, GRASS)
    b.flat(f"{row}_e", 7, y, 0.0, PAD if y in (2, 5) else GRASS)
# 祭坛行 (y [3,4] 与 [4,5]): 祭坛脚下四块石位方板
for row, y in (("g3", 3), ("g4", 4)):
    b.flat(f"{row}_w", 0, y, 0.0, GRASS)
    b.flat_rect(f"{row}_a", 1, y, 0.0, GRASS)
    b.flat(f"{row}_3", 3, y, 0.0, PAD)
    b.flat(f"{row}_4", 4, y, 0.0, PAD)
    b.flat_rect(f"{row}_c", 5, y, 0.0, GRASS)
    b.flat(f"{row}_e", 7, y, 0.0, GRASS)
# 北行 (y [7,8]): 北门柱脚踩 (2,7) 与 (5,7)
b.flat("g7_0", 0, 7, 0.0, GRASS)
b.flat("g7_1", 1, 7, 0.0, GRASS)
b.flat("g7_2", 2, 7, 0.0, PAD)
b.flat_rect("g7_m", 3, 7, 0.0, GRASS)
b.flat("g7_5", 5, 7, 0.0, PAD)
b.flat("g7_6", 6, 7, 0.0, GRASS)
b.flat("g7_7", 7, 7, 0.0, GRASS)

# =================================================================
# 2. 南门 (立在 y=1 线上, 门洞朝向祭坛): 柱 + L 扶壁 + 梁 + 压顶
# =================================================================
b.wall_ns("sg_cw0", 2, 1.0, 0, STONE)   # 西柱一/二层
b.wall_ns("sg_cw1", 2, 1.0, 1, STONE)
b.wall_ns("sg_ce0", 5, 1.0, 0, STONE)   # 东柱一/二层
b.wall_ns("sg_ce1", 5, 1.0, 1, STONE)
b.wall_ew("sg_bw0", 2.0, 0, 0, STONE)   # 西扶壁 (L 形互咬)
b.wall_ew("sg_bw1", 2.0, 0, 1, STONE)
b.wall_ew("sg_be0", 6.0, 0, 0, STONE)   # 东扶壁
b.wall_ew("sg_be1", 6.0, 0, 1, STONE)
b.lintel_ns("sg_lin", 3, 1.0, 1, STONE)  # 横梁跨 2 格门洞
b.flat("sg_capw", 2, 0, 2.0, CAPSTONE)  # 晨光压顶
b.flat("sg_cape", 5, 0, 2.0, CAPSTONE)

# =================================================================
# 3. 西门 (立在 x=1 线上)
# =================================================================
b.wall_ew("wg_cs0", 1.0, 2, 0, STONE)
b.wall_ew("wg_cs1", 1.0, 2, 1, STONE)
b.wall_ew("wg_cn0", 1.0, 5, 0, STONE)
b.wall_ew("wg_cn1", 1.0, 5, 1, STONE)
b.wall_ns("wg_bs0", 0, 2.0, 0, STONE)
b.wall_ns("wg_bs1", 0, 2.0, 1, STONE)
b.wall_ns("wg_bn0", 0, 6.0, 0, STONE)
b.wall_ns("wg_bn1", 0, 6.0, 1, STONE)
b.lintel_ew("wg_lin", 1.0, 3, 1, STONE)
b.flat("wg_caps", 0, 2, 2.0, CAPSTONE)
b.flat("wg_capn", 0, 5, 2.0, CAPSTONE)

# =================================================================
# 4. 东门 (立在 x=7 线上): 日出方向, 光柱穿门洞照进祭坛
# =================================================================
b.wall_ew("eg_cs0", 7.0, 2, 0, STONE)
b.wall_ew("eg_cs1", 7.0, 2, 1, STONE)
b.wall_ew("eg_cn0", 7.0, 5, 0, STONE)
b.wall_ew("eg_cn1", 7.0, 5, 1, STONE)
b.wall_ns("eg_bs0", 7, 2.0, 0, STONE)
b.wall_ns("eg_bs1", 7, 2.0, 1, STONE)
b.wall_ns("eg_bn0", 7, 6.0, 0, STONE)
b.wall_ns("eg_bn1", 7, 6.0, 1, STONE)
b.lintel_ew("eg_lin", 7.0, 3, 1, STONE)
b.flat("eg_caps", 7, 2, 2.0, CAPSTONE)
b.flat("eg_capn", 7, 5, 2.0, CAPSTONE)

# =================================================================
# 5. 北门 (立在 y=7 线上)
# =================================================================
b.wall_ns("ng_cw0", 2, 7.0, 0, STONE)
b.wall_ns("ng_cw1", 2, 7.0, 1, STONE)
b.wall_ns("ng_ce0", 5, 7.0, 0, STONE)
b.wall_ns("ng_ce1", 5, 7.0, 1, STONE)
b.wall_ew("ng_bw0", 2.0, 7, 0, STONE)
b.wall_ew("ng_bw1", 2.0, 7, 1, STONE)
b.wall_ew("ng_be0", 6.0, 7, 0, STONE)
b.wall_ew("ng_be1", 6.0, 7, 1, STONE)
b.lintel_ns("ng_lin", 3, 7.0, 1, STONE)
b.flat("ng_capw", 2, 7, 2.0, CAPSTONE)
b.flat("ng_cape", 5, 7, 2.0, CAPSTONE)

# =================================================================
# 6. 日晷祭坛 (x [3,5], y [3,5]): 墙环 + 坛面 + 日晷尖 + 火苗
# =================================================================
b.wall_ns("a_s_w", 3, 3.0, 0, ALTAR)
b.wall_ns("a_s_e", 4, 3.0, 0, ALTAR)
b.wall_ns("a_n_w", 3, 5.0, 0, ALTAR)
b.wall_ns("a_n_e", 4, 5.0, 0, ALTAR)
b.wall_ew("a_w_s", 3.0, 3, 0, ALTAR)
b.wall_ew("a_w_n", 3.0, 4, 0, ALTAR)
b.wall_ew("a_e_s", 5.0, 3, 0, ALTAR)
b.wall_ew("a_e_n", 5.0, 4, 0, ALTAR)
b.flat("a_cap_sw", 3, 3, 1.0, ALTAR_TOP)
b.flat("a_cap_se", 4, 3, 1.0, ALTAR_TOP)
b.flat("a_cap_nw", 3, 4, 1.0, ALTAR_TOP)
b.flat("a_cap_ne", 4, 4, 1.0, ALTAR_TOP)
b.spire_ew("gnomon", 4.0, 3, 1.0, GNOMON)   # 日晷尖 2.94 全场制高
b.crest_ns("flame_w", 3, 4.0, 1.0, FLAME)   # 日出火苗骑坛面板缝
b.crest_ns("flame_e", 4, 4.0, 1.0, FLAME)

# =================================================================
# 教程步骤 (18 步)
# =================================================================
b.step(
    "铺南边两行: 南门柱脚下的透明石位是单位方板, 东西两端也各留一块。",
    ["g0_0", "g0_1", "g0_2", "g0_m", "g0_5", "g0_6", "g0_7",
     "g1_w", "g1_a", "g1_b", "g1_c", "g1_e"],
    tip="远古的太阳日历开工啦 —— 石头脚下必须踩单位方板, "
        "墙底边要和方板边等长吸合。",
)
b.step(
    "铺第三行与祭坛南行: 透明石位给西门东门和祭坛留位。",
    ["g2_w", "g2_a", "g2_b", "g2_c", "g2_e",
     "g3_w", "g3_a", "g3_3", "g3_4", "g3_c", "g3_e"],
    highlight=["g1_w"],
    tip="东西两列单位方板从南贯到北 —— 整片草原吸成一体。",
)
b.step(
    "铺祭坛北行与第六行: 祭坛脚下四块石位凑齐。",
    ["g4_w", "g4_a", "g4_3", "g4_4", "g4_c", "g4_e",
     "g5_w", "g5_a", "g5_b", "g5_c", "g5_e"],
    highlight=["g3_3"],
)
b.step(
    "铺北边两行收口: 北门柱脚的两块石位就位, 草原完工。",
    ["g6_w", "g6_a", "g6_b", "g6_c", "g6_e",
     "g7_0", "g7_1", "g7_2", "g7_m", "g7_5", "g7_6", "g7_7"],
    highlight=["g5_w"],
)
b.step(
    "立南门一层: 两根石柱踩住石位, 两片扶壁与柱竖边直角互咬成 L 形。",
    ["sg_cw0", "sg_ce0", "sg_bw0", "sg_be0"],
    highlight=["g0_2", "g0_5"],
    tip="L 形折边就是薄柱的靠山 —— 巨石阵的立柱一站就是几千年。",
)
b.step(
    "摞南门二层: 柱与扶壁整边共线上叠, 互咬棱一通到顶。",
    ["sg_cw1", "sg_ce1", "sg_bw1", "sg_be1"],
    highlight=["sg_cw0"],
)
b.step(
    "架南门横梁并放压顶: 横梁两端竖边与柱顶互咬锁成门式刚架, "
    "两片黄色晨光石板同时咬住柱顶与扶壁顶。",
    ["sg_lin", "sg_capw", "sg_cape"],
    highlight=["sg_cw1", "sg_ce1"],
    tip="两柱一梁就是'三石塔' —— 巨石阵最经典的一景。",
)
b.step(
    "立西门一层: 石柱与扶壁换个方向, 同样的 L 形互咬。",
    ["wg_cs0", "wg_cn0", "wg_bs0", "wg_bn0"],
    highlight=["g2_w", "g5_w"],
)
b.step(
    "摞西门二层: 四片石墙整边上叠。",
    ["wg_cs1", "wg_cn1", "wg_bs1", "wg_bn1"],
    highlight=["wg_cs0"],
)
b.step(
    "架西门横梁并放压顶: 第二座三石塔合拢。",
    ["wg_lin", "wg_caps", "wg_capn"],
    highlight=["wg_cs1", "wg_cn1"],
)
b.step(
    "立东门一层: 日出方向的石门, 光柱要从这个门洞照进祭坛。",
    ["eg_cs0", "eg_cn0", "eg_bs0", "eg_bn0"],
    highlight=["g2_e", "g5_e"],
    tip="每年最长的白天, 太阳正好从东门门洞里升起来。",
)
b.step(
    "摞东门二层: 柱与扶壁继续通高互咬。",
    ["eg_cs1", "eg_cn1", "eg_bs1", "eg_bn1"],
    highlight=["eg_cs0"],
)
b.step(
    "架东门横梁并放压顶: 日出之门完工。",
    ["eg_lin", "eg_caps", "eg_capn"],
    highlight=["eg_cs1", "eg_cn1"],
)
b.step(
    "立北门一层: 最后一座石门的柱脚踩上北行石位。",
    ["ng_cw0", "ng_ce0", "ng_bw0", "ng_be0"],
    highlight=["g7_2", "g7_5"],
)
b.step(
    "摞北门二层: 四门环阵初见雏形。",
    ["ng_cw1", "ng_ce1", "ng_bw1", "ng_be1"],
    highlight=["ng_cw0"],
)
b.step(
    "架北门横梁并放压顶: 四座三石塔对准东南西北, 环阵合围。",
    ["ng_lin", "ng_capw", "ng_cape"],
    highlight=["ng_cw1", "ng_ce1"],
    tip="站在场地正中转一圈 —— 四个门洞正好指着四个方向。",
)
b.step(
    "砌日晷祭坛墙环: 八片石墙踩住四块石位, 四角竖边互咬闭环。",
    ["a_s_w", "a_s_e", "a_n_w", "a_n_e",
     "a_w_s", "a_w_n", "a_e_s", "a_e_n"],
    highlight=["g3_3", "g4_4"],
    tip="祭坛在整个石阵的正中央 —— 它就是日历的表盘。",
)
b.step(
    "盖坛面, 竖日晷尖, 点日出火苗: 红色瘦高尖直上 2.94 全场制高, "
    "两簇火苗骑在坛面板缝上。",
    ["a_cap_sw", "a_cap_se", "a_cap_nw", "a_cap_ne",
     "gnomon", "flame_w", "flame_e"],
    highlight=["a_s_w"],
    tip="太阳从东门升起, 光柱照在日晷尖上 —— 远古的日历走起来了!",
)

b.finalize(
    model_id="stonehenge_01",
    name="太阳石门阵",
    name_en="Sun Stone Circle 01",
    description=(
        "只用核心九片型的全库第一座史前巨石阵: 与凯旋门 / 中世纪城门"
        "的'一座门'都不同, 本作的招牌是'四门环阵' —— 四座两柱一梁的"
        "三石塔石门对准东南西北, 围着正中的日晷祭坛站成一圈; 每根石柱"
        "都带 L 形互咬扶壁两层通高 (薄柱的抗侧刚度来自直角折边), 长方"
        "形横梁两端竖边与柱顶互咬锁成门式刚架, 黄色晨光压顶石板同时"
        "咬住柱顶与扶壁顶双路吸合; 祭坛墙环四角互咬闭环, 红色日晷尖"
        "直上 2.94 全场制高 —— 太阳从东门升起, 光柱穿过门洞照在日晷"
        "尖上, 远古的人们就是这样读日历的!"
    ),
    difficulty=4,
    tags=["世界地标", "建筑地标", "巨石阵", "史前", "挑战"],
    min_pieces=105,
    min_steps=18,
)
