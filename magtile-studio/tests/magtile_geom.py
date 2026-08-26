#!/usr/bin/env python3
# =============================================================
# MagTile Studio - 测试共用几何库 (纯 Python 复算 C++ 几何约定)
#
# 被 test_step_assembly.py / test_library_uniqueness.py 共用。
# 所有约定与 C++ 端严格一致 (src/physics/geometry.cpp / core/types):
#
#   - 旋转: R = Rz * Ry * Rx (欧拉角, 度), 本地顶点位于 XY 平面;
#   - 世界坐标: world = R * (x, y, 0) + position;
#   - 面法向: 本地 +Z 经旋转后的方向 (即 R 的第三列);
#   - 磁力边: 形状目录 magnet_edges 列出的边索引, 边 i 连接顶点 i 与 i+1;
#   - 吸合判定: 短边被长边线段完整包含 (容差 connect_tolerance);
#     等长整边即退化为端点两两重合 (正序或反序), 长短边搭配 (大正方形
#     边长 2 吸小方边长 1 等) 时短边两端点都须落在长边上, 错位半搭
#     (短边端点悬出长边) 仍判为未连接 —— 与 C++ R2 完全一致;
#   - 接地判定: 存在顶点 z <= ground_tolerance。
#
# 本模块只依赖标准库, 内容作者无需 C++ 工具链即可在本地运行数据层质检。
# =============================================================

import json
import math
from pathlib import Path

# 与 C++ PhysicsConfig 默认值一致 (docs/PHYSICS_RULES.md 1.1 节)
CONNECT_TOLERANCE = 0.02
GROUND_TOLERANCE = 0.02

# 相对姿态分类容差 (法向点积): 见 CONTENT_STRATEGY.md 5.2 节
COPLANAR_NORMAL_DOT = 0.99
FOLD90_NORMAL_DOT = 0.01


def load_tile_catalog(catalog_path):
    """加载形状目录, 返回 {type: 形状定义}。"""
    catalog = json.loads(Path(catalog_path).read_text(encoding="utf-8"))
    return {t["type"]: t for t in catalog["tiles"]}


def find_tile_catalog(models_dir):
    """按约定定位 tile_catalog.json: 模型目录的父目录 (data/) 优先,
    其次仓库根 data/ (脚本相对路径), 找不到返回 None。"""
    candidates = [
        Path(models_dir).resolve().parent / "tile_catalog.json",
        Path(__file__).resolve().parent.parent / "data" / "tile_catalog.json",
    ]
    for candidate in candidates:
        if candidate.is_file():
            return candidate
    return None


def rotation_matrix(rotation_deg):
    """R = Rz * Ry * Rx, 与 core::eulerZYX 一致。"""
    rx, ry, rz = (math.radians(d) for d in rotation_deg)
    cx, sx = math.cos(rx), math.sin(rx)
    cy, sy = math.cos(ry), math.sin(ry)
    cz, sz = math.cos(rz), math.sin(rz)
    return (
        (cz * cy, cz * sy * sx - sz * cx, cz * sy * cx + sz * sx),
        (sz * cy, sz * sy * sx + cz * cx, sz * sy * cx - cz * sx),
        (-sy, cy * sx, cy * cx),
    )


class TransformedTile:
    """一片磁力片的世界坐标几何: 顶点、磁力边、法向、接地状态。"""

    __slots__ = ("tile_id", "tile_type", "vertices", "magnet_edges", "normal",
                 "min_z")

    def __init__(self, tile, shape):
        self.tile_id = tile["id"]
        self.tile_type = tile["type"]
        rot = rotation_matrix(tile["rotation"])
        px, py, pz = tile["position"]
        self.vertices = [
            (rot[0][0] * lx + rot[0][1] * ly + px,
             rot[1][0] * lx + rot[1][1] * ly + py,
             rot[2][0] * lx + rot[2][1] * ly + pz)
            for lx, ly in shape["vertices"]
        ]
        self.min_z = min(v[2] for v in self.vertices)
        # 本地 +Z 经旋转 = R 的第三列
        self.normal = (rot[0][2], rot[1][2], rot[2][2])
        n = len(self.vertices)
        self.magnet_edges = [
            (self.vertices[i], self.vertices[(i + 1) % n])
            for i in shape["magnet_edges"]
        ]

    def touches_ground(self, tolerance=GROUND_TOLERANCE):
        return self.min_z <= tolerance


def transform_tiles(tiles, shapes):
    """批量转换; 形状目录缺失的 type 抛 KeyError (由调用方转为 FAIL)。"""
    return [TransformedTile(t, shapes[t["type"]]) for t in tiles]


def points_close(a, b, tolerance=CONNECT_TOLERANCE):
    return (math.dist(a, b) <= tolerance)


def _point_to_segment(p, a, b):
    """点到线段的最短距离。"""
    ab = (b[0] - a[0], b[1] - a[1], b[2] - a[2])
    len_sq = ab[0] * ab[0] + ab[1] * ab[1] + ab[2] * ab[2]
    if len_sq < 1e-12:
        return math.dist(p, a)
    t = ((p[0] - a[0]) * ab[0] + (p[1] - a[1]) * ab[1] + (p[2] - a[2]) * ab[2]) / len_sq
    t = max(0.0, min(1.0, t))
    return math.dist(p, (a[0] + ab[0] * t, a[1] + ab[1] * t, a[2] + ab[2] * t))


def edges_connect(edge_a, edge_b, tolerance=CONNECT_TOLERANCE):
    """磁力吸合判定: 短边被长边线段完整包含, 与 C++ R2 完全一致。

    等长整边贴合退化为端点两两重合 (正序或反序); 长短边搭配 (大正方形
    边长 2 吸小方边长 1, 长方形长边吸小方边等) 时短边两端点都落在长边
    上即吸合; 错位半搭 (短边端点悬出长边) 判为未连接。
    """
    (a1, b1), (a2, b2) = edge_a, edge_b
    if math.dist(a1, b1) <= math.dist(a2, b2):
        shorter, longer = (a1, b1), (a2, b2)
    else:
        shorter, longer = (a2, b2), (a1, b1)
    return (_point_to_segment(shorter[0], longer[0], longer[1]) <= tolerance
            and _point_to_segment(shorter[1], longer[0], longer[1]) <= tolerance)


def pose_class(normal_a, normal_b):
    """两片相对姿态类别: 共面 / 90° 折 / 其他角度 (CONTENT_STRATEGY.md 5.2)。"""
    d = abs(normal_a[0] * normal_b[0] + normal_a[1] * normal_b[1]
            + normal_a[2] * normal_b[2])
    if d > COPLANAR_NORMAL_DOT:
        return "coplanar"
    if d < FOLD90_NORMAL_DOT:
        return "fold90"
    return "angled"


class EdgeIndex:
    """磁力边空间索引: 按边中点所在网格单元分桶, 查询时扫相邻 27 单元。

    等长整边吸合时两条边的中点距离 <= connect_tolerance (0.02); 长短边
    搭配 (短边完整贴合在长边上) 时中点距离最大为 (长边-短边)/2, 目前
    最长磁力边约 2.06 (等腰三角形长腰)、最短为 1, 即至多约 0.53 + 容差。
    单元尺寸取 0.6 覆盖该距离, 相邻 27 单元扫描不会漏检。用于把逐片
    连通性检查从 O(已放边数) 降为 O(1) 邻域查询, 支撑 500 模型规模的
    批量执行。
    """

    CELL = 0.6

    def __init__(self):
        self._buckets = {}

    def _cell(self, edge):
        (a, b) = edge
        mx = (a[0] + b[0]) * 0.5
        my = (a[1] + b[1]) * 0.5
        mz = (a[2] + b[2]) * 0.5
        c = self.CELL
        return (math.floor(mx / c), math.floor(my / c), math.floor(mz / c))

    def add(self, tile_id, edge):
        self._buckets.setdefault(self._cell(edge), []).append((tile_id, edge))

    def add_tile(self, transformed):
        for edge in transformed.magnet_edges:
            self.add(transformed.tile_id, edge)

    def find_connection(self, edge, tolerance=CONNECT_TOLERANCE):
        """返回与 edge 吸合的 (tile_id, edge), 无则 None。"""
        cx, cy, cz = self._cell(edge)
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                for dz in (-1, 0, 1):
                    for tile_id, other in self._buckets.get(
                            (cx + dx, cy + dy, cz + dz), ()):
                        if edges_connect(edge, other, tolerance):
                            return tile_id, other
        return None


def build_connection_graph(transformed_tiles, tolerance=CONNECT_TOLERANCE):
    """构建磁力连接图: 返回邻接表 {下标: [(邻居下标, 姿态类别), ...]}。

    利用 EdgeIndex 做候选剪枝, 每对片只登记一条图边 (多条边吸合也算一条)。
    """
    index = EdgeIndex()
    for i, tile in enumerate(transformed_tiles):
        for edge in tile.magnet_edges:
            index.add(i, edge)

    adjacency = {i: [] for i in range(len(transformed_tiles))}
    seen_pairs = set()
    for i, tile in enumerate(transformed_tiles):
        for edge in tile.magnet_edges:
            cx, cy, cz = index._cell(edge)
            for dx in (-1, 0, 1):
                for dy in (-1, 0, 1):
                    for dz in (-1, 0, 1):
                        for j, other in index._buckets.get(
                                (cx + dx, cy + dy, cz + dz), ()):
                            if j <= i or (i, j) in seen_pairs:
                                continue
                            if edges_connect(edge, other, tolerance):
                                pc = pose_class(tile.normal,
                                                transformed_tiles[j].normal)
                                adjacency[i].append((j, pc))
                                adjacency[j].append((i, pc))
                                seen_pairs.add((i, j))
    return adjacency


def collect_model_files(args):
    """把命令行参数 (目录或文件混合) 展开为模型 JSON 列表。"""
    model_files = []
    for arg in args:
        path = Path(arg)
        if path.is_dir():
            model_files.extend(sorted(path.glob("*.json")))
        else:
            model_files.append(path)
    return model_files
