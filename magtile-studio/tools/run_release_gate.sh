#!/usr/bin/env bash
# =============================================================
# MagTile Studio - 发布前 QA 门禁一键脚本 (Release Gate)
#
# 日常 push CI (tests/run_full_qa.sh) 为控制流水线时长默认跳过
# 两道发布专项关卡; 本脚本把发布/打包前必跑的检查串成一条命令,
# 何时跑与完整说明见 docs/TESTING.md 「发布门禁」一节:
#
#   1. 免费层清单对齐核验   tools/verify_free_tier.py      [阻断]
#      免费标签恰 30 + 全 core-9 + 与 starter 打包清单一致
#      (对齐决议见 docs/FREE_TIER_MANIFEST.md)
#   2. 弱磁严格档全库巡检   tools/run_strict_audit.sh      [阻断]
#      strict 零警告审计 + 逐步装配质检 (缺 magtile_app 自动构建)
#   3. L3 实物复核缺口报告  tools/list_physical_pending.py [报告]
#      D4+ 未实物复核数量, 默认仅报告不阻断 (与 run_full_qa.sh
#      关卡 16 同一口径); --fail-on-pending 时升级为硬闸门
#
# 用法:
#   tools/run_release_gate.sh [build_dir] [选项]
#     build_dir          构建目录 (默认 build)
#     --full             发布档: 改为完整跑 16 关全量 QA 并开启
#                        全部可选关卡 (= MAGTILE_FREE_TIER_CHECK=1
#                        MAGTILE_STRICT_AUDIT=1 tests/run_full_qa.sh),
#                        CI 手动流水线 release-gate.yml 默认即此档
#     --fail-on-pending  L3 待复核清单非空按失败处理 (正式出包终防线)
#     --report FILE      strict 巡检附带 Markdown 报告 (透传
#                        run_strict_audit.sh --report; 不支持与 --full 同用)
#     --dry-run          只打印将执行的关卡与命令, 不实际执行
#     -h | --help        打印本说明
#
# 退出码: 0 = 全部阻断关卡通过; 1 = 存在失败关卡; 2 = 环境/参数不满足
# =============================================================
set -u

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
BUILD_DIR=""
FULL=0
FAIL_ON_PENDING=0
REPORT_FILE=""
DRY_RUN=0

usage() { sed -n '2,32p' "$0"; }

while [ "$#" -gt 0 ]; do
    case "$1" in
        --full)            FULL=1; shift ;;
        --fail-on-pending) FAIL_ON_PENDING=1; shift ;;
        --report)
            [ "$#" -ge 2 ] || { echo "错误: --report 需要文件参数" >&2; exit 2; }
            REPORT_FILE="$2"; shift 2 ;;
        --report=*)        REPORT_FILE="${1#--report=}"; shift ;;
        --dry-run)         DRY_RUN=1; shift ;;
        -h|--help)         usage; exit 0 ;;
        -*)
            echo "错误: 未知选项 $1 (用法见 --help)" >&2; exit 2 ;;
        *)
            if [ -n "$BUILD_DIR" ]; then
                echo "错误: 多余的位置参数 $1 (build_dir 已是 $BUILD_DIR)" >&2
                exit 2
            fi
            BUILD_DIR="$1"; shift ;;
    esac
done

BUILD_DIR="${BUILD_DIR:-$ROOT/build}"
case "$BUILD_DIR" in
    /*) ;;
    *) BUILD_DIR="$ROOT/$BUILD_DIR" ;;
esac
if [ "$FULL" -eq 1 ] && [ -n "$REPORT_FILE" ]; then
    echo "错误: --report 只在默认档可用 (--full 档 strict 巡检嵌在全量 QA 内," >&2
    echo "      如需报告请单独执行 tools/run_strict_audit.sh --report FILE)" >&2
    exit 2
fi

PYTHON="$(command -v python3 || command -v python)"
if [ -z "$PYTHON" ]; then
    echo "错误: 需要 python3 (免费层核验与实物复核报告依赖)" >&2
    exit 2
fi

# ---- 彩色输出 (与 run_full_qa.sh 同一约定) -----------------------
if { [ -t 1 ] || [ -n "${FORCE_COLOR:-}" ]; } && [ -z "${NO_COLOR:-}" ]; then
    RED=$'\033[31m'; GREEN=$'\033[32m'; YELLOW=$'\033[33m'
    CYAN=$'\033[36m'; BOLD=$'\033[1m'; RESET=$'\033[0m'
else
    RED=""; GREEN=""; YELLOW=""; CYAN=""; BOLD=""; RESET=""
fi

LOG_DIR="$(mktemp -d /tmp/magtile_release_gate_XXXXXX)"
STAGE_NAMES=()
STAGE_RESULTS=()
STAGE_TIMES=()
stage_index=0

# run_gate <关卡名> <命令...>
#   dry-run 档只打印命令; 实跑档输出实时透传并留档 $LOG_DIR,
#   失败不中断 (报告一次给全), 计入失败总数。
run_gate() {
    local name="$1"; shift
    stage_index=$((stage_index + 1))

    if [ "$DRY_RUN" -eq 1 ]; then
        printf '  %d. %-32s $ %s\n' "$stage_index" "$name" "$*"
        return 0
    fi

    local log="$LOG_DIR/$(printf '%02d' "$stage_index")_${name// /_}.log"
    echo ""
    echo "${BOLD}${CYAN}==============================================================${RESET}"
    echo "${BOLD}${CYAN} 门禁关卡 $stage_index: $name${RESET}"
    echo "${BOLD}${CYAN} $ $*${RESET}"
    echo "${BOLD}${CYAN}==============================================================${RESET}"

    local start end status
    start=$(date +%s)
    "$@" 2>&1 | tee "$log"
    status=${PIPESTATUS[0]}
    end=$(date +%s)

    STAGE_NAMES+=("$name")
    STAGE_TIMES+=("$((end - start))s")
    if [ "$status" -eq 0 ]; then
        STAGE_RESULTS+=("PASS")
        echo "${GREEN}${BOLD}[通过] $name${RESET}"
    else
        STAGE_RESULTS+=("FAIL")
        echo "${RED}${BOLD}[失败] $name (退出码 $status, 日志: $log)${RESET}"
    fi
    return "$status"
}

if [ "$DRY_RUN" -eq 1 ]; then
    echo "${BOLD}发布门禁 dry-run (只列关卡, 不执行):${RESET}"
else
    echo "${BOLD}=============================================================="
    echo " MagTile Studio 发布门禁 (Release Gate)"
    echo " 项目根: $ROOT"
    echo " 构建目录: $BUILD_DIR"
    echo " 档位: $([ "$FULL" -eq 1 ] && echo '--full (16 关全量 QA + 发布专项)' || echo '默认 (三道发布专项)')"
    echo "==============================================================${RESET}"
fi

# ---- 关卡编排 ----------------------------------------------------
pending_args=("$ROOT/data/models")
pending_name="L3 实物复核缺口报告 (报告型)"
if [ "$FAIL_ON_PENDING" -eq 1 ]; then
    pending_args+=(--fail-on-pending)
    pending_name="L3 实物复核缺口 (硬闸门)"
fi

if [ "$FULL" -eq 1 ]; then
    # 发布档: 全量 QA 一并跑, 免费层对齐/strict 巡检/待复核报告
    # 分别是其中的关卡 10/15/16
    run_gate "全量 QA (含免费层对齐 + strict 巡检)" \
        env MAGTILE_FREE_TIER_CHECK=1 MAGTILE_STRICT_AUDIT=1 \
        bash "$ROOT/tests/run_full_qa.sh" "$BUILD_DIR"
    if [ "$FAIL_ON_PENDING" -eq 1 ]; then
        # 全量 QA 内的关卡 16 是报告型, 终防线在这里单独加闸
        run_gate "$pending_name" \
            "$PYTHON" "$ROOT/tools/list_physical_pending.py" "${pending_args[@]}"
    fi
else
    run_gate "免费层清单对齐核验" \
        "$PYTHON" "$ROOT/tools/verify_free_tier.py" \
        --models-dir "$ROOT/data/models" \
        --catalog "$ROOT/data/tile_catalog.json"

    if [ -n "$REPORT_FILE" ]; then
        run_gate "弱磁严格档全库巡检 (strict)" \
            bash "$ROOT/tools/run_strict_audit.sh" "$BUILD_DIR" --report "$REPORT_FILE"
    else
        run_gate "弱磁严格档全库巡检 (strict)" \
            bash "$ROOT/tools/run_strict_audit.sh" "$BUILD_DIR"
    fi

    run_gate "$pending_name" \
        "$PYTHON" "$ROOT/tools/list_physical_pending.py" "${pending_args[@]}"
fi

if [ "$DRY_RUN" -eq 1 ]; then
    rm -rf "$LOG_DIR"
    exit 0
fi

# ---- 总结报告 ----------------------------------------------------
pass_count=0; fail_count=0
echo ""
echo "${BOLD}=============================================================="
echo " 发布门禁报告"
echo "==============================================================${RESET}"
for i in "${!STAGE_NAMES[@]}"; do
    case "${STAGE_RESULTS[$i]}" in
        PASS) pass_count=$((pass_count + 1))
              printf '  %s%-6s%s %-44s %s\n' "$GREEN" "PASS" "$RESET" "${STAGE_NAMES[$i]}" "${STAGE_TIMES[$i]}" ;;
        FAIL) fail_count=$((fail_count + 1))
              printf '  %s%-6s%s %-44s %s\n' "$RED" "FAIL" "$RESET" "${STAGE_NAMES[$i]}" "${STAGE_TIMES[$i]}" ;;
    esac
done
echo "${BOLD}--------------------------------------------------------------${RESET}"
if [ "$fail_count" -gt 0 ]; then
    echo "${RED}${BOLD} 结论: $((pass_count + fail_count)) 个门禁关卡中 $fail_count 个失败, 不可发布${RESET}"
    echo " 分项日志: $LOG_DIR"
    exit 1
fi
if [ "$FAIL_ON_PENDING" -eq 0 ]; then
    echo "${YELLOW} 提醒: L3 实物复核为报告型不阻断; 正式出包前追加 --fail-on-pending 作为终防线${RESET}"
fi
echo "${GREEN}${BOLD} 结论: 全部 $pass_count 个门禁关卡通过, 可进入打包流程${RESET}"
echo " 打包手册: scripts/package_qt_desktop.md / scripts/package_windows.md"
rm -rf "$LOG_DIR"
exit 0
