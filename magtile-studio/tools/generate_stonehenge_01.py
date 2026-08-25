#!/usr/bin/env python3
"""生成模型 data/models/stonehenge_01.json (草原巨石阵)。

内容批 F 模型 3/4: 全库第一处史前遗迹 —— 古代建筑此前只有
temple_greek (希腊神庙) / roman_aqueduct (罗马水道桥), 都是
"连续柱廊"逻辑, 还没有一组"彼此分立、围成环阵"的纪念性结构。
结构签名是"巨石门过梁悬空搭桥": 南北两座巨石门各由两座 2 层
箱楼石柱夹出一格真门洞, 门洞上方的门楣墙不落地 —— 两条竖边
分别咬住左右石柱的墙竖缝 (救援总部门楣同款受力), 门楣墙顶
再托一块悬空桥板, 桥板四边同时吸双侧门楣墙顶与两侧柱顶盖板,
过梁三件像搭桥一样把两座石柱锁成一座门; 东西各立一座紫晶尖
独石 (四坡锥自锁), 中央祭坛压阵, 五组巨石围成十字环阵 —— 与
triumphal_arch (单体凯旋门) / medieval_gate (城墙门楼) 的
"门附着于建筑"逻辑刻意区分: 这里的门孤零零立在草原上。

结构总览 (世界单位: 1.0 = 正方形磁力片边长, 场地 7x7):
  - 草原与石板场地 (x [0,7], y [0,7]): 巨石脚下全单位方板     25 片
  - 巨石门 x2 (南 y [1,2] / 北 y [5,6]): 每座 = 两座 2 层
    箱楼石柱 (8 墙 x2) + 门楣墙 x2 + 柱顶盖板 x2 + 悬空桥板   42 片
  - 独石 x2 (西 x [1,2] / 东 x [5,6], y [3,4]): 一层箱楼
    + 紫晶四坡锥尖                                            16 片
  - 中央祭坛 (x [3,4], y [3,4]): 四墙 + 金顶板 + 日晷三角      6 片
  - 小游客 x2: 骑草缝三角                                      2 片
  合计 91 片, 19 个教程步骤, 3 种磁力片形状 (全部 CORE-9 之内)。

物理规则要点 (validate 常规 + strict 双档零警告 + jitter 全绿):
  - 石柱是 1x1 闭环箱楼摞两层, 四角竖边互咬, 荷载沿墙直下;
  - 门楣墙 (z 1..2) 不接地, 两条竖边分别整边咬住左右石柱上层
    墙的竖缝, 前后两面门楣对称受力;
  - 悬空桥板四边全部有可吸整边: 两长边吸前后门楣墙顶, 两短边
    吸左右柱顶盖板 —— 四路受力, 抖动 50 轮不动摇;
  - 独石锥尖四条斜棱两两互吸自锁 (投石机石弹金字塔同款);
  - 地坪拼缝纪律: 全部墙脚与骑缝三角脚下都是单位方板/短边对齐。

用法: python3 tools/generate_stonehenge_01.py  (在 magtile-studio 目录下运行)
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from magtile_gen import ModelBuilder  # noqa: E402

b = ModelBuilder()

GRASS = "green"     # 草原
PAD = "gray"        # 巨石脚下石板
STONE = "gray"      # 巨石
LINTEL = "gray"     # 门楣墙
BRIDGE = "yellow"   # 悬空桥板 (夏至日光斑)
TIP = "purple"      # 独石紫晶尖
ALTAR = "orange"    # 祭坛
ALTAR_CAP = "yellow"  # 祭坛金顶
DIAL = "red"        # 日晷三角
KID_S = "blue"      # 小游客 (南)
KID_N = "pink"      # 小游客 (北)


def megalith_gate(prefix, y0):
    """巨石门: 石柱 x [2,3] 与 [4,5], 门洞 x [3,4], 进深 y [y0,y0+1]。"""
    for z in (0, 1):
        # 西柱 (x [2,3]) 闭环箱楼
        b.wall_ew(f"{prefix}_w_w{z}", 2.0, y0, z, STONE)
        b.wall_ew(f"{prefix}_w_e{z}", 3.0, y0, z, STONE)
        b.wall_ns(f"{prefix}_w_s{z}", 2, float(y0), z, STONE)
        b.wall_ns(f"{prefix}_w_n{z}", 2, float(y0 + 1), z, STONE)
        # 东柱 (x [4,5]) 闭环箱楼
        b.wall_ew(f"{prefix}_e_w{z}", 4.0, y0, z, STONE)
        b.wall_ew(f"{prefix}_e_e{z}", 5.0, y0, z, STONE)
        b.wall_ns(f"{prefix}_e_s{z}", 4, float(y0), z, STONE)
        b.wall_ns(f"{prefix}_e_n{z}", 4, float(y0 + 1), z, STONE)
    # 门楣墙 (z 1..2): 前后两面, 竖边咬住左右石柱上层墙
    b.wall_ns(f"{prefix}_lin_s", 3, float(y0), 1, LINTEL)
    b.wall_ns(f"{prefix}_lin_n", 3, float(y0 + 1), 1, LINTEL)
    # 柱顶盖板 + 悬空桥板
    b.flat(f"{prefix}_cap_w", 2, y0, 2.0, STONE)
    b.flat(f"{prefix}_cap_e", 4, y0, 2.0, STONE)
    b.flat(f"{prefix}_bridge", 3, y0, 2.0, BRIDGE)


def monolith(prefix, x0):
    """独石: 一层箱楼 + 紫晶四坡锥尖, 占位 x [x0,x0+1], y [3,4]。"""
    b.wall_ew(f"{prefix}_w", float(x0), 3, 0, STONE)
    b.wall_ew(f"{prefix}_e", float(x0 + 1), 3, 0, STONE)
    b.wall_ns(f"{prefix}_s", x0, 3.0, 0, STONE)
    b.wall_ns(f"{prefix}_n", x0, 4.0, 0, STONE)
    return b.hat4(f"{prefix}_tip", x0, 3, 1.0, TIP,
                  shape="equilateral_triangle")


# =================================================================
# 1. 场地地坪 (x [0,7], y [0,7])
# =================================================================
# 南门石板行 (y [1,2]): 五片单位方板, 石柱脚全踩拼缝
for x in range(1, 6):
    b.flat(f"gs_{x}", x, 1, 0.0, PAD)
# 北门石板行 (y [5,6])
for x in range(1, 6):
    b.flat(f"gn_{x}", x, 5, 0.0, PAD)
# 中轴行 (y [3,4]): 独石脚 + 祭坛脚 + 石板小径
b.flat("gm_1", 1, 3, 0.0, PAD)
b.flat("gm_2", 2, 3, 0.0, PAD)
b.flat("gm_3", 3, 3, 0.0, PAD)
b.flat("gm_4", 4, 3, 0.0, PAD)
b.flat("gm_5", 5, 3, 0.0, PAD)
# 连接行 (y [2,3] 与 y [4,5]): 单位方板把三条石板带连成一体
b.flat("gc_s2", 2, 2, 0.0, GRASS)
b.flat("gc_s3", 3, 2, 0.0, GRASS)
b.flat("gc_n3", 3, 4, 0.0, GRASS)
b.flat("gc_n4", 4, 4, 0.0, GRASS)
# 南北草缘行 (y [0,1] 与 y [6,7])
b.flat_rect("ge_s_w", 1, 0, 0.0, GRASS)
b.flat_rect("ge_s_e", 3, 0, 0.0, GRASS)
b.flat("ge_s_5", 5, 0, 0.0, GRASS)
b.flat_rect("ge_n_w", 1, 6, 0.0, GRASS)
b.flat_rect("ge_n_e", 3, 6, 0.0, GRASS)
b.flat("ge_n_5", 5, 6, 0.0, GRASS)

# =================================================================
# 2. 南巨石门 + 北巨石门
# =================================================================
megalith_gate("s", 1)
megalith_gate("n", 5)

# =================================================================
# 3. 西独石 + 东独石
# =================================================================
W_TIP = monolith("mw", 1)
E_TIP = monolith("me", 5)

# =================================================================
# 4. 中央祭坛 + 日晷三角
# =================================================================
b.wall_ew("alt_w", 3.0, 3, 0, ALTAR)
b.wall_ew("alt_e", 4.0, 3, 0, ALTAR)
b.wall_ns("alt_s", 3, 3.0, 0, ALTAR)
b.wall_ns("alt_n", 3, 4.0, 0, ALTAR)
b.flat("alt_cap", 3, 3, 1.0, ALTAR_CAP)
b.crest_ns("dial", 3, 4.0, 1.0, DIAL)   # 日晷三角骑金顶北沿

# =================================================================
# 5. 小游客 x2: 骑草缘拼缝
# =================================================================
b.crest_ew("kid_s", 3.0, 0, 0.0, KID_S)
b.crest_ew("kid_n", 3.0, 6, 0.0, KID_N)

# =================================================================
# 教程步骤 (19 步)
# =================================================================
b.step(
    "铺南门石板行: 五片灰方板一字排开, 南巨石门的柱脚全踩这行。",
    [f"gs_{x}" for x in range(1, 6)],
    tip="草原考古营开工! 巨石脚下必须是单位方板。",
)
b.step(
    "从南向北铺中轴: 两片草坪方板接住南石板行, 再铺独石与祭坛的脚位。",
    ["gc_s2", "gc_s3", "gm_1", "gm_2", "gm_3", "gm_4", "gm_5"],
    highlight=["gs_2", "gs_3"],
    tip="草坪方板上下对齐整边互吸 —— 场地一路向北长过去。",
)
b.step(
    "接着铺到北门: 两片草坪方板 + 北门石板行五片。",
    ["gc_n3", "gc_n4", "gn_1", "gn_2", "gn_3", "gn_4", "gn_5"],
    highlight=["gm_3", "gm_4"],
    tip="南北两座门遥遥相对 —— 三条石板带连成一整片场地。",
)
b.step(
    "铺南北草缘收口: 长板加方板围出场地边缘。",
    ["ge_s_5", "ge_s_e", "ge_s_w", "ge_n_5", "ge_n_e", "ge_n_w"],
    highlight=["gs_5", "gn_5"],
    tip="先放角上的方板再接长板, 短边对整边吸合 —— 环阵草原就位。",
)
b.step(
    "砌南门西柱一层: 四片石墙围成 1x1 闭环。",
    ["s_w_w0", "s_w_e0", "s_w_s0", "s_w_n0"],
    highlight=["gs_2"],
    tip="闭环箱楼四角竖边互咬 —— 巨石柱从第一层就稳如泰山。",
)
b.step(
    "砌南门东柱一层: 隔一格门洞, 再围一座闭环石柱。",
    ["s_e_w0", "s_e_e0", "s_e_s0", "s_e_n0"],
    highlight=["gs_4"],
    tip="中间空出的一格就是门洞 —— 人可以从巨石门下走过!",
)
b.step(
    "两柱同步长到二层: 底边与一层墙顶整边共线吸合。",
    ["s_w_w1", "s_w_e1", "s_w_s1", "s_w_n1",
     "s_e_w1", "s_e_e1", "s_e_s1", "s_e_n1"],
    highlight=["s_w_s0"],
    tip="左右石柱一起长高, 门洞也跟着升到两层。",
)
b.step(
    "挂南门门楣墙: 前后两面墙悬在门洞上方, 竖边咬住左右石柱。",
    ["s_lin_s", "s_lin_n"],
    highlight=["s_w_e1", "s_e_w1"],
    tip="门楣不落地 —— 两条竖边整边咬住石柱墙缝, 悬空也牢固。",
)
b.step(
    "南门封顶搭桥: 两块柱顶盖板 + 一块金色桥板压住门楣。",
    ["s_cap_w", "s_cap_e", "s_bridge"],
    highlight=["s_lin_s"],
    tip="桥板四边全有整边可吸 —— 过梁一压, 两座石柱锁成一座门!",
)
b.step(
    "砌北门西柱一层: 换到北边, 再围一座闭环石柱。",
    ["n_w_w0", "n_w_e0", "n_w_s0", "n_w_n0"],
    highlight=["gn_2"],
    tip="北巨石门和南门一模一样 —— 你已经是老手啦。",
)
b.step(
    "砌北门东柱一层: 同样隔一格门洞。",
    ["n_e_w0", "n_e_e0", "n_e_s0", "n_e_n0"],
    highlight=["gn_4"],
    tip="两座门洞正对, 从南门能一眼望穿北门。",
)
b.step(
    "北门两柱长到二层。",
    ["n_w_w1", "n_w_e1", "n_w_s1", "n_w_n1",
     "n_e_w1", "n_e_e1", "n_e_s1", "n_e_n1"],
    highlight=["n_w_s0"],
    tip="左右同步、整边共线 —— 石柱直直向上。",
)
b.step(
    "挂北门门楣墙: 前后两面, 竖边咬柱。",
    ["n_lin_s", "n_lin_n"],
    highlight=["n_w_e1", "n_e_w1"],
    tip="又一对悬空门楣 —— 巨石门的招牌绝活。",
)
b.step(
    "北门封顶搭桥: 盖板加金色桥板, 第二座巨石门完工。",
    ["n_cap_w", "n_cap_e", "n_bridge"],
    highlight=["n_lin_n"],
    tip="两块金色桥板是夏至日光斑 —— 太阳会从门洞正中升起。",
)
b.step(
    "砌西独石: 四片石墙围成一层箱楼。",
    ["mw_w", "mw_e", "mw_s", "mw_n"],
    highlight=["gm_1"],
    tip="独石孤零零立在草原西侧, 给环阵站岗。",
)
b.step(
    "给西独石戴紫晶尖: 四片等边三角斜棱两两互吸自锁成锥。",
    W_TIP,
    highlight=["mw_s"],
    tip="紫晶锥尖四条斜棱互相咬住 —— 一顶就位, 自己锁自己。",
)
b.step(
    "砌东独石: 与西独石隔着祭坛遥遥相望。",
    ["me_w", "me_e", "me_s", "me_n"],
    highlight=["gm_5"],
    tip="东西独石一对, 南北巨石门一双 —— 十字环阵成形。",
)
b.step(
    "给东独石戴紫晶尖。",
    E_TIP,
    highlight=["me_s"],
    tip="第二顶紫晶锥 —— 阳光下会闪闪发亮。",
)
b.step(
    "砌中央祭坛并请小游客入场: 四面橙墙 + 金顶板, 红色日晷三角"
    "骑顶沿, 两位小游客骑草缝看巨石。",
    ["alt_w", "alt_e", "alt_s", "alt_n", "alt_cap", "dial",
     "kid_s", "kid_n"],
    highlight=["gm_3", "s_bridge"],
    tip="日晷影子指向巨石门 —— 五千年前的大钟表, 开阵!",
)

b.finalize(
    model_id="stonehenge_01",
    name="草原巨石阵",
    name_en="Stonehenge 01",
    description=(
        "只用核心九片型的史前遗迹, 全库第一处巨石阵, 给古代建筑"
        "补上'彼此分立、围成环阵'的纪念性结构: 结构签名是'巨石门"
        "过梁悬空搭桥' —— 南北两座巨石门各由两座两层闭环箱楼石柱"
        "夹出一格真门洞, 门楣墙不落地、两条竖边分别整边咬住左右"
        "石柱的墙竖缝, 门楣墙顶再托一块金色悬空桥板, 桥板四边同时"
        "吸双侧门楣墙顶与两侧柱顶盖板, 过梁三件像搭桥一样把两座"
        "石柱锁成一座门; 东西各立一座戴紫晶四坡锥尖的独石, 中央"
        "橙色祭坛顶着金顶板与红色日晷三角压阵, 五组巨石在 7x7 草原"
        "上围成十字环阵, 两位小游客骑草缝仰头看 —— 太阳从门洞正中"
        "升起, 五千年前的大钟表开阵!"
    ),
    difficulty=4,
    tags=["古代建筑", "巨石阵", "史前", "遗迹", "挑战"],
    min_pieces=91,
    min_steps=19,
)
