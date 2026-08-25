#!/usr/bin/env bash
# =============================================================
# MagTile Studio - 全库 strict 物理巡检一键脚本
#
# 一条命令完成 "弱磁严格档全库巡检" 的全部动作:
#   0. magtile_app 不存在时自动 CMake 配置 + 构建;
#   1. 全库 validate --profile strict 零警告审计
#      (复用 tools/audit_strict_physics.sh: 零警告政策 + 白名单豁免);
#   2. 全库逐步装配质检 (tests/test_step_assembly.py: 逐片连通/
#      引用对账/步骤粒度);
#   3. (可选) --report FILE 生成 Markdown 巡检报告: 通过/豁免/失败
#      计数、按规则 R1~R8 分类的问题统计、D4+ 实物复核清单。
#
# 用法:
#   tools/run_strict_audit.sh [build_dir] [--report FILE]
#     build_dir      构建目录 (默认 build)
#     --report FILE  同时生成 Markdown 报告 (如
#                    docs/reports/STRICT_AUDIT_$(date +%F).md)
#
# CI 接入: tests/run_full_qa.sh 的可选关卡 (MAGTILE_STRICT_AUDIT=1
# 时执行), 也可单独在流水线中调用。
# 退出码: 0 = 两阶段全部通过; 1 = 任一阶段失败; 2 = 环境不满足
# =============================================================
set -u

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
BUILD_DIR="$ROOT/build"
REPORT_FILE=""

while [ "$#" -gt 0 ]; do
    case "$1" in
        --report)
            [ "$#" -ge 2 ] || { echo "错误: --report 需要文件参数" >&2; exit 2; }
            REPORT_FILE="$2"; shift 2 ;;
        --report=*)
            REPORT_FILE="${1#--report=}"; shift ;;
        -h|--help)
            sed -n '2,24p' "$0"; exit 0 ;;
        *)
            BUILD_DIR="$1"; shift ;;
    esac
done
case "$BUILD_DIR" in
    /*) ;;
    *) BUILD_DIR="$ROOT/$BUILD_DIR" ;;
esac
if [ -n "$REPORT_FILE" ]; then
    case "$REPORT_FILE" in
        /*) ;;
        *) REPORT_FILE="$ROOT/$REPORT_FILE" ;;
    esac
fi

APP="$BUILD_DIR/magtile_app"
DATA_DIR="$ROOT/data"
PYTHON="$(command -v python3 || command -v python)"
if [ -z "$PYTHON" ]; then
    echo "错误: 需要 python3 (逐步装配质检与报告生成依赖)" >&2
    exit 2
fi

# ---- 0. 自动构建 (一键: 缺可执行文件时不报错而是补齐) ------------
if [ ! -x "$APP" ]; then
    echo ">> magtile_app 不存在, 自动配置并构建 ($BUILD_DIR) ..."
    cmake -S "$ROOT" -B "$BUILD_DIR" -DCMAKE_BUILD_TYPE=Release || exit 2
    nproc_val="$( (command -v nproc >/dev/null && nproc) || sysctl -n hw.ncpu 2>/dev/null || echo 2)"
    cmake --build "$BUILD_DIR" -j "$nproc_val" --target magtile_app || exit 2
fi

LOG_DIR="$(mktemp -d /tmp/magtile_strict_audit_XXXXXX)"
AUDIT_LOG="$LOG_DIR/strict_audit.log"
STEP_LOG="$LOG_DIR/step_assembly.log"

# ---- 1. strict 零警告审计 ----------------------------------------
echo ""
echo ">> 阶段 1/2: 全库 validate --profile strict (零警告政策)"
NO_COLOR=1 bash "$ROOT/tools/audit_strict_physics.sh" "$BUILD_DIR" 2>&1 | tee "$AUDIT_LOG"
audit_status=${PIPESTATUS[0]}

# ---- 2. 逐步装配质检 ---------------------------------------------
echo ""
echo ">> 阶段 2/2: 全库逐步装配质检 (test_step_assembly.py)"
"$PYTHON" "$ROOT/tests/test_step_assembly.py" "$DATA_DIR/models" \
    --catalog "$DATA_DIR/tile_catalog.json" 2>&1 | tee "$STEP_LOG"
step_status=${PIPESTATUS[0]}

# ---- 3. Markdown 报告 (可选) -------------------------------------
if [ -n "$REPORT_FILE" ]; then
    echo ""
    echo ">> 生成巡检报告: $REPORT_FILE"
    mkdir -p "$(dirname "$REPORT_FILE")"
    MAGTILE_ROOT="$ROOT" AUDIT_LOG="$AUDIT_LOG" STEP_LOG="$STEP_LOG" \
    AUDIT_STATUS="$audit_status" STEP_STATUS="$step_status" \
    REPORT_FILE="$REPORT_FILE" "$PYTHON" - <<'PYEOF'
import datetime
import glob
import json
import os
import re

root = os.environ["MAGTILE_ROOT"]
audit_log = open(os.environ["AUDIT_LOG"], encoding="utf-8").read().splitlines()
step_log = open(os.environ["STEP_LOG"], encoding="utf-8").read().splitlines()
audit_ok = os.environ["AUDIT_STATUS"] == "0"
step_ok = os.environ["STEP_STATUS"] == "0"

# ---- 解析 strict 审计日志 (tools/audit_strict_physics.sh 输出) ----
RULE_OF_CODE = {
    "floating_tile": "R1 接地支撑",
    "isolated_tile": "R2 磁力连接",
    "disconnected_assembly": "R2 磁力连接",
    "tile_overlap": "R3 无重叠",
    "unstable_center_of_mass": "R4 重心稳定",
    "no_ground_contact": "R4 重心稳定",
    "hanging_chain_overload": "R5 悬挂承重",
    "hanging_chain_long": "R5 悬挂承重",
    "cantilever_overload": "R6 悬臂力矩",
    "unplaceable_tile": "R7 装配可达",
    "enclosed_placement": "R7 装配可达",
    "single_point_of_failure": "R8 结构冗余",
    "no_structural_redundancy": "R8 结构冗余",
    "unbraced_wall_too_tall": "R8 结构冗余",
}
RULES = ["R1 接地支撑", "R2 磁力连接", "R3 无重叠", "R4 重心稳定",
         "R5 悬挂承重", "R6 悬臂力矩", "R7 装配可达", "R8 结构冗余"]

status_re = re.compile(r"^\[(通过|豁免|警告|失败)\] (\S+)")
issue_re = re.compile(r"^\s+\[(错误|警告)\] (.*)\((\w+)\)\s*$")

models = {}          # id -> 状态 (通过/豁免/警告/失败)
issues = []          # (model_id, 模型状态, 严重级, code, 文案)
current = None
for line in audit_log:
    m = status_re.match(line)
    if m:
        current = m.group(2)
        models[current] = m.group(1)
        continue
    m = issue_re.match(line)
    if m and current:
        issues.append((current, models[current], m.group(1), m.group(3),
                       m.group(2).strip().rstrip(",")))

total = len(models)
n_pass = sum(1 for s in models.values() if s == "通过")
n_waived = sum(1 for s in models.values() if s == "豁免")
n_warned = sum(1 for s in models.values() if s == "警告")
n_failed = sum(1 for s in models.values() if s == "失败")

# 按规则聚合: {规则: {"error": n, "warning": n, "waived": n}}
by_rule = {r: {"error": 0, "warning": 0, "waived": 0} for r in RULES}
by_code = {}
for _, model_status, severity, code, _ in issues:
    rule = RULE_OF_CODE.get(code, "未知规则")
    by_rule.setdefault(rule, {"error": 0, "warning": 0, "waived": 0})
    by_code[code] = by_code.get(code, 0) + 1
    if severity == "错误":
        by_rule[rule]["error"] += 1
    elif model_status == "豁免":
        by_rule[rule]["waived"] += 1
    else:
        by_rule[rule]["warning"] += 1

# ---- 解析逐步装配日志 --------------------------------------------
step_pass = sum(1 for l in step_log if l.startswith("[PASS]"))
step_fail = sum(1 for l in step_log if l.startswith("[FAIL]"))

# ---- D4+ 实物复核清单 (L3, 政策见 BUILD_VERIFICATION.md) ----------
d4 = []
for path in sorted(glob.glob(os.path.join(root, "data/models/*.json"))):
    m = json.load(open(path, encoding="utf-8"))
    if m.get("difficulty", 0) >= 4:
        mid = m.get("id", os.path.basename(path)[:-5])
        d4.append((mid, m["difficulty"], len(m.get("final_assembly", [])),
                   models.get(mid, "未跑")))

# ---- 生成 Markdown -----------------------------------------------
now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
out = []
out.append("# 全库 strict 物理巡检报告")
out.append("")
out.append(f"- 生成时间: {now}")
out.append("- 生成工具: `tools/run_strict_audit.sh` "
           "(`magtile_app validate --profile strict` 零警告审计 + "
           "`tests/test_step_assembly.py` 逐步装配质检)")
out.append("- 校验档位: `strict_consumer` (悬挂额定 120g/单位边长, "
           "抗碰撞安全系数 0.7 → 有效悬挂预算 84g/边长, 有效抗弯预算 "
           "17.5 g·单位; 参数依据见 `docs/PHYSICS_RULES.md` 1.4 节)")
out.append("- 零警告政策与豁免白名单: `tools/audit_strict_physics.sh` / "
           "`docs/STRICT_PHYSICS_AUDIT.md`")
out.append("")
out.append("## 1. 总览")
out.append("")
out.append("| 指标 | 数值 |")
out.append("| --- | --- |")
out.append(f"| 模型总数 | {total} |")
out.append(f"| strict 通过 (零警告零错误) | {n_pass} |")
out.append(f"| 白名单豁免 (警告经书面论证) | {n_waived} |")
out.append(f"| 未豁免警告 (拦截) | {n_warned} |")
out.append(f"| 失败 (Error 级) | {n_failed} |")
out.append(f"| 逐步装配质检 | {step_pass} 通过 / {step_fail} 失败 |")
overall = "全绿" if (audit_ok and step_ok) else "未达标"
out.append(f"| 巡检结论 | **{overall}** |")
out.append("")
out.append("## 2. 按规则分类 (R1~R8)")
out.append("")
out.append("统计口径: strict 档全库审计输出的每一条问题行 "
           "(同一模型多个步骤重复报告的问题按行计, 与审计日志一致)。")
out.append("")
out.append("| 规则 | Error | 拦截 Warning | 豁免 Warning |")
out.append("| --- | --- | --- | --- |")
for rule in RULES:
    c = by_rule[rule]
    out.append(f"| {rule} | {c['error']} | {c['warning']} | {c['waived']} |")
extra = {r: c for r, c in by_rule.items() if r not in RULES and any(c.values())}
for rule, c in extra.items():
    out.append(f"| {rule} | {c['error']} | {c['warning']} | {c['waived']} |")
out.append("")
if by_code:
    out.append("问题代码分布:")
    out.append("")
    for code, n in sorted(by_code.items(), key=lambda kv: -kv[1]):
        out.append(f"- `{code}`: {n} 条")
    out.append("")
out.append("## 3. 问题明细")
out.append("")
blocking = [i for i in issues if i[1] in ("警告", "失败")]
if blocking:
    out.append("| 模型 | 级别 | 代码 | 文案 |")
    out.append("| --- | --- | --- | --- |")
    for mid, _, severity, code, msg in blocking:
        out.append(f"| `{mid}` | {severity} | `{code}` | {msg} |")
else:
    out.append("无 —— 全库不存在任何 Error 级问题与未豁免 Warning。")
out.append("")
out.append("## 4. 豁免清单")
out.append("")
waived_issues = [i for i in issues if i[1] == "豁免"]
if waived_issues:
    out.append("| 模型 | 代码 | 条数 | 论证出处 |")
    out.append("| --- | --- | --- | --- |")
    agg = {}
    for mid, _, _, code, _ in waived_issues:
        agg[(mid, code)] = agg.get((mid, code), 0) + 1
    for (mid, code), n in sorted(agg.items()):
        out.append(f"| `{mid}` | `{code}` | {n} | `docs/STRICT_PHYSICS_AUDIT.md` |")
else:
    out.append("无豁免。")
out.append("")
out.append("## 5. D4+ 实物复核清单 (L3)")
out.append("")
out.append(f"以下 {len(d4)} 个 difficulty ≥ 4 模型软件校验全绿后, 按 "
           "`docs/BUILD_VERIFICATION.md` 必须逐个完成 L3 实物复核 "
           "(计时分步搭建 / 敲击 / 提起 / 拆解重搭 / 儿童实测), "
           "结论写入旁车文件 `data/verification/<model_id>.json` 并与内容哈希绑定。"
           "**strict 全绿是入库必要条件, 不替代实物复核。**")
out.append("")
out.append("| 模型 | 难度 | 片数 | strict 结果 |")
out.append("| --- | --- | --- | --- |")
for mid, diff, pieces, status in d4:
    out.append(f"| `{mid}` | D{diff} | {pieces} | {status} |")
out.append("")

with open(os.environ["REPORT_FILE"], "w", encoding="utf-8") as f:
    f.write("\n".join(out))
print(f"报告已写入: {os.environ['REPORT_FILE']}")
PYEOF
fi

# ---- 汇总 --------------------------------------------------------
echo ""
echo "=============================================================="
if [ "$audit_status" -eq 0 ] && [ "$step_status" -eq 0 ]; then
    echo " strict 巡检结论: 全绿 (strict 零警告审计 + 逐步装配质检均通过)"
    rm -rf "$LOG_DIR"
    exit 0
fi
[ "$audit_status" -ne 0 ] && echo " strict 巡检结论: strict 零警告审计未通过 (退出码 $audit_status)"
[ "$step_status" -ne 0 ] && echo " strict 巡检结论: 逐步装配质检未通过 (退出码 $step_status)"
echo " 分项日志: $LOG_DIR"
exit 1
