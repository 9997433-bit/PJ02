#!/usr/bin/env python3
"""软著源程序鉴别材料导出 —— CPCC 前 30 页 + 后 30 页连续源代码。

依据 docs/ADMIN_LAUNCH_CHECKLIST.md §2.2 与 docs/CHINA_STORE_COMPLIANCE.md §2:
  - 自研连续源代码, 排除 third_party/ 与构建产物;
  - 每页 >= 50 行, 页眉标注软件名称 + 版本号 + 页码;
  - 总量不足 60 页则全交, 否则交前 30 + 后 30 页;
  - 末页须为程序结尾 (本工具按文件排序拼接, 末行来自排序最后的源文件)。

输出 (默认目录 docs/exports/copyright/):
  - source_pages_submission.txt  —— 可直接导入 Word/LibreOffice 转 PDF;
  - source_pages_submission.html —— 浏览器打印为 PDF (推荐);
  - manifest.json                —— 页数/行数/文件清单摘要。

退出码:
  0  校验通过且已写出 (或 --validate-only 通过);
  1  页数/行数不达标或含禁用路径片段;
  2  参数/IO 错误。

用法:
  python3 tools/export_copyright_source_pages.py
  python3 tools/export_copyright_source_pages.py --validate-only
  python3 tools/export_copyright_source_pages.py --output-dir /tmp/copyright
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from html import escape
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_OUTPUT = ROOT / "docs" / "exports" / "copyright"

DEFAULT_SOFTWARE_NAME = "MagTile Studio 磁力片工坊软件 V1.0"
DEFAULT_VERSION = "V1.0"
LINES_PER_PAGE = 50
FIRST_PAGES = 30
LAST_PAGES = 30
SUBMISSION_PAGES = FIRST_PAGES + LAST_PAGES

SOURCE_EXTENSIONS = {".cpp", ".hpp", ".h", ".qml", ".java", ".kt"}

# 自研产品代码根 (不含 third_party / 内容生成脚本 / 模型 JSON)
SOURCE_ROOTS = (
    "include",
    "src",
    "apps",
    "platforms",
    "tests",
)

PRUNE_DIR_NAMES = {
    "third_party",
    "build",
    ".git",
    "__pycache__",
    "_deps",
    "node_modules",
}

PRUNE_PATH_PARTS = {
    "moc_",
    "autogen",
    "qmlcache",
    "CMakeFiles",
}

FORBIDDEN_LINE_PATTERNS = [
    # 仅拦截真实引入第三方源码的行, 注释中提及依赖路径允许
    re.compile(r'#\s*include\s+[<"].*third_party/', re.I),
    re.compile(r"The author disclaims copyright", re.I),
    re.compile(r"Copyright \(c\).*GLFW", re.I),
    re.compile(r"Copyright \(c\).*Dear ImGui", re.I),
]


@dataclass
class Page:
    number: int
    lines: list[str]


def should_prune_dir(path: Path) -> bool:
    name = path.name
    if name in PRUNE_DIR_NAMES:
        return True
    if name.startswith("build-"):
        return True
    return any(part in name for part in PRUNE_PATH_PARTS)


def collect_source_files(root: Path) -> list[Path]:
    files: list[Path] = []
    for rel_root in SOURCE_ROOTS:
        base = root / rel_root
        if not base.is_dir():
            continue
        for path in sorted(base.rglob("*")):
            if not path.is_file():
                continue
            if path.suffix.lower() not in SOURCE_EXTENSIONS:
                continue
            if any(should_prune_dir(part) for part in path.parents):
                continue
            if "third_party" in path.parts:
                continue
            files.append(path)
    return sorted(files, key=lambda p: str(p.relative_to(root)).replace("\\", "/"))


def flatten_source(files: list[Path], root: Path) -> list[str]:
    lines: list[str] = []
    for path in files:
        rel = path.relative_to(root).as_posix()
        lines.append(f"// ===== file: {rel} =====")
        try:
            content = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            content = path.read_text(encoding="utf-8", errors="replace")
        for raw in content.splitlines():
            lines.append(raw.rstrip("\r\n"))
        lines.append("")
    while lines and lines[-1] == "":
        lines.pop()
    return lines


def paginate(lines: list[str], lines_per_page: int) -> list[Page]:
    if not lines:
        return []
    pages: list[Page] = []
    page_no = 1
    for start in range(0, len(lines), lines_per_page):
        chunk = lines[start : start + lines_per_page]
        pages.append(Page(number=page_no, lines=chunk))
        page_no += 1
    return pages


def select_submission_pages(pages: list[Page]) -> list[Page]:
    if len(pages) <= SUBMISSION_PAGES:
        return pages
    first = pages[:FIRST_PAGES]
    last = pages[-LAST_PAGES:]
    return first + last


def check_forbidden_lines(lines: list[str]) -> list[str]:
    issues: list[str] = []
    for idx, line in enumerate(lines, start=1):
        for pat in FORBIDDEN_LINE_PATTERNS:
            if pat.search(line):
                issues.append(f"行 {idx}: 命中禁用片段 ({pat.pattern}): {line[:80]}")
                break
    return issues


def format_page_header(software_name: str, page: Page, total_pages: int) -> str:
    return f"{software_name}    第 {page.number} 页 / 共 {total_pages} 页"


def write_text_submission(
    path: Path,
    software_name: str,
    all_pages: list[Page],
    submission: list[Page],
) -> None:
    total = len(all_pages)
    parts: list[str] = [
        f"# 软著源程序鉴别材料 (前 {FIRST_PAGES} 页 + 后 {LAST_PAGES} 页)",
        f"# 软件名称: {software_name}",
        f"# 生成时间: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}",
        f"# 全库总页数: {total} (每页 {LINES_PER_PAGE} 行)",
        "",
    ]
    for page in submission:
        parts.append("=" * 72)
        parts.append(format_page_header(software_name, page, total))
        parts.append("=" * 72)
        parts.extend(page.lines)
        parts.append("")
    path.write_text("\n".join(parts) + "\n", encoding="utf-8")


def write_html_submission(
    path: Path,
    software_name: str,
    all_pages: list[Page],
    submission: list[Page],
) -> None:
    total = len(all_pages)
    body_parts: list[str] = []
    for page in submission:
        header = escape(format_page_header(software_name, page, total))
        body_parts.append(f'<section class="page">')
        body_parts.append(f'  <div class="header">{header}</div>')
        body_parts.append('  <pre class="code">')
        for line in page.lines:
            body_parts.append(escape(line))
        body_parts.append("  </pre>")
        body_parts.append("</section>")

    html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8"/>
  <title>{escape(software_name)} — 源程序鉴别材料</title>
  <style>
    @page {{ size: A4; margin: 18mm 15mm; }}
    body {{ font-family: "Courier New", Consolas, monospace; font-size: 9pt; margin: 0; }}
    .page {{ page-break-after: always; }}
    .page:last-child {{ page-break-after: auto; }}
    .header {{
      font-family: "Microsoft YaHei", "PingFang SC", sans-serif;
      font-size: 10pt;
      font-weight: bold;
      border-bottom: 1px solid #333;
      margin-bottom: 6px;
      padding-bottom: 4px;
    }}
    pre.code {{ margin: 0; white-space: pre-wrap; word-break: break-all; line-height: 1.15; }}
  </style>
</head>
<body>
{chr(10).join(body_parts)}
</body>
</html>
"""
    path.write_text(html, encoding="utf-8")


def write_manifest(
    path: Path,
    software_name: str,
    files: list[Path],
    all_pages: list[Page],
    submission: list[Page],
    root: Path,
) -> None:
    manifest = {
        "software_name": software_name,
        "version": DEFAULT_VERSION,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "lines_per_page": LINES_PER_PAGE,
        "total_source_files": len(files),
        "total_lines": sum(len(p.lines) for p in all_pages) if all_pages else 0,
        "total_pages": len(all_pages),
        "submission_page_count": len(submission),
        "submission_mode": "all" if len(all_pages) <= SUBMISSION_PAGES else "first30+last30",
        "source_roots": list(SOURCE_ROOTS),
        "source_files_sample": [f.relative_to(root).as_posix() for f in files[:20]],
        "last_source_file": files[-1].relative_to(root).as_posix() if files else None,
        "notes": [
            "提交前请用浏览器打开 HTML 打印为 PDF, 或导入 TXT 到 Word 设置页眉后导出 PDF。",
            "操作手册/用户手册 60 页需另行准备 (含真实界面截图), 本工具不生成文档鉴别材料。",
        ],
    }
    path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def validate_pages(pages: list[Page]) -> list[str]:
    issues: list[str] = []
    if not pages:
        issues.append("未收集到任何源代码行")
        return issues
    short_pages = [p for p in pages if len(p.lines) < LINES_PER_PAGE]
    # 仅最后一页允许不足 50 行
    for p in short_pages:
        if p.number != len(pages):
            issues.append(
                f"第 {p.number} 页仅 {len(p.lines)} 行 (< {LINES_PER_PAGE}), 中间页不允许不足"
            )
    if len(pages) < 1:
        issues.append("总页数为 0")
    return issues


def main() -> int:
    parser = argparse.ArgumentParser(description="导出软著源程序鉴别材料 (CPCC)")
    parser.add_argument("--root", type=Path, default=ROOT, help="仓库根目录")
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=DEFAULT_OUTPUT,
        help="输出目录 (默认 docs/exports/copyright/)",
    )
    parser.add_argument(
        "--software-name",
        default=DEFAULT_SOFTWARE_NAME,
        help="页眉软件全称 (须与申请表一致)",
    )
    parser.add_argument(
        "--validate-only",
        action="store_true",
        help="只校验页数/禁用片段, 不写文件",
    )
    args = parser.parse_args()
    root: Path = args.root.resolve()
    if not (root / "tools" / "export_copyright_source_pages.py").is_file():
        print("[错误] --root 不是 MagTile Studio 仓库根", file=sys.stderr)
        return 2

    files = collect_source_files(root)
    flat = flatten_source(files, root)
    forbidden = check_forbidden_lines(flat)
    if forbidden:
        print("[失败] 源代码含禁用片段 (可能混入第三方库):", file=sys.stderr)
        for item in forbidden[:10]:
            print(f"  - {item}", file=sys.stderr)
        if len(forbidden) > 10:
            print(f"  ... 另有 {len(forbidden) - 10} 条", file=sys.stderr)
        return 1

    all_pages = paginate(flat, LINES_PER_PAGE)
    page_issues = validate_pages(all_pages)
    if page_issues:
        print("[失败] 分页校验未通过:", file=sys.stderr)
        for item in page_issues:
            print(f"  - {item}", file=sys.stderr)
        return 1

    submission = select_submission_pages(all_pages)
    print(
        f"[信息] 源文件 {len(files)} 个, 总行 {len(flat)}, "
        f"全库 {len(all_pages)} 页, 提交 {len(submission)} 页"
    )

    if args.validate_only:
        print("[通过] --validate-only 校验完成")
        return 0

    out_dir: Path = args.output_dir
    out_dir.mkdir(parents=True, exist_ok=True)
    write_text_submission(
        out_dir / "source_pages_submission.txt",
        args.software_name,
        all_pages,
        submission,
    )
    write_html_submission(
        out_dir / "source_pages_submission.html",
        args.software_name,
        all_pages,
        submission,
    )
    write_manifest(
        out_dir / "manifest.json",
        args.software_name,
        files,
        all_pages,
        submission,
        root,
    )
    print(f"[完成] 已写出 {out_dir}/source_pages_submission.html")
    print(f"[完成] 已写出 {out_dir}/source_pages_submission.txt")
    print(f"[完成] 已写出 {out_dir}/manifest.json")
    print("[提示] 用浏览器打开 HTML → 打印 → 另存为 PDF, 即可上传 CPCC")
    return 0


if __name__ == "__main__":
    sys.exit(main())
