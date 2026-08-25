#!/usr/bin/env python3
"""生成模型库缩略图 data/thumbnails/<id>.png (模型卡片用)。

对每个 data/models/*.json 模型, 按优先级尝试三种渲染方式:

  1. gl 离线渲染 (mode=auto/gl): 调用
         magtile_app tutorial <model> --gui --step <末步> --frames 5
                     --screenshot <tmp.ppm>
     在无头环境下经 xvfb-run 跑真实 OpenGL 管线, 截取最终成品画面,
     内容感知裁剪 (自动找到画面中的彩色模型区域, 避开 HUD 面板)
     后缩放为 320x240;
  2. procedural 程序化预览 (mode=procedural 或 GL 不可用/翻车):
     纯 Python 复算模型几何 (与 tests/magtile_geom.py 同一套约定),
     以轴测投影 + 画家算法逐片填色, 不依赖任何显示环境与三方库;
  3. placeholder 主题色占位图 (mode=placeholder 或模型加载失败):
     按主题色生成简单的斜纹占位 PNG。

输出一律为 8-bit RGB PNG (纯标准库编码, 无 PIL 依赖)。生成后请运行
tools/update_model_catalog.py 把 thumbnail 路径登记进模型库目录。

用法 (在 magtile-studio 目录下运行):
  python3 tools/generate_thumbnails.py                 # auto: GL 优先, 失败回退
  python3 tools/generate_thumbnails.py --mode procedural
  python3 tools/generate_thumbnails.py --only butterfly_01 --force
  python3 tools/generate_thumbnails.py --app build/magtile_app
"""

import argparse
import json
import math
import os
import shutil
import struct
import subprocess
import sys
import tempfile
import zlib
from pathlib import Path

from update_model_catalog import derive_theme

ROOT = Path(__file__).resolve().parent.parent
MODELS_DIR = ROOT / "data" / "models"
THUMBS_DIR = ROOT / "data" / "thumbnails"
TILE_CATALOG = ROOT / "data" / "tile_catalog.json"

THUMB_W, THUMB_H = 320, 240  # 4:3, 与模型卡片图区一致

# 磁力片基准色, 与 src/render/gl/gl_renderer.cpp tileBaseColor 一致
TILE_COLORS = {
    "red": (232, 56, 64),
    "orange": (250, 140, 38),
    "yellow": (252, 212, 46),
    "green": (71, 191, 92),
    "cyan": (51, 189, 209),
    "blue": (59, 117, 230),
    "purple": (148, 92, 219),
    "pink": (242, 122, 179),
    "clear": (217, 230, 240),
    "gray": (140, 148, 158),
}

# 主题 -> 主题色, 与 src/render/gl/gl_renderer.cpp themeColor32 一致
THEME_COLORS = {
    "城堡王国": (103, 111, 219),
    "建筑地标": (66, 133, 244),
    "工程结构": (230, 124, 55),
    "自然世界": (52, 168, 111),
    "航天探索": (126, 87, 194),
    "城市生活": (220, 88, 70),
    "游乐园": (236, 64, 122),
    "滚珠乐园": (0, 172, 193),
    "海洋航行": (2, 136, 209),
}
FALLBACK_THEME_COLOR = (66, 133, 244)


# =============================================================
# 图像基元: 纯标准库的 RGB 光栅 + PPM 读取 + PNG 写出
# =============================================================

class Raster:
    """朴素 RGB 光栅: bytearray 逐像素存 (r, g, b)。"""

    def __init__(self, width, height, fill=(255, 255, 255)):
        self.width = width
        self.height = height
        self.px = bytearray(bytes(fill) * (width * height))

    def put(self, x, y, color):
        if 0 <= x < self.width and 0 <= y < self.height:
            i = (y * self.width + x) * 3
            self.px[i:i + 3] = bytes(color)

    def hspan(self, x0, x1, y, color):
        """水平实心线段 [x0, x1] (含端点), 越界自动截断。"""
        if y < 0 or y >= self.height:
            return
        x0 = max(0, x0)
        x1 = min(self.width - 1, x1)
        if x0 > x1:
            return
        i = (y * self.width + x0) * 3
        self.px[i:i + (x1 - x0 + 1) * 3] = bytes(color) * (x1 - x0 + 1)

    def line(self, p0, p1, color):
        """DDA 直线 (缩略图描边用, 无需亚像素精度)。"""
        x0, y0 = p0
        x1, y1 = p1
        steps = max(abs(x1 - x0), abs(y1 - y0), 1e-6)
        n = int(steps) + 1
        for k in range(n + 1):
            t = k / n
            self.put(int(x0 + (x1 - x0) * t), int(y0 + (y1 - y0) * t), color)

    def fill_polygon(self, points, color):
        """偶奇规则扫描线填充凸/凹多边形 (points 为浮点屏幕坐标)。"""
        if len(points) < 3:
            return
        y_min = max(0, int(math.floor(min(p[1] for p in points))))
        y_max = min(self.height - 1, int(math.ceil(max(p[1] for p in points))))
        n = len(points)
        for y in range(y_min, y_max + 1):
            yc = y + 0.5
            xs = []
            for i in range(n):
                (ax, ay), (bx, by) = points[i], points[(i + 1) % n]
                if (ay <= yc < by) or (by <= yc < ay):
                    xs.append(ax + (yc - ay) * (bx - ax) / (by - ay))
            xs.sort()
            for j in range(0, len(xs) - 1, 2):
                self.hspan(int(math.ceil(xs[j] - 0.5)),
                           int(math.floor(xs[j + 1] - 0.5)), y, color)


def write_png(path, raster):
    """最小 PNG 编码器: 8-bit RGB, 每行滤波器 0, 单个 IDAT。"""
    def chunk(tag, payload):
        data = tag + payload
        return struct.pack(">I", len(payload)) + data + struct.pack(
            ">I", zlib.crc32(data) & 0xFFFFFFFF)

    w, h = raster.width, raster.height
    row_bytes = w * 3
    scanlines = bytearray()
    for y in range(h):
        scanlines.append(0)  # 滤波器: None
        scanlines += raster.px[y * row_bytes:(y + 1) * row_bytes]

    png = bytearray(b"\x89PNG\r\n\x1a\n")
    png += chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0))
    png += chunk(b"IDAT", zlib.compress(bytes(scanlines), 9))
    png += chunk(b"IEND", b"")
    Path(path).write_bytes(png)


def read_ppm(path):
    """读取渲染器输出的 PPM (P6, maxval 255), 返回 Raster。"""
    data = Path(path).read_bytes()
    if not data.startswith(b"P6"):
        raise ValueError(f"{path}: 不是 PPM (P6) 文件")
    # 头部: P6 <width> <height> <maxval>\n, 允许注释行
    pos, fields = 2, []
    while len(fields) < 3:
        while pos < len(data) and data[pos] in b" \t\r\n":
            pos += 1
        if data[pos:pos + 1] == b"#":
            while pos < len(data) and data[pos] not in b"\r\n":
                pos += 1
            continue
        start = pos
        while pos < len(data) and data[pos] not in b" \t\r\n":
            pos += 1
        fields.append(int(data[start:pos]))
    pos += 1  # maxval 后单个空白
    width, height, maxval = fields
    if maxval != 255:
        raise ValueError(f"{path}: 不支持 maxval={maxval}")
    raster = Raster(width, height)
    raster.px = bytearray(data[pos:pos + width * height * 3])
    if len(raster.px) != width * height * 3:
        raise ValueError(f"{path}: 像素数据不完整")
    return raster


def resample(src, x0, y0, x1, y1, out_w, out_h):
    """把 src 的 [x0,x1)x[y0,y1) 区域盒式采样缩放为 out_w x out_h。"""
    out = Raster(out_w, out_h)
    sx = (x1 - x0) / out_w
    sy = (y1 - y0) / out_h
    k = max(1, int(math.ceil(max(sx, sy))))  # 每目标像素采样 k x k 个源点
    for ty in range(out_h):
        for tx in range(out_w):
            r = g = b = cnt = 0
            for j in range(k):
                yy = int(y0 + (ty + (j + 0.5) / k) * sy)
                if yy < 0 or yy >= src.height:
                    continue
                row = yy * src.width
                for i in range(k):
                    xx = int(x0 + (tx + (i + 0.5) / k) * sx)
                    if xx < 0 or xx >= src.width:
                        continue
                    p = (row + xx) * 3
                    r += src.px[p]
                    g += src.px[p + 1]
                    b += src.px[p + 2]
                    cnt += 1
            if cnt:
                out.put(tx, ty, (r // cnt, g // cnt, b // cnt))
    return out


def mix(a, b, t):
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))


# =============================================================
# 方式 1: GL 离线渲染 (真实渲染管线截图)
# =============================================================

def gl_runner_prefix():
    """无显示环境时用 xvfb-run 包一层; 都不可用返回 None (GL 不可用)。"""
    if shutil.which("xvfb-run"):
        return ["xvfb-run", "-a", "-s", "-screen 0 1600x1000x24"]
    if os.environ.get("DISPLAY"):
        return []
    return None


def content_crop_box(shot):
    """内容感知裁剪: 找到画面中彩色 (高饱和度) 模型区域的包围盒。

    先 4x4 盒式降采样 (顺带把 1~2px 的网格轴线摊薄进背景), 在小图上
    做饱和度掩码 + 邻域腐蚀去噪, 再把包围盒映射回原图坐标。为避开
    教程 HUD, 掩码排除左上信息面板与底部步骤面板所在区域。
    返回 (x0, y0, x1, y1); 未检测到内容时返回 None (视为渲染翻车)。
    """
    step = 4
    small_w, small_h = shot.width // step, shot.height // step
    hud_left_x, hud_left_y = 360 // step, 130 // step   # 左上信息面板
    hud_bottom_y = (shot.height - 240) // step          # 底部步骤面板

    mask = [[False] * small_w for _ in range(small_h)]
    for sy in range(small_h):
        if sy >= hud_bottom_y:
            continue
        for sx in range(small_w):
            if sx < hud_left_x and sy < hud_left_y:
                continue
            r = g = b = 0
            for j in range(step):
                p = ((sy * step + j) * shot.width + sx * step) * 3
                for i in range(step):
                    r += shot.px[p]
                    g += shot.px[p + 1]
                    b += shot.px[p + 2]
                    p += 3
            n = step * step
            r, g, b = r // n, g // n, b // n
            hi, lo = max(r, g, b), min(r, g, b)
            if hi > 40 and (hi - lo) / hi > 0.25:  # HSV 饱和度阈值
                mask[sy][sx] = True

    # 邻域腐蚀: 至少 3 个八邻域同为内容才保留, 去掉孤立噪点
    xs, ys = [], []
    for sy in range(1, small_h - 1):
        for sx in range(1, small_w - 1):
            if not mask[sy][sx]:
                continue
            neighbors = sum(mask[sy + j][sx + i]
                            for j in (-1, 0, 1) for i in (-1, 0, 1)
                            if (i, j) != (0, 0))
            if neighbors >= 3:
                xs.append(sx)
                ys.append(sy)
    if not xs:
        return None

    margin = 28
    x0 = max(0, min(xs) * step - margin)
    x1 = min(shot.width, (max(xs) + 1) * step + margin)
    y0 = max(0, min(ys) * step - margin)
    y1 = min(shot.height - 200, (max(ys) + 1) * step + margin)
    if x1 - x0 < 64 or y1 - y0 < 48:
        return None

    # 扩成 4:3 (缩略图无形变), 越界时向另一侧滑动
    target = THUMB_W / THUMB_H
    w, h = x1 - x0, y1 - y0
    if w / h > target:
        grow = w / target - h
        y0 -= grow / 2
        y1 += grow / 2
    else:
        grow = h * target - w
        x0 -= grow / 2
        x1 += grow / 2
    if x0 < 0:
        x1 -= x0
        x0 = 0
    if y0 < 0:
        y1 -= y0
        y0 = 0
    x1 = min(x1, shot.width)
    y1 = min(y1, shot.height)
    return int(x0), int(y0), int(x1), int(y1)


def render_gl(app, runner, model_file, step_count):
    """离线 GL 渲染最终成品并裁剪为缩略图; 任何一步翻车返回 None。"""
    with tempfile.TemporaryDirectory(prefix="magtile_thumb_") as tmp:
        shot_path = Path(tmp) / "shot.ppm"
        cmd = runner + [
            str(app), "tutorial", str(model_file), "--data-dir",
            str(ROOT / "data"), "--gui", "--step", str(step_count),
            "--frames", "5", "--screenshot", str(shot_path),
        ]
        try:
            result = subprocess.run(cmd, capture_output=True, timeout=120)
        except (subprocess.TimeoutExpired, OSError) as e:
            print(f"    [gl] 渲染进程异常: {e}")
            return None
        if result.returncode != 0:
            print(f"    [gl] 渲染退出码 {result.returncode}")
            return None
        if not shot_path.is_file() or shot_path.stat().st_size == 0:
            print("    [gl] 未生成截图")
            return None
        try:
            shot = read_ppm(shot_path)
        except ValueError as e:
            print(f"    [gl] 截图不可读: {e}")
            return None

    box = content_crop_box(shot)
    if box is None:
        print("    [gl] 截图中未检测到模型内容 (疑似空白/纯色)")
        return None
    return resample(shot, *box, THUMB_W, THUMB_H)


# =============================================================
# 方式 2: 程序化预览 (纯 Python 轴测投影 + 画家算法)
# =============================================================

def rotation_matrix(rotation_deg):
    """R = Rz * Ry * Rx, 与 core::eulerZYX / tests/magtile_geom.py 一致。"""
    rx, ry, rz = (math.radians(d) for d in rotation_deg)
    cx, sx = math.cos(rx), math.sin(rx)
    cy, sy = math.cos(ry), math.sin(ry)
    cz, sz = math.cos(rz), math.sin(rz)
    return (
        (cz * cy, cz * sy * sx - sz * cx, cz * sy * cx + sz * sx),
        (sz * cy, sz * sy * sx + cz * cx, sz * sy * cx - cz * sx),
        (-sy, cy * sx, cy * cx),
    )


def normalize(v):
    n = math.sqrt(v[0] * v[0] + v[1] * v[1] + v[2] * v[2])
    return (v[0] / n, v[1] / n, v[2] / n)


def dot(a, b):
    return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]


def cross(a, b):
    return (a[1] * b[2] - a[2] * b[1],
            a[2] * b[0] - a[0] * b[2],
            a[0] * b[1] - a[1] * b[0])


def render_procedural(model, shapes, theme):
    """轴测投影渲染最终成品: 与 GL 后端同一套几何约定与配色。"""
    # ---- 世界坐标几何 (逐片: 顶点 + 法向 + 颜色) --------------------
    tiles = []
    for inst in model["final_assembly"]:
        shape = shapes[inst["type"]]
        rot = rotation_matrix(inst["rotation"])
        px, py, pz = inst["position"]
        vertices = [
            (rot[0][0] * lx + rot[0][1] * ly + px,
             rot[1][0] * lx + rot[1][1] * ly + py,
             rot[2][0] * lx + rot[2][1] * ly + pz)
            for lx, ly in shape["vertices"]
        ]
        normal = (rot[0][2], rot[1][2], rot[2][2])
        tiles.append((vertices, normal,
                      TILE_COLORS.get(inst["color"], (140, 148, 158))))
    if not tiles:
        return None

    # ---- 相机基 (与 GL 默认视角同方向: 从东南上方看向模型中心) -------
    all_points = [v for vertices, _, _ in tiles for v in vertices]
    center = tuple(sum(p[i] for p in all_points) / len(all_points)
                   for i in range(3))
    forward = normalize((-1.0, 1.0, -0.85))  # 视线方向
    right = normalize(cross(forward, (0.0, 0.0, 1.0)))
    up = cross(right, forward)

    def project(p):
        d = (p[0] - center[0], p[1] - center[1], p[2] - center[2])
        return dot(d, right), dot(d, up), dot(d, forward)

    projected = []  # (深度, 屏幕平面多边形, 填充色)
    light = normalize((0.35, 0.25, 0.9))
    for vertices, normal, base in tiles:
        pts = [project(v) for v in vertices]
        depth = sum(p[2] for p in pts) / len(pts)
        shade = 0.55 + 0.45 * abs(dot(normal, light))
        fill = tuple(min(255, int(c * shade + 24)) for c in base)
        projected.append((depth, [(p[0], p[1]) for p in pts], fill))

    # ---- 视口拟合 (2x 超采样渲染, 收尾降采样抗锯齿) ------------------
    render_w, render_h = THUMB_W * 2, THUMB_H * 2
    xs = [x for _, pts, _ in projected for x, _ in pts]
    ys = [y for _, pts, _ in projected for _, y in pts]
    span_x = max(xs) - min(xs) or 1.0
    span_y = max(ys) - min(ys) or 1.0
    scale = min(render_w * 0.86 / span_x, render_h * 0.86 / span_y)
    off_x = render_w / 2 - (min(xs) + max(xs)) / 2 * scale
    off_y = render_h / 2 + (min(ys) + max(ys)) / 2 * scale

    def to_screen(x, y):
        return x * scale + off_x, -y * scale + off_y  # 屏幕 y 向下

    theme_color = THEME_COLORS.get(theme, FALLBACK_THEME_COLOR)
    img = Raster(render_w, render_h)
    for y in range(render_h):  # 背景: 白 -> 主题色淡染的竖向渐变
        img.hspan(0, render_w - 1, y,
                  mix((248, 250, 252), mix(theme_color, (255, 255, 255), 0.82),
                      y / render_h))

    # 地面网格 (z=0 平面, 覆盖模型 xy 范围外扩 2 格), 提供空间感
    gx0 = math.floor(min(p[0] for p in all_points)) - 2
    gx1 = math.ceil(max(p[0] for p in all_points)) + 2
    gy0 = math.floor(min(p[1] for p in all_points)) - 2
    gy1 = math.ceil(max(p[1] for p in all_points)) + 2
    grid_color = (214, 220, 228)
    for gx in range(gx0, gx1 + 1):
        a = project((gx, gy0, 0.0))
        b = project((gx, gy1, 0.0))
        img.line(to_screen(*a[:2]), to_screen(*b[:2]), grid_color)
    for gy in range(gy0, gy1 + 1):
        a = project((gx0, gy, 0.0))
        b = project((gx1, gy, 0.0))
        img.line(to_screen(*a[:2]), to_screen(*b[:2]), grid_color)

    # 画家算法: 由远及近逐片填色 + 深色描边
    projected.sort(key=lambda t: -t[0])
    for _, pts, fill in projected:
        screen_pts = [to_screen(x, y) for x, y in pts]
        img.fill_polygon(screen_pts, fill)
        edge = tuple(int(c * 0.62) for c in fill)
        for i in range(len(screen_pts)):
            img.line(screen_pts[i], screen_pts[(i + 1) % len(screen_pts)],
                     edge)

    return resample(img, 0, 0, render_w, render_h, THUMB_W, THUMB_H)


# =============================================================
# 方式 3: 主题色占位图 (最后兜底)
# =============================================================

def render_placeholder(theme):
    """主题色斜纹占位图: 模型几何都不可用时的最后兜底。"""
    theme_color = THEME_COLORS.get(theme, FALLBACK_THEME_COLOR)
    light = mix(theme_color, (255, 255, 255), 0.78)
    lighter = mix(theme_color, (255, 255, 255), 0.86)
    img = Raster(THUMB_W, THUMB_H)
    for y in range(THUMB_H):
        for x in range(THUMB_W):
            img.put(x, y, light if ((x + y) // 24) % 2 == 0 else lighter)
    # 中央主题色横条, 与卡片主题角标呼应
    bar_h = 44
    y0 = (THUMB_H - bar_h) // 2
    for y in range(y0, y0 + bar_h):
        img.hspan(0, THUMB_W - 1, y, mix(theme_color, (255, 255, 255), 0.25))
    return img


# =============================================================
# 主流程
# =============================================================

def main():
    parser = argparse.ArgumentParser(description="生成模型库缩略图 PNG")
    parser.add_argument("--mode", choices=["auto", "gl", "procedural",
                                           "placeholder"], default="auto",
                        help="auto: GL 优先, 失败回退程序化预览 (默认)")
    parser.add_argument("--app", type=Path,
                        default=ROOT / "build" / "magtile_app",
                        help="magtile_app 可执行文件 (GL 渲染用)")
    parser.add_argument("--only", nargs="*", default=None, metavar="MODEL_ID",
                        help="只生成指定模型 (默认全部)")
    parser.add_argument("--force", action="store_true",
                        help="已存在的缩略图也重新生成")
    args = parser.parse_args()

    shapes = {t["type"]: t
              for t in json.loads(TILE_CATALOG.read_text(encoding="utf-8"))
              ["tiles"]}
    THUMBS_DIR.mkdir(parents=True, exist_ok=True)

    # GL 可用性: 需要可执行文件 + 显示环境 (xvfb-run 或 DISPLAY)
    runner = gl_runner_prefix()
    gl_available = args.mode in ("auto", "gl") and args.app.is_file() and \
        os.access(args.app, os.X_OK) and runner is not None
    if args.mode in ("auto", "gl") and not gl_available:
        reason = "无显示环境 (xvfb-run/DISPLAY)" if runner is None else \
            f"未找到可执行文件 {args.app} (先构建: cmake -S . -B build && cmake --build build -j)"
        if args.mode == "gl":
            print(f"错误: GL 渲染不可用: {reason}")
            return 1
        print(f"[信息] GL 渲染不可用 ({reason}), 全部改用程序化预览")

    generated, skipped, failures = [], [], []
    for model_file in sorted(MODELS_DIR.glob("*.json")):
        try:
            model = json.loads(model_file.read_text(encoding="utf-8"))
            model_id = model["id"]
            theme = derive_theme(model)
        except (ValueError, KeyError) as e:
            print(f"[警告] 跳过不可读的模型文件 {model_file.name}: {e}")
            failures.append(model_file.stem)
            continue
        if args.only is not None and model_id not in args.only:
            continue

        out_path = THUMBS_DIR / f"{model_id}.png"
        if out_path.is_file() and not args.force:
            skipped.append(model_id)
            continue

        print(f"[{model_id}] 生成缩略图 (主题: {theme})...")
        img = None
        source = None
        if args.mode == "placeholder":
            img, source = render_placeholder(theme), "placeholder"
        else:
            if gl_available:
                img = render_gl(args.app, runner, model_file,
                                len(model["steps"]))
                source = "gl"
            if img is None and args.mode != "gl":
                try:
                    img = render_procedural(model, shapes, theme)
                    source = "procedural"
                except (KeyError, ValueError) as e:
                    print(f"    [procedural] 几何复算失败: {e}")
            if img is None and args.mode != "gl":
                img, source = render_placeholder(theme), "placeholder"
        if img is None:
            failures.append(model_id)
            continue

        write_png(out_path, img)
        print(f"    -> {out_path.relative_to(ROOT)} ({source}, "
              f"{out_path.stat().st_size // 1024} KB)")
        generated.append((model_id, source))

    print()
    by_source = {}
    for _, source in generated:
        by_source[source] = by_source.get(source, 0) + 1
    summary = ", ".join(f"{s} x {n}" for s, n in sorted(by_source.items()))
    print(f"完成: 新生成 {len(generated)} 张 ({summary or '无'}), "
          f"跳过已存在 {len(skipped)} 张, 失败 {len(failures)} 个")
    if generated:
        print("提示: 运行 tools/update_model_catalog.py 把缩略图登记进模型库目录")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
