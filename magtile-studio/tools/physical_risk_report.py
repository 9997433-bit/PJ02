#!/usr/bin/env python3
"""全库实物风险巡检报告 (Physical Risk Report, L2 标记判定 + L3 排产底稿)。

背景: 全库模型软件 L1 (R1~R8) 全绿后, 剩下的风险集中在"真实磁力片
搭不搭得起来" —— docs/BUILD_VERIFICATION.md 的三层验证金字塔用 L2
(仿真抽检) + L3 (实物复核) 兜底。本工具是 BUILD_VERIFICATION.md
**2.1 节 L2 工具接口约定第 1 件套** (标记判定 / 风险报告): 扫描
data/models/*.json (或单个模型 JSON), 把 §2 的 L2 标记触发条件逐条
落实为机器可读检测编码, 并叠加一组结构风险信号量化为每模型 0~100
的风险分, 回答两个排产问题:

  1. 哪些模型被 §2 触发条件点亮"需要实物复核"标记 (flags / flagged /
     l2_required, CI 与编辑器共用本判定);
  2. 人手/仿真资源有限时, 先验哪 N 个 (--top 建议人手验清单, 默认 15;
     与 tools/physical_family_pack.py 结构族代表取并集 = 人手缩减集,
     见 V1_LAUNCH_CHECKLIST.md §8)。

L2 标记触发条件与检测编码 (BUILD_VERIFICATION.md §2, 满足任一即标记):

  1   l1_warning              L1 产生任何 Warning (magtile_app validate
                              default 档实跑, 含每个教程中间状态);
  2a  tall_structure          成品最高点 > 6 单位;
  2b  tall_wall_chain         连续 >= 3 片垂直墙链 (墙上立墙再立墙);
  3   critical_com_margin     重心投影到接地凸包边界距离 <
                              stability_margin (0.15) 的 50% ——
                              成品与每个教程中间状态取最小裕量;
  4   weak_edge_load_bearing  扇形/六边形等低磁力边占比形状承重
                              (从磁力连接图中拿掉这些片后, 有其他片
                              失去到地面的支撑路径);
  5   manual_flag             设计师手动标记 (content_meta.l2_manual_flag
                              == true, 或旁车验证文件 flags 含
                              "manual_flag"); 只可追加, 不可取消自动命中。

l2_required (综合结论) = flagged, 或 difficulty 达到 §2 分级表 T4/T5
"每个模型必做"档 (T3 另有随机 20% 抽检, 属排产政策不在本字段内)。

风险分 (0~100) = 8 个分项的加权和 (权重 WEIGHTS, 归一化阈值 NORMS):

  difficulty    难度 D1~D5 ((d-1)/4)                            权重 20
  l1_warnings   L1 default 档警告条数 (validate 实跑)             权重 12
  height        成品最高点 (单位 = 正方形边长)                     权重 12
  wall_chain    悬挂链长: 垂直墙链最长连击 (墙上立墙再立墙)          权重 12
  com_margin    重心临界距: 重心水平投影到接地凸包边界的带符号        权重 14
                距离, 取成品与全部中间状态的最小值 (正 = 在凸包内)
  odd_ratio     扇形/异形片占比: 扩展片型 (扇形/六边形/菱形/梯形)     权重 10
  steps         步数                                             权重  8
  pieces        片数                                             权重 12

是否已 physical_verified 不改变结构风险分 (结构就在那里), 但决定
模型是否进入 --top 建议人手验清单 (已复核模型不再占用人手)。

口径对齐 (与既有工具单一来源, 不各算各的):

  - "已实物复核"判定直接 import tools/list_physical_pending.classify
    (content_meta.physical_verified == true, 或旁车验证文件哈希一致);
  - 抽样包交叉标注直接 import tools/physical_sample_pack.select_sample
    (S1/S2/S3 确定性规则), 分难度耗时预算同 TIME_BUDGET_MIN;
  - 几何计算 (旋转/世界顶点) 直接 import tools/magtile_gen
    (与 C++ 端 R = Rz*Ry*Rx 完全一致), 容差同 PHYSICS_RULES.md 1.1 节;
  - L1 警告数用 build/magtile_app validate (default 档) 实跑统计,
    二进制缺失时自动降级: 该分项计 0 并在报告中注明 (不崩溃);
  - 反向复用: tools/physical_family_pack.py (结构族去重包) 依次探测
    docs/reports/physical_risk_report.json / PHYSICAL_RISK_REPORT.json
    (--json 输出存盘即用, 含 flags) 或本模块公共入口 risk_score(model)
    (纯结构分, L1 警告分项按 0 计), 均缺位才退化其内置启发式。

用法:
    tools/physical_risk_report.py [models_path] [选项]
        models_path           模型目录或单个模型 JSON
                              (默认: 仓库 data/models)
        --data-dir D          数据目录 (tile_catalog / model_catalog /
                              verification 的默认基准; 默认为模型目录上级)
        --verification-dir D  旁车验证记录目录 (默认 <data-dir>/verification)
        --catalog FILE        模型库目录 (名称/主题来源,
                              默认 <data-dir>/model_catalog.json)
        --validator BIN       magtile_app 路径 (默认 <仓库>/build/magtile_app)
        --no-validate         跳过 L1 校验器实跑 (警告分项计 0)
        --top N               建议人手验清单规模 (默认 15; 0 = 不出清单)
        --json                机器可读 JSON 输出 (每模型含 model_id /
                              flags / flagged / l2_required, 2.1 节约定)
        --markdown FILE       生成 Markdown 报告
                              (docs/reports/PHYSICAL_RISK_REPORT.md 即由此生成)
        --fail-on-flagged     门禁旗标 (2.1 节): 存在 l2_required 且无有效
                              L2 通过凭据 (旁车 layer:"L2" 记录哈希绑定且
                              状态达 sim_passed, 或已实物复核) 的模型时
                              以退出码 1 结束; 默认仅报告不阻断

退出码: 0 = 报告完成 / 1 = --fail-on-flagged 且存在缺凭据模型 / 2 = 数据错误
"""

import argparse
import json
import math
import re
import subprocess
import sys
from collections import Counter
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from list_physical_pending import classify, content_hash  # noqa: E402  (复核判定单一来源)
from magtile_gen import MAGNET_EDGES, world_vertices  # noqa: E402  (几何单一来源)
from physical_sample_pack import TIME_BUDGET_MIN, select_sample  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
FREE_TAG = "免费"  # 与 tools/verify_free_tier.py / physical_sample_pack.py 同口径

# ---- 与 PHYSICS_RULES.md 1.1/1.3 节一致的容差 ----------------------
CONNECT_TOL = 0.02       # 磁力边吸合容差
GROUND_TOL = 0.02        # 接地判定高度
STABILITY_MARGIN = 0.15  # 重心允许超出接地凸包的裕量 (R4)

# ---- BUILD_VERIFICATION.md §2 触发条件阈值与检测编码 -----------------
L2_HEIGHT_LIMIT = 6.0    # 2a: 结构高度 > 6 单位
L2_CHAIN_LIMIT = 3       # 2b: 连续 >= 3 片垂直墙链
L2_COM_FRACTION = 0.5    # 3: 边界距 < stability_margin 的 50%
LOWMAG_TYPES = frozenset({"sector", "hexagon"})  # 4 的形状族 (§2 原文例举)

# 检测编码 -> §2 表格行号 (紧凑展示用; JSON 输出用完整编码)
L2_CODE_NO = {
    "l1_warning": "1",
    "tall_structure": "2a",
    "tall_wall_chain": "2b",
    "critical_com_margin": "3",
    "weak_edge_load_bearing": "4",
    "manual_flag": "5",
}

# 状态机顺序 (BUILD_VERIFICATION.md 5.2 节), --fail-on-flagged 凭据判定用
STATUS_ORDER = ["draft", "software_passed", "sim_passed",
                "physical_pending", "physical_passed"]

# 扇形/异形片 = 扩展装片型 (tile_catalog.json tier=expansion 的四种,
# docs/TILE_CATALOG.md; 目录缺失时用此兜底集合)
EXPANSION_TYPES_FALLBACK = frozenset({"rhombus", "trapezoid", "hexagon", "sector"})

# 垂直墙链判定: 片面法向 z 分量 <= 0.30 视为立片 (墙),
# 吸合边方向 z 分量 <= 0.30 视为水平铰链, 上下片重心 z 差 > 0.15 视为叠放
WALL_NORMAL_Z_MAX = 0.30
HINGE_DIR_Z_MAX = 0.30
STACK_MIN_DZ = 0.15

# ---- 风险分权重与归一化满分阈值 (合计 100) --------------------------
WEIGHTS = {
    "difficulty": 20, "l1_warnings": 12, "height": 12, "wall_chain": 12,
    "com_margin": 14, "odd_ratio": 10, "steps": 8, "pieces": 12,
}
NORMS = {
    "l1_warnings": 3,    # >= 3 条警告即满分 (任何警告都已触发 l1_warning)
    "height": 8.0,       # 8 单位封顶 (全库最高 10, 触发线 6 -> 0.75)
    "wall_chain": 5,     # 5 连击封顶 (触发线 3 -> 0.6)
    "odd_ratio": 0.30,   # 异形片占比 30% 即满分
    "steps": 24,         # 全库最多 26 步
    "pieces": 120,       # 全库最多 122 片
}
assert sum(WEIGHTS.values()) == 100

# 风险带划分 (报告分层展示用; 阈值为工程约定, 非物理量)
BAND_HIGH = 60.0
BAND_MID = 40.0

REPORT_DOC = "docs/reports/PHYSICAL_RISK_REPORT.md"


def load_json(path: Path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        print(f"错误: {path} 无法解析: {exc}", file=sys.stderr)
        sys.exit(2)


# ---- 基础几何 ------------------------------------------------------
def _sub(a, b):
    return (a[0] - b[0], a[1] - b[1], a[2] - b[2])


def _cross(a, b):
    return (a[1] * b[2] - a[2] * b[1],
            a[2] * b[0] - a[0] * b[2],
            a[0] * b[1] - a[1] * b[0])


def _dot(a, b):
    return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]


def _length(a):
    return math.sqrt(_dot(a, a))


def poly_area_centroid(verts):
    """平面凸多边形 (3D 顶点) 的面积与质心 (以顶点 0 为扇心三角剖分)。"""
    o = verts[0]
    total = 0.0
    acc = [0.0, 0.0, 0.0]
    for i in range(1, len(verts) - 1):
        a = _length(_cross(_sub(verts[i], o), _sub(verts[i + 1], o))) / 2.0
        total += a
        for k in range(3):
            acc[k] += a * (o[k] + verts[i][k] + verts[i + 1][k]) / 3.0
    if total < 1e-12:
        return 0.0, list(o)
    return total, [c / total for c in acc]


def pt_seg_dist(p, a, b):
    """点到线段距离 (3D 或 2D 补零后)。"""
    ab = _sub(b, a)
    denom = _dot(ab, ab)
    t = 0.0 if denom < 1e-12 else max(0.0, min(1.0, _dot(_sub(p, a), ab) / denom))
    proj = (a[0] + t * ab[0], a[1] + t * ab[1], a[2] + t * ab[2])
    return math.dist(p, proj)


class TileGeo:
    """单片几何缓存: 世界顶点 / 磁力边 / 面积质心 / 法向 / 包围球。"""

    __slots__ = ("verts", "edges", "area", "centroid", "normal_z",
                 "center", "radius", "min_z")

    def __init__(self, tile):
        self.verts = world_vertices(tile)
        self.edges = []
        n = len(self.verts)
        for i in MAGNET_EDGES[tile["type"]]:
            a, b = self.verts[i], self.verts[(i + 1) % n]
            self.edges.append((a, b, math.dist(a, b)))
        self.area, self.centroid = poly_area_centroid(self.verts)
        normal = _cross(_sub(self.verts[1], self.verts[0]),
                        _sub(self.verts[2], self.verts[0]))
        nl = _length(normal)
        self.normal_z = abs(normal[2] / nl) if nl > 1e-12 else 1.0
        cx = sum(v[0] for v in self.verts) / n
        cy = sum(v[1] for v in self.verts) / n
        cz = sum(v[2] for v in self.verts) / n
        self.center = (cx, cy, cz)
        self.radius = max(math.dist(self.center, v) for v in self.verts)
        self.min_z = min(v[2] for v in self.verts)


def magnet_connections(geos):
    """磁力连接判定, 与 R2 同规则: 较短磁力边两端点都落在较长边线段上
    (点到线段距离 <= connect_tolerance)。返回 [(i, j, 吸合段端点对)]。"""
    conns = []
    n = len(geos)
    for i in range(n):
        gi = geos[i]
        for j in range(i + 1, n):
            gj = geos[j]
            if math.dist(gi.center, gj.center) > gi.radius + gj.radius + 5 * CONNECT_TOL:
                continue
            for a0, a1, la in gi.edges:
                for b0, b1, lb in gj.edges:
                    if la <= lb:
                        s0, s1, l0, l1 = a0, a1, b0, b1
                    else:
                        s0, s1, l0, l1 = b0, b1, a0, a1
                    if (pt_seg_dist(s0, l0, l1) <= CONNECT_TOL
                            and pt_seg_dist(s1, l0, l1) <= CONNECT_TOL):
                        conns.append((i, j, (s0, s1)))
    return conns


def max_wall_chain(geos, conns):
    """垂直墙链最长连击 (§2 检测编码 tall_wall_chain 的"墙上立墙再立墙")。

    立片 (法向近水平) 之间经近水平铰链边上下叠放构成有向图
    (下 -> 上, 重心 z 严格递增), 返回最长路径的片数。
    """
    vertical = {i for i, g in enumerate(geos) if g.normal_z <= WALL_NORMAL_Z_MAX}
    above = {}
    for i, j, (s0, s1) in conns:
        if i not in vertical or j not in vertical:
            continue
        seg = _sub(s1, s0)
        seg_len = _length(seg)
        if seg_len < 1e-9 or abs(seg[2] / seg_len) > HINGE_DIR_Z_MAX:
            continue
        dz = geos[j].centroid[2] - geos[i].centroid[2]
        if abs(dz) <= STACK_MIN_DZ:
            continue
        lo, hi = (i, j) if dz > 0 else (j, i)
        above.setdefault(lo, set()).add(hi)

    memo = {}

    def depth(node):
        if node in memo:
            return memo[node]
        memo[node] = 1  # 防御环路 (重心 z 严格递增, 理论上无环)
        memo[node] = 1 + max((depth(u) for u in above.get(node, ())), default=0)
        return memo[node]

    return max((depth(i) for i in vertical), default=0)


def com_boundary_margin(geos):
    """重心水平投影到接地凸包边界的带符号距离 (正 = 在凸包内)。

    与 R4 同口径: 重量 ∝ 面积, 接地区域 = z <= ground_tolerance 顶点的
    水平凸包 (Andrew 单调链)。无接地顶点返回 None (no_ground_contact)。
    """
    total_area = sum(g.area for g in geos)
    if total_area < 1e-12:
        return None
    com = [sum(g.area * g.centroid[k] for g in geos) / total_area for k in range(3)]
    pts = sorted({(round(v[0], 6), round(v[1], 6))
                  for g in geos for v in g.verts if v[2] <= GROUND_TOL})
    if not pts:
        return None
    p = (com[0], com[1], 0.0)
    if len(pts) == 1:
        return -math.dist(p, (pts[0][0], pts[0][1], 0.0))

    def half_hull(points):
        hull = []
        for q in points:
            while len(hull) >= 2:
                ox, oy = hull[-2]
                ax, ay = hull[-1]
                if (ax - ox) * (q[1] - oy) - (ay - oy) * (q[0] - ox) <= 1e-12:
                    hull.pop()
                else:
                    break
            hull.append(q)
        return hull

    lower = half_hull(pts)
    upper = half_hull(list(reversed(pts)))
    hull = lower[:-1] + upper[:-1]
    if len(hull) < 3:  # 共线退化: 接地区域是一条线段 (如单面立墙)
        a, b = pts[0], pts[-1]
        return -pt_seg_dist(p, (a[0], a[1], 0.0), (b[0], b[1], 0.0))

    inside = True
    boundary = math.inf
    m = len(hull)
    for i in range(m):
        ax, ay = hull[i]
        bx, by = hull[(i + 1) % m]
        if (bx - ax) * (p[1] - ay) - (by - ay) * (p[0] - ax) < 0:
            inside = False
        boundary = min(boundary, pt_seg_dist(p, (ax, ay, 0.0), (bx, by, 0.0)))
    return boundary if inside else -boundary


def com_margin_over_states(model, geos):
    """成品与每个教程中间状态的重心边界距, 返回 (最小值, 所在状态, 成品值)。

    §2 检测编码 critical_com_margin 的口径: "成品与每个中间状态取最小
    裕量与阈值比较"。中间状态 = 按教程步骤放置到第 k 步完成后的前缀。
    步骤数据异常 (未覆盖全部片) 时退化为只看成品。
    """
    final_margin = com_boundary_margin(geos)
    idx = {t["id"]: k for k, t in enumerate(model.get("final_assembly", []))}
    placed, states = [], []
    for step in model.get("steps", []):
        for tid in step.get("tiles_to_add", []):
            if tid not in idx:
                return final_margin, "成品", final_margin  # 引用异常, 退化
            placed.append(idx[tid])
        states.append((step.get("step_number"), list(placed)))
    if not states or len(placed) != len(geos):
        return final_margin, "成品", final_margin

    best, best_at = final_margin, "成品"
    for step_no, prefix in states[:-1]:  # 最后一步完成后 = 成品
        margin = com_boundary_margin([geos[k] for k in prefix])
        if margin is None:
            return None, f"第 {step_no} 步后", final_margin
        if best is None or margin < best:
            best, best_at = margin, f"第 {step_no} 步后"
    return best, best_at, final_margin


def lowmag_load_bearing(model, geos, conns):
    """§2 检测编码 weak_edge_load_bearing: 扇形/六边形等低磁力边占比
    形状是否承重。

    判定: 在磁力连接图上, 以接地片为源做可达性分析; 拿掉全部
    低磁力片后若有其他片失去到地面的支撑路径, 即为承重。
    """
    n = len(geos)
    low = {i for i, t in enumerate(model.get("final_assembly", []))
           if t["type"] in LOWMAG_TYPES}
    if not low:
        return False
    adj = [[] for _ in range(n)]
    for i, j, _seg in conns:
        adj[i].append(j)
        adj[j].append(i)
    grounded = [i for i in range(n) if geos[i].min_z <= GROUND_TOL]

    def reachable(blocked):
        seen = set()
        stack = [i for i in grounded if i not in blocked]
        while stack:
            u = stack.pop()
            if u in seen:
                continue
            seen.add(u)
            stack.extend(v for v in adj[u] if v not in seen and v not in blocked)
        return seen

    full = reachable(frozenset())
    cut = reachable(low)
    return any(i in full and i not in cut for i in range(n) if i not in low)


# ---- 旁车验证文件 (BUILD_VERIFICATION.md 5.2 节) --------------------
def load_sidecar(model, ver_dir):
    path = ver_dir / f"{model['id']}.json"
    if not path.is_file():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None  # 解析警告由 classify 统一上报


def has_l2_credential(model, sidecar, verified):
    """--fail-on-flagged 的"有效 L2 通过凭据"判定 (2.1 节):
    已实物复核 (L3 >= L2), 或旁车文件内容哈希绑定当前版本、状态达
    sim_passed 且 records 存在 layer=="L2" 记录。"""
    if verified:
        return True
    if not sidecar or sidecar.get("content_hash") != content_hash(model):
        return False
    status = sidecar.get("status", "draft")
    if status not in STATUS_ORDER or \
            STATUS_ORDER.index(status) < STATUS_ORDER.index("sim_passed"):
        return False
    return any(rec.get("layer") == "L2" for rec in sidecar.get("records", []))


# ---- L1 校验器实跑 -------------------------------------------------
WARN_RE = re.compile(r"\(([a-z_]+)\)\s*$")


def run_validator(binary, model_path, data_dir):
    """跑 magtile_app validate (default 档), 返回 (警告数, 警告 code 集, 错误数)。"""
    proc = subprocess.run(
        [str(binary), "validate", str(model_path), "--data-dir", str(data_dir)],
        capture_output=True, text=True)
    warn_lines, err_lines = [], []
    for line in (proc.stdout + "\n" + proc.stderr).splitlines():
        if line.startswith("[警告]"):
            warn_lines.append(line)
        elif line.startswith("[错误]"):
            err_lines.append(line)
    codes = sorted({m.group(1) for line in warn_lines
                    if (m := WARN_RE.search(line))})
    return len(warn_lines), codes, max(len(err_lines), proc.returncode and 1 or 0)


# ---- 风险分与 L2 标记 ----------------------------------------------
def clamp01(x):
    return max(0.0, min(1.0, x))


def sub_risks(entry):
    """各分项归一化到 0~1 (与 WEIGHTS 键一一对应)。"""
    margin = entry["com_margin"]
    return {
        "difficulty": clamp01((entry["difficulty"] - 1) / 4.0),
        "l1_warnings": clamp01((entry["l1_warnings"] or 0) / NORMS["l1_warnings"]),
        "height": clamp01(entry["height"] / NORMS["height"]),
        "wall_chain": clamp01(entry["wall_chain"] / NORMS["wall_chain"]),
        "com_margin": 1.0 if margin is None
        else clamp01(1.0 - margin / STABILITY_MARGIN),
        "odd_ratio": clamp01(entry["odd_ratio"] / NORMS["odd_ratio"]),
        "steps": clamp01(entry["steps"] / NORMS["steps"]),
        "pieces": clamp01(entry["pieces"] / NORMS["pieces"]),
    }


def l2_flags(entry):
    """BUILD_VERIFICATION.md §2 触发条件 -> 检测编码列表 (表格顺序)。"""
    flags = []
    if (entry["l1_warnings"] or 0) > 0:
        flags.append("l1_warning")
    if entry["height"] > L2_HEIGHT_LIMIT:
        flags.append("tall_structure")
    if entry["wall_chain"] >= L2_CHAIN_LIMIT:
        flags.append("tall_wall_chain")
    margin = entry["com_margin"]
    if margin is None or margin < STABILITY_MARGIN * L2_COM_FRACTION:
        flags.append("critical_com_margin")
    if entry["lowmag_load_bearing"]:
        flags.append("weak_edge_load_bearing")
    if entry["manual_flag"]:
        flags.append("manual_flag")
    return flags


def l2_requirement_text(entry):
    """§2 分级表: 该难度的 L2 仿真抽检要求 (人读说明)。"""
    if entry["difficulty"] >= 4:
        return "必做"
    if entry["flagged"]:
        return "被标记必做"
    if entry["difficulty"] == 3:
        return "随机 20% 抽检"
    return "-"


def band(score):
    if score >= BAND_HIGH:
        return "高"
    if score >= BAND_MID:
        return "中"
    return "低"


def flags_compact(flags):
    """检测编码 -> §2 表格行号紧凑串 (终端/表格列用)。"""
    return ",".join(L2_CODE_NO[f] for f in flags) if flags else "-"


def structural_metrics(model, expansion_types=EXPANSION_TYPES_FALLBACK):
    """单模型纯结构分项 (不含 L1 实跑与复核状态), analyze 与 risk_score 共用。"""
    assembly = model.get("final_assembly", [])
    geos = [TileGeo(t) for t in assembly]
    conns = magnet_connections(geos)
    margin_min, margin_at, margin_final = com_margin_over_states(model, geos)
    odd_pieces = sum(1 for t in assembly if t["type"] in expansion_types)
    rnd = lambda m: None if m is None else round(m, 4) + 0.0  # noqa: E731  (+0.0 归一化 -0.0)
    return {
        "difficulty": int(model.get("difficulty", 0)),
        "pieces": int(model.get("total_pieces", len(assembly))),
        "steps": len(model.get("steps", [])),
        "height": round(max((v[2] for g in geos for v in g.verts), default=0.0), 3),
        "wall_chain": max_wall_chain(geos, conns),
        "com_margin": rnd(margin_min),      # 成品与全部中间状态的最小裕量
        "com_margin_at": margin_at,
        "com_margin_final": rnd(margin_final),
        "odd_pieces": odd_pieces,
        "odd_ratio": round(odd_pieces / len(assembly), 4) if assembly else 0.0,
        "lowmag_pieces": sum(1 for t in assembly if t["type"] in LOWMAG_TYPES),
        "lowmag_load_bearing": lowmag_load_bearing(model, geos, conns),
    }


def risk_score(model: dict) -> float:
    """单模型风险分 (0~100) 公共入口, 供 tools/physical_family_pack.py
    模块探测复用 (2.1 节探测链第 2 级)。

    只依赖模型 JSON 本身: L1 警告分项需要校验器实跑, 此入口按 0 计;
    完整口径 (含 L1 警告与 flags) 用 --json 报告存盘为
    docs/reports/PHYSICAL_RISK_REPORT.json 走探测链第 1 级。
    """
    entry = dict(structural_metrics(model), l1_warnings=0)
    return round(sum(WEIGHTS[k] * v for k, v in sub_risks(entry).items()), 1)


# ---- 扫描 ----------------------------------------------------------
def analyze(paths, data_dir, ver_dir, catalog_path, validator, do_validate):
    names, themes = {}, {}
    if catalog_path.is_file():
        for c in load_json(catalog_path).get("models", []):
            names[c["id"]] = c.get("name", c["id"])
            themes[c["id"]] = c.get("theme", "(未登记)")

    expansion_types = set(EXPANSION_TYPES_FALLBACK)
    tile_catalog = data_dir / "tile_catalog.json"
    if tile_catalog.is_file():
        expansion_types = {t["type"] for t in load_json(tile_catalog).get("tiles", [])
                           if t.get("tier") != "core"} or expansion_types

    validator_used = bool(do_validate and validator and Path(validator).is_file())
    notes = []
    if do_validate and not validator_used:
        notes.append(f"校验器不存在 ({validator}), L1 警告分项按 0 计 "
                     "(先构建 magtile_app 或用 --validator 指定)")
    if not do_validate:
        notes.append("--no-validate: 跳过 L1 校验器实跑, L1 警告分项按 0 计")

    models, entries = [], []
    for path in paths:
        model = load_json(path)
        model.setdefault("id", path.stem)
        models.append(model)
        cm = model.get("content_meta") or {}
        sidecar = load_sidecar(model, ver_dir)

        warn_count, warn_codes, err_count = None, [], 0
        if validator_used:
            warn_count, warn_codes, err_count = run_validator(
                validator, path, data_dir)

        verified, via, warnings = classify(model, ver_dir)
        entry = {
            "model_id": model["id"],
            "name": names.get(model["id"], model.get("name", path.stem)),
            "theme": themes.get(model["id"], "(未登记)"),
            "free_tier": FREE_TAG in model.get("tags", []),
            "l1_warnings": warn_count,
            "l1_warning_codes": warn_codes,
            "l1_errors": err_count,
            **structural_metrics(model, expansion_types),
            "manual_flag": cm.get("l2_manual_flag") is True
            or "manual_flag" in ((sidecar or {}).get("flags") or []),
            "physical_verified": verified,
            "verified_via": via,
            "classify_warnings": warnings,
        }
        risks = sub_risks(entry)
        entry["sub_risks"] = {k: round(v, 4) for k, v in risks.items()}
        entry["sub_scores"] = {k: round(WEIGHTS[k] * v, 2) for k, v in risks.items()}
        entry["risk_score"] = round(sum(entry["sub_scores"].values()), 1)
        entry["risk_band"] = band(entry["risk_score"])
        entry["flags"] = l2_flags(entry)
        entry["flagged"] = bool(entry["flags"])
        entry["l2_required"] = entry["flagged"] or entry["difficulty"] >= 4
        entry["l2_requirement"] = l2_requirement_text(entry)
        entry["l2_credential"] = has_l2_credential(model, sidecar, verified)
        entry["est_minutes"] = TIME_BUDGET_MIN.get(entry["difficulty"], 120)
        entries.append(entry)

    entries.sort(key=lambda e: (-e["risk_score"], e["model_id"]))

    # 抽样包交叉标注 (physical_sample_pack 默认 target=10, 同一确定性规则)
    picked, _hits = select_sample(models, themes, target=10)
    sample_layer = {m["id"]: layer for m, layer in picked}
    for e in entries:
        e["sample_pack_layer"] = sample_layer.get(e["model_id"], "")
    return entries, notes, validator_used


def summarize(entries, top_n):
    d4 = [e for e in entries if e["difficulty"] >= 4]
    top = [e for e in entries if not e["physical_verified"]][:top_n]
    return {
        "models_scanned": len(entries),
        "flagged_l2": sum(1 for e in entries if e["flagged"]),
        "flag_hits": {code: n for code, n in sorted(
            Counter(f for e in entries for f in e["flags"]).items(),
            key=lambda kv: L2_CODE_NO[kv[0]])},
        "l2_required_count": sum(1 for e in entries if e["l2_required"]),
        "missing_l2_credential": [e["model_id"] for e in entries
                                  if e["l2_required"] and not e["l2_credential"]],
        "bands": dict(Counter(e["risk_band"] for e in entries)),
        "l1_error_models": [e["model_id"] for e in entries if e["l1_errors"]],
        "d4plus_total": len(d4),
        "d4plus_verified": sum(1 for e in d4 if e["physical_verified"]),
        "d4plus_pending": sum(1 for e in d4 if not e["physical_verified"]),
        "verified_total": sum(1 for e in entries if e["physical_verified"]),
        "top": top,
        "top_minutes": sum(e["est_minutes"] for e in top),
    }


# ---- 输出 ----------------------------------------------------------
def fmt_margin(margin):
    return "无接地" if margin is None else f"{margin:+.3f}"


def render_terminal(entries, summary, notes, top_n, validator_used, fail_on_flagged):
    print("== 全库实物风险巡检 (L2 标记: docs/BUILD_VERIFICATION.md §2 / 2.1 接口约定) ==")
    print(f"扫描 {summary['models_scanned']} 个模型: "
          f"L2 标记 {summary['flagged_l2']} 个, "
          f"l2_required {summary['l2_required_count']} 个 "
          f"(缺 L2 凭据 {len(summary['missing_l2_credential'])}); "
          f"风险带 高 {summary['bands'].get('高', 0)} / "
          f"中 {summary['bands'].get('中', 0)} / "
          f"低 {summary['bands'].get('低', 0)}")
    hits = summary["flag_hits"]
    print("触发编码命中: " + (", ".join(
        f"{L2_CODE_NO[c]} {c}={n}" for c, n in hits.items()) if hits else "无"))
    print(f"D4+ 共 {summary['d4plus_total']} 个 "
          f"(已复核 {summary['d4plus_verified']}, 待复核 {summary['d4plus_pending']}"
          "; 判定与 tools/list_physical_pending.py 同源)")
    if summary["l1_error_models"]:
        print(f"!! L1 存在 Error 的模型: {', '.join(summary['l1_error_models'])}")
    for n in notes:
        print(f"[注] {n}")

    top = summary["top"]
    if top_n > 0 and top:
        print(f"\n-- 建议人手验清单 Top {len(top)} (未复核, 按风险分降序; "
              f"预算合计 {summary['top_minutes']} 分钟"
              f" ≈ {summary['top_minutes'] / 60:.1f} 小时) --")
        print(f"{'#':<3} {'模型':<26} {'难度':<4} {'风险':>5} {'L2标记':<10} "
              f"{'抽样层':<6} {'预计':>5}")
        for i, e in enumerate(top, 1):
            print(f"{i:<3} {e['model_id']:<26} D{e['difficulty']:<3} "
                  f"{e['risk_score']:>5.1f} {flags_compact(e['flags']):<10} "
                  f"{e['sample_pack_layer'] or '-':<6} {e['est_minutes']:>3}min")

    warn_col = "L1警" if validator_used else "L1警?"
    print(f"\n-- 全库明细 ({len(entries)} 个, 按风险分降序; L2 标记列为 §2 "
          "表格行号: 1=l1_warning 2a=tall_structure 2b=tall_wall_chain "
          "3=critical_com_margin 4=weak_edge_load_bearing 5=manual_flag) --")
    print(f"{'#':<4} {'模型':<26} {'难度':<4} {'风险':>5} 带 {warn_col:>4} "
          f"{'高度':>6} {'链':>3} {'重心距':>7} {'异形%':>6} {'步':>3} {'片':>4} "
          f"{'L2标记':<10} {'L2需':<4} 状态")
    for i, e in enumerate(entries, 1):
        status = f"已复核 ({e['verified_via']})" if e["physical_verified"] else "待复核"
        warn = "-" if e["l1_warnings"] is None else str(e["l1_warnings"])
        print(f"{i:<4} {e['model_id']:<26} D{e['difficulty']:<3} {e['risk_score']:>5.1f} "
              f"{e['risk_band']} {warn:>4} {e['height']:>6.2f} {e['wall_chain']:>3} "
              f"{fmt_margin(e['com_margin']):>7} {e['odd_ratio'] * 100:>5.1f}% "
              f"{e['steps']:>3} {e['pieces']:>4} "
              f"{flags_compact(e['flags']):<10} "
              f"{'是' if e['l2_required'] else '-':<4} {status}")

    cw = sorted({w for e in entries for w in e["classify_warnings"]})
    if cw:
        print(f"\n-- 复核标注警告 ({len(cw)}) --")
        for w in cw:
            print(f"  [WARN] {w}")
    print(f"\n口径对账: 已复核 {summary['verified_total']} / "
          f"{summary['models_scanned']}, D4+ 待复核 {summary['d4plus_pending']} "
          "(= tools/list_physical_pending.py 待复核数); 抽样包标注 = "
          "tools/physical_sample_pack.py S1/S2/S3 (target 10)")
    missing = summary["missing_l2_credential"]
    if missing:
        print(f"l2_required 且缺 L2 通过凭据: {len(missing)} 个"
              + (" (--fail-on-flagged 生效, 退出码 1)" if fail_on_flagged else
                 " (旁车 layer:\"L2\" 记录落盘后消失; --fail-on-flagged 可作门禁)"))


def json_payload(entries, summary, notes, top_n, validator_used):
    return {
        "doc": "docs/BUILD_VERIFICATION.md §2 / 2.1 接口约定",
        "weights": WEIGHTS,
        "norms": {**NORMS, "stability_margin": STABILITY_MARGIN},
        "l2_thresholds": {
            "tall_structure": L2_HEIGHT_LIMIT,
            "tall_wall_chain": L2_CHAIN_LIMIT,
            "critical_com_margin": STABILITY_MARGIN * L2_COM_FRACTION,
            "weak_edge_types": sorted(LOWMAG_TYPES),
        },
        "bands": {"high": BAND_HIGH, "mid": BAND_MID},
        "validator_used": validator_used,
        "notes": notes,
        "summary": {k: v for k, v in summary.items() if k != "top"},
        "top_recommendation": [e["model_id"] for e in summary["top"]] if top_n > 0 else [],
        "models": entries,
    }


def render_markdown(entries, summary, notes, top_n, validator_used) -> str:
    lines = []
    a = lines.append
    a("# 全库实物风险巡检报告 (Physical Risk Report)")
    a("")
    a(f"- 生成日期: {date.today().isoformat()}")
    a(f"- 生成工具: `tools/physical_risk_report.py --markdown {REPORT_DOC}` —— "
      "模型库 / 复核状态变化后**重新生成**, 勿手改")
    a("- 口径: L2 标记触发条件与检测编码对齐 "
      "[`docs/BUILD_VERIFICATION.md`](../BUILD_VERIFICATION.md) §2 "
      "(接口约定 2.1 节第 1 件套); \"已实物复核\"判定与 "
      "`tools/list_physical_pending.py` 同源 (同一 classify 函数); "
      "抽样层标注与 `tools/physical_sample_pack.py` 同源 "
      "(同一 select_sample 规则)")
    for n in notes:
        a(f"- **注**: {n}")
    a("")
    a("## 1. 定位与方法")
    a("")
    a("软件 L1 全绿只回答\"静力模型认为撑得住\", 实物风险要靠 L2 仿真抽检与 "
      "L3 实物复核兜底 (三层验证金字塔, BUILD_VERIFICATION.md §1)。本报告把"
      "每个模型的结构风险量化为 **0~100 风险分** (8 个分项加权和), 并逐模型"
      "判定 §2 的 L2 标记触发条件 (机器可读检测编码), 供排产: 分高者先验。"
      "风险分是**排序信号**不是物理结论 —— 已实物复核的模型结构风险分不变, "
      "但不再占用人手 (不进入第 3 节建议清单)。")
    a("")
    a("| 分项 | 含义 | 权重 | 归一化 (满分阈值) |")
    a("| --- | --- | ---: | --- |")
    a("| difficulty | 难度 D1~D5 | 20 | (d-1)/4 |")
    a("| l1_warnings | L1 default 档警告条数 (validate 实跑) | 12 | "
      f"{NORMS['l1_warnings']} 条封顶 |")
    a(f"| height | 成品最高点 (单位=正方形边长) | 12 | {NORMS['height']:g} 封顶 |")
    a("| wall_chain | 悬挂链长: 垂直墙链最长连击 (墙上立墙再立墙) | 12 | "
      f"{NORMS['wall_chain']} 连击封顶 |")
    a("| com_margin | 重心临界距: 重心投影到接地凸包边界带符号距离, "
      "取成品与全部中间状态最小值 | 14 | "
      f"1 - 距离/stability_margin({STABILITY_MARGIN:g}) |")
    a("| odd_ratio | 扇形/异形 (扩展片型) 片数占比 | 10 | "
      f"{NORMS['odd_ratio']:.0%} 封顶 |")
    a(f"| steps | 步数 | 8 | {NORMS['steps']} 步封顶 |")
    a(f"| pieces | 片数 | 12 | {NORMS['pieces']} 片封顶 |")
    a("")
    a(f"风险带: **高 ≥ {BAND_HIGH:g}** / 中 ≥ {BAND_MID:g} / 低 < {BAND_MID:g} "
      "(工程约定阈值, 用于分层展示)。")
    a("")
    a("## 2. L2 标记触发条件与检测编码 (BUILD_VERIFICATION.md §2) 对齐")
    a("")
    hits = summary["flag_hits"]
    a("| # | 检测编码 | §2 触发条件 | 本工具判定 | 命中 |")
    a("| --- | --- | --- | --- | ---: |")
    a("| 1 | `l1_warning` | L1 产生任何 Warning | `magtile_app validate` "
      "(default 档) 实跑警告条数 > 0 (含每个教程中间状态) | "
      f"{hits.get('l1_warning', 0)} |")
    a(f"| 2a | `tall_structure` | 结构高度 > {L2_HEIGHT_LIMIT:g} 单位 | "
      f"世界顶点最高 z | {hits.get('tall_structure', 0)} |")
    a(f"| 2b | `tall_wall_chain` | 连续 ≥ {L2_CHAIN_LIMIT} 片垂直墙链 "
      "(墙上立墙再立墙) | 立片间经水平铰链边叠放的最长链 | "
      f"{hits.get('tall_wall_chain', 0)} |")
    a(f"| 3 | `critical_com_margin` | 重心投影到接地凸包边界距离 < "
      f"stability_margin 的 {L2_COM_FRACTION:.0%} | 面积加权重心 → 接地凸包 "
      "(Andrew 单调链) 带符号边界距, 成品与每个中间状态取最小裕量 < "
      f"{STABILITY_MARGIN * L2_COM_FRACTION:g} | {hits.get('critical_com_margin', 0)} |")
    a("| 4 | `weak_edge_load_bearing` | 扇形/六边形等低磁力边占比形状承重 "
      "| 磁力连接图中拿掉扇形/六边形后有片失去到地面的支撑路径 | "
      f"{hits.get('weak_edge_load_bearing', 0)} |")
    a("| 5 | `manual_flag` | 设计师手动标记 | `content_meta.l2_manual_flag "
      "== true` 或旁车文件 `flags` 含 `manual_flag` (只可追加, 不可取消"
      f"自动命中) | {hits.get('manual_flag', 0)} |")
    a("")
    a(f"全库 {summary['models_scanned']} 个模型中 **{summary['flagged_l2']} 个"
      f"被 L2 标记** (满足任一条件); `l2_required` (被标记, 或 D4+ 必做档) 共 "
      f"**{summary['l2_required_count']} 个**, 其中缺有效 L2 通过凭据 (旁车 "
      f"`layer:\"L2\"` 记录哈希绑定) {len(summary['missing_l2_credential'])} 个 "
      "—— jitter 蒙特卡洛按 2.1 节接口约定跑完落盘后此数应清零 "
      "(`--fail-on-flagged` 即以此为门禁)。按 §2 分级表, D4+ 无论是否被标记 "
      "L2 仿真都必做, D3 被标记 100% + 随机 20%; 明细见第 4 节 \"L2 要求\" 列。")
    a("")
    top = summary["top"]
    a(f"## 3. 建议人手验清单 (Top {len(top)})")
    a("")
    a("未实物复核的模型按风险分降序取前 N (默认 15, `--top N` 调整); 人手实搭"
      "缩减集 = **本清单 + `tools/physical_family_pack.py` 结构族代表**并集 "
      "(V1_LAUNCH_CHECKLIST.md §8)。与 V1 抽样包 "
      "([`PHYSICAL_SAMPLE_V1.md`](PHYSICAL_SAMPLE_V1.md)) 的关系: 抽样包回答"
      "\"上架前最少先搭哪 10 个\" (免费层/D5/付费 D4 规则), 本清单回答\"人手"
      "继续投入时按结构风险还应优先哪些\" —— 两者取并集排产, 抽样层列已交叉"
      "标注。落盘操作按 PHYSICAL_SAMPLE_V1.md 第 5 节 (`content_meta` 三字段), "
      "复核规程见 "
      "[`docs/PHYSICAL_REBUILD_CHECKLIST.md`](../PHYSICAL_REBUILD_CHECKLIST.md) "
      "(0.5 节: 先跑 L2 再排人手, jitter 未过的模型不要开始实搭)。")
    a("")
    a("| # | 模型 | 名称 | 难度 | 风险分 | L2 标记 | 抽样层 | 免费层 | 预计搭时 |")
    a("| --- | --- | --- | --- | --- | --- | --- | --- | --- |")
    for i, e in enumerate(top, 1):
        a(f"| {i} | `{e['model_id']}` | {e['name']} | D{e['difficulty']} "
          f"| {e['risk_score']:.1f} | {flags_compact(e['flags'])} "
          f"| {e['sample_pack_layer'] or '-'} | {'是' if e['free_tier'] else '-'} "
          f"| {e['est_minutes']} 分钟 |")
    a("")
    a(f"预计总耗时 **{summary['top_minutes']} 分钟** "
      f"(约 {summary['top_minutes'] / 60:.1f} 小时, "
      "PHYSICAL_REBUILD_CHECKLIST.md 第 2 节难度预算口径)。")
    a("")
    a(f"## 4. 全库明细 ({len(entries)} 个, 按风险分降序)")
    a("")
    a("\"L2 标记\"列为第 2 节表格行号 (1=l1_warning, 2a=tall_structure, "
      "2b=tall_wall_chain, 3=critical_com_margin, 4=weak_edge_load_bearing, "
      "5=manual_flag); \"重心距\"为成品与全部中间状态的最小裕量。")
    a("")
    warn_head = "L1 警" if validator_used else "L1 警 (未实跑)"
    a(f"| # | 模型 | 难度 | 风险分 | 带 | {warn_head} | 高度 | 链长 | 重心距 "
      "| 异形占比 | 步 | 片 | L2 标记 | L2 要求 | 复核状态 |")
    a("| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- "
      "| --- | --- | --- | --- |")
    for i, e in enumerate(entries, 1):
        status = f"已复核 ({e['verified_via']})" if e["physical_verified"] \
            else "**待复核**" if e["difficulty"] >= 4 else "待复核"
        warn = "-" if e["l1_warnings"] is None else str(e["l1_warnings"])
        a(f"| {i} | `{e['model_id']}` | D{e['difficulty']} | {e['risk_score']:.1f} "
          f"| {e['risk_band']} | {warn} | {e['height']:.2f} | {e['wall_chain']} "
          f"| {fmt_margin(e['com_margin'])} | {e['odd_ratio']:.0%} | {e['steps']} "
          f"| {e['pieces']} | {flags_compact(e['flags'])} "
          f"| {e['l2_requirement']} | {status} |")
    a("")
    a("## 5. 与其他工具的口径对账")
    a("")
    a(f"- 已实物复核 {summary['verified_total']} / {summary['models_scanned']}; "
      f"D4+ 共 {summary['d4plus_total']} 个, 待复核 "
      f"**{summary['d4plus_pending']}** 个 —— 与 "
      "`tools/list_physical_pending.py` 完全一致 (同一 classify 函数, "
      "content_meta 轻量字段与旁车验证文件两种凭据都认, 哈希失配作废);")
    a("- 抽样层列 (S1/S2/S3) 与 `tools/physical_sample_pack.py --target 10` "
      "完全一致 (同一 select_sample 函数); 抽样包全绿不豁免全集清零, "
      "终防线仍是 `tools/list_physical_pending.py --fail-on-pending`;")
    a("- L1 警告实跑用 default 档 (入库基准); 弱磁 strict 档零警告政策由 "
      "`tools/run_strict_audit.sh` 单独把守, 不在本报告重复计分;")
    a("- `--json` 每模型输出 `model_id` / `flags` / `flagged` / `l2_required` "
      "(BUILD_VERIFICATION.md 2.1 节接口约定字段), `--fail-on-flagged` 在存在 "
      "l2_required 且缺有效 L2 通过凭据的模型时退出码 1 (门禁挂接用);")
    a("- 复核状态变化 (落盘 `physical_verified` / 模型改动哈希失配) 后"
      "**重新生成本报告**, 三份产物 (本报告 / PHYSICAL_SAMPLE_V1.md / "
      "PHYSICAL_SIGNOFF_WORKSHEET.md) 一并刷新。")
    a("")
    a("```bash")
    a("python3 tools/physical_risk_report.py                  # 终端表 + Top 15")
    a("python3 tools/physical_risk_report.py --json           # 机器可读 (2.1 节字段)")
    a(f"python3 tools/physical_risk_report.py --markdown {REPORT_DOC}")
    a("```")
    a("")
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(
        description="全库实物风险巡检: L2 标记判定 (BUILD_VERIFICATION.md §2) "
                    "+ 风险分 + 建议人手验清单")
    parser.add_argument("models_path", nargs="?",
                        default=str(ROOT / "data" / "models"),
                        help="模型目录或单个模型 JSON")
    parser.add_argument("--data-dir", default=None,
                        help="数据目录 (默认: 模型目录上级)")
    parser.add_argument("--verification-dir", default=None)
    parser.add_argument("--catalog", default=None,
                        help="模型库目录 model_catalog.json (名称/主题来源)")
    parser.add_argument("--validator", default=None,
                        help="magtile_app 路径 (默认 <仓库>/build/magtile_app)")
    parser.add_argument("--no-validate", action="store_true",
                        help="跳过 L1 校验器实跑 (警告分项计 0)")
    parser.add_argument("--top", type=int, default=15,
                        help="建议人手验清单规模 (默认 15; 0 = 不出清单)")
    parser.add_argument("--json", action="store_true", dest="as_json")
    parser.add_argument("--markdown", default=None, metavar="FILE")
    parser.add_argument("--fail-on-flagged", action="store_true",
                        help="存在 l2_required 且缺有效 L2 通过凭据的模型时"
                             "以退出码 1 结束 (2.1 节门禁语义)")
    args = parser.parse_args()

    models_path = Path(args.models_path)
    if models_path.is_dir():
        paths = sorted(models_path.glob("*.json"))
        base_dir = models_path
    elif models_path.is_file():
        paths = [models_path]
        base_dir = models_path.parent
    else:
        print(f"错误: 模型目录或文件不存在: {models_path}", file=sys.stderr)
        return 2
    if args.top < 0:
        print(f"错误: --top 必须 >= 0 (给的是 {args.top})", file=sys.stderr)
        return 2
    data_dir = Path(args.data_dir) if args.data_dir else base_dir.parent
    ver_dir = Path(args.verification_dir) if args.verification_dir \
        else data_dir / "verification"
    catalog_path = Path(args.catalog) if args.catalog \
        else data_dir / "model_catalog.json"
    validator = Path(args.validator) if args.validator \
        else data_dir.parent / "build" / "magtile_app"

    entries, notes, validator_used = analyze(
        paths, data_dir, ver_dir, catalog_path, validator, not args.no_validate)
    summary = summarize(entries, args.top)

    if args.markdown:
        out = Path(args.markdown)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(
            render_markdown(entries, summary, notes, args.top, validator_used),
            encoding="utf-8")
        print(f"已生成: {out}")

    if args.as_json:
        print(json.dumps(json_payload(entries, summary, notes, args.top,
                                      validator_used),
                         ensure_ascii=False, indent=2))
    else:
        render_terminal(entries, summary, notes, args.top, validator_used,
                        args.fail_on_flagged)

    if args.fail_on_flagged and summary["missing_l2_credential"]:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
