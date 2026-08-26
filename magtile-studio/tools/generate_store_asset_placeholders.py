#!/usr/bin/env python3
"""商店素材占位图生成器 —— 排版审阅用纯色+文字标签 PNG, 非提交件。

背景 (docs/STORE_ASSETS_SPEC.md / store_assets/README.md): 商店后台
表单联调与详情页排版审阅需要「尺寸正确的图」先行占位, 而成品素材
(母版图标 / 置顶大图 / 实机截图) 依赖美术定稿与 Android 壳实机 ——
本工具按两文规格生成**占位 PNG** (纯色底 + 居中文字标签), 尺寸与
命名与正式素材完全一致, 使排版/上传链路可以先跑通:

  icons/       图标母版 1024×1024 + Play 512×512 + 华为 216×216;
  feature/     Play 置顶大图 1024×500;
  screenshots/phone/zh-CN/
               手机截图 8 张 1080×1920 (README §3 脚本顺序与场景)。

红线 (勿删): 占位图**只做排版审阅**, 不是提交质量 —— 商店禁止合成
假界面截图 (README §3), 提交前必须全部替换为真实素材; 每张占位图
画面上均烙有「PLACEHOLDER 占位图」字样防误传。入库规则: 单文件
≤300KB 方可进 git (README §4), 本工具生成后逐一断言。

确定性: 配色/文案/字体固定, 不含时间戳 —— 重跑输出字节级可复现,
diff 干净。字体按 Noto Sans CJK → WQY MicroHei → DejaVu 顺序探测,
无 CJK 字体时自动退化为纯英文标签 (占位语义不变)。

退出码:
  0  全部生成并通过 ≤300KB 断言;
  1  存在超限文件 (不得入库);
  2  结构错误 (Pillow 缺失 / 输出目录不可写)。

用法:
  python3 tools/generate_store_asset_placeholders.py [--root 仓库根]
参数默认取仓库内路径, 日常直接裸跑, 全部生成秒级。
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError:
    print("[错误] 需要 Pillow: pip install Pillow", file=sys.stderr)
    sys.exit(2)

ROOT = Path(__file__).resolve().parent.parent

MAX_BYTES = 300 * 1024  # store_assets/README.md §4: 入库 PNG 单文件 ≤300KB

# CJK 字体探测链 (缺失时退化为纯英文标签)
CJK_FONT_CANDIDATES = [
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc",
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
    "/usr/share/fonts/truetype/wqy/wqy-microhei.ttc",
]
LATIN_FONT_CANDIDATES = [
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
]

# 8 张手机截图: (场景 slug, 中文场景名, 英文标签) —— 顺序与场景锁定
# store_assets/README.md §3 (前 4 张为 STORE_LISTING §5 定死口径)。
PHONE_SHOTS = [
    ("tutorial3d", "3D 教程视口", "3D Tutorial Viewport"),
    ("library", "模型库网格", "Model Library Grid"),
    ("canbuild", "「我能搭的」筛选", "Can-Build Filter"),
    ("privacy", "家长中心 · 隐私与数据", "Parent Center: Privacy"),
    ("agemodes", "分龄界面 (4-6 档)", "Age Modes UI"),
    ("achievements", "成就墙", "Achievement Wall"),
    ("resume", "步骤列表 + 断点续搭", "Steps + Resume Build"),
    ("realphoto", "成品实拍对比", "Real Build Photo"),
]

# 儿童向品牌感的高饱和平涂色, 逐张区分便于排版时一眼对位
SHOT_COLORS = [
    (233, 116, 81),   # 橙红
    (52, 152, 219),   # 蓝
    (46, 174, 96),    # 绿
    (155, 89, 182),   # 紫
    (241, 196, 15),   # 黄
    (26, 188, 156),   # 青
    (231, 76, 60),    # 红
    (100, 116, 228),  # 蓝紫
]

ICON_COLOR = (41, 128, 185)     # 图标: 深蓝
FEATURE_COLOR = (230, 126, 34)  # 置顶大图: 橙


def find_font_path(candidates: list[str]) -> str | None:
    for path in candidates:
        if Path(path).is_file():
            return path
    return None


CJK_FONT_PATH = find_font_path(CJK_FONT_CANDIDATES)
LATIN_FONT_PATH = find_font_path(LATIN_FONT_CANDIDATES)


def load_font(size: int) -> ImageFont.ImageFont | ImageFont.FreeTypeFont:
    path = CJK_FONT_PATH or LATIN_FONT_PATH
    if path:
        return ImageFont.truetype(path, size=size)
    return ImageFont.load_default(size=size)


def draw_centered_lines(
    img: Image.Image, lines: list[tuple[str, float]], color=(255, 255, 255)
) -> None:
    """把 (文本, 字号系数) 列表竖向整体居中绘制; 系数相对短边。"""
    draw = ImageDraw.Draw(img)
    short_edge = min(img.size)
    rendered: list[tuple[str, ImageFont.FreeTypeFont, int, int]] = []
    gap = short_edge // 40
    total_h = 0
    for text, ratio in lines:
        font = load_font(max(12, int(short_edge * ratio)))
        left, top, right, bottom = draw.textbbox((0, 0), text, font=font)
        w, h = right - left, bottom - top
        rendered.append((text, font, w, h))
        total_h += h
    total_h += gap * (len(rendered) - 1)
    y = (img.height - total_h) // 2
    for text, font, w, h in rendered:
        left, top, _, _ = draw.textbbox((0, 0), text, font=font)
        draw.text(((img.width - w) // 2 - left, y - top), text, font=font, fill=color)
        y += h + gap


def make_placeholder(
    path: Path, size: tuple[int, int], color: tuple[int, int, int], label_zh: str, label_en: str
) -> None:
    img = Image.new("RGB", size, color)
    dims = f"{size[0]}x{size[1]}"
    if CJK_FONT_PATH:
        lines = [
            (label_zh, 0.085),
            (label_en, 0.05),
            (dims, 0.05),
            ("PLACEHOLDER 占位图", 0.045),
            ("仅供排版审阅 · 提交前必须替换", 0.035),
        ]
    else:
        lines = [
            (label_en, 0.07),
            (dims, 0.05),
            ("PLACEHOLDER", 0.045),
            ("layout review only - replace before submission", 0.03),
        ]
    draw_centered_lines(img, lines)
    path.parent.mkdir(parents=True, exist_ok=True)
    img.save(path, format="PNG", optimize=True)


def main() -> int:
    parser = argparse.ArgumentParser(description="商店素材占位图生成器 (排版审阅用)")
    parser.add_argument("--root", type=Path, default=ROOT, help="仓库根目录 (默认: 本脚本上级)")
    args = parser.parse_args()
    assets_dir: Path = args.root.resolve() / "store_assets"
    if not assets_dir.is_dir():
        print(f"[错误] store_assets 目录不存在: {assets_dir}", file=sys.stderr)
        return 2

    jobs: list[tuple[Path, tuple[int, int], tuple[int, int, int], str, str]] = [
        # 图标: 母版 1024 唯一源头, 向下导出 (README §2 / SPEC §4)
        (assets_dir / "icons/icon_master_1024.png", (1024, 1024), ICON_COLOR,
         "图标母版", "Icon Master"),
        (assets_dir / "icons/play_icon_512.png", (512, 512), ICON_COLOR,
         "Play 图标", "Play Icon"),
        (assets_dir / "icons/huawei_icon_216.png", (216, 216), ICON_COLOR,
         "华为图标", "Huawei Icon"),
        # 置顶大图: Play feature graphic 1024×500 固定 (SPEC §3.1)
        (assets_dir / "feature/play_feature_1024x500.png", (1024, 500), FEATURE_COLOR,
         "Play 置顶大图", "Play Feature Graphic"),
    ]
    # 手机截图 8 张 1080×1920 zh-CN (README §3 顺序; SPEC §2.1 尺寸)
    for i, (slug, zh, en) in enumerate(PHONE_SHOTS):
        jobs.append((
            assets_dir / f"screenshots/phone/zh-CN/{i + 1:02d}_{slug}_1080x1920.png",
            (1080, 1920), SHOT_COLORS[i], f"{i + 1:02d} {zh}", en,
        ))

    oversized: list[tuple[Path, int]] = []
    for path, size, color, zh, en in jobs:
        make_placeholder(path, size, color, zh, en)
        n_bytes = path.stat().st_size
        rel = path.relative_to(assets_dir.parent)
        status = "OK" if n_bytes <= MAX_BYTES else "超限"
        print(f"[{status}] {rel}  {size[0]}x{size[1]}  {n_bytes / 1024:.1f}KB")
        if n_bytes > MAX_BYTES:
            oversized.append((path, n_bytes))

    if oversized:
        print(f"\n结论: {len(oversized)} 个文件超过 300KB 入库上限, 不得提交 (README §4)。")
        return 1
    print(f"\n结论: 共 {len(jobs)} 张占位图生成完毕, 全部 ≤300KB 可入库; "
          "仅供排版审阅, 提交前必须替换为真实素材。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
