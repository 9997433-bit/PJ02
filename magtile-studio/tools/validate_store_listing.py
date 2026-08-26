#!/usr/bin/env python3
"""商店上架文档完整性守卫 —— 防止必填章节被删改与内链失效。

背景 (docs/STORE_LISTING.md): 商店上架字段与素材规格分别固化在
docs/STORE_LISTING.md (文案/字段) 与 store_assets/README.md (图形素材)。
两文是提交商店后台时的单一事实来源, 章节缺失意味着某个必填字段没有
落点 (如数据安全表要点、订阅披露文案), 上架时必然临场即兴 —— 本工具
把「必填章节存在」固化为断言:

  1. 章节: 两份文档各自的必填章节 (标题关键词) 全部存在;
  2. 内链: 两份文档中的相对 markdown 链接全部指向真实存在的文件
     (http/mailto/纯锚点跳过) —— 交叉引用 (PRIVACY_POLICY_DRAFT /
     COMMERCIAL_PLAN / android README / package_qt_desktop 等) 是
     口径对齐的载体, 断链即口径失联。

注意: 本工具只验结构不验内容 —— 「【待定稿】占位是否清零」属上架前
人工清单 (STORE_LISTING.md 第 11 节), 不在此拦截 (脚手架阶段占位是
合法状态)。

退出码:
  0  全部断言通过;
  1  存在断言失败 (章节缺失 / 内链失效);
  2  结构错误 (文档文件不存在 / 不可读)。

用法:
  python3 tools/validate_store_listing.py [--root 仓库根]
参数默认取仓库内路径, 日常直接裸跑。
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# 必填章节: {文档相对路径: [标题必须包含的关键词, ...]}
# 关键词匹配任意级别标题行 (行首 #), 章节可重排/改编号但不可删。
REQUIRED_SECTIONS: dict[str, list[str]] = {
    "docs/STORE_LISTING.md": [
        "范围与状态",
        "通用应用元数据",
        "简短描述",
        "完整描述",
        "Google Play 字段清单",
        "国内安卓商店字段清单",
        "截图与图形素材规格",
        "平板要求",
        "年龄分级",
        "隐私政策 URL 与数据安全表",
        "订阅与付费披露文案",
        "儿童侧零价格红线",
        "文案红线与 IP 规避",
        "提交前核对清单",
        "关联文档",
    ],
    "store_assets/README.md": [
        "目录结构与命名约定",
        "尺寸规格表",
        "截图内容脚本",
        "占位与入库规则",
        "关联文档",
    ],
}

MD_LINK = re.compile(r"\[[^\]]*\]\(([^)\s]+)\)")


def load_text(path: Path) -> str:
    if not path.is_file():
        print(f"[错误] 文档不存在: {path}", file=sys.stderr)
        sys.exit(2)
    try:
        return path.read_text(encoding="utf-8")
    except OSError as exc:
        print(f"[错误] 文档不可读: {path}: {exc}", file=sys.stderr)
        sys.exit(2)


def heading_lines(text: str) -> list[str]:
    return [line for line in text.splitlines() if line.lstrip().startswith("#")]


def check_sections(rel_path: str, text: str) -> list[str]:
    """返回缺失章节关键词列表 (空列表 = 通过)。"""
    headings = heading_lines(text)
    return [
        keyword
        for keyword in REQUIRED_SECTIONS[rel_path]
        if not any(keyword in line for line in headings)
    ]


def check_links(root: Path, rel_path: str, text: str) -> list[str]:
    """返回失效相对链接列表 (空列表 = 通过)。"""
    base = (root / rel_path).parent
    broken: list[str] = []
    for target in MD_LINK.findall(text):
        if target.startswith(("http://", "https://", "mailto:", "#")):
            continue
        target_path = target.split("#", 1)[0]
        if not target_path:
            continue
        if not (base / target_path).exists():
            broken.append(target)
    return broken


def main() -> int:
    parser = argparse.ArgumentParser(description="商店上架文档完整性守卫")
    parser.add_argument("--root", type=Path, default=ROOT, help="仓库根目录 (默认: 本脚本上级)")
    args = parser.parse_args()
    root: Path = args.root.resolve()

    failed = False
    for rel_path in REQUIRED_SECTIONS:
        text = load_text(root / rel_path)

        missing = check_sections(rel_path, text)
        if missing:
            failed = True
            print(f"[失败] {rel_path} 缺失必填章节 {len(missing)} 个:")
            for keyword in missing:
                print(f"    - {keyword}")
        else:
            print(f"[通过] {rel_path} 必填章节齐全 ({len(REQUIRED_SECTIONS[rel_path])} 个)")

        broken = check_links(root, rel_path, text)
        if broken:
            failed = True
            print(f"[失败] {rel_path} 存在失效内链 {len(broken)} 条:")
            for target in broken:
                print(f"    - {target}")
        else:
            print(f"[通过] {rel_path} 相对内链全部有效")

    if failed:
        print("\n结论: 存在断言失败 —— 修复后重跑; 章节口径见本脚本 REQUIRED_SECTIONS。")
        return 1
    print("\n结论: 商店上架文档结构完整, 内链全部有效。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
