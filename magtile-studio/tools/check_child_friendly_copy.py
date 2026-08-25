#!/usr/bin/env python3
"""儿童友好文案守卫 —— 用户可见中文文案的恐吓词/催促话术红线检查。

背景 (docs/UI_UX_SPEC.md): 儿童可达界面是验收红线 ——
  P3   零挫败: 永不弹「失败」字样, 无惩罚性文案 (§1.1);
  §4.3 反馈只有正向与中性两档, 不用「错误/警告」吓孩子;
  §4.5 无暗黑模式: 无倒计时/无限时促销/无稀缺话术;
  §11  订阅页禁止事项: 无倒计时、无「即将涨价」;
  §14  验收清单: 无红叉/失败文案。
技术诊断细节一律走 stderr / logcat / 异常消息 (开发者可见),
用户侧永远是温和、鼓励、信息而非门槛的中文文案。

扫描面 (只看用户可见的中文串, 注释与日志行自动跳过):
  1. Qt QML 界面      apps/desktop_qt/qml/*.qml 的字符串字面量;
  2. Android 资源     platforms/android/app/src/main/res/values/strings.xml;
  3. Android Kotlin   platforms/android/.../kotlin/**/*.kt 硬编码串
                      (跳过 Log.* / check(...) / require(...) 等日志与断言行);
  4. 展示层 C++       apps/desktop_qt/src/*.cpp、platforms/android/jni/*.cpp、
                      src/render/gl/gl_renderer.cpp (GL HUD / JNI 返回给弹窗的
                      文案; 跳过 fprintf / *printf / MAGTILE_*LOG* / throw /
                      {"error"...} 日志与诊断行, 以及 "[tag] " 前缀的日志串);
  5. 模型内容文案     data/model_catalog.json 与 data/models/*.json 的
                      name / description / steps[].description / steps[].tip
                      (儿童可见且会被 TTS 朗读, §4.2)。

规则两类:
  - 恐吓/惩罚词 (无条件禁止): 失败 / 错误 / 出错 / 崩溃 / 死机 / 异常 /
    无法连接 / 答错 / 重新开始;
  - 催促/稀缺话术 (否定语境豁免, 如订阅页承诺「无倒计时」):
    倒计时 / 限时 / 涨价 / 最后机会 / 仅剩 / 秒杀 / 抢购。

退出码:
  0  全部通过;
  1  存在违规文案 (逐条列出 文件:行号 与命中规则);
  2  结构错误 (扫描面文件缺失 / 不可解析)。

用法:
  python3 tools/check_child_friendly_copy.py [--root 仓库根]
参数默认取仓库内路径, 日常直接裸跑, 全库秒级。
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

CJK_RE = re.compile(r"[\u4e00-\u9fff]")

# ---- 规则 -------------------------------------------------------
# (正则, 说明)。恐吓词无条件禁止。
FORBIDDEN_SCARE: list[tuple[str, str]] = [
    (r"失败", "恐吓词: P3 零挫败, 永不弹「失败」(§1.1/§4.3/§14)"),
    (r"错误", "恐吓词: 不用「错误」表达, 用温和提示 (§4.3, 琥珀色规范)"),
    (r"出错", "恐吓词: 同「错误」, 用「这次没…, 再试一次就好」句式 (§4.3)"),
    (r"崩溃", "恐吓词: 技术事故不进用户界面, 细节只写日志 (P3)"),
    (r"死机", "恐吓词: 同「崩溃」(P3)"),
    (r"异常", "恐吓词: 「网络异常」类表达禁止, 说明发生了什么即可 (P3)"),
    (r"无法连接", "恐吓词: 网络问题用温和信息句, 不用「无法」恐吓 (P3)"),
    (r"答错", "惩罚性文案: P3 反例「你答错了」, 家长门用「再试一次吧」"),
    (r"重新开始", "惩罚性文案: P3 反例, 主动重来用「再搭一次/从头再来」"),
]
# 催促/稀缺话术: (正则, 说明, 主题语境豁免正则或 None)。
# 两类豁免:
#   1. 否定语境 —— 前文 4 字内出现否定词 (无/不/没/拒/非/反/零),
#      订阅页明示「无倒计时、无『即将涨价』」的反套路承诺是合规文案;
#   2. 主题语境 —— 同段文案命中豁免正则, 如火箭模型步骤叙事
#      「发射场落成, 倒计时开始!」是庆祝性内容, 不是促销计时器。
FORBIDDEN_URGENCY: list[tuple[str, str, str | None]] = [
    (r"倒计时", "催促话术: 儿童可达界面与订阅页均无倒计时 (§4.5/§11)",
     r"发射|火箭|点火|升空"),
    (r"限时", "催促话术: 无限时促销 (§4.5)", None),
    (r"涨价", "催促话术: 无「即将涨价」(§11)", None),
    (r"最后机会", "稀缺话术: 禁止 (§4.5)", None),
    (r"仅剩", "稀缺话术: 禁止 (§4.5)", None),
    (r"秒杀", "稀缺话术: 禁止 (§4.5)", None),
    (r"抢购", "稀缺话术: 禁止 (§4.5)", None),
]
NEGATION_CHARS = set("无不没拒非反零")

# 代码行级跳过: 日志 / 断言 / 异常 / 诊断载荷 —— 开发者可见, 不是用户文案
DEV_LINE_RE = re.compile(
    r"fprintf\(|std::printf\(|MAGTILE_\w*LOG\w*|Log\.[ewidv]\(|"
    r"\bcheck\(|\brequire\(|\bthrow |qWarning|qCritical|qDebug|qInfo|"
    r"console\.|\"error\""
)
# 串级跳过: "[tag] ..." 形式 (纯 ASCII tag) 是日志约定前缀
LOG_PREFIX_RE = re.compile(r"^\[[\x20-\x7e]+\]\s")


class Violation:
    def __init__(self, where: str, text: str, reason: str) -> None:
        self.where = where
        self.text = text
        self.reason = reason


def check_text(text: str, where: str, out: list[Violation]) -> None:
    """对一段用户可见文案跑全部规则。"""
    for pattern, reason in FORBIDDEN_SCARE:
        for m in re.finditer(pattern, text):
            out.append(Violation(where, text.strip(), reason))
            break  # 每条规则每段文案只报一次
    for pattern, reason, thematic_exempt in FORBIDDEN_URGENCY:
        if thematic_exempt and re.search(thematic_exempt, text):
            continue  # 主题语境 (火箭发射叙事) 豁免
        for m in re.finditer(pattern, text):
            lookback = text[max(0, m.start() - 4):m.start()]
            if any(ch in NEGATION_CHARS for ch in lookback):
                continue  # 否定语境 (「无倒计时」) 豁免
            out.append(Violation(where, text.strip(), reason))
            break


# ---- 代码文件: 注释剥离 + 字符串字面量提取 ----------------------
def iter_code_literals(source: str):
    """string-aware 扫描: 跳过 // 与 /* */ 注释, 产出 (行号, 字面量)。"""
    i, n, line = 0, len(source), 1
    in_block = False
    while i < n:
        ch = source[i]
        if ch == "\n":
            line += 1
            i += 1
            continue
        if in_block:
            if source.startswith("*/", i):
                in_block = False
                i += 2
            else:
                i += 1
            continue
        if source.startswith("//", i):
            nl = source.find("\n", i)
            i = n if nl < 0 else nl
            continue
        if source.startswith("/*", i):
            in_block = True
            i += 2
            continue
        if ch in ('"', "'"):
            quote = ch
            start_line = line
            j = i + 1
            buf: list[str] = []
            while j < n:
                cj = source[j]
                if cj == "\\" and j + 1 < n:
                    buf.append(source[j:j + 2])
                    j += 2
                    continue
                if cj == quote:
                    break
                if cj == "\n":  # 未闭合串跨行 (原则上不出现), 行号照常推进
                    line += 1
                buf.append(cj)
                j += 1
            yield start_line, "".join(buf)
            i = j + 1
            continue
        i += 1


def scan_code_file(path: Path, out: list[Violation]) -> int:
    source = path.read_text(encoding="utf-8")
    lines = source.splitlines()
    count = 0
    for line_no, literal in iter_code_literals(source):
        if not CJK_RE.search(literal):
            continue
        raw_line = lines[line_no - 1] if 0 < line_no <= len(lines) else ""
        if DEV_LINE_RE.search(raw_line):
            continue  # 日志 / 断言 / 诊断行
        if LOG_PREFIX_RE.match(literal):
            continue  # "[tag] " 日志前缀串
        count += 1
        check_text(literal, f"{path.relative_to(ROOT)}:{line_no}", out)
    return count


# ---- Android strings.xml ---------------------------------------
STRING_ELEM_RE = re.compile(r"<string\b[^>]*>(.*?)</string>", re.DOTALL)
XML_COMMENT_RE = re.compile(r"<!--.*?-->", re.DOTALL)


def scan_strings_xml(path: Path, out: list[Violation]) -> int:
    source = path.read_text(encoding="utf-8")
    # 注释挖空但保留换行, 行号不漂移
    def blank(m: re.Match) -> str:
        return "".join(c if c == "\n" else " " for c in m.group(0))

    stripped = XML_COMMENT_RE.sub(blank, source)
    count = 0
    for m in STRING_ELEM_RE.finditer(stripped):
        line_no = stripped.count("\n", 0, m.start()) + 1
        count += 1
        check_text(m.group(1), f"{path.relative_to(ROOT)}:{line_no}", out)
    return count


# ---- 模型内容文案 (儿童可见 + TTS 朗读, §4.2) --------------------
def scan_model_json(path: Path, out: list[Violation]) -> int:
    data = json.loads(path.read_text(encoding="utf-8"))
    rel = path.relative_to(ROOT)
    count = 0

    def check_field(value, where: str) -> int:
        if isinstance(value, str) and CJK_RE.search(value):
            check_text(value, where, out)
            return 1
        return 0

    def scan_model(model: dict, prefix: str) -> int:
        n = 0
        n += check_field(model.get("name"), f"{prefix} name")
        n += check_field(model.get("description"), f"{prefix} description")
        for idx, step in enumerate(model.get("steps") or []):
            n += check_field(step.get("description"),
                             f"{prefix} steps[{idx}].description")
            n += check_field(step.get("tip"), f"{prefix} steps[{idx}].tip")
        return n

    if isinstance(data, dict) and isinstance(data.get("models"), list):
        for entry in data["models"]:  # model_catalog.json
            model_id = entry.get("id", "?")
            count += scan_model(entry, f"{rel} [{model_id}]")
    elif isinstance(data, dict):
        count += scan_model(data, str(rel))
    return count


# ---- 主流程 -----------------------------------------------------
def main() -> int:
    global ROOT
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--root", type=Path, default=None,
                        help="仓库根目录 (默认按脚本位置推断)")
    args = parser.parse_args()
    if args.root is not None:
        ROOT = args.root.resolve()

    surfaces: list[tuple[str, list[Path]]] = [
        ("Qt QML", sorted((ROOT / "apps/desktop_qt/qml").glob("*.qml"))),
        ("Android strings.xml",
         [ROOT / "platforms/android/app/src/main/res/values/strings.xml"]),
        ("Android Kotlin",
         sorted((ROOT / "platforms/android/app/src/main/kotlin").rglob("*.kt"))),
        ("展示层 C++",
         sorted((ROOT / "apps/desktop_qt/src").glob("*.cpp"))
         + sorted((ROOT / "platforms/android/jni").glob("*.cpp"))
         + [ROOT / "src/render/gl/gl_renderer.cpp"]),
        ("模型内容",
         [ROOT / "data/model_catalog.json"]
         + sorted((ROOT / "data/models").glob("*.json"))),
    ]

    violations: list[Violation] = []
    total_strings = 0
    total_files = 0
    for surface_name, files in surfaces:
        if not files:
            print(f"结构错误: 扫描面「{surface_name}」没有找到任何文件", file=sys.stderr)
            return 2
        for path in files:
            if not path.is_file():
                print(f"结构错误: 文件不存在 {path}", file=sys.stderr)
                return 2
            try:
                if path.suffix == ".xml":
                    total_strings += scan_strings_xml(path, violations)
                elif path.suffix == ".json":
                    total_strings += scan_model_json(path, violations)
                else:
                    total_strings += scan_code_file(path, violations)
            except (UnicodeDecodeError, json.JSONDecodeError) as e:
                print(f"结构错误: 无法解析 {path}: {e}", file=sys.stderr)
                return 2
            total_files += 1

    if violations:
        print(f"儿童友好文案守卫: 发现 {len(violations)} 处违规 "
              f"(共检查 {total_files} 个文件 / {total_strings} 段文案)\n")
        for v in violations:
            text = v.text if len(v.text) <= 60 else v.text[:57] + "…"
            print(f"  {v.where}")
            print(f"    文案: {text}")
            print(f"    规则: {v.reason}\n")
        print("整改口径: 技术细节只写日志; 用户侧用温和信息句, 如"
              "「这次没…, 稍后再试一次就好」(参考 UI_UX_SPEC §4.3)。")
        return 1

    print(f"儿童友好文案守卫: 通过 —— {total_files} 个文件 / "
          f"{total_strings} 段用户可见中文文案, 无恐吓词与催促话术")
    return 0


if __name__ == "__main__":
    sys.exit(main())
