#!/usr/bin/env python3
"""生成模型 data/models/dinosaur_stego_01.json (剑龙)。

第三批模型 ③: 动物世界主题 —— 与霸王龙骨架 (悬挑箱形梁) 完全不同的
恐龙搭法: 剑龙是一只"活着"的立姿动物 —— 四条腿柱托起箱形躯干,
背脊拼缝上交替立起高低两种背板, 尾巴和脖子各用一条 30 度坡道
自然垂到地面: 尾尖翘着骨钉, 龙头正低头啃食地上的蕨丛。

结构总览 (世界单位: 1.0 = 正方形磁力片边长):
  - 公园地台 6x4: 中央步道方板 + 草地长方形                     14 片
  - 四条腿柱: 前后各一对立墙                                     4 片
  - 箱形躯干: 底板 6 + 两侧壁 8 + 胸/臀封板 4 + 背板 8          26 片
  - 背脊: 等腰(高)/等边(矮) 背板沿背缝交替立起                   4 片
  - 尾巴: 尾根板 + 30 度尾坡道 + 尾钉 x2                         4 片
  - 脖子与头: 30 度颈坡道 + 头箱 (地板/三壁/顶/吻尖)             7 片
  - 植被: 蕨丛 2 + 苏铁 2                                        4 片
  合计 63 片, 16 个教程步骤, 5 种磁力片形状。

几何要点:
  - 躯干底板悬在 z=1, 全部重量经四条腿柱传到地面, 底板/侧壁/背板
    围成箱形环, 剪断任何一条铰链线都塌不了;
  - 尾巴与脖子是"接地斜撑": 坡道尾端落地, 悬挑子结构因含接地片
    而免于悬臂预算 —— 这就是大型动物模型收尾巴的正确姿势;
  - 背板底边吸在背脊两排背板的公共拼缝上, 一条缝同时咬住三片。

用法: python3 tools/generate_dinosaur_stego.py  (在 magtile-studio 目录下运行)
"""

from magtile_gen import ModelBuilder, SQ3

b = ModelBuilder()

# =================================================================
# 1. 公园地台 6x4 ([0,6]x[0,4]); 躯干将占 [1,5]x[1,3] 上空
# =================================================================
for x0, y0 in ((1, 1), (4, 1), (1, 2), (4, 2)):     # 腿柱线旁必须是单格方板
    b.flat(f"walk_{x0}{y0}", x0, y0, 0, "yellow")
b.flat("lawn_w1", 0, 1, 0, "green")                 # 西列草地
b.flat("lawn_w2", 0, 2, 0, "green")
b.flat_rect("lawn_c1", 2, 1, 0, "green")            # 躯干正下方草地
b.flat_rect("lawn_c2", 2, 2, 0, "green")
b.flat("lawn_e1", 5, 1, 0, "green")                 # 东列草地
b.flat("lawn_e2", 5, 2, 0, "green")
for row, y0 in (("s", 0), ("n", 3)):                # 南/北排: 方-方-长-方-方
    b.flat(f"lawn_{row}0", 0, y0, 0, "green")
    b.flat(f"lawn_{row}1", 1, y0, 0, "green")
    b.flat_rect(f"lawn_{row}2", 2, y0, 0, "green")
    b.flat(f"lawn_{row}3", 4, y0, 0, "green")
    b.flat(f"lawn_{row}4", 5, y0, 0, "green")

# =================================================================
# 2. 四条腿柱 (z 0..1): 前后各一对, 立在步道方板的边线上
# =================================================================
b.wall_ns("leg_fs", 1, 1, 0, "gray")    # 前左 (南)
b.wall_ns("leg_fn", 1, 3, 0, "gray")    # 前右 (北)
b.wall_ns("leg_rs", 4, 1, 0, "gray")    # 后左
b.wall_ns("leg_rn", 4, 3, 0, "gray")    # 后右

# =================================================================
# 3. 箱形躯干: 底板 (z=1) -> 侧壁 (z 1..2) -> 胸/臀封板 -> 背板 (z=2)
# =================================================================
b.flat("belly_fs", 1, 1, 1, "green")
b.flat("belly_fn", 1, 2, 1, "green")
b.flat_rect("belly_cs", 2, 1, 1, "green")
b.flat_rect("belly_cn", 2, 2, 1, "green")
b.flat("belly_rs", 4, 1, 1, "green")
b.flat("belly_rn", 4, 2, 1, "green")
for i in range(4):
    b.wall_ns(f"flank_s{i}", 1 + i, 1, 1, "green")  # 南侧壁
    b.wall_ns(f"flank_n{i}", 1 + i, 3, 1, "green")  # 北侧壁
b.wall_ew("chest_s", 1, 1, 1, "green")              # 胸口封板
b.wall_ew("chest_n", 1, 2, 1, "green")
b.wall_ew("rump_s", 5, 1, 1, "green")               # 臀部封板
b.wall_ew("rump_n", 5, 2, 1, "green")
for i in range(4):
    b.flat(f"back_s{i}", 1 + i, 1, 2, "green")      # 背板南排
    b.flat(f"back_n{i}", 1 + i, 2, 2, "green")      # 背板北排

# =================================================================
# 4. 背脊: 高 (等腰) 低 (等边) 背板沿 y=2 背缝交替立起
# =================================================================
b.crest_ns("plate_0", 1, 2, 2, "orange")            # 矮板
b.spire_ns("plate_1", 2, 2, 2, "red")               # 高板
b.spire_ns("plate_2", 3, 2, 2, "red")
b.crest_ns("plate_3", 4, 2, 2, "orange")

# =================================================================
# 5. 尾巴: 尾根板悬挑 -> 30 度尾坡道落地 -> 尾钉
# =================================================================
b.flat("tail_root", 5, 1, 1, "green")
b.ramp("tail_ramp", "+x", 6.0, 1, 1.0, "green")     # 尾尖落在 x=7.73
b.crest_ew("tail_spike_hi", 6, 1, 1, "yellow")      # 尾根骨钉
b.crest_ew("tail_spike_lo", 6 + SQ3, 1, 0, "yellow")  # 尾尖骨钉

# =================================================================
# 6. 脖子与头: 30 度颈坡道落地, 头箱正低头啃蕨丛
# =================================================================
b.ramp("neck_ramp", "-x", 1.0, 1, 1.0, "green")     # 颈坡道, 头端 x=-0.73
b.flat("head_floor", -1 - SQ3 + 1, 1, 0, "green")   # 头箱地板 [-1.73,-0.73]
b.wall_ns("head_s", -1 - SQ3 + 1, 1, 0, "green")
b.wall_ns("head_n", -1 - SQ3 + 1, 2, 0, "green")
b.wall_ew("head_w", -1 - SQ3 + 1, 1, 0, "green")
b.flat("head_top", -1 - SQ3 + 1, 1, 1, "green")
b.crest_ew("head_horn", -1 - SQ3 + 1, 1, 1, "orange")  # 头顶小角

# =================================================================
# 7. 植被: 蕨丛与苏铁
# =================================================================
b.crest_ns("fern_w", 0, 1, 0, "green")
b.crest_ns("fern_e", 5, 1, 0, "green")
b.spire_ns("cycad_w", 0, 3, 0, "purple")
b.spire_ns("cycad_e", 5, 3, 0, "purple")

# =================================================================
# 教程步骤 (16 步)
# =================================================================
b.step(
    "铺中央地台: 4 片黄色步道方板放在四条腿柱将要立起的位置旁, "
    "中间用长方形、东西两侧用方板草地补齐。",
    ["walk_11", "walk_41", "walk_12", "walk_42",
     "lawn_c1", "lawn_c2", "lawn_w1", "lawn_w2", "lawn_e1", "lawn_e2"],
    tip="腿柱线两旁必须是单格方板 —— 立墙的底边只吸等长的整边。",
)
b.step(
    "铺南北草地: 南北各按 方-方-长-方-方 铺一排, 地台合拢成 6x4。",
    ["lawn_s0", "lawn_s1", "lawn_s2", "lawn_s3", "lawn_s4",
     "lawn_n0", "lawn_n1", "lawn_n2", "lawn_n3", "lawn_n4"],
    highlight=["lawn_w1", "lawn_e1"],
    tip="长方形只与等长的长边吸合, 方板只与方板边吸合 —— 对缝铺。",
)
b.step(
    "立四条腿柱: 4 片灰色正方形立在步道方板的边线上, 前后各一对。",
    ["leg_fs", "leg_fn", "leg_rs", "leg_rn"],
    highlight=["walk_11", "walk_42"],
    tip="腿柱底边整边吸住地台拼缝 —— 剑龙的四条大柱子腿。",
)
b.step(
    "架躯干底板: 6 片绿色板在 z=1 高度铺满 4x2 的肚皮, "
    "四角先吸住腿柱顶边, 再向中间合拢。",
    ["belly_fs", "belly_fn", "belly_rs", "belly_rn",
     "belly_cs", "belly_cn"],
    highlight=["leg_fs", "leg_rn"],
    tip="先放四角四片 (各骑一条腿柱), 中间两根长方形最后合拢。",
)
b.step(
    "立南侧腹壁: 4 片绿色正方形沿底板南沿立起。",
    ["flank_s0", "flank_s1", "flank_s2", "flank_s3"],
    highlight=["belly_fs", "belly_rs"],
    tip="侧壁底边与腿柱顶边共线 —— 一条铰链线双重受力。",
)
b.step(
    "立北侧腹壁: 4 片绿色正方形沿底板北沿立起。",
    ["flank_n0", "flank_n1", "flank_n2", "flank_n3"],
    highlight=["belly_fn", "belly_rn"],
    tip="两侧腹壁像船帮一样夹住肚皮。",
)
b.step(
    "封胸口与臀部: 前后各 2 片绿色正方形把躯干围成箱形。",
    ["chest_s", "chest_n", "rump_s", "rump_n"],
    highlight=["flank_s0", "flank_n3"],
    tip="封板竖边与侧壁竖边互吸, 躯干从此成为一个刚性箱体。",
)
b.step(
    "盖背板南排: 4 片绿色正方形盖住躯干南半个背。",
    ["back_s0", "back_s1", "back_s2", "back_s3"],
    highlight=["flank_s0", "chest_s"],
    tip="背板边吸侧壁顶边, 箱形环在背上合龙。",
)
b.step(
    "盖背板北排: 4 片绿色正方形, 背中央留出一条笔直的拼缝。",
    ["back_n0", "back_n1", "back_n2", "back_n3"],
    highlight=["back_s0"],
    tip="这条 y=2 的背缝就是下一步背板的立足之地。",
)
b.step(
    "立背脊板: 沿背缝交替立起 矮-高-高-矮 4 片背板 (橙色等边 + "
    "红色等腰), 剑龙的招牌轮廓出现了!",
    ["plate_0", "plate_1", "plate_2", "plate_3"],
    highlight=["back_s1", "back_n2"],
    tip="每片背板的底边同时吸住背缝两侧的两片背板。",
)
b.step(
    "甩尾巴: 尾根板从臀部向东悬挑一格, 30 度尾坡道从尾根滑到地面。",
    ["tail_root", "tail_ramp"],
    highlight=["rump_s", "belly_rs"],
    tip="坡道尾端落地 —— 尾巴自己就是一根接地斜撑, 稳得很。",
)
b.step(
    "插尾钉: 2 片黄色等边三角形分别立在尾根拼缝与尾尖落地边上。",
    ["tail_spike_hi", "tail_spike_lo"],
    highlight=["tail_ramp"],
    tip="尾尖的骨钉学名叫 thagomizer —— 剑龙的防身武器。",
)
b.step(
    "垂脖子: 30 度颈坡道从胸口滑向地面, 头箱地板接住坡道尾端。",
    ["neck_ramp", "head_floor"],
    highlight=["chest_s", "belly_fs"],
    tip="剑龙脖子短、头朝下 —— 它正要低头吃地上的蕨类。",
)
b.step(
    "围头箱: 3 片绿色正方形沿头箱地板立起 (南/北/西三面)。",
    ["head_s", "head_n", "head_w"],
    highlight=["head_floor"],
    tip="头箱东面不封 —— 那里是连着脖子的咽喉。",
)
b.step(
    "盖头顶并立小角: 1 片绿色板盖住头箱, 1 片橙色等边三角形立在"
    "头顶西沿做角冠。",
    ["head_top", "head_horn"],
    highlight=["head_s", "head_n"],
    tip="盖板四边吸住三面头壁与颈坡道方向, 头箱自锁。",
)
b.step(
    "种蕨丛: 2 片绿色等边三角形立在南侧草缝上 —— 一丛正对龙头。",
    ["fern_w", "fern_e"],
    highlight=["head_floor"],
    tip="西边那丛蕨就是剑龙的午餐。",
)
b.step(
    "种苏铁: 2 片紫色等腰三角形立在北侧草缝上 —— 侏罗纪公园开园!",
    ["cycad_w", "cycad_e"],
    highlight=["fern_w"],
    tip="从侧面看: 高低背板、垂尾、低头, 正是教科书里的剑龙剪影。",
)

b.finalize(
    model_id="dinosaur_stego_01",
    name="低头觅食的剑龙",
    name_en="Stegosaurus 01",
    description=(
        "动物世界主题: 与霸王龙化石骨架完全不同的活体恐龙搭法 —— "
        "四条腿柱托起悬空箱形躯干 (底板/侧壁/封板/背板锁成刚性环), "
        "背缝上交替立起 矮-高-高-矮 的背脊板; 尾巴与脖子各用一条 "
        "30 度坡道自然垂到地面, 坡道尾端落地成为接地斜撑, 尾尖翘着"
        "骨钉、龙头正低头啃食蕨丛 —— 大型动物模型的收尾新技法。"
    ),
    difficulty=3,
    tags=["恐龙", "剑龙", "动物世界", "腿柱箱体", "接地斜撑"],
    min_pieces=60,
    min_steps=16,
)
