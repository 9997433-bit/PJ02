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
#    9. 片型分层检查         (core-9 覆盖率 + 需要扩展装标签, --strict 硬闸门)
#   10. 免费层清单对齐       (可选: MAGTILE_FREE_TIER_CHECK=1 时执行,
#       tools/verify_free_tier.py —— 免费标签数=30 + 全 core-9 +
#       与 starter 打包清单一致, 决议见 docs/FREE_TIER_MANIFEST.md)
#   11. 教程完整性           (静态走查 + 教程引擎实跑)
#   12. 物理负例 x N         (不成立的结构必须被拒绝, 错误码必须正确)
#   13. 物理正例 x N         (预算内的合法结构必须放行)
#   14. GL 渲染冒烟          (无头渲染 + 截图校验, 无显示环境自动降级)
#   15. 弱磁严格档全库巡检   (可选: MAGTILE_STRICT_AUDIT=1 时执行,
#       tools/run_strict_audit.sh —— strict 零警告审计 + 逐步装配质检)
#   16. L3 实物复核缺口报告   (报告型: 输出 D4+ 未实物复核模型数量,
#       tools/list_physical_pending.py —— 仅报告不阻断, 实物复核是
#       线下人工流程, 规程见 docs/PHYSICAL_REBUILD_CHECKLIST.md)
#   17. 教程步进性能基准       (可选: MAGTILE_TUTORIAL_BENCH=1 时执行,
#       tools/bench_tutorial_step.py —— 小/中/大代表模型逐步计时
#       nextStep/goToStep + 渲染层每步查询, 输出每步 ms 与 P95,
#       超预算退出 1; CTest 关卡已含 bench_tutorial_step 同口径回归,
#       此处为输出完整耗时表的显式巡检, 见 docs/TESTING.md 3.16 节)
#   18. 儿童友好文案守卫       (用户可见中文文案红线: 恐吓词/催促话术,
#       tools/check_child_friendly_copy.py —— Qt QML / Android strings.xml /
#       Kotlin / 展示层 C++ / 模型步骤文案, UI_UX_SPEC §4.3 §4.5 P3, 秒级)
#   19. L2 抗扰动巡检          (可选: MAGTILE_L2_JITTER=1 时执行,
#       tools/run_strict_audit.sh --jitter-only —— D4+ 模型逐个
#       validate --profile strict --jitter 50, 验证金字塔 L2 层门禁挂钩;
#       CLI 未实装 --jitter 前为占位通过, 实装后自动实跑, TESTING.md 3.17)
#   20. 内容系列归类机检        (可选: MAGTILE_SERIES_CHECK=1 时执行,
#       tools/check_content_series.py --strict —— 每模型须带
#       content_meta.series (13 主题词值) 或 matrix_bucket (矩阵外桶),
#       词值对照 data/content_series_map.json 词表, 输出主题 × 难度
#       矩阵计数; CONTENT_GAP_AUDIT.md §7.3 机检化, 回填底稿见其附录 A)
#
# 用法:
#   tests/run_full_qa.sh [构建目录]          # 默认 build
# 环境变量:
#   MAGTILE_CMAKE_ARGS   附加 CMake 配置参数 (如 "-DMAGTILE_BUILD_GL_RENDERER=OFF")
#   MAGTILE_FREE_TIER_CHECK=1  启用可选关卡 10 (免费层清单对齐核验)
#   MAGTILE_STRICT_AUDIT=1  启用可选关卡 15 (弱磁严格档全库巡检)
#   MAGTILE_TUTORIAL_BENCH=1  启用可选关卡 17 (教程步进性能基准)
#   MAGTILE_L2_JITTER=1  启用可选关卡 19 (L2 抗扰动巡检, D4+ jitter)
#   MAGTILE_SERIES_CHECK=1  启用可选关卡 20 (内容系列归类机检)
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

# ---- 4~11: 内容质量关卡 (脚本直跑, 与 CTest 注册互为冗余防线) ----
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

# 片型分层 (core-9 覆盖率 + 需要扩展装标签 + 免费层红线): 免费 30
# 选品已定稿 (CONTENT_STRATEGY.md §2.5.1), --strict 使任何 WARN
# (缺标 / 多标 / 免费层 core-9 占比 < 80%) 都作为硬失败
run_stage "片型分层检查 (core-9, strict)" \
    "$PYTHON" "$ROOT/tools/check_core5_usage.py" "$DATA_DIR/models" \
    --catalog "$DATA_DIR/tile_catalog.json" --strict

# 免费层三端清单对齐 (可选): 免费标签数=30 + 全 core-9 + 与 Windows
# starter 打包清单集合相等 (对齐决议见 docs/FREE_TIER_MANIFEST.md)。
# 免费层清单只在选品换血时变化, 日常合入不受它约束, 故默认跳过;
# 发布打包前置 MAGTILE_FREE_TIER_CHECK=1 作为终防线。
if [ -n "${MAGTILE_FREE_TIER_CHECK:-}" ]; then
    run_stage "免费层清单对齐核验" \
        "$PYTHON" "$ROOT/tools/verify_free_tier.py" \
        --models-dir "$DATA_DIR/models" \
        --catalog "$DATA_DIR/tile_catalog.json"
else
    skip_stage "免费层清单对齐核验" \
        "可选关卡, 置 MAGTILE_FREE_TIER_CHECK=1 开启 (tools/verify_free_tier.py)"
fi

run_stage "教程完整性" \
    bash "$TESTS_DIR/test_tutorial_integrity.sh" "$APP" "$ROOT"

# ---- 12: 物理负例 (注册表完整性 + 每个夹具一个关卡) ---------------
# 每个夹具的期望 (错误/警告码 + 级别) 由同名 .expected sidecar 声明,
# 执行器 test_physics_negative.sh 读取并断言; 注册表关卡保证必备负例
# 清单齐全、夹具与 sidecar 一一对应、正例目录非空 —— 缺夹具即 FAIL,
# 负例套件不允许悄悄缩水。
run_stage "物理负例夹具注册表" \
    bash "$TESTS_DIR/test_physics_fixture_registry.sh" "$TESTS_DIR"

negative_found=0
for fixture in "$TESTS_DIR"/test_physics_negative/*.json; do
    [ -e "$fixture" ] || continue
    negative_found=$((negative_found + 1))
    fixture_name="$(basename "$fixture" .json)"
    run_stage "物理负例: $fixture_name" \
        bash "$TESTS_DIR/test_physics_negative.sh" "$APP" "$DATA_DIR" "$fixture"
done
if [ "$negative_found" -eq 0 ]; then
    skip_stage "物理负例" "tests/test_physics_negative/ 下没有夹具 (可用 tools/generate_test_models.py 生成)"
fi

# ---- 13: 物理正例 (每个夹具一个关卡) -----------------------------
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

# ---- 13.5: R9 蒙特卡洛容差抖动 (每个夹具一个关卡) ------------------
# 带 .expected sidecar 的是抖动负例 ("静态全绿但注入 ±1.5mm/±2° 误差
# 后必挂" 的边缘设计, 执行器先断言普通 validate 放行再断言 --jitter
# 拒绝); 不带 sidecar 的是抖动正例 (加固后同构造放行, 防矫枉过正)。
# 物理正例对照组的抖动档与旗舰模型抖动回归由 CTest 关卡覆盖
# (physics_jitter_positive_* / validate_jitter_*), 详见 TESTING.md 3.18。
jitter_found=0
for fixture in "$TESTS_DIR"/test_physics_jitter/*.json; do
    [ -e "$fixture" ] || continue
    jitter_found=$((jitter_found + 1))
    fixture_name="$(basename "$fixture" .json)"
    run_stage "物理抖动 R9: $fixture_name" \
        bash "$TESTS_DIR/test_physics_jitter.sh" "$APP" "$DATA_DIR" "$fixture"
done
if [ "$jitter_found" -eq 0 ]; then
    skip_stage "物理抖动 R9" "tests/test_physics_jitter/ 下没有夹具"
fi

# ---- 14: GL 渲染冒烟 --------------------------------------------
run_stage "GL 渲染冒烟" bash "$TESTS_DIR/test_gl_smoke.sh" "$BUILD_DIR"

# ---- 15: 弱磁严格档全库巡检 (可选关卡) ---------------------------
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

# ---- 16: L3 实物复核缺口报告 (报告型, 不阻断) ---------------------
# 软件全绿不替代实物复核: D4+ 模型须按 docs/PHYSICAL_REBUILD_CHECKLIST.md
# 实搭复核后落盘 content_meta.physical_verified 或旁车验证文件。
# 本关卡只报告未复核数量供 QA 排产, 默认永不失败 (线下人工进度不卡 CI);
# 发布打包前可单独执行 --fail-on-pending 作为终防线。
run_stage "L3 实物复核缺口报告" \
    "$PYTHON" "$ROOT/tools/list_physical_pending.py" "$DATA_DIR/models"

# ---- 17: 教程步进性能基准 (可选关卡) ------------------------------
# 大模型 (100+ 片) 教程步进不能卡死: 小/中/大代表模型逐步计时
# nextStep/goToStep + 渲染层每步查询, 每步 ms 与 P95, 超预算退出 1。
# CTest 关卡已含 bench_tutorial_step 同口径回归, 此处为输出完整
# 每步耗时表的显式巡检, 默认跳过避免重复计时 (docs/TESTING.md 3.16)。
if [ -n "${MAGTILE_TUTORIAL_BENCH:-}" ]; then
    run_stage "教程步进性能基准" \
        "$PYTHON" "$ROOT/tools/bench_tutorial_step.py" --build-dir "$BUILD_DIR"
else
    skip_stage "教程步进性能基准" \
        "可选关卡, 置 MAGTILE_TUTORIAL_BENCH=1 开启 (tools/bench_tutorial_step.py)"
fi

# ---- 18: 儿童友好文案守卫 (UI_UX_SPEC §4.3/§4.5/P3 红线) ----------
# 用户可见中文文案不得出现「失败/错误/崩溃/网络异常」等恐吓词与
# 倒计时/限时/稀缺催促话术, 技术诊断只进日志; 覆盖 Qt QML /
# Android strings.xml / Kotlin / 展示层 C++ / 模型步骤与提示文案。
run_stage "儿童友好文案守卫" \
    "$PYTHON" "$ROOT/tools/check_child_friendly_copy.py"

# ---- 19: L2 抗扰动巡检 (可选关卡, 占位挂钩) -----------------------
# 验证金字塔 L2 层 (BUILD_VERIFICATION.md 第 1 节蒙特卡洛容差抖动)
# 的 CI 挂钩: D4+ 模型逐个 validate --profile strict --jitter 50。
# CLI 尚未实装 --jitter (并行 L2 任务落地中): 实装并登记进 --help 用法文本前,
# 开启本关卡也只打印占位说明并计通过; 实装后自动切换为实跑, 任一
# D4+ 模型退出码非零即失败 (占位与启用条件见 docs/TESTING.md 3.17)。
# 关卡 15 的 strict 巡检已含同一阶段 (auto 档), 本关卡供只想单独
# 加验 jitter 而不重跑全库 strict 审计的流水线使用。
if [ -n "${MAGTILE_L2_JITTER:-}" ]; then
    run_stage "L2 抗扰动巡检 (D4+ jitter)" \
        bash "$ROOT/tools/run_strict_audit.sh" "$BUILD_DIR" --jitter-only
else
    skip_stage "L2 抗扰动巡检 (D4+ jitter)" \
        "可选关卡, 置 MAGTILE_L2_JITTER=1 开启 (tools/run_strict_audit.sh --jitter-only; CLI --jitter 未实装时为占位)"
fi

# ---- 20: 内容系列归类机检 (可选关卡) ------------------------------
# CONTENT_GAP_AUDIT.md §7.3 「series 回填 + 矩阵进度机检化」的门禁挂钩:
# 每个模型必须带 content_meta.series (13 主题词值) 或
# content_meta.matrix_bucket (矩阵外桶), 词值对照
# data/content_series_map.json 词表, --strict 使任何缺失/非法即失败。
# series 回填 (审计附录 A 为底稿) 落库前全库缺失、开启即红, 故默认
# 跳过; 回填合入后内容批次评审置 MAGTILE_SERIES_CHECK=1 作为硬闸门。
if [ -n "${MAGTILE_SERIES_CHECK:-}" ]; then
    run_stage "内容系列归类机检 (series)" \
        "$PYTHON" "$ROOT/tools/check_content_series.py" "$DATA_DIR/models" \
        --map "$DATA_DIR/content_series_map.json" --strict
else
    skip_stage "内容系列归类机检 (series)" \
        "可选关卡, 置 MAGTILE_SERIES_CHECK=1 开启 (tools/check_content_series.py --strict)"
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
