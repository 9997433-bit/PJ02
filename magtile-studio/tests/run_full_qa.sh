#!/usr/bin/env bash
# =============================================================
# MagTile Studio - 全量质量保证流水线 (一键 QA)
#
# 按固定顺序执行全部质量关卡, 输出彩色分项报告与总结论。
# 测试对象不只是代码 —— 更是内容: 每一个入库模型的物理合理性
# (搭得起来)、教程逻辑 (讲得通)、内容体量 (值得搭) 都在关卡之内。
#
# 关卡顺序 (详见 docs/TESTING.md):
#    1. CMake 配置
#    2. 增量构建
#    3. CTest 全量回归 (物理/教程/负例/正例/逻辑/反平凡 ... 全部注册用例)
#    4. 模型库全量质检       (>= 40 片 + validate 全绿)
#    5. 反平凡模型检查       (>= 3 种片形, >= 2 个 Z 层, 有立置片)
#    6. 模型逻辑质检         (步骤粒度/中文说明/对账/难度区间/BOM)
#    7. 逐步装配质检         (逐片零差错 P1~P8, 见 docs/MODEL_QUALITY.md)
#    8. 模型库唯一性         (结构签名两两比对, 拒绝换皮克隆)
#    9. 片型分层检查         (core-9 覆盖率 + 需要扩展装标签, WARN 不拦截)
#   10. 教程完整性           (静态走查 + 教程引擎实跑)
#   11. 物理负例 x N         (不成立的结构必须被拒绝, 错误码必须正确)
#   12. 物理正例 x N         (预算内的合法结构必须放行)
#   13. GL 渲染冒烟          (无头渲染 + 截图校验, 无显示环境自动降级)
#   14. 弱磁严格档全库巡检   (可选: MAGTILE_STRICT_AUDIT=1 时执行,
#       tools/run_strict_audit.sh —— strict 零警告审计 + 逐步装配质检)
#
# 用法:
#   tests/run_full_qa.sh [构建目录]          # 默认 build
# 环境变量:
#   MAGTILE_CMAKE_ARGS   附加 CMake 配置参数 (如 "-DMAGTILE_BUILD_GL_RENDERER=OFF")
#   MAGTILE_STRICT_AUDIT=1  启用可选关卡 14 (弱磁严格档全库巡检)
#   FORCE_COLOR=1        非终端环境 (CI) 强制彩色输出
#   NO_COLOR=1           禁用彩色输出
#
# 退出码: 0 = 全部关卡通过; 1 = 存在失败关卡; 2 = 环境不满足
# =============================================================
set -u

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
BUILD_DIR="${1:-$ROOT/build}"
case "$BUILD_DIR" in
    /*) ;;
    *) BUILD_DIR="$ROOT/$BUILD_DIR" ;;
esac
TESTS_DIR="$ROOT/tests"
DATA_DIR="$ROOT/data"
APP="$BUILD_DIR/magtile_app"
LOG_DIR="$(mktemp -d /tmp/magtile_qa_XXXXXX)"

# ---- 彩色输出 ---------------------------------------------------
if { [ -t 1 ] || [ -n "${FORCE_COLOR:-}" ]; } && [ -z "${NO_COLOR:-}" ]; then
    RED=$'\033[31m'; GREEN=$'\033[32m'; YELLOW=$'\033[33m'
    CYAN=$'\033[36m'; BOLD=$'\033[1m'; RESET=$'\033[0m'
else
    RED=""; GREEN=""; YELLOW=""; CYAN=""; BOLD=""; RESET=""
fi

PYTHON="$(command -v python3 || command -v python)"
if [ -z "$PYTHON" ]; then
    echo "${RED}错误: 需要 python3 (模型逻辑/反平凡检查依赖)${RESET}" >&2
    exit 2
fi

# ---- 关卡执行器 -------------------------------------------------
# run_stage <关卡名> <命令...>
#   输出实时透传 (CI 日志保留全部细节), 同时记录到 $LOG_DIR 便于回看;
#   失败不中断流水线 (报告要一次给全), 但会计入失败总数。
STAGE_NAMES=()
STAGE_RESULTS=()
STAGE_TIMES=()
stage_index=0

run_stage() {
    local name="$1"; shift
    stage_index=$((stage_index + 1))
    local log="$LOG_DIR/$(printf '%02d' "$stage_index")_${name// /_}.log"

    echo ""
    echo "${BOLD}${CYAN}==============================================================${RESET}"
    echo "${BOLD}${CYAN} 关卡 $stage_index: $name${RESET}"
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

skip_stage() {
    local name="$1" reason="$2"
    stage_index=$((stage_index + 1))
    STAGE_NAMES+=("$name")
    STAGE_RESULTS+=("SKIP")
    STAGE_TIMES+=("-")
    echo "${YELLOW}[跳过] $name: $reason${RESET}"
}

echo "${BOLD}=============================================================="
echo " MagTile Studio 全量 QA 流水线"
echo " 项目根: $ROOT"
echo " 构建目录: $BUILD_DIR"
echo "==============================================================${RESET}"

# ---- 1/2: 配置 + 构建 (失败则后续关卡全部无从谈起, 直接终止) -----
# shellcheck disable=SC2086  # MAGTILE_CMAKE_ARGS 按词拆分是预期行为
if ! run_stage "CMake 配置" \
        cmake -S "$ROOT" -B "$BUILD_DIR" -DCMAKE_BUILD_TYPE=Release \
        ${MAGTILE_CMAKE_ARGS:-}; then
    echo "${RED}${BOLD}配置失败, 流水线终止${RESET}" >&2
    exit 1
fi

nproc_val="$( (command -v nproc >/dev/null && nproc) || sysctl -n hw.ncpu 2>/dev/null || echo 2)"
if ! run_stage "增量构建" cmake --build "$BUILD_DIR" -j "$nproc_val"; then
    echo "${RED}${BOLD}构建失败, 流水线终止${RESET}" >&2
    exit 1
fi

# ---- 3: CTest 全量回归 ------------------------------------------
run_stage "CTest 全量回归" ctest --test-dir "$BUILD_DIR" --output-on-failure

# ---- 4~9: 内容质量关卡 (脚本直跑, 与 CTest 注册互为冗余防线) -----
run_stage "模型库全量质检 (>=40 片)" \
    bash "$TESTS_DIR/test_all_models.sh" "$APP" "$ROOT" 40

run_stage "反平凡模型检查" \
    "$PYTHON" "$TESTS_DIR/test_anti_trivial.py" "$DATA_DIR/models"

run_stage "模型逻辑质检" \
    "$PYTHON" "$TESTS_DIR/test_model_logic.py" "$DATA_DIR/models"

run_stage "逐步装配质检 (逐片零差错)" \
    "$PYTHON" "$TESTS_DIR/test_step_assembly.py" "$DATA_DIR/models" \
    --catalog "$DATA_DIR/tile_catalog.json"

run_stage "模型库唯一性 (克隆检测)" \
    "$PYTHON" "$TESTS_DIR/test_library_uniqueness.py" "$DATA_DIR/models" \
    --catalog "$DATA_DIR/tile_catalog.json"

# 片型分层 (core-9 覆盖率 + 需要扩展装标签 + 免费层红线): 现阶段
# WARN 不计失败 (工具默认退出码 0), 免费 30 选品定稿后加 --strict
run_stage "片型分层检查 (core-9)" \
    "$PYTHON" "$ROOT/tools/check_core5_usage.py" "$DATA_DIR/models" \
    --catalog "$DATA_DIR/tile_catalog.json"

run_stage "教程完整性" \
    bash "$TESTS_DIR/test_tutorial_integrity.sh" "$APP" "$ROOT"

# ---- 10: 物理负例 (每个夹具一个关卡) -----------------------------
# 期望错误码默认与夹具文件名一致, 少数历史夹具通过下表映射
# (与 CMakeLists.txt 中的注册列表保持一致)。
expected_code_for() {
    case "$1" in
        unstable_cantilever) echo "unstable_center_of_mass" ;;
        unplaceable_order)   echo "unplaceable_tile" ;;
        *)                   echo "$1" ;;
    esac
}

negative_found=0
for fixture in "$TESTS_DIR"/test_physics_negative/*.json; do
    [ -e "$fixture" ] || continue
    negative_found=$((negative_found + 1))
    fixture_name="$(basename "$fixture" .json)"
    run_stage "物理负例: $fixture_name" \
        bash "$TESTS_DIR/test_physics_negative.sh" "$APP" "$DATA_DIR" \
        "$fixture" "$(expected_code_for "$fixture_name")"
done
if [ "$negative_found" -eq 0 ]; then
    skip_stage "物理负例" "tests/test_physics_negative/ 下没有夹具 (可用 tools/generate_test_models.py 生成)"
fi

# ---- 11: 物理正例 (每个夹具一个关卡) -----------------------------
positive_found=0
for fixture in "$TESTS_DIR"/test_physics_positive/*.json; do
    [ -e "$fixture" ] || continue
    positive_found=$((positive_found + 1))
    fixture_name="$(basename "$fixture" .json)"
    run_stage "物理正例: $fixture_name" \
        bash "$TESTS_DIR/test_physics_positive.sh" "$APP" "$DATA_DIR" "$fixture"
done
if [ "$positive_found" -eq 0 ]; then
    skip_stage "物理正例" "tests/test_physics_positive/ 下没有夹具 (可用 tools/generate_test_models.py 生成)"
fi

# ---- 12: GL 渲染冒烟 --------------------------------------------
run_stage "GL 渲染冒烟" bash "$TESTS_DIR/test_gl_smoke.sh" "$BUILD_DIR"

# ---- 13: 弱磁严格档全库巡检 (可选关卡) ---------------------------
# strict 档零警告审计 + 逐步装配质检; CTest 关卡已覆盖旗舰模型的
# strict 回归, 这里是全库 131 模型的完整巡检, 默认关闭以控制
# 流水线时长, 发布前 / 内容批量合入时置 MAGTILE_STRICT_AUDIT=1 开启。
if [ -n "${MAGTILE_STRICT_AUDIT:-}" ]; then
    run_stage "弱磁严格档全库巡检 (strict)" \
        bash "$ROOT/tools/run_strict_audit.sh" "$BUILD_DIR"
else
    skip_stage "弱磁严格档全库巡检 (strict)" \
        "可选关卡, 置 MAGTILE_STRICT_AUDIT=1 开启 (tools/run_strict_audit.sh)"
fi

# ---- 总结报告 ---------------------------------------------------
pass_count=0; fail_count=0; skip_count=0
echo ""
echo "${BOLD}=============================================================="
echo " 全量 QA 报告"
echo "==============================================================${RESET}"
for i in "${!STAGE_NAMES[@]}"; do
    case "${STAGE_RESULTS[$i]}" in
        PASS) pass_count=$((pass_count + 1))
              printf '  %s%-6s%s %-40s %s\n' "$GREEN" "PASS" "$RESET" "${STAGE_NAMES[$i]}" "${STAGE_TIMES[$i]}" ;;
        FAIL) fail_count=$((fail_count + 1))
              printf '  %s%-6s%s %-40s %s\n' "$RED" "FAIL" "$RESET" "${STAGE_NAMES[$i]}" "${STAGE_TIMES[$i]}" ;;
        SKIP) skip_count=$((skip_count + 1))
              printf '  %s%-6s%s %-40s %s\n' "$YELLOW" "SKIP" "$RESET" "${STAGE_NAMES[$i]}" "${STAGE_TIMES[$i]}" ;;
    esac
done
echo "${BOLD}--------------------------------------------------------------${RESET}"
total=$((pass_count + fail_count + skip_count))
if [ "$fail_count" -gt 0 ]; then
    echo "${RED}${BOLD} 结论: $total 个关卡中 $fail_count 个失败 (通过 $pass_count, 跳过 $skip_count)${RESET}"
    echo " 分项日志: $LOG_DIR"
    exit 1
fi
echo "${GREEN}${BOLD} 结论: 全部 $pass_count 个关卡通过 (跳过 $skip_count), 内容可发布${RESET}"
rm -rf "$LOG_DIR"
exit 0
