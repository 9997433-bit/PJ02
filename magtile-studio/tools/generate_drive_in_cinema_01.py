#!/usr/bin/env python3
"""生成模型 data/models/drive_in_cinema_01.json (星光露天汽车影院)。

城市生活主题的第一座夜场娱乐场景: 与立体车库 (柱-板框架) 和
出租车 (单车特写) 的结构语言都不同 —— 本作是"一面巨幕 + 一排
观影车位"的场景组合: 四格宽两层高的银幕墙靠三条直角斜撑站稳
(斜撑双边吸合, 幕-撑-地锁成三角刚性节点); 放映室两层箱塔顶着
双窗格放映窗正对银幕; 三辆轮座小车错落停进星光车位 —— 每辆
都是"轮座车板 + 单间驾驶舱"的最小车辆单元, 车头一律朝幕。

结构总览 (世界单位: 1.0 = 正方形磁力片边长, 银幕在北, 入口在南):
  - 观影场坪 (x [0,6], y [0,4]): 单位方板 x11 + 长板 x4
    (车位 6 格留空)                                              15 片
  - 幕后检修带 (x [1,5], y [4,5]): 单位方板 x4                    4 片
  - 银幕墙 (y=4, x [1,5], z 0..2): 两层立墙 4+4                   8 片
  - 银幕斜撑 x3 (x=2/3/4, 幕后): 直角三角双边吸合                 3 片
  - 幕顶彩旗 x4: 等边三角骑放映层墙顶                             4 片
  - 放映室 (x [2,4], y [0,1], z 0..2): 两层墙环 6+6 (上层北面
    双窗格放映窗) + 长板平顶                                     13 片
  - 观影车 x3 (每辆 2x1): 轮座车板 + 驾驶舱四墙 + 舱顶            18 片
  - 入口灯牌 (瘦高等腰) + 检票旗 + 场边音响 x2 (等边三角)          4 片
  合计 68 片, 15 个教程步骤, 7 种磁力片形状 (全部 CORE-9 之内)。

物理规则要点 (validate 常规 + strict 双档零警告):
  - 银幕墙两层: 上层墙脚整边压下层墙顶, 墙墙侧边互吸连成整面;
    三条斜撑竖直角边吸幕墙竖边、水平直角边吸检修带拼缝,
    幕-撑-地成环, 剪断任一铰链仍有支撑路径;
  - 观影车: 轮座车板平铺吸场坪拼缝, 驾驶舱墙脚吸车板短边与
    邻近场坪拼缝, 舱顶四边入扣墙顶 —— 车头前甲板零悬挑;
  - 放映室两层墙环四角竖边互咬, 平顶双板边边入扣墙顶;
  - 灯牌/旗/音响底边整边吸拼缝, 剪断任何一条装饰连接最多失联
    1 片 (< 3), R8 单点失效通过。

用法: python3 tools/generate_drive_in_cinema_01.py  (在 magtile-studio 目录下运行)
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from magtile_gen import ModelBuilder  # noqa: E402

b = ModelBuilder()

LOT_A = "gray"       # 场坪 (深浅相间)
LOT_B = "purple"
BACK = "gray"        # 幕后检修带
SCREEN = "clear"     # 银幕
SCREEN_BASE = "blue" # 银幕基座层
BRACE = "yellow"     # 银幕斜撑
BOOTH = "blue"       # 放映室
BOOTH_WIN = "clear"  # 放映窗
BOOTH_ROOF = "gray"  # 放映室平顶
CAR_1 = "red"        # 三辆观影车
CAR_2 = "green"
CAR_3 = "orange"
CAR_TOP = "clear"    # 舱顶
SIGN = "pink"        # 入口灯牌
FLAG = "yellow"      # 检票旗
SPEAKER = "cyan"     # 场边音响


def wall_ns_t(tid, tile_type, x0, y, z0, color):
    b.add(tid, tile_type, (x0 + 0.5, y, z0 + 0.5), (90, 0, 0), color)


# 车位单元: 轮座车板 (x [x0,x0+2]) + 驾驶舱 (西端单间), 车头朝东/朝幕
def car(prefix, x0, y0, body, roof_ids):
    b.add(f"{prefix}_base", "wheel_base",
          (x0 + 1.0, y0 + 0.5, 0.0), (0, 0, 0), body)
    b.wall_ns(f"{prefix}_cab_s", x0, float(y0), 0, body)
    b.wall_ns(f"{prefix}_cab_n", x0, float(y0 + 1), 0, body)
    b.wall_ew(f"{prefix}_cab_w", float(x0), y0, 0, body)
    b.wall_ew(f"{prefix}_cab_e", float(x0 + 1), y0, 0, CAR_TOP)
    b.flat(f"{prefix}_cab_top", x0, y0, 1.0, CAR_TOP)
    roof_ids.extend([
        f"{prefix}_base", f"{prefix}_cab_s", f"{prefix}_cab_n",
        f"{prefix}_cab_w", f"{prefix}_cab_e", f"{prefix}_cab_top",
    ])


# =================================================================
# 1. 观影场坪 (y [0,4]): 入场行为单位方板 (供墙脚/灯牌拼缝),
#    车位 6 格留空, 北两行嵌长板
#    车位: 车 1 (0,2)+(1,2), 车 2 (3,2)+(4,2), 车 3 (1,1)+(2,1)
# =================================================================
for x0 in range(6):
    color = LOT_A if x0 % 2 == 0 else LOT_B
    b.flat(f"lot_{x0}_0", x0, 0, 0.0, color)              # 入场行
b.flat("lot_0_1", 0, 1, 0.0, LOT_B)
b.flat("lot_3_1", 3, 1, 0.0, LOT_A)
b.flat_rect("lot_e_1", 4, 1, 0.0, LOT_B)                  # x [4,6]
b.flat("lot_2_2", 2, 2, 0.0, LOT_A)
b.flat("lot_5_2", 5, 2, 0.0, LOT_B)
b.flat_rect("lot_w_3", 0, 3, 0.0, LOT_A)                  # 前排行 x [0,2]
b.flat_rect("lot_m_3", 2, 3, 0.0, LOT_B)                  # x [2,4]
b.flat_rect("lot_e_3", 4, 3, 0.0, LOT_A)                  # x [4,6]

# 幕后检修带 (y [4,5]): 斜撑的落脚拼缝
for x0 in (1, 2, 3, 4):
    b.flat(f"back_{x0}", x0, 4, 0.0, BACK)

# =================================================================
# 2. 银幕墙 (y=4, x [1,5], z 0..2) + 三条幕后斜撑
# =================================================================
for x0 in (1, 2, 3, 4):
    b.wall_ns(f"screen_lo_{x0}", x0, 4.0, 0, SCREEN_BASE)
for x0 in (1, 2, 3, 4):
    b.wall_ns(f"screen_hi_{x0}", x0, 4.0, 1, SCREEN)
b.brace("brace_2", (2.0, 4.0, 0.0), "+y", BRACE)
b.brace("brace_3", (3.0, 4.0, 0.0), "+y", BRACE)
b.brace("brace_4", (4.0, 4.0, 0.0), "+y", BRACE)
# 幕顶彩旗: 四面等边三角骑在放映层墙顶上
FLAG_COLORS = ("red", "yellow", "pink", "cyan")
for x0, color in zip((1, 2, 3, 4), FLAG_COLORS):
    b.crest_ns(f"bunting_{x0}", x0, 4.0, 2.0, color)

# =================================================================
# 3. 放映室 (x [2,4], y [0,1], z 0..2): 两层墙环 + 双窗格 + 平顶
# =================================================================
b.wall_ns("booth_lo_s_w", 2, 0.0, 0, BOOTH)
b.wall_ns("booth_lo_s_e", 3, 0.0, 0, BOOTH)
b.wall_ns("booth_lo_n_w", 2, 1.0, 0, BOOTH)
b.wall_ns("booth_lo_n_e", 3, 1.0, 0, BOOTH)
b.wall_ew("booth_lo_w", 2.0, 0, 0, BOOTH)
b.wall_ew("booth_lo_e", 4.0, 0, 0, BOOTH)
b.wall_ns("booth_hi_s_w", 2, 0.0, 1, BOOTH)
b.wall_ns("booth_hi_s_e", 3, 0.0, 1, BOOTH)
wall_ns_t("booth_win_w", "window_square", 2, 1.0, 1, BOOTH_WIN)
wall_ns_t("booth_win_e", "window_square", 3, 1.0, 1, BOOTH_WIN)
b.wall_ew("booth_hi_w", 2.0, 0, 1, BOOTH)
b.wall_ew("booth_hi_e", 4.0, 0, 1, BOOTH)
b.flat_rect("booth_roof", 2, 0, 2.0, BOOTH_ROOF)          # 短边入扣东西墙顶

# =================================================================
# 4. 三辆观影车: 车头 (前甲板) 一律朝幕
# =================================================================
CAR1, CAR2, CAR3 = [], [], []
car("car1", 0, 2, CAR_1, CAR1)
car("car2", 3, 2, CAR_2, CAR2)
car("car3", 1, 1, CAR_3, CAR3)

# =================================================================
# 5. 入口灯牌 + 检票旗 + 场边音响
# =================================================================
b.spire_ns("gate_sign", 5, 0.0, 0.0, SIGN)      # 入口灯牌 (顶尖 2.0)
b.crest_ns("gate_flag", 0, 0.0, 0.0, FLAG)      # 检票旗
b.crest_ew("speaker_e", 5.0, 2, 0.0, SPEAKER)   # 东侧音响
b.crest_ew("speaker_w", 0.0, 1, 0.0, SPEAKER)   # 西侧音响

# =================================================================
# 教程步骤 (15 步)
# =================================================================
b.step(
    "铺入场行场坪: 六片方板深浅相间, 边边互吸。",
    [f"lot_{x0}_0" for x0 in range(6)],
    tip="天一擦黑, 汽车影院就热闹起来 —— 先把场地铺平。",
)
b.step(
    "铺第二行场坪: 两片方板加一条长板, 中间两格留给 3 号车。",
    ["lot_0_1", "lot_3_1", "lot_e_1"],
    highlight=["lot_0_0"],
    tip="留空的格子先不管它, 车来了正好停进去。",
)
b.step(
    "铺前排行: 三条长板连成一线, 银幕就立在这行的北沿上。",
    ["lot_w_3", "lot_m_3", "lot_e_3"],
    highlight=["lot_0_1"],
    tip="第一排是最抢手的位置, 记得早点来占。",
)
b.step(
    "补第三行场坪: 两片方板贴住前排长板, 再留出两个双格车位。",
    ["lot_2_2", "lot_5_2"],
    highlight=["lot_m_3"],
    tip="三个车位错开排 —— 后排的车也能看到整块银幕。",
)
b.step(
    "铺幕后检修带: 四片方板贴着场坪北沿再铺一行。",
    ["back_1", "back_2", "back_3", "back_4"],
    highlight=["lot_w_3"],
    tip="这行是给斜撑和检修工人留的 —— 观众看不到的后台。",
)
b.step(
    "立银幕基座层: 四片蓝色立墙踩住拼缝, 侧边互吸连成整面。",
    ["screen_lo_1", "screen_lo_2", "screen_lo_3", "screen_lo_4"],
    highlight=["back_1"],
    tip="墙脚前后都有方板拼缝咬住 —— 巨幕的地基要打牢。",
)
b.step(
    "叠银幕放映层: 四片白幕整边压住基座墙顶。",
    ["screen_hi_1", "screen_hi_2", "screen_hi_3", "screen_hi_4"],
    highlight=["screen_lo_1"],
    tip="白色的一层才是银幕 —— 放映机的光会打在这上面。",
)
b.step(
    "幕后贴三条黄色斜撑, 幕顶插四面彩旗: 巨幕落成。",
    ["brace_2", "brace_3", "brace_4",
     "bunting_1", "bunting_2", "bunting_3", "bunting_4"],
    highlight=["screen_lo_2", "back_2"],
    tip="幕-撑-地锁成三角, 彩旗骑住幕顶 —— 晚风再大, 巨幕也稳稳站住。",
)
b.step(
    "起放映室底层: 六面蓝墙合环, 墙脚踩住场坪拼缝。",
    ["booth_lo_s_w", "booth_lo_s_e", "booth_lo_n_w",
     "booth_lo_n_e", "booth_lo_w", "booth_lo_e"],
    highlight=["lot_2_0"],
    tip="放映室在场地正南, 和银幕面对面 —— 底层放着电影胶片。",
)
b.step(
    "叠放映室二层: 北面装两扇窗格放映窗, 正对银幕。",
    ["booth_hi_s_w", "booth_hi_s_e", "booth_win_w",
     "booth_win_e", "booth_hi_w", "booth_hi_e"],
    highlight=["booth_lo_n_w"],
    tip="放映机的镜头就从这两扇窗里探出来 —— 高度刚好越过车顶。",
)
b.step(
    "盖放映室长板平顶: 两条短边整边入扣东西墙顶。",
    ["booth_roof"],
    highlight=["booth_win_w"],
    tip="盖上顶, 放映室就是一座结实的两层小塔。",
)
b.step(
    "开进 1 号红车: 轮座车板吸进车位, 驾驶舱盖在车尾。",
    CAR1,
    highlight=["lot_0_1"],
    tip="车板短边就是墙脚线 —— 驾驶舱墙咬住它, 车头甲板朝着银幕。",
)
b.step(
    "开进 2 号绿车: 同样的手法, 停进东侧车位。",
    CAR2,
    highlight=["car1_cab_top"],
    tip="舱顶四边入扣墙顶 —— 每辆车都是一个结实的小盒子。",
)
b.step(
    "开进 3 号橙车: 前排正中的黄金车位。",
    CAR3,
    highlight=["car2_cab_top"],
    tip="三辆车错落排开, 谁也不挡谁 —— 就等电影开场了。",
)
b.step(
    "立入口灯牌、插检票旗、摆场边音响: 今晚满场!",
    ["gate_sign", "gate_flag", "speaker_e", "speaker_w"],
    highlight=["car3_cab_top", "screen_hi_2"],
    tip="音响一响, 灯牌一亮 —— 嘘, 电影马上开始!",
)

b.finalize(
    model_id="drive_in_cinema_01",
    name="星光露天汽车影院",
    name_en="Drive-in Cinema 01",
    description=(
        "只用核心九片型的夜场娱乐场景: 与立体车库的柱-板框架和"
        "出租车的单车特写都不同 —— 这里是'一面巨幕 + 一排观影"
        "车位'的组合: 四格宽两层高的银幕墙靠三条黄色直角斜撑"
        "站稳 (幕-撑-地锁成三角刚性节点), 蓝色放映室两层箱塔"
        "顶着双窗格放映窗正对银幕; 红绿橙三辆轮座小车错落停进"
        "星光车位, 每辆都是'轮座车板 + 单间驾驶舱'的最小车辆"
        "单元, 车头一律朝幕 —— 灯牌亮了, 音响响了, 电影开场!"
    ),
    difficulty=3,
    tags=["城市", "汽车影院", "夜晚", "车轮底座", "娱乐", "进阶"],
    min_pieces=68,
    min_steps=15,
)
