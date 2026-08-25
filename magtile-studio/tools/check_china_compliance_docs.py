#!/usr/bin/env python3
"""国内上架合规文档完整性守卫 —— docs/CHINA_STORE_COMPLIANCE.md 章节与条目核验。

背景 (docs/CHINA_STORE_COMPLIANCE.md): 国内安卓商店上架的法务/行政
事项 (软著、App 备案、年龄分级、隐私托管、订阅披露、数据安全自评估、
逐家商店资质) 集中维护在该文档, 每个条目要求「checkbox + 阻塞级别
(P0/P1) + 负责方」三要素齐全。本工具把该约定固化为四条断言:

  1. 章节: 七大必备章节 (软著 / App 备案 / 年龄分级 / 隐私政策托管 /
     订阅披露 / 数据安全自评估 / 各商店特殊要求) 与五家商店小节
     (华为 / 小米 / OPPO / vivo / 应用宝) 全部存在;
  2. 条目格式: 文档内每一条 checkbox 均为
     「- [ ] **P0|P1 · 负责方** — 描述」格式, 缺级别或缺负责方即失败;
  3. 覆盖: 每个必备章节 (含商店小节) 至少含 1 条合格 checkbox;
  4. 交叉引用: 文档正文链接 PRIVACY_POLICY_DRAFT / STORE_LISTING /
     COMMERCIAL_PLAN / SECURITY_AND_PRIVACY / V1_LAUNCH_CHECKLIST
     且这五份文档实际存在 (V1_LAUNCH_CHECKLIST §9 与本文档互为
     状态快照/办理动作的对账双方, 断链即口径失联)。

退出码:
  0  全部断言通过;
  1  存在断言失败 (章节缺失 / 条目格式不合规 / 交叉引用缺失);
  2  结构错误 (文档不存在 / 不可读)。

用法:
  python3 tools/check_china_compliance_docs.py [--doc 文件] [--docs-dir 目录]
所有参数默认取仓库内路径, 日常直接裸跑。
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_DOC = ROOT / "docs" / "CHINA_STORE_COMPLIANCE.md"
DEFAULT_DOCS_DIR = ROOT / "docs"

# 七大必备章节: (人类可读名, 二级标题匹配用正则)
REQUIRED_SECTIONS: list[tuple[str, str]] = [
    ("软件著作权登记 (软著)", r"软件著作权"),
    ("App 备案 (ICP)", r"App 备案"),
    ("儿童应用年龄分级", r"年龄分级"),
    ("隐私政策托管 URL", r"隐私政策托管"),
    ("订阅与自动续费披露", r"订阅.*披露|自动续费"),
    ("数据安全自评估", r"数据安全自评估"),
    ("各安卓商店特殊要求", r"各安卓商店|商店特殊要求"),
]

# 五家商店小节 (三级标题, 属「各安卓商店特殊要求」章)
REQUIRED_STORES: list[str] = ["华为", "小米", "OPPO", "vivo", "应用宝"]

# 交叉引用: (显示名, 链接中必须出现的文件名, 是否要求文件实际存在)
REQUIRED_XREFS: list[tuple[str, str, bool]] = [
    ("隐私政策草稿", "PRIVACY_POLICY_DRAFT.md", True),
    ("商店上架素材清单", "STORE_LISTING.md", True),
    ("商业化总纲", "COMMERCIAL_PLAN.md", True),
    ("安全与隐私规范", "SECURITY_AND_PRIVACY.md", True),
    ("V1 上架总清单", "V1_LAUNCH_CHECKLIST.md", True),
]

# 合格条目: - [ ] **P0 · 负责方** — 描述  (允许已勾选 [x])
ITEM_OK = re.compile(r"^\s*- \[[ xX]\] \*\*(P0|P1) · [^*]+\*\* —")
# 任意 checkbox 行 (用于揪出格式不合规的条目)
ITEM_ANY = re.compile(r"^\s*- \[[ xX]\]")


def fail_structural(message: str) -> "sys.NoReturn":
    print(f"[错误] {message}", file=sys.stderr)
    sys.exit(2)


def split_blocks(lines: list[str], prefixes: tuple[str, ...]) -> list[tuple[str, list[str]]]:
    """按给定级别标题切块, 返回 [(标题文本, 块内行)]; 文档头归入空标题块。

    章级核验只按 "## " 切 (办理清单在 "### x.1" 小节里, 须归属所在章);
    商店小节核验按 "## " + "### " 切。
    """
    blocks: list[tuple[str, list[str]]] = [("", [])]
    for line in lines:
        if any(line.startswith(p) for p in prefixes):
            blocks.append((line.lstrip("#").strip(), []))
        else:
            blocks[-1][1].append(line)
    return blocks


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--doc", type=Path, default=DEFAULT_DOC,
                        help="合规文档路径 (默认仓库内 docs/CHINA_STORE_COMPLIANCE.md)")
    parser.add_argument("--docs-dir", type=Path, default=DEFAULT_DOCS_DIR,
                        help="交叉引用文档所在目录 (默认仓库内 docs/)")
    args = parser.parse_args()

    if not args.doc.is_file():
        fail_structural(f"合规文档不存在: {args.doc}")
    try:
        text = args.doc.read_text(encoding="utf-8")
    except OSError as exc:
        fail_structural(f"合规文档不可读: {args.doc}: {exc}")

    lines = text.splitlines()
    problems: list[str] = []

    # 断言 1: 必备章节与商店小节存在
    headings = [ln.lstrip("#").strip() for ln in lines
                if ln.startswith("## ") or ln.startswith("### ")]
    for name, pattern in REQUIRED_SECTIONS:
        if not any(re.search(pattern, h) for h in headings):
            problems.append(f"缺少必备章节: {name} (标题需匹配 /{pattern}/)")
    for store in REQUIRED_STORES:
        if not any(store in h for h in headings):
            problems.append(f"缺少商店小节: {store}")

    # 断言 2: 全部 checkbox 条目须带 P0/P1 与负责方
    for idx, line in enumerate(lines, start=1):
        if ITEM_ANY.match(line) and not ITEM_OK.match(line):
            problems.append(
                f"第 {idx} 行条目缺阻塞级别或负责方 (要求「- [ ] **P0|P1 · 负责方** — …」): "
                f"{line.strip()[:60]}")

    # 断言 3: 每个必备章节 (含商店小节) 至少 1 条合格条目
    chapters = split_blocks(lines, ("## ",))
    subsections = split_blocks(lines, ("## ", "### "))

    def block_has_item(blocks: list[tuple[str, list[str]]], pattern: str) -> bool:
        return any(re.search(pattern, title) and any(ITEM_OK.match(ln) for ln in body)
                   for title, body in blocks)

    for name, pattern in REQUIRED_SECTIONS:
        # 「各安卓商店」章的条目在商店小节里, 由商店小节断言覆盖
        if pattern.startswith("各安卓商店"):
            continue
        if any(re.search(pattern, h) for h in headings) and not block_has_item(chapters, pattern):
            problems.append(f"章节「{name}」内没有任何合格 checklist 条目")
    for store in REQUIRED_STORES:
        if any(store in h for h in headings) and not block_has_item(subsections, re.escape(store)):
            problems.append(f"商店小节「{store}」内没有任何合格 checklist 条目")

    # 断言 4: 交叉引用存在且被引用文档在库
    for name, needle, must_exist in REQUIRED_XREFS:
        if needle not in text:
            problems.append(f"缺少交叉引用: {name} (正文未出现 {needle})")
        elif must_exist and not (args.docs_dir / needle).is_file():
            problems.append(f"交叉引用指向不存在的文档: {needle}")

    if problems:
        print(f"[失败] {args.doc.name} 完整性核验未通过, 共 {len(problems)} 项:")
        for p in problems:
            print(f"  - {p}")
        return 1

    ok_items = sum(1 for ln in lines if ITEM_OK.match(ln))
    p0 = sum(1 for ln in lines if ITEM_OK.match(ln) and "**P0" in ln)
    print(f"[通过] {args.doc.name}: 七大章节 + 五家商店小节齐全; "
          f"checklist 条目 {ok_items} 条 (P0 {p0} / P1 {ok_items - p0}) 全部带级别与负责方; "
          f"交叉引用 {len(REQUIRED_XREFS)} 项就位。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
