#!/usr/bin/env bash
# =============================================================
# MagTile Studio - 核心用户路径 E2E 冒烟 (上架验收自动子集)
#
# 把 docs/E2E_TEST_MATRIX.md 中已自动化的关键用户路径串成一条命令,
# 供上架前快速回归与 CI 消费 (矩阵编号见该文档第 1 节):
#
#   E2E-01a  CLI 启动冒烟        magtile_app catalog (13 种片型齐全)
#   E2E-11a  免费层清单对齐      tools/verify_free_tier.py
#            (免费标签恰 30 + 全 core-9 + starter 打包清单一致)
#   E2E-11b  CLI 免费筛选对账    library --free-only 数量与 starter
#            清单一致 + 抽样模型在列 + 目录元数据对账通过
#   E2E-06a  免费模型教程步进    tutorial 全程步进, 放置片数与
#            total_pieces 对账 (教程引擎真实跑完)
#   E2E-17a  跨端存档键契约      CLI 写 age_mode -> python sqlite 直读
#            settings 表键名/编码契约 + settings show 回读; 构建目录
#            有 magtile_cross_platform_test 时另跑全量跨端互通断言
#            (样例存档含年龄段/订阅/引导/完成/成就, 见
#            tests/test_cross_platform_progress.cpp)
#   E2E-QT   Qt 无头冒烟         tests/test_qt_smoke.sh 全部路径
#            (首页/家长门/过门流含订阅页/完成庆祝+存档断言, offscreen)
#   E2E-12a  Qt 进度页深链       --smoke-complete-model 造非空存档后
#            --smoke-open-progress 实例化进度页/成就墙, QML 运行时
#            错误一票否决
#   E2E-14a  Android JNI 符号    NDK 交叉编译 libmagtile_core.so +
#            JNI 符号断言 (符号清单运行时解析自 CI android.yml,
#            与流水线口径自动同步); 无 NDK 环境自动 SKIP
#
# 用法:
#   tools/run_e2e_smoke.sh [选项]
#     --build-dir DIR          CLI 构建目录 (默认 build; 缺 magtile_app
#                              时自动 cmake 配置 + 构建)
#     --qt-build-dir DIR       Qt 构建目录 (默认 build-qt; 缺
#                              magtile_studio_qt 时尝试自动构建,
#                              环境无 Qt6 则 SKIP)
#     --android-build-dir DIR  Android 交叉编译目录 (默认 build-android)
#     --skip-qt                跳过 Qt 冒烟项 (记 SKIP)
#     --skip-android           跳过 Android 符号项 (记 SKIP)
#     --strict                 验收档: 任何 SKIP 也按失败处理
#                              (上架签核用, 见矩阵文档第 3 节)
#     -h | --help              打印本说明
#
# 退出码: 0 = 全部执行项通过 (默认档 SKIP 不算失败);
#         1 = 存在失败项 (或 --strict 下存在 SKIP);
#         2 = 环境/参数不满足
# 颜色: FORCE_COLOR=1 强制 / NO_COLOR=1 禁用 (与 run_full_qa.sh 同约定)
# =============================================================
set -u

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
BUILD_DIR="$ROOT/build"
QT_BUILD_DIR="$ROOT/build-qt"
ANDROID_BUILD_DIR="$ROOT/build-android"
SKIP_QT=0
SKIP_ANDROID=0
STRICT=0

usage() { sed -n '2,42p' "$0"; }

while [ "$#" -gt 0 ]; do
    case "$1" in
        --build-dir)
            [ "$#" -ge 2 ] || { echo "错误: --build-dir 需要目录参数" >&2; exit 2; }
            BUILD_DIR="$2"; shift 2 ;;
        --qt-build-dir)
            [ "$#" -ge 2 ] || { echo "错误: --qt-build-dir 需要目录参数" >&2; exit 2; }
            QT_BUILD_DIR="$2"; shift 2 ;;
        --android-build-dir)
            [ "$#" -ge 2 ] || { echo "错误: --android-build-dir 需要目录参数" >&2; exit 2; }
            ANDROID_BUILD_DIR="$2"; shift 2 ;;
        --skip-qt)      SKIP_QT=1; shift ;;
        --skip-android) SKIP_ANDROID=1; shift ;;
        --strict)       STRICT=1; shift ;;
        -h|--help)      usage; exit 0 ;;
        *) echo "错误: 未知参数 $1 (用法见 --help)" >&2; exit 2 ;;
    esac
done
case "$BUILD_DIR"         in /*) ;; *) BUILD_DIR="$ROOT/$BUILD_DIR" ;; esac
case "$QT_BUILD_DIR"      in /*) ;; *) QT_BUILD_DIR="$ROOT/$QT_BUILD_DIR" ;; esac
case "$ANDROID_BUILD_DIR" in /*) ;; *) ANDROID_BUILD_DIR="$ROOT/$ANDROID_BUILD_DIR" ;; esac

PYTHON="$(command -v python3 || command -v python)"
if [ -z "$PYTHON" ]; then
    echo "错误: 需要 python3 (免费层核验与教程对账依赖)" >&2
    exit 2
fi

# ---- 彩色输出 (与 run_full_qa.sh / run_release_gate.sh 同约定) ----
if { [ -t 1 ] || [ -n "${FORCE_COLOR:-}" ]; } && [ -z "${NO_COLOR:-}" ]; then
    RED=$'\033[31m'; GREEN=$'\033[32m'; YELLOW=$'\033[33m'
    CYAN=$'\033[36m'; BOLD=$'\033[1m'; RESET=$'\033[0m'
else
    RED=""; GREEN=""; YELLOW=""; CYAN=""; BOLD=""; RESET=""
fi

LOG_DIR="$(mktemp -d /tmp/magtile_e2e_smoke_XXXXXX)"
TMP_DIR="$(mktemp -d /tmp/magtile_e2e_tmp_XXXXXX)"
trap 'rm -rf "$TMP_DIR"' EXIT
STAGE_NAMES=()
STAGE_RESULTS=()
STAGE_TIMES=()
stage_index=0

# run_stage <名称> <命令/函数...>: 实时透传输出并留档, 失败不中断
# (报告一次给全); skip_stage <名称> <原因>: 记 SKIP 不执行。
run_stage() {
    local name="$1"; shift
    stage_index=$((stage_index + 1))
    local log="$LOG_DIR/$(printf '%02d' "$stage_index")_${name// /_}.log"
    echo ""
    echo "${BOLD}${CYAN}==============================================================${RESET}"
    echo "${BOLD}${CYAN} E2E 冒烟 $stage_index: $name${RESET}"
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
    echo ""
    echo "${YELLOW}[跳过] $name —— $reason${RESET}"
}

echo "${BOLD}=============================================================="
echo " MagTile Studio 核心用户路径 E2E 冒烟"
echo " 路径矩阵: docs/E2E_TEST_MATRIX.md"
echo " 项目根: $ROOT"
echo " CLI 构建: $BUILD_DIR / Qt 构建: $QT_BUILD_DIR"
echo " 档位: $([ "$STRICT" -eq 1 ] && echo '--strict (SKIP 按失败处理)' || echo '默认 (SKIP 不阻断)')"
echo "==============================================================${RESET}"

# ---- 前置: CLI 可执行 (缺失时自动构建, 与 run_strict_audit.sh 同策略)
APP="$BUILD_DIR/magtile_app"
if [ ! -x "$APP" ]; then
    echo "未找到 $APP, 自动构建 magtile_app ..."
    cmake -S "$ROOT" -B "$BUILD_DIR" -DCMAKE_BUILD_TYPE=Release || exit 2
    nproc_val="$( (command -v nproc >/dev/null && nproc) || echo 4 )"
    cmake --build "$BUILD_DIR" -j "$nproc_val" --target magtile_app || exit 2
fi
[ -x "$APP" ] || { echo "错误: magtile_app 构建后仍不可用" >&2; exit 2; }

# ---- 免费层口径: 数量与抽样模型都取自 starter 清单 (不硬编码 30) --
STARTER_LIST="$ROOT/platforms/windows/packaging/starter_models.txt"
if [ ! -f "$STARTER_LIST" ]; then
    echo "错误: 缺少免费层打包清单 $STARTER_LIST" >&2
    exit 2
fi
FREE_COUNT="$(grep -cvE '^[[:space:]]*(#|$)' "$STARTER_LIST")"
SAMPLE_MODEL="$(grep -vE '^[[:space:]]*(#|$)' "$STARTER_LIST" | head -n 1 | tr -d '[:space:]')"
SAMPLE_JSON="$ROOT/data/models/$SAMPLE_MODEL.json"

# =============================================================
# E2E-01a CLI 启动冒烟: 目录加载 + 13 种片型齐全
# =============================================================
e2e_cli_catalog() {
    local out
    out="$("$APP" catalog --data-dir "$ROOT/data" 2>&1)" || {
        echo "$out"; echo "[断言失败] catalog 非零退出"; return 1; }
    echo "$out" | head -n 2
    echo "$out" | grep -q "共 13 种" || {
        echo "[断言失败] 片型目录不是 13 种 (输出首行: $(echo "$out" | head -n 1))"
        return 1
    }
    echo "[断言通过] 目录加载成功, 13 种片型齐全"
}

# =============================================================
# E2E-11b CLI 免费筛选对账: --free-only 数量与 starter 清单一致
# =============================================================
e2e_cli_free_filter() {
    local out
    out="$("$APP" library --free-only --data-dir "$ROOT/data" \
        --db "$TMP_DIR/e2e_cli.db" 2>&1)" || {
        echo "$out"; echo "[断言失败] library --free-only 非零退出"; return 1; }
    echo "$out" | tail -n 3
    echo "$out" | grep -q " ${FREE_COUNT} 个属于免费层" || {
        echo "[断言失败] 免费层数量与 starter 清单 (${FREE_COUNT} 个) 不一致"
        return 1
    }
    echo "$out" | grep -q "$SAMPLE_MODEL" || {
        echo "[断言失败] 抽样免费模型 $SAMPLE_MODEL 未出现在 --free-only 列表"
        return 1
    }
    echo "$out" | grep -q "目录对账通过" || {
        echo "[断言失败] 模型库目录元数据对账未通过"
        return 1
    }
    echo "[断言通过] 免费筛选 ${FREE_COUNT} 个与清单一致, 抽样 $SAMPLE_MODEL 在列, 目录对账通过"
}

# =============================================================
# E2E-06a CLI 免费模型教程步进: 全程步进 + 放置片数对账
# =============================================================
e2e_cli_free_tutorial() {
    [ -f "$SAMPLE_JSON" ] || {
        echo "[断言失败] 抽样免费模型文件缺失: $SAMPLE_JSON"; return 1; }
    local total out
    total="$("$PYTHON" -c "import json,sys; print(json.load(open(sys.argv[1]))['total_pieces'])" \
        "$SAMPLE_JSON")" || { echo "[断言失败] 无法读取 total_pieces"; return 1; }
    out="$("$APP" tutorial "$SAMPLE_JSON" --data-dir "$ROOT/data" 2>&1)" || {
        echo "$out" | tail -n 5; echo "[断言失败] tutorial 非零退出"; return 1; }
    echo "$out" | tail -n 2
    echo "$out" | grep -q "教程结束, 共放置 ${total} 片磁力片" || {
        echo "[断言失败] 教程步进片数与 total_pieces (${total}) 不一致"
        return 1
    }
    echo "[断言通过] 免费模型 $SAMPLE_MODEL 教程全程步进, ${total} 片对账一致"
}

# =============================================================
# E2E-17a 跨端存档键契约: CLI 写入端 -> 独立读取端 (python sqlite
# 直读, 模拟另一端不经 C++ 存档层直接打开同一 SQLite 文件) 断言
# settings 表键名/编码符合 progress 模块契约; 构建目录已有
# magtile_cross_platform_test 时另跑全量跨端互通断言 (与 CTest
# cross_platform_progress 同一载体, 缺二进制不阻断轻量档)
# =============================================================
e2e_cross_platform_keys() {
    local db="$TMP_DIR/e2e_cross.db"
    echo "  (a) CLI 写入端: settings set-age 4 (age_mode 键) ..."
    "$APP" settings set-age 4 --db "$db" >/dev/null || {
        echo "[断言失败] settings set-age 非零退出"; return 1; }
    echo "  (b) 独立读取端: python sqlite 直读 settings 表键契约 ..."
    "$PYTHON" - "$db" <<'PYEOF' || return 1
import sqlite3, sys
rows = dict(sqlite3.connect(sys.argv[1]).execute(
    "SELECT key, value FROM settings").fetchall())
if rows.get("age_mode") != "age_4_6":
    sys.exit("[断言失败] age_mode 键/编码不符 progress 模块契约: %r" % rows)
PYEOF
    echo "  (c) CLI 回读端: settings show 读回启蒙模式 ..."
    "$APP" settings show --db "$db" | grep -q "启蒙模式" || {
        echo "[断言失败] settings show 未回读出启蒙模式"; return 1; }
    local cross_bin="$BUILD_DIR/magtile_cross_platform_test"
    if [ -x "$cross_bin" ]; then
        echo "  (d) 全量跨端互通断言 (magtile_cross_platform_test) ..."
        "$cross_bin" "$TMP_DIR/e2e_cross_full.db" || {
            echo "[断言失败] 跨端进度存档互通测试非零退出"; return 1; }
    else
        echo "  (d) 构建目录无 magtile_cross_platform_test, 全量断言由 CTest cross_platform_progress 兜底"
    fi
    echo "[断言通过] 跨端存档 settings 键契约一致 (CLI 写 -> sqlite 直读 -> CLI 回读)"
}

# =============================================================
# E2E-12a Qt 进度页深链: 完成存档非空后 --smoke-open-progress
# 实例化进度页/成就墙数据源; QML 运行时错误一票否决
# =============================================================
e2e_qt_progress_deeplink() {
    local qt_app="$1" log="$TMP_DIR/qt_progress_deeplink.log"
    export QT_QPA_PLATFORM=offscreen
    echo "  (a) --smoke-complete-model $SAMPLE_MODEL 造非空存档 ..."
    "$qt_app" --data-dir "$ROOT/data" --db "$TMP_DIR/e2e_qt_progress.db" \
        --smoke-complete-model "$SAMPLE_MODEL" --smoke-quit-ms 2500 \
        2>&1 | tee "$log"
    [ "${PIPESTATUS[0]}" -eq 0 ] || {
        echo "[断言失败] 完成链路非零退出"; return 1; }
    echo "  (b) --smoke-open-progress 深链实例化进度页 ..."
    "$qt_app" --data-dir "$ROOT/data" --db "$TMP_DIR/e2e_qt_progress.db" \
        --smoke-open-progress --smoke-quit-ms 1500 2>&1 | tee -a "$log"
    [ "${PIPESTATUS[0]}" -eq 0 ] || {
        echo "[断言失败] 进度页深链非零退出"; return 1; }
    "$PYTHON" - "$TMP_DIR/e2e_qt_progress.db" "$SAMPLE_MODEL" <<'PYEOF' || return 1
import sqlite3, sys
row = sqlite3.connect(sys.argv[1]).execute(
    "SELECT completed_at FROM model_progress WHERE model_id=?",
    (sys.argv[2],)).fetchone()
if row is None or row[0] is None:
    sys.exit("[断言失败] 完成链路未写入存档: %s 无 completed_at" % sys.argv[2])
PYEOF
    if grep -E "ReferenceError|TypeError|is not defined" "$log" >/dev/null 2>&1; then
        echo "[断言失败] 发现 QML 运行时错误:"
        grep -E "ReferenceError|TypeError|is not defined" "$log"
        return 1
    fi
    echo "[断言通过] 完成存档落盘 + 进度页深链实例化, 无 QML 运行时错误"
}

# =============================================================
# E2E-14a Android JNI 符号断言: 符号清单运行时解析自 CI android.yml
# (仓库根 .github/workflows/android.yml, 与流水线口径自动同步;
#  找不到工作流文件时回退到内置基线清单)
# =============================================================
android_workflow_file() {
    local git_top
    git_top="$(git -C "$ROOT" rev-parse --show-toplevel 2>/dev/null)"
    for cand in "$git_top/.github/workflows/android.yml" \
                "$ROOT/.github/workflows/android.yml"; do
        [ -n "$cand" ] && [ -f "$cand" ] && { echo "$cand"; return 0; }
    done
    return 1
}

jni_symbol_list() {
    local wf
    if wf="$(android_workflow_file)"; then
        echo "  (符号清单解析自 $wf)" >&2
        grep -oE '(MainActivity|MagTileNative|TutorialSceneNative)_[A-Za-z]+' "$wf" | sort -u
    else
        echo "  (未找到 android.yml, 使用内置基线清单)" >&2
        printf '%s\n' \
            MainActivity_loadCatalog MainActivity_listModels \
            MainActivity_validateModel MainActivity_getTutorialStepCount \
            MagTileNative_openProgressStore MagTileNative_inventoryRows \
            MagTileNative_saveInventory MagTileNative_canBuildModel \
            MagTileNative_missingPiecesJson \
            MagTileNative_ageModeId MagTileNative_setAgeModeId \
            MagTileNative_progressOverviewJson \
            MagTileNative_getTutorialSteps MagTileNative_savedTutorialStep \
            MagTileNative_saveTutorialStep \
            MagTileNative_parentGateOpenJson MagTileNative_parentGateSubmitJson \
            MagTileNative_parentGateSessionActive \
            TutorialSceneNative_loadScene TutorialSceneNative_setStep \
            TutorialSceneNative_releaseScene \
            TutorialSceneNative_dragRotate TutorialSceneNative_pinchZoom \
            TutorialSceneNative_pan \
            TutorialSceneNative_surfaceCreated TutorialSceneNative_drawFrame
    fi
}

detect_ndk() {
    # 与 android.yml 的 NDK_VERSION 保持一致 (存在即优先选用)
    local pinned="27.2.12479018"
    if [ -n "${ANDROID_NDK:-}" ] && [ -d "$ANDROID_NDK" ]; then
        echo "$ANDROID_NDK"; return 0
    fi
    local sdk
    for sdk in "${ANDROID_HOME:-}" "${ANDROID_SDK_ROOT:-}"; do
        [ -n "$sdk" ] && [ -d "$sdk/ndk" ] || continue
        if [ -d "$sdk/ndk/$pinned" ]; then echo "$sdk/ndk/$pinned"; return 0; fi
        local latest
        latest="$(ls "$sdk/ndk" 2>/dev/null | sort -V | tail -n 1)"
        [ -n "$latest" ] && { echo "$sdk/ndk/$latest"; return 0; }
    done
    return 1
}

e2e_android_symbols() {
    local ndk="$1"
    echo "  NDK: $ndk"
    local gen_args=()
    command -v ninja >/dev/null 2>&1 && gen_args=(-G Ninja)
    cmake -S "$ROOT" -B "$ANDROID_BUILD_DIR" "${gen_args[@]}" \
        -DCMAKE_TOOLCHAIN_FILE="$ndk/build/cmake/android.toolchain.cmake" \
        -DANDROID_ABI=arm64-v8a \
        -DANDROID_PLATFORM=android-26 \
        -DCMAKE_BUILD_TYPE=Release || {
        echo "[断言失败] Android 交叉编译配置失败"; return 1; }
    cmake --build "$ANDROID_BUILD_DIR" || {
        echo "[断言失败] Android 交叉编译失败"; return 1; }
    local so="$ANDROID_BUILD_DIR/platforms/android/libmagtile_core.so"
    [ -f "$so" ] || { echo "[断言失败] 未产出 $so"; return 1; }
    local nm
    nm="$(ls "$ndk"/toolchains/llvm/prebuilt/*/bin/llvm-nm 2>/dev/null | head -n 1)"
    [ -n "$nm" ] || { echo "[断言失败] NDK 内未找到 llvm-nm"; return 1; }
    local symbols missing=0 count=0
    symbols="$(jni_symbol_list)"
    local defined
    defined="$("$nm" -D --defined-only "$so")"
    local symbol
    while IFS= read -r symbol; do
        [ -n "$symbol" ] || continue
        count=$((count + 1))
        echo "$defined" | grep -q "Java_com_magtile_studio_$symbol" || {
            echo "[断言失败] 缺少 JNI 符号: $symbol"; missing=1; }
    done <<< "$symbols"
    [ "$missing" -eq 0 ] || return 1
    echo "[断言通过] JNI 符号断言通过 ($count 个, 与 android.yml 同口径)"
}

# ---- 关卡编排 ----------------------------------------------------
run_stage "E2E-01a CLI 启动冒烟 (catalog 13 片型)"      e2e_cli_catalog
run_stage "E2E-11a 免费层清单对齐 (verify_free_tier)" \
    "$PYTHON" "$ROOT/tools/verify_free_tier.py" \
    --models-dir "$ROOT/data/models" \
    --catalog "$ROOT/data/tile_catalog.json"
run_stage "E2E-11b CLI 免费筛选对账 (--free-only)"       e2e_cli_free_filter
run_stage "E2E-06a CLI 免费模型教程步进 ($SAMPLE_MODEL)" e2e_cli_free_tutorial
run_stage "E2E-17a 跨端存档键契约 (CLI 写 -> sqlite 直读)" e2e_cross_platform_keys

# ---- Qt 冒烟 (缺二进制时尝试自动构建, 环境无 Qt6 则 SKIP) --------
QT_APP="$QT_BUILD_DIR/apps/desktop_qt/magtile_studio_qt"
if [ "$SKIP_QT" -eq 1 ]; then
    skip_stage "E2E-QT Qt 无头冒烟 (test_qt_smoke.sh)" "--skip-qt"
    skip_stage "E2E-12a Qt 进度页深链 (--smoke-open-progress)" "--skip-qt"
else
    if [ ! -x "$QT_APP" ]; then
        echo ""
        echo "未找到 $QT_APP, 尝试自动构建 (需要 Qt6) ..."
        if cmake -S "$ROOT" -B "$QT_BUILD_DIR" -DMAGTILE_BUILD_QT=ON \
               -DCMAKE_BUILD_TYPE=Release >"$LOG_DIR/qt_configure.log" 2>&1; then
            nproc_val="$( (command -v nproc >/dev/null && nproc) || echo 4 )"
            cmake --build "$QT_BUILD_DIR" -j "$nproc_val" \
                --target magtile_studio_qt >"$LOG_DIR/qt_build.log" 2>&1 \
                || echo "${YELLOW}Qt 构建失败 (日志: $LOG_DIR/qt_build.log)${RESET}"
        else
            echo "${YELLOW}Qt 配置失败, 环境可能缺 Qt6 (日志: $LOG_DIR/qt_configure.log)${RESET}"
        fi
    fi
    if [ -x "$QT_APP" ]; then
        run_stage "E2E-QT Qt 无头冒烟 (test_qt_smoke.sh)" \
            bash "$ROOT/tests/test_qt_smoke.sh" "$QT_APP" "$ROOT"
        run_stage "E2E-12a Qt 进度页深链 (--smoke-open-progress)" \
            e2e_qt_progress_deeplink "$QT_APP"
    else
        skip_stage "E2E-QT Qt 无头冒烟 (test_qt_smoke.sh)" \
            "magtile_studio_qt 不可用且自动构建失败 (需要 Qt6, 构建方法见 docs/TESTING.md §3.15)"
        skip_stage "E2E-12a Qt 进度页深链 (--smoke-open-progress)" "同上"
    fi
fi

# ---- Android JNI 符号 (环境允许时) --------------------------------
if [ "$SKIP_ANDROID" -eq 1 ]; then
    skip_stage "E2E-14a Android JNI 符号断言" "--skip-android"
elif NDK_DIR="$(detect_ndk)"; then
    run_stage "E2E-14a Android JNI 符号断言 (NDK 交叉编译)" \
        e2e_android_symbols "$NDK_DIR"
else
    skip_stage "E2E-14a Android JNI 符号断言" \
        "未检测到 Android NDK (设 ANDROID_NDK 或 ANDROID_HOME 后重试; CI 由 android.yml 兜底)"
fi

# ---- 总结报告 ----------------------------------------------------
pass_count=0; fail_count=0; skip_count=0
echo ""
echo "${BOLD}=============================================================="
echo " E2E 冒烟报告 (路径矩阵: docs/E2E_TEST_MATRIX.md)"
echo "==============================================================${RESET}"
for i in "${!STAGE_NAMES[@]}"; do
    case "${STAGE_RESULTS[$i]}" in
        PASS) pass_count=$((pass_count + 1))
              printf '  %s%-6s%s %-52s %s\n' "$GREEN" "PASS" "$RESET" "${STAGE_NAMES[$i]}" "${STAGE_TIMES[$i]}" ;;
        FAIL) fail_count=$((fail_count + 1))
              printf '  %s%-6s%s %-52s %s\n' "$RED" "FAIL" "$RESET" "${STAGE_NAMES[$i]}" "${STAGE_TIMES[$i]}" ;;
        SKIP) skip_count=$((skip_count + 1))
              printf '  %s%-6s%s %-52s %s\n' "$YELLOW" "SKIP" "$RESET" "${STAGE_NAMES[$i]}" "${STAGE_TIMES[$i]}" ;;
    esac
done
echo "${BOLD}--------------------------------------------------------------${RESET}"
total_count=$((pass_count + fail_count + skip_count))
if [ "$fail_count" -gt 0 ]; then
    echo "${RED}${BOLD} 结论: $total_count 项中 $fail_count 项失败, 核心用户路径不健康${RESET}"
    echo " 分项日志: $LOG_DIR"
    exit 1
fi
if [ "$STRICT" -eq 1 ] && [ "$skip_count" -gt 0 ]; then
    echo "${RED}${BOLD} 结论: --strict 档存在 $skip_count 项 SKIP, 上架签核不放行${RESET}"
    echo " 分项日志: $LOG_DIR"
    exit 1
fi
if [ "$skip_count" -gt 0 ]; then
    echo "${YELLOW} 提醒: $skip_count 项 SKIP (默认档不阻断); 上架签核请用 --strict 并补齐环境${RESET}"
fi
echo "${GREEN}${BOLD} 结论: $pass_count 项通过 ($skip_count 项跳过), 自动子集全绿${RESET}"
echo " 人工侧: 按 docs/E2E_TEST_MATRIX.md 第 1 节 P0 的 Manual 要点逐条打钩"
rm -rf "$LOG_DIR"
exit 0
