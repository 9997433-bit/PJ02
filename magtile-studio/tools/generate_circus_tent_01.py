#!/usr/bin/env python3
"""生成模型 data/models/circus_tent_01.json (马戏团大帐篷)。

内容批 H 模型 3/4: 全库第一座马戏团。游乐园主题此前只有旋转
木马 (圈层砌法转台)、摩天轮 (桁架)、过山车 (轨道) —— 还没有
一座"演出建筑"。与它们全部刻意区分, 本作的结构签名是
"条纹大顶再起一节": 4x3 红白条纹墙环托起十二片满铺大顶
(周圈盖板边边直压墙顶, 中央两片邻板共面环撑), 大顶正中再起
一节 2x1 天窗箱环, 二段顶心拼缝上黄色团旗瘦高尖直上 4.0
全场制高 —— 大帐篷的经典轮廓"塔在顶上"就此立起; 南面两扇
黄色门框方并排成双开检票大门, 门顶四面彩旗骑满大顶南沿,
红毯直铺到场心; 场外紫色售票亭戴四坡锥顶, 小丑骑红毯拼缝
迎宾 —— 马戏团进城啦!

结构总览 (世界单位: 1.0 = 正方形磁力片边长, 大门朝南):
  - 广场地面 (x [0,6], y [0,5]): 方板 16 + 长板 6            22 片
  - 大帐篷墙环 (x [1,5], y [1,4], z 0..1): 方墙 12 + 门框 2   14 片
  - 满铺大顶 (z=1): 方板 x12                                  12 片
  - 门楣彩旗 x4 (等边骑大顶南沿)                                4 片
  - 天窗箱环 (x [2,4], y [2,3], z 1..2): 方墙 x6               6 片
  - 二段顶 x2 + 团旗 x1 (瘦高尖) + 顶旗 x2 (等边)              5 片
  - 售票亭 (x [5,6], y [0,1]): 方墙 3 + 窗格 1 + 四坡锥顶 4    8 片
  - 小丑 x1 + 气球 x1 (骑沿口)                                  2 片
  合计 73 片, 13 个教程步骤, 5 种磁力片形状 (全部 CORE-9 之内)。

物理规则要点 (validate 常规 + strict 双档零警告 + jitter 全绿):
  - 墙环墙脚全部踩地面拼缝 (墙脚下全单位方板), 四角竖边互咬闭环;
  - 大顶十二片全单位方板: 周圈十片每片至少一条边直压墙顶,
    中央两片由四邻共面环撑 (雪人身盖同款技法);
  - 天窗箱环墙脚全部踩大顶拼缝, 二段顶两片边边入扣箱环墙顶;
  - 售票亭四墙闭环 + 等边四坡锥顶四棱自锁 (蜂箱同款);
  - 彩旗/团旗/小丑/气球剪断任何一条装饰连接最多失联 1 片 (< 3),
    R8 单点失效通过。

用法: python3 tools/generate_circus_tent_01.py  (在 magtile-studio 目录下运行)
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from magtile_gen import ModelBuilder  # noqa: E402

b = ModelBuilder()

PLAZA = "green"      # 草坪广场
CARPET = "red"       # 入场红毯
RING = "yellow"      # 场心沙圈
TENT_A = "red"       # 帐篷条纹 (红)
TENT_B = "clear"     # 帐篷条纹 (白)
GATE = "yellow"      # 检票大门
CANVAS = "red"       # 大顶帆布
FLAG_A = "yellow"    # 彩旗
FLAG_B = "cyan"
BANNER = "yellow"    # 团旗
BOOTH = "purple"     # 售票亭
TICKET = "cyan"      # 售票窗
CLOWN = "purple"     # 小丑
BALLOON = "pink"     # 气球


def wall_ns_t(tid, tile_type, x0, y, z0, color):
    b.add(tid, tile_type, (x0 + 0.5, y, z0 + 0.5), (90, 0, 0), color)


def wall_ew_t(tid, tile_type, x, y0, z0, color):
    b.add(tid, tile_type, (x, y0 + 0.5, z0 + 0.5), (90, 0, 90), color)


# =================================================================
# 1. 广场地面 (x [0,6], y [0,5])
# =================================================================
# 门前行 (y [0,1]): 红毯对准大门, 售票亭底格是单位方板
b.flat_rect("plaza_0_0", 0, 0, 0.0, PLAZA)
b.flat("carpet_w", 2, 0, 0.0, CARPET)
b.flat("carpet_e", 3, 0, 0.0, CARPET)
b.flat("plaza_4_0", 4, 0, 0.0, PLAZA)
b.flat("booth_base", 5, 0, 0.0, BOOTH)
# 场内南行 (y [1,2]): 全单位方板, 场心红毯续进场
b.flat("ring_1_1", 1, 1, 0.0, RING)
b.flat("ring_2_1", 2, 1, 0.0, CARPET)
b.flat("ring_3_1", 3, 1, 0.0, CARPET)
b.flat("ring_4_1", 4, 1, 0.0, RING)
# 场内中行 (y [2,3]): 两条长板, 短边吸边墙脚线
b.flat_rect("ring_1_2", 1, 2, 0.0, RING)
b.flat_rect("ring_3_2", 3, 2, 0.0, RING)
# 场内北行 (y [3,4]): 全单位方板
b.flat("ring_1_3", 1, 3, 0.0, RING)
b.flat("ring_2_3", 2, 3, 0.0, RING)
b.flat("ring_3_3", 3, 3, 0.0, RING)
b.flat("ring_4_3", 4, 3, 0.0, RING)
# 场外西/东侧翼 (y [1,4])
b.flat_rect("plaza_0_1", 0, 1, 0.0, PLAZA, axis="y")
b.flat("plaza_0_3", 0, 3, 0.0, PLAZA)
b.flat_rect("plaza_5_1", 5, 1, 0.0, PLAZA, axis="y")
b.flat("plaza_5_3", 5, 3, 0.0, PLAZA)
# 场后行 (y [4,5])
b.flat_rect("plaza_0_4", 0, 4, 0.0, PLAZA)
b.flat_rect("plaza_2_4", 2, 4, 0.0, PLAZA)
b.flat_rect("plaza_4_4", 4, 4, 0.0, PLAZA)

# =================================================================
# 2. 大帐篷墙环 (x [1,5], y [1,4], z 0..1): 红白条纹 + 双开大门
# =================================================================
b.wall_ns("tent_s_w", 1, 1.0, 0, TENT_A)
wall_ns_t("gate_w", "door_frame", 2, 1.0, 0, GATE)
wall_ns_t("gate_e", "door_frame", 3, 1.0, 0, GATE)
b.wall_ns("tent_s_e", 4, 1.0, 0, TENT_A)
b.wall_ns("tent_n_1", 1, 4.0, 0, TENT_A)
b.wall_ns("tent_n_2", 2, 4.0, 0, TENT_B)
b.wall_ns("tent_n_3", 3, 4.0, 0, TENT_B)
b.wall_ns("tent_n_4", 4, 4.0, 0, TENT_A)
b.wall_ew("tent_w_s", 1.0, 1, 0, TENT_B)
b.wall_ew("tent_w_m", 1.0, 2, 0, TENT_A)
b.wall_ew("tent_w_n", 1.0, 3, 0, TENT_B)
b.wall_ew("tent_e_s", 5.0, 1, 0, TENT_B)
b.wall_ew("tent_e_m", 5.0, 2, 0, TENT_A)
b.wall_ew("tent_e_n", 5.0, 3, 0, TENT_B)

# =================================================================
# 3. 满铺大顶 (z=1): 周圈直压墙顶, 中央两片邻板共面环撑
# =================================================================
b.flat("roof_1_1", 1, 1, 1.0, CANVAS)
b.flat("roof_2_1", 2, 1, 1.0, CANVAS)
b.flat("roof_3_1", 3, 1, 1.0, CANVAS)
b.flat("roof_4_1", 4, 1, 1.0, CANVAS)
b.flat("roof_1_2", 1, 2, 1.0, CANVAS)
b.flat("roof_2_2", 2, 2, 1.0, CANVAS)   # 中央片: 四邻共面环撑
b.flat("roof_3_2", 3, 2, 1.0, CANVAS)   # 中央片: 四邻共面环撑
b.flat("roof_4_2", 4, 2, 1.0, CANVAS)
b.flat("roof_1_3", 1, 3, 1.0, CANVAS)
b.flat("roof_2_3", 2, 3, 1.0, CANVAS)
b.flat("roof_3_3", 3, 3, 1.0, CANVAS)
b.flat("roof_4_3", 4, 3, 1.0, CANVAS)

# =================================================================
# 4. 门楣彩旗 x4: 骑大顶南沿 (盖板沿边 + 墙顶边双路受力)
# =================================================================
b.crest_ns("flag_1", 1, 1.0, 1.0, FLAG_A)
b.crest_ns("flag_2", 2, 1.0, 1.0, FLAG_B)
b.crest_ns("flag_3", 3, 1.0, 1.0, FLAG_A)
b.crest_ns("flag_4", 4, 1.0, 1.0, FLAG_B)

# =================================================================
# 5. 天窗箱环 (x [2,4], y [2,3], z 1..2) + 二段顶 + 团旗 + 顶旗
# =================================================================
b.wall_ns("sky_s_w", 2, 2.0, 1, TENT_A)
b.wall_ns("sky_s_e", 3, 2.0, 1, TENT_B)
b.wall_ns("sky_n_w", 2, 3.0, 1, TENT_B)
b.wall_ns("sky_n_e", 3, 3.0, 1, TENT_A)
b.wall_ew("sky_w", 2.0, 2, 1, TENT_A)
b.wall_ew("sky_e", 4.0, 2, 1, TENT_A)
b.flat("crown_w", 2, 2, 2.0, CANVAS)
b.flat("crown_e", 3, 2, 2.0, CANVAS)
b.spire_ew("banner", 3.0, 2, 2.0, BANNER)   # 骑二段顶心缝, 尖 4.0 全场制高
b.crest_ns("crown_flag_s", 2, 2.0, 2.0, FLAG_B)
b.crest_ns("crown_flag_n", 3, 3.0, 2.0, FLAG_B)

# =================================================================
# 6. 售票亭 (x [5,6], y [0,1], z 0..1): 售票窗朝西对红毯
# =================================================================
wall_ew_t("booth_w", "window_square", 5.0, 0, 0, TICKET)
b.wall_ew("booth_e", 6.0, 0, 0, BOOTH)
b.wall_ns("booth_s", 5, 0.0, 0, BOOTH)
b.wall_ns("booth_n", 5, 1.0, 0, BOOTH)
b.hat4("booth_roof", 5, 0, 1.0, BOOTH, shape="equilateral_triangle")

# =================================================================
# 7. 小丑 (骑红毯拼缝) + 气球 (骑广场沿口)
# =================================================================
b.crest_ew("clown", 3.0, 0, 0.0, CLOWN)
b.spire_ns("balloon", 4, 0.0, 0.0, BALLOON)

# =================================================================
# 教程步骤 (13 步)
# =================================================================
b.step(
    "铺门前行: 两片红毯居中对准将来的大门, 东端紫格是售票亭底。",
    ["plaza_0_0", "carpet_w", "carpet_e", "plaza_4_0", "booth_base"],
    tip="马戏团进城啦! 先把门前广场铺出来, 红毯要正对大门。",
)
b.step(
    "铺场内地坪: 南行全单位方板, 红毯一直铺进场心。",
    ["ring_1_1", "ring_2_1", "ring_3_1", "ring_4_1",
     "ring_1_2", "ring_3_2"],
    highlight=["carpet_w"],
    tip="墙脚要踩的行全用单位方板 —— 墙底边要和方板边等长吸合。",
)
b.step(
    "铺场内北行与东西侧翼: 帐篷的四圈墙脚全部有了着落。",
    ["ring_1_3", "ring_2_3", "ring_3_3", "ring_4_3",
     "plaza_0_1", "plaza_0_3", "plaza_5_1", "plaza_5_3"],
    highlight=["ring_1_2"],
    tip="行行等边互吸 —— 黄色沙圈就是马戏表演的场心。",
)
b.step(
    "铺场后行收口: 三条草坪长板, 广场铺满。",
    ["plaza_0_4", "plaza_2_4", "plaza_4_4"],
    highlight=["ring_2_3"],
    tip="观众们已经在广场上排起队了。",
)
b.step(
    "立帐篷南墙与西墙: 两扇黄色门框方并排, 就是双开检票大门。",
    ["tent_s_w", "gate_w", "gate_e", "tent_s_e",
     "tent_w_s", "tent_w_m", "tent_w_n"],
    highlight=["ring_2_1"],
    tip="红白条纹墙一片隔一片 —— 这就是马戏团的颜色。",
)
b.step(
    "合帐篷北墙与东墙: 十四片墙环四角竖边互咬闭环。",
    ["tent_n_1", "tent_n_2", "tent_n_3", "tent_n_4",
     "tent_e_s", "tent_e_m", "tent_e_n"],
    highlight=["tent_s_w"],
    tip="闭环墙才站得稳 —— 大帐篷的圆场围合完成。",
)
b.step(
    "满铺大顶: 十二片红帆布盖板, 周圈直压墙顶, 中央靠四邻环撑。",
    ["roof_1_1", "roof_2_1", "roof_3_1", "roof_4_1",
     "roof_1_2", "roof_2_2", "roof_3_2", "roof_4_2",
     "roof_1_3", "roof_2_3", "roof_3_3", "roof_4_3"],
    highlight=["tent_s_w"],
    tip="先铺周圈再合中央 —— 中央两片的四条边都有邻板可吸。",
)
b.step(
    "挂门楣彩旗: 四面彩旗骑满大顶南沿, 底边双路受力。",
    ["flag_1", "flag_2", "flag_3", "flag_4"],
    highlight=["roof_1_1"],
    tip="彩旗同时咬住大顶沿边和墙顶边 —— 开演的信号挂出来了。",
)
b.step(
    "起天窗箱环: 六片条纹墙踩住大顶正中的拼缝, 再围一圈。",
    ["sky_s_w", "sky_s_e", "sky_n_w", "sky_n_e", "sky_w", "sky_e"],
    highlight=["roof_2_2"],
    tip="大顶再起一节 —— 大帐篷的经典轮廓就靠这个二段顶。",
)
b.step(
    "封二段顶, 升团旗: 顶心拼缝上黄色瘦高尖直上全场最高点。",
    ["crown_w", "crown_e", "banner", "crown_flag_s", "crown_flag_n"],
    highlight=["sky_s_w"],
    tip="团旗一升, 十里八乡都看得见 —— 今晚有大戏!",
)
b.step(
    "砌售票亭: 青色窗格朝西对着红毯, 就是售票窗口。",
    ["booth_w", "booth_e", "booth_s", "booth_n"],
    highlight=["booth_base"],
    tip="四片墙四角互咬围成小亭 —— 买票请从红毯这边排队。",
)
b.step(
    "戴售票亭锥顶: 四片紫色等边三角斜棱互吸, 自锁成锥。",
    ["booth_roof_s", "booth_roof_e", "booth_roof_n", "booth_roof_w"],
    highlight=["booth_w"],
    tip="小亭子也要打扮得漂漂亮亮 —— 四条底边整边吸住墙顶。",
)
b.step(
    "小丑迎宾, 气球起飞: 马戏团开演!",
    ["clown", "balloon"],
    highlight=["gate_w", "banner"],
    tip="小丑骑着红毯拼缝翻跟头 —— 女士们先生们, 欢迎入场!",
)

b.finalize(
    model_id="circus_tent_01",
    name="马戏团大帐篷",
    name_en="Circus Big Top 01",
    description=(
        "只用核心九片型的马戏团首秀: 游乐园主题里第一座'演出建筑', "
        "与旋转木马的圈层转台和摩天轮的桁架都不同 —— 结构签名是"
        "'条纹大顶再起一节': 4x3 红白条纹墙环托起十二片满铺大顶 "
        "(周圈直压墙顶, 中央两片四邻共面环撑), 大顶正中再起一节 "
        "2x1 天窗箱环, 黄色团旗瘦高尖从二段顶心拼缝直上全场制高; "
        "南面两扇黄色门框方并排成双开检票大门, 门顶四面彩旗骑满"
        "大顶南沿, 红毯从广场一直铺进场心沙圈; 场外紫色售票亭戴"
        "四坡锥顶, 售票窗正对红毯, 小丑骑缝翻跟头, 粉气球升空 —— "
        "女士们先生们, 马戏团开演啦!"
    ),
    difficulty=3,
    tags=["游乐园", "马戏团", "大帐篷", "演出", "进阶"],
    min_pieces=73,
    min_steps=13,
)
