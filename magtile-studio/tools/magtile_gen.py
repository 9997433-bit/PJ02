#!/usr/bin/env python3
"""模型生成器共用几何库 (供 tools/generate_*.py import, 不直接运行)。

第二批 16 个模型的生成器共享的搭建词汇表: 与 C++ 端完全一致的
旋转/顶点数学 (include/magtile/core/vec3.hpp: R = Rz * Ry * Rx),
以及一组已被 R1~R8 物理校验反复验证过的结构件辅助函数:

  - flat / flat_rect             平铺正方形 / 长方形
  - wall_ns / wall_ew            单位正方形立墙 (南北向 / 东西向)
  - lintel_ns / lintel_ew        长方形横楣 (跨 2 格门洞)
  - crest_* / spire_*            立在沿口上的等边 / 等腰三角装饰
  - ramp                         30 度长方形坡道 (滚珠塔同款)
  - brace                        直角三角形斜撑 (摩天大楼同款)
  - hat4                         1x1 洞口的四坡三角锥顶
  - hip_roof2                    2x2 洞口的梯形四坡屋顶 + 正方形压顶
  - place_edge                   万能放置: 指定某条本地边贴到世界线段上
  - place_tri                    按三个世界顶点放置三角形

自检: finalize() 在写盘前重演 R2 (每片至少一条整边磁力吸合) 与
R7a (按步骤顺序逐片放置时接地或吸附), 提前拦截绝大多数几何笔误;
最终裁决仍以 `magtile_app validate` 的 C++ 校验器为准。

坐标约定与 C++ 端一致 (include/magtile/core/tile_instance.hpp):
  世界单位 1.0 = 正方形磁力片边长; 旋转为欧拉角 (度), R = Rz * Ry * Rx。
"""

import json
import math
from pathlib import Path

# ---- 常量 (与 data/tile_catalog.json 一致) ------------------------
TRI_CENTROID = round(math.sqrt(3) / 6, 6)      # 等边三角形质心到底边 0.288675
ISO_CENTROID = 0.666667                        # 等腰三角形质心到底边 (底 1 高 2 瘦高片)
ISO_H = 2.0                                    # 等腰三角形高 (实物瘦高比例)
ISO_SIDE = round(math.sqrt(4.25), 6)           # 等腰三角形腰长 2.061553
RT_THIRD = 1 / 3                               # 直角三角形质心到直角边
HEX_APOTHEM = round(math.sqrt(3) / 2, 6)       # 六边形中心到边 0.866025
COS30 = round(math.cos(math.radians(30)), 6)   # 0.866025
SQ3 = round(math.sqrt(3), 6)                   # 30 度坡道水平投影长 1.732051
PYR_TILT = round(math.degrees(math.atan(math.sqrt(2))), 6)  # 54.735610
EQ_APEX = round(math.sqrt(0.5), 6)             # 等边四坡锥顶高 0.707107
ISO_APEX = round(math.sqrt(3.75), 6)           # 等腰四坡锥顶高 1.936492 (高 2 瘦高片)
TRAP_H = 0.866025                              # 梯形高
TRAP_CENTROID = 0.3849                         # 梯形质心到下底

# 本地顶点表 (逆时针), 与 data/tile_catalog.json 完全一致
SHAPES = {
    "square": [(-0.5, -0.5), (0.5, -0.5), (0.5, 0.5), (-0.5, 0.5)],
    "large_square": [(-1.0, -1.0), (1.0, -1.0), (1.0, 1.0), (-1.0, 1.0)],
    # 窗格方 / 门框方: 外框与正方形完全一致, 窗格/镂空仅为语义标记
    # (hollow / variant, 见 docs/TILE_SET.md), 物理与拼接按实心正方形处理
    "window_square": [(-0.5, -0.5), (0.5, -0.5), (0.5, 0.5), (-0.5, 0.5)],
    "door_frame": [(-0.5, -0.5), (0.5, -0.5), (0.5, 0.5), (-0.5, 0.5)],
    "equilateral_triangle": [(-0.5, -0.288675), (0.5, -0.288675), (0.0, 0.57735)],
    "right_triangle": [(-0.333333, -0.333333), (0.666667, -0.333333), (-0.333333, 0.666667)],
    "isosceles_triangle": [(-0.5, -0.666667), (0.5, -0.666667), (0.0, 1.333333)],
    "rectangle": [(-1.0, -0.5), (1.0, -0.5), (1.0, 0.5), (-1.0, 0.5)],
    # 车轮底座: 外框与长方形完全一致, 车轮仅为语义标记 (wheeled)
    "wheel_base": [(-1.0, -0.5), (1.0, -0.5), (1.0, 0.5), (-1.0, 0.5)],
    "rhombus": [(-0.75, -0.433013), (0.25, -0.433013), (0.75, 0.433013), (-0.25, 0.433013)],
    "trapezoid": [(-1.0, -0.3849), (1.0, -0.3849), (0.5, 0.481125), (-0.5, 0.481125)],
    "hexagon": [(1.0, 0.0), (0.5, 0.866025), (-0.5, 0.866025), (-1.0, 0.0),
                (-0.5, -0.866025), (0.5, -0.866025)],
    "sector": [(0.0, 0.0), (1.0, 0.0), (0.965926, 0.258819), (0.866025, 0.5),
               (0.707107, 0.707107), (0.5, 0.866025), (0.258819, 0.965926), (0.0, 1.0)],
}
MAGNET_EDGES = {
    "square": (0, 1, 2, 3),
    "large_square": (0, 1, 2, 3),
    "window_square": (0, 1, 2, 3),
    "door_frame": (0, 1, 2, 3),
    "equilateral_triangle": (0, 1, 2),
    "right_triangle": (0, 1, 2),
    "isosceles_triangle": (0, 1, 2),
    "rectangle": (0, 1, 2, 3),
    "wheel_base": (0, 1, 2, 3),
    "rhombus": (0, 1, 2, 3),
    "trapezoid": (0, 1, 2, 3),
    "hexagon": (0, 1, 2, 3, 4, 5),
    "sector": (0, 7),
}


# ---- 与 C++ 端一致的旋转数学 --------------------------------------
def _rot_x(d):
    c, s = math.cos(math.radians(d)), math.sin(math.radians(d))
    return [[1, 0, 0], [0, c, -s], [0, s, c]]


def _rot_y(d):
    c, s = math.cos(math.radians(d)), math.sin(math.radians(d))
    return [[c, 0, s], [0, 1, 0], [-s, 0, c]]


def _rot_z(d):
    c, s = math.cos(math.radians(d)), math.sin(math.radians(d))
    return [[c, -s, 0], [s, c, 0], [0, 0, 1]]


def _mat_mul(a, b):
    return [[sum(a[i][k] * b[k][j] for k in range(3)) for j in range(3)] for i in range(3)]


def _mat_vec(m, v):
    return tuple(sum(m[i][k] * v[k] for k in range(3)) for i in range(3))


def euler_zyx(rot):
    """R = Rz * Ry * Rx (度), 与 core::eulerZYX 一致。"""
    return _mat_mul(_rot_z(rot[2]), _mat_mul(_rot_y(rot[1]), _rot_x(rot[0])))


def world_vertices(tile):
    m = euler_zyx(tile["rotation"])
    px, py, pz = tile["position"]
    out = []
    for lx, ly in SHAPES[tile["type"]]:
        wx, wy, wz = _mat_vec(m, (lx, ly, 0.0))
        out.append((wx + px, wy + py, wz + pz))
    return out


def _decompose_zyx(m):
    """旋转矩阵 -> 欧拉角 (度), 满足 R = Rz * Ry * Rx。"""
    sy = -m[2][0]
    sy = max(-1.0, min(1.0, sy))
    beta = math.asin(sy)
    if abs(math.cos(beta)) > 1e-9:
        alpha = math.atan2(m[2][1], m[2][2])
        gamma = math.atan2(m[1][0], m[0][0])
    else:  # 万向锁: 约定 alpha = 0
        alpha = 0.0
        gamma = math.atan2(-m[0][1], m[1][1])
    return (math.degrees(alpha), math.degrees(beta), math.degrees(gamma))


def _sub(a, b):
    return (a[0] - b[0], a[1] - b[1], a[2] - b[2])


def _cross(a, b):
    return (a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0])


def _dot(a, b):
    return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]


def _norm(a):
    l = math.sqrt(_dot(a, a))
    if l < 1e-12:
        raise ValueError("零向量无法归一化")
    return (a[0] / l, a[1] / l, a[2] / l)


class ModelBuilder:
    """收集磁力片与教程步骤, 自检后输出模型 JSON。"""

    def __init__(self):
        self.tiles = []
        self.steps = []
        self._ids = set()

    # ---- 基础放置 -------------------------------------------------
    def add(self, tile_id, tile_type, pos, rot, color):
        if tile_id in self._ids:
            raise ValueError(f"磁力片 id 重复: {tile_id}")
        self._ids.add(tile_id)
        self.tiles.append({
            "id": tile_id,
            "type": tile_type,
            "position": [round(v + 0.0, 6) for v in pos],
            "rotation": [round(v + 0.0, 6) for v in rot],
            "color": color,
        })

    def place_edge(self, tile_id, tile_type, edge_index, w_from, w_to, interior_hint, color):
        """万能放置: 使本地第 edge_index 条边贴合世界线段 w_from -> w_to。

        interior_hint: 大致指向形状内部 (相对该边) 的世界方向;
        形状平面 = 线段方向与该方向张成的平面。
        """
        verts = SHAPES[tile_type]
        l0 = verts[edge_index]
        l1 = verts[(edge_index + 1) % len(verts)]
        edge_len = math.hypot(l1[0] - l0[0], l1[1] - l0[1])
        seg = _sub(w_to, w_from)
        seg_len = math.sqrt(_dot(seg, seg))
        if abs(edge_len - seg_len) > 1e-4:
            raise ValueError(
                f"{tile_id}: 本地边长 {edge_len:.6f} 与世界线段长 {seg_len:.6f} 不一致")
        u_w = _norm(seg)
        m_raw = _sub(interior_hint, (0, 0, 0))
        m_w = _norm(_sub(m_raw, tuple(c * _dot(m_raw, u_w) for c in u_w)))
        n_w = _cross(u_w, m_w)
        # 本地系: 边方向 u_l, 内侧方向 m_l = n_l x u_l (顶点逆时针 => 内部在边左侧)
        u_l = _norm((l1[0] - l0[0], l1[1] - l0[1], 0.0))
        m_l = _cross((0, 0, 1), u_l)
        # R = [u_w m_w n_w] * [u_l m_l n_l]^T
        basis_w = [[u_w[i], m_w[i], n_w[i]] for i in range(3)]
        basis_l_t = [[u_l[0], u_l[1], u_l[2]],
                     [m_l[0], m_l[1], m_l[2]],
                     [0.0, 0.0, 1.0]]
        rot_m = _mat_mul(basis_w, basis_l_t)
        rot = _decompose_zyx(rot_m)
        anchor = _mat_vec(euler_zyx(rot), (l0[0], l0[1], 0.0))
        pos = _sub(w_from, anchor)
        self.add(tile_id, tile_type, pos, rot, color)
        # 重建校验: 该边端点必须精确落到目标线段上
        wv = world_vertices(self.tiles[-1])
        got = (wv[edge_index], wv[(edge_index + 1) % len(wv)])
        for got_p, want_p in zip(got, (w_from, w_to)):
            if math.dist(got_p, want_p) > 1e-4:
                raise AssertionError(f"{tile_id}: place_edge 重建误差过大 {got_p} != {want_p}")

    def place_tri(self, tile_id, tile_type, w0, w1, w2, color):
        """按三个世界顶点放置三角形 (顶点顺序对应本地顶点 0/1/2)。"""
        mid = tuple((w0[i] + w1[i]) / 3 + w2[i] / 3 for i in range(3))
        self.place_edge(tile_id, tile_type, 0, w0, w1, _sub(w2, mid), color)
        wv = world_vertices(self.tiles[-1])
        if math.dist(wv[2], w2) > 1e-4:
            raise AssertionError(f"{tile_id}: 第三顶点 {wv[2]} 未落在 {w2}")

    # ---- 平铺 -----------------------------------------------------
    def flat(self, tile_id, x0, y0, z, color):
        """平铺正方形, 覆盖 [x0,x0+1] x [y0,y0+1]。"""
        self.add(tile_id, "square", (x0 + 0.5, y0 + 0.5, z), (0, 0, 0), color)

    def flat_rect(self, tile_id, x0, y0, z, color, axis="x"):
        """平铺长方形: axis='x' 覆盖 2x1, axis='y' 覆盖 1x2。"""
        if axis == "x":
            self.add(tile_id, "rectangle", (x0 + 1.0, y0 + 0.5, z), (0, 0, 0), color)
        else:
            self.add(tile_id, "rectangle", (x0 + 0.5, y0 + 1.0, z), (0, 0, 90), color)

    # ---- 立墙 -----------------------------------------------------
    def wall_ns(self, tile_id, x0, y, z0, color):
        """南北朝向立墙 (平面 y=y), 覆盖 x [x0,x0+1], z [z0,z0+1]。"""
        self.add(tile_id, "square", (x0 + 0.5, y, z0 + 0.5), (90, 0, 0), color)

    def wall_ew(self, tile_id, x, y0, z0, color):
        """东西朝向立墙 (平面 x=x), 覆盖 y [y0,y0+1], z [z0,z0+1]。"""
        self.add(tile_id, "square", (x, y0 + 0.5, z0 + 0.5), (90, 0, 90), color)

    def lintel_ns(self, tile_id, x0, y, z0, color):
        """南北向长方形横楣: 覆盖 x [x0,x0+2], z [z0,z0+1]。"""
        self.add(tile_id, "rectangle", (x0 + 1.0, y, z0 + 0.5), (90, 0, 0), color)

    def lintel_ew(self, tile_id, x, y0, z0, color):
        """东西向长方形横楣: 覆盖 y [y0,y0+2], z [z0,z0+1]。"""
        self.add(tile_id, "rectangle", (x, y0 + 1.0, z0 + 0.5), (90, 0, 90), color)

    # ---- 沿口立三角 -----------------------------------------------
    def crest_ns(self, tile_id, x0, y, z, color):
        """等边三角形立在南北向沿口, 底边落在高度 z。"""
        self.add(tile_id, "equilateral_triangle",
                 (x0 + 0.5, y, z + TRI_CENTROID), (90, 0, 0), color)

    def crest_ew(self, tile_id, x, y0, z, color):
        self.add(tile_id, "equilateral_triangle",
                 (x, y0 + 0.5, z + TRI_CENTROID), (90, 0, 90), color)

    def spire_ns(self, tile_id, x0, y, z, color):
        """等腰三角形高塔尖立在南北向沿口, 底边落在高度 z。"""
        self.add(tile_id, "isosceles_triangle",
                 (x0 + 0.5, y, z + ISO_CENTROID), (90, 0, 0), color)

    def spire_ew(self, tile_id, x, y0, z, color):
        self.add(tile_id, "isosceles_triangle",
                 (x, y0 + 0.5, z + ISO_CENTROID), (90, 0, 90), color)

    # ---- 坡道 (滚珠塔同款 30 度长方形) -----------------------------
    def ramp(self, tile_id, direction, edge, lane0, z_top, color):
        """30 度长方形坡道: 顶边在网格线 edge 高度 z_top, 坡尾在 z_top-1。"""
        if direction == "+x":
            self.add(tile_id, "rectangle",
                     (edge + COS30, lane0 + 0.5, z_top - 0.5), (0, 30, 0), color)
        elif direction == "-x":
            self.add(tile_id, "rectangle",
                     (edge - COS30, lane0 + 0.5, z_top - 0.5), (0, -30, 0), color)
        elif direction == "+y":
            self.add(tile_id, "rectangle",
                     (lane0 + 0.5, edge + COS30, z_top - 0.5), (0, 30, 90), color)
        elif direction == "-y":
            self.add(tile_id, "rectangle",
                     (lane0 + 0.5, edge - COS30, z_top - 0.5), (0, -30, 90), color)
        else:
            raise ValueError(direction)

    # ---- 直角三角形斜撑 (摩天大楼同款) -----------------------------
    def brace(self, tile_id, corner, horiz_dir, color):
        """直角三角形斜撑: 直角顶点在 corner, 水平直角边指向 horiz_dir,
        竖直直角边向上。两条直角边分别吸住楼板边与墙竖边。"""
        h = {"+x": (1, 0, 0), "-x": (-1, 0, 0), "+y": (0, 1, 0), "-y": (0, -1, 0)}[horiz_dir]
        w0 = tuple(corner)
        w1 = (corner[0] + h[0], corner[1] + h[1], corner[2] + h[2])
        w2 = (corner[0], corner[1], corner[2] + 1.0)
        self.place_tri(tile_id, "right_triangle", w0, w1, w2, color)

    # ---- 屋顶 -----------------------------------------------------
    def hat4(self, prefix, x0, y0, z, color, shape="isosceles_triangle"):
        """1x1 洞口 [x0,x0+1]x[y0,y0+1] 的四坡三角锥顶, 返回 4 个 id。

        等腰 (瘦高片): 内倾 75.52 度, 锥尖高 z+1.936;
        等边: 内倾 54.74 度, 锥尖高 z+0.707。
        四条斜棱两两互吸, 自锁成环 (摩天大楼金顶同款)。
        """
        apex_h = ISO_APEX if shape == "isosceles_triangle" else EQ_APEX
        apex = (x0 + 0.5, y0 + 0.5, z + apex_h)
        bases = {
            "s": ((x0, y0, z), (x0 + 1, y0, z)),
            "e": ((x0 + 1, y0, z), (x0 + 1, y0 + 1, z)),
            "n": ((x0 + 1, y0 + 1, z), (x0, y0 + 1, z)),
            "w": ((x0, y0 + 1, z), (x0, y0, z)),
        }
        ids = []
        for side, (b0, b1) in bases.items():
            tid = f"{prefix}_{side}"
            self.place_tri(tid, shape, b0, b1, apex, color)
            ids.append(tid)
        return ids

    def hip_roof2(self, prefix, x0, y0, z, color, cap_color=None):
        """2x2 洞口 [x0,x0+2]x[y0,y0+2] 的梯形四坡屋顶 + 正方形压顶。

        四片梯形下底吸洞口沿边 (下底长 2, 须与长方形楼板长边等长贴合),
        腰两两互吸, 上底围成 1x1 洞口由压顶正方形封住 (高 z+0.707)。
        返回 (梯形 id 列表, 压顶 id)。
        """
        zt = z + EQ_APEX
        faces = {
            # side: (下底两端点, 上底中点 —— hint 必须精确落在面内)
            "s": ((x0, y0, z), (x0 + 2, y0, z), (x0 + 1.0, y0 + 0.5, zt)),
            "e": ((x0 + 2, y0, z), (x0 + 2, y0 + 2, z), (x0 + 1.5, y0 + 1.0, zt)),
            "n": ((x0 + 2, y0 + 2, z), (x0, y0 + 2, z), (x0 + 1.0, y0 + 1.5, zt)),
            "w": ((x0, y0 + 2, z), (x0, y0, z), (x0 + 0.5, y0 + 1.0, zt)),
        }
        ids = []
        for side, (b0, b1, top_mid) in faces.items():
            tid = f"{prefix}_{side}"
            bottom_mid = tuple((b0[i] + b1[i]) / 2 for i in range(3))
            self.place_edge(tid, "trapezoid", 0, b0, b1, _sub(top_mid, bottom_mid), color)
            ids.append(tid)
        cap_id = f"{prefix}_cap"
        self.flat(cap_id, x0 + 0.5, y0 + 0.5, zt, cap_color or color)
        return ids, cap_id

    # ---- 教程步骤 --------------------------------------------------
    def step(self, description, tiles_to_add, highlight=(), tip=""):
        for tid in tiles_to_add:
            if tid not in self._ids:
                raise ValueError(f"步骤引用了不存在的磁力片: {tid}")
        self.steps.append({
            "step_number": len(self.steps) + 1,
            "description": description,
            "tip": tip,
            "tiles_to_add": list(tiles_to_add),
            "highlight_tiles": list(highlight),
        })

    # ---- 自检 (预演 R2 / R7a, 提前拦截几何笔误) --------------------
    def _self_check(self):
        geo = {}
        for t in self.tiles:
            verts = world_vertices(t)
            edges = []
            for i in MAGNET_EDGES[t["type"]]:
                edges.append((verts[i], verts[(i + 1) % len(verts)]))
            min_z = min(v[2] for v in verts)
            geo[t["id"]] = (edges, min_z)

        def snapped(edges_a, edges_b):
            for a0, a1 in edges_a:
                for b0, b1 in edges_b:
                    if ((math.dist(a0, b0) <= 0.02 and math.dist(a1, b1) <= 0.02)
                            or (math.dist(a0, b1) <= 0.02 and math.dist(a1, b0) <= 0.02)):
                        return True
            return False

        # R2 预演: 每片至少与一片整边吸合
        all_ids = [t["id"] for t in self.tiles]
        if len(all_ids) > 1:
            for tid in all_ids:
                if not any(snapped(geo[tid][0], geo[o][0]) for o in all_ids if o != tid):
                    raise AssertionError(f"自检失败 (R2): {tid} 没有任何整边磁力吸合")

        # R7a 预演: 按步骤顺序逐片放置须接地或吸附
        placed = []
        for s in self.steps:
            for tid in s["tiles_to_add"]:
                grounded = geo[tid][1] <= 0.02
                attached = any(snapped(geo[tid][0], geo[p][0]) for p in placed)
                if not grounded and not attached:
                    raise AssertionError(
                        f"自检失败 (R7a): 第 {s['step_number']} 步的 {tid} "
                        f"放下瞬间既不接地也吸不到已放置磁力片")
                placed.append(tid)

    # ---- 汇总输出 --------------------------------------------------
    def finalize(self, *, model_id, name, name_en, description, difficulty, tags,
                 min_pieces, min_steps):
        placed = [tid for s in self.steps for tid in s["tiles_to_add"]]
        assert len(placed) == len(self.tiles) == len(set(placed)), \
            "步骤必须恰好覆盖全部磁力片"
        assert len(self.tiles) >= min_pieces, \
            f"{model_id} 片数 {len(self.tiles)} 低于目标 {min_pieces}"
        assert len(self.steps) >= min_steps, \
            f"{model_id} 步数 {len(self.steps)} 低于目标 {min_steps}"
        for s in self.steps:
            assert 1 <= len(s["tiles_to_add"]) <= 12, \
                f"第 {s['step_number']} 步放置 {len(s['tiles_to_add'])} 片, 超出 1~12 粒度"
        self._self_check()

        # BOM 备料清单: tests/test_model_logic.py 核对其与 final_assembly 一致
        bom = {}
        for t in self.tiles:
            bom[t["type"]] = bom.get(t["type"], 0) + 1
        bom = dict(sorted(bom.items(), key=lambda kv: (-kv[1], kv[0])))

        model = {
            "schema_version": 1,
            "id": model_id,
            "name": name,
            "name_en": name_en,
            "description": description,
            "difficulty": difficulty,
            "total_pieces": len(self.tiles),
            "tags": list(tags),
            "content_meta": {
                "structural_signature": {
                    "tile_histogram": bom,
                },
            },
            "final_assembly": self.tiles,
            "steps": self.steps,
        }

        out = Path(__file__).resolve().parent.parent / "data" / "models" / f"{model_id}.json"
        out.write_text(json.dumps(model, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        by_type = ", ".join(f"{k} x {v}" for k, v in sorted(bom.items()))
        print(f"已生成 {out} ({len(self.tiles)} 片, {len(self.steps)} 步)")
        print(f"片形统计: {by_type}")
        return model
