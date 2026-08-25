#!/usr/bin/env python3
"""生成模型 data/models/lifeguard_tower_01.json (海滩救生站)。

海洋探险主题批 2/3: 全库第一座海滩救生站 —— 与同为海岸场景的
whale_watching_01 (2x2 观景台 + 塔 + 30 度栈道) 刻意错开结构
词汇: 本作没有平台没有坡道, 主角是"高脚瞭望椅"这把救生员的
标志性座椅 —— 1x1 足印双层窄塔配瞭望窗, 塔基两片红色直角三角
斜撑像椅子的撑脚; 旁边红白配色的值班房两坡脊饰, 沙滩上橙色
四坡遮阳伞直接落沙自锁, 红蓝冲浪板插在沙缝里, 清色浪花拍岸 ——
全库唯一的"高脚椅 + 落沙伞"组合。

结构总览 (世界单位: 1.0 = 正方形磁力片边长, 海在南, 沙滩在北):
  - 海面 (y [0,1]): 蓝色长板 x3 + 清色浪花等边三角 x2             5 片
  - 沙滩 (x [0,6], y [1,4]): 单位方板 x12 + 长板 x3 (伞位留沙)   15 片
  - 高脚瞭望椅 (x [1,2], y [2,3], z 0..2): 双层墙环 x8 (含瞭望
    窗格 x3) + 座板 x1 + 红旗 x1 + 撑脚斜撑 x2                   12 片
  - 值班房 (x [3,5], y [2,3], z 0..1): 环墙 x6 (含门框 x1) +
    盖板 x2 + 红白脊饰 x2                                        10 片
  - 遮阳伞: 橙色等边四坡锥直接落沙自锁 (x [5,6], y [3,4])         4 片
  - 冲浪板 x2: 红蓝等腰塔尖插在沙缝 (板尖 2.0)                    2 片
  合计 48 片, 11 个教程步骤, 7 种磁力片形状 (全部 CORE-9 之内)。

物理规则要点 (validate 常规 + strict 双档零警告):
  - 瞭望椅双层墙环整边咬合, 座板压顶锁箱; 两片斜撑竖直角边吸
    塔角竖棱、水平直角边吸沙滩拼缝 (双边受力零悬挑);
  - 遮阳伞四坡锥不需要盖板: 四条底边落沙 (接地), 南/西底边各吸
    一条沙板沿, 四条斜棱两两互吸自锁成环;
  - 值班房环墙合环 + 盖板压顶, 脊饰骑盖板北沿 (同吸北墙顶);
  - 浪花/冲浪板底边整边吸沙缝, 重心正压铰链线, 剪断只失联 1 片;
  - 沙滩拼缝纪律: 塔脚/房脚/板缝处全单位方板, 行行等边互吸。

用法: python3 tools/generate_lifeguard_tower_01.py  (在 magtile-studio 目录下运行)
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from magtile_gen import ModelBuilder  # noqa: E402

b = ModelBuilder()

SEA = "blue"        # 海面
WAVE = "clear"      # 浪花
SAND = "yellow"     # 沙滩
CHAIR = "red"       # 瞭望椅塔身
WIN = "cyan"        # 瞭望窗
SEAT = "gray"       # 座板
FLAG = "red"        # 救生旗
BRACE = "red"       # 撑脚斜撑
HUT = "clear"       # 值班房墙 (白)
DOOR = "orange"     # 值班房门
HUT_CAP = "gray"    # 值班房盖板
RIDGE_A = "red"     # 脊饰 (红白相间)
RIDGE_B = "clear"
UMBRELLA = "orange"  # 遮阳伞
BOARD_A = "red"     # 冲浪板
BOARD_B = "blue"


def wall_ns_t(tid, tile_type, x0, y, z0, color):
    b.add(tid, tile_type, (x0 + 0.5, y, z0 + 0.5), (90, 0, 0), color)


def wall_ew_t(tid, tile_type, x, y0, z0, color):
    b.add(tid, tile_type, (x, y0 + 0.5, z0 + 0.5), (90, 0, 90), color)


# =================================================================
# 1. 海面 (y [0,1]) + 沙滩 (y [1,4]): 塔脚/房脚线全单位方板
# =================================================================
b.flat_rect("sea_0", 0, 0, 0.0, SEA)
b.flat_rect("sea_2", 2, 0, 0.0, SEA)
b.flat_rect("sea_4", 4, 0, 0.0, SEA)
for x0 in range(6):
    b.flat(f"sand_{x0}_1", x0, 1, 0.0, SAND)      # 滩前行
for x0 in range(6):
    b.flat(f"sand_{x0}_2", x0, 2, 0.0, SAND)      # 塔房行
b.flat_rect("sand_w_3", 0, 3, 0.0, SAND)          # 后排 (伞位留沙)
b.flat("sand_2_3", 2, 3, 0.0, SAND)
b.flat_rect("sand_e_3", 3, 3, 0.0, SAND)
b.crest_ns("wave_w", 1, 1.0, 0.0, WAVE)           # 浪花拍岸
b.crest_ns("wave_e", 4, 1.0, 0.0, WAVE)

# =================================================================
# 2. 高脚瞭望椅 (x [1,2], y [2,3], z 0..2): 双层窄塔 + 座板 + 旗
# =================================================================
b.wall_ns("ch1_s", 1, 2.0, 0, CHAIR)
b.wall_ns("ch1_n", 1, 3.0, 0, CHAIR)
b.wall_ew("ch1_w", 1.0, 2, 0, CHAIR)
b.wall_ew("ch1_e", 2.0, 2, 0, CHAIR)
b.brace("br_w", (1.0, 2.0, 0.0), "-x", BRACE)     # 撑脚 (平面 y=2)
b.brace("br_e", (2.0, 2.0, 0.0), "+x", BRACE)
wall_ns_t("ch2_s", "window_square", 1, 2.0, 1, WIN)   # 瞭望窗朝海
wall_ns_t("ch2_n", "window_square", 1, 3.0, 1, WIN)
wall_ew_t("ch2_w", "window_square", 1.0, 2, 1, WIN)
b.wall_ew("ch2_e", 2.0, 2, 1, CHAIR)
b.flat("seat", 1, 2, 2.0, SEAT)
b.crest_ns("flag", 1, 2.0, 2.0, FLAG)             # 旗尖 2.87

# =================================================================
# 3. 值班房 (x [3,5], y [2,3], z 0..1): 环墙 + 盖板 + 脊饰
# =================================================================
wall_ns_t("hut_s_3", "door_frame", 3, 2.0, 0, DOOR)   # 房门朝海
b.wall_ns("hut_s_4", 4, 2.0, 0, HUT)
b.wall_ns("hut_n_3", 3, 3.0, 0, HUT)
b.wall_ns("hut_n_4", 4, 3.0, 0, HUT)
b.wall_ew("hut_w", 3.0, 2, 0, HUT)
b.wall_ew("hut_e", 5.0, 2, 0, HUT)
b.flat("hut_cap_3", 3, 2, 1.0, HUT_CAP)
b.flat("hut_cap_4", 4, 2, 1.0, HUT_CAP)
b.crest_ns("ridge_3", 3, 3.0, 1.0, RIDGE_A)       # 脊饰骑北沿
b.crest_ns("ridge_4", 4, 3.0, 1.0, RIDGE_B)

# =================================================================
# 4. 遮阳伞 + 冲浪板: 落沙自锁 / 插缝直立
# =================================================================
UMB = b.hat4("umb", 5, 3, 0.0, UMBRELLA, shape="equilateral_triangle")
b.spire_ns("board_w", 0, 3.0, 0.0, BOARD_A)       # 板尖 2.0
b.spire_ew("board_e", 3.0, 3, 0.0, BOARD_B)

# =================================================================
# 教程步骤 (11 步)
# =================================================================
b.step(
    "铺海面立浪花: 三条蓝色长板短边互吸, 两朵清色浪花骑岸线拼缝。",
    ["sea_0", "sea_2", "sea_4", "wave_w", "wave_e"],
    tip="浪花底边整边吸住岸线 —— 今天风平浪静, 适合下水。",
)
b.step(
    "铺滩前行沙板: 六片黄色单位方板贴着海面排成一行。",
    [f"sand_{x0}_1" for x0 in range(6)],
    highlight=["sea_0"],
    tip="全用单位方板 —— 瞭望椅和值班房的墙脚拼缝就在这行北沿。",
)
b.step(
    "铺塔房行沙板: 再来六片, 与滩前行行行等边互吸。",
    [f"sand_{x0}_2" for x0 in range(6)],
    highlight=["sand_0_1"],
    tip="沙滩连成一整张网, 高脚椅才立得稳。",
)
b.step(
    "铺后排沙板插冲浪板: 伞位留出一格沙地, 红蓝板尖插进沙缝。",
    ["sand_w_3", "sand_2_3", "sand_e_3", "board_w", "board_e"],
    highlight=["sand_0_2"],
    tip="冲浪板底边整边吸沙缝, 板尖 2.0 —— 下班就去追浪!",
)
b.step(
    "立瞭望椅一层: 红色墙环四角竖边互咬合环。",
    ["ch1_s", "ch1_n", "ch1_w", "ch1_e"],
    highlight=["sand_1_1"],
    tip="1x1 足印的窄塔全靠闭环 —— 四角一咬就是一圈保险。",
)
b.step(
    "装撑脚斜撑: 两片红色直角三角, 竖边吸塔角竖棱、横边吸沙缝。",
    ["br_w", "br_e"],
    highlight=["ch1_s"],
    tip="像高脚椅的两条撑脚 —— 双边受力零悬挑, 海风吹不晃。",
)
b.step(
    "立瞭望层: 三面瞭望窗格环列, 整边骑一层墙顶。",
    ["ch2_s", "ch2_n", "ch2_w", "ch2_e"],
    highlight=["ch1_w"],
    tip="朝海的三面全是窗 —— 救生员的眼睛不能离开海面。",
)
b.step(
    "盖座板升红旗: 灰色座板压顶锁箱, 红旗骑南沿正对海面。",
    ["seat", "flag"],
    highlight=["ch2_s"],
    tip="红旗升起 = 救生员在岗 —— 旗尖 2.87 全场最高。",
)
b.step(
    "立值班房环墙: 门框方房门朝海, 六片墙合环。",
    ["hut_s_3", "hut_s_4", "hut_n_3", "hut_n_4", "hut_w", "hut_e"],
    highlight=["sand_3_1"],
    tip="急救箱和救生圈都放这间白房子里 —— 门正对沙滩。",
)
b.step(
    "盖值班房顶: 两片盖板压顶, 红白脊饰骑北沿。",
    ["hut_cap_3", "hut_cap_4", "ridge_3", "ridge_4"],
    highlight=["hut_s_3"],
    tip="脊饰同吸盖板沿与墙顶 —— 红白条纹是救生站的招牌色。",
)
b.step(
    "撑遮阳伞收尾: 四片橙色等边三角直接落沙, 斜棱互咬自锁。",
    UMB,
    highlight=["flag"],
    tip="伞底边落沙又吸板沿, 四坡自锁不用盖板 —— 救生站开张!",
)

b.finalize(
    model_id="lifeguard_tower_01",
    name="海滩救生站",
    name_en="Lifeguard Tower 01",
    description=(
        "只用核心九片型的海滩救生站: 与观鲸瞭望站的'平台 + 栈道'不同, "
        "这里没有平台没有坡道, 主角是救生员标志性的高脚瞭望椅 —— "
        "1x1 足印双层窄塔三面瞭望窗环列, 塔基两片红色直角三角斜撑像"
        "椅子撑脚 (竖边吸塔角竖棱、横边吸沙缝, 双边受力零悬挑), 座板"
        "压顶红旗骑沿; 红白配色值班房门框朝海、脊饰骑沿, 橙色四坡"
        "遮阳伞四条底边直接落沙、斜棱互咬自锁成环, 红蓝冲浪板插在"
        "沙缝里, 清色浪花拍岸 —— 红旗升起, 救生员在岗!"
    ),
    difficulty=2,
    tags=["海洋", "探险", "沙滩", "救生站", "海岸"],
    min_pieces=48,
    min_steps=11,
)
