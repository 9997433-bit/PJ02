#!/usr/bin/env bash
# =============================================================
# MagTile Studio - 内容批 PR 评审一键脚本 (Content Batch Review)
#
# 内容批 PR (新增/改动模型 JSON) 的机器侧评审一条命令跑完, 与
# docs/CONTENT_STRATEGY.md 4.3 节的批次评审流程对应, 五道关卡全部
# 阻断 (任一 FAIL 即退出非零):
#
#   1. strict 物理校验     magtile_app validate --profile strict
#      逐文件零警告政策; 豁免白名单与 tools/audit_strict_physics.sh
#      共用同一来源 (该脚本内 WAIVERS, 论证见 docs/STRICT_PHYSICS_AUDIT.md)
#   2. 难度配额 (D3 冻结)  tools/check_difficulty_quota.py --batch
#      冻结生效期间批次内 difficulty=3 直接 FAIL (CONTENT_GAP_AUDIT.md
#      7.3 节); 策展人豁免用 --whitelist-file 透传
#   3. 内容系列归类        tools/check_content_series.py --strict
#      批次每个模型须带 content_meta.series (13 主题词值) 或
#      matrix_bucket (矩阵外桶) 恰好其一, 词值受控于
#      data/content_series_map.json
#   4. 片型分层 (core-9)   tools/check_core5_usage.py --strict
#      全库口径 (批次文件须已在 data/models 下, 即 PR 检出状态):
#      扩展片型打标一致性 + 免费层 80% 红线
#   5. 唯一性抽查          tests/test_library_uniqueness.py
#      全库两两结构签名比对 (250 模型约 7 秒; 批次文件在 data/models
#      之外时自动追加进比对集), sim > 0.85 克隆判定 FAIL
#
# 关卡 2/3 对批次文件生成临时目录副本后按目录审查 (两工具的批次输入
# 均为目录口径); 关卡 4/5 为全库口径, 批次已检出到 data/models 时
# 自然覆盖。机器侧评审只是入库必要条件, 不替代策展终审 (人工 10 项
# 清单, CONTENT_STRATEGY.md 3.4 节) 与 D4+ 实物复核 (4.3 节)。
#
# 用法:
#   tools/review_content_batch.sh [选项] <模型.json> [模型.json ...]
#     模型.json             本批新增/改动的模型文件 (通常在 data/models 下)
#     --build-dir DIR       构建目录 (默认 build; 缺 magtile_app 自动构建)
#     --whitelist-file FILE 策展人 D3 豁免白名单 (每行一个模型 id,
#                           透传给 check_difficulty_quota.py --batch)
#     --skip-uniqueness     跳过关卡 5 唯一性抽查 (快速档, 入库前必须补跑)
#     -h | --help           打印本说明
#
# 退出码: 0 = 全部关卡通过; 1 = 存在失败关卡; 2 = 用法/环境不满足
# =============================================================
set -u

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
BUILD_DIR="$ROOT/build"
WHITELIST_FILE=""
SKIP_UNIQUENESS=0
MODEL_FILES=()

usage() { sed -n '2,44p' "$0"; }

while [ "$#" -gt 0 ]; do
    case "$1" in
        --build-dir)
            [ "$#" -ge 2 ] || { echo "错误: --build-dir 需要目录参数" >&2; exit 2; }
            BUILD_DIR="$2"; shift 2 ;;
        --build-dir=*)      BUILD_DIR="${1#--build-dir=}"; shift ;;
        --whitelist-file)
            [ "$#" -ge 2 ] || { echo "错误: --whitelist-file 需要文件参数" >&2; exit 2; }
            WHITELIST_FILE="$2"; shift 2 ;;
        --whitelist-file=*) WHITELIST_FILE="${1#--whitelist-file=}"; shift ;;
        --skip-uniqueness)  SKIP_UNIQUENESS=1; shift ;;
        -h|--help)          usage; exit 0 ;;
        -*)
            echo "错误: 未知选项 $1 (用法见 --help)" >&2; exit 2 ;;
        *)
            MODEL_FILES+=("$1"); shift ;;
    esac
done

if [ "${#MODEL_FILES[@]}" -eq 0 ]; then
    echo "错误: 至少给出一个模型 JSON (本批新增/改动的文件)" >&2
    echo "用法: tools/review_content_batch.sh [选项] <模型.json> [模型.json ...]" >&2
    exit 2
fi
for model in "${MODEL_FILES[@]}"; do
    if [ ! -f "$model" ]; then
        echo "错误: 模型文件不存在: $model" >&2
        exit 2
    fi
    case "$model" in
        *.json) ;;
        *) echo "错误: 不是 JSON 文件: $model" >&2; exit 2 ;;
    esac
done
if [ -n "$WHITELIST_FILE" ] && [ ! -f "$WHITELIST_FILE" ]; then
    echo "错误: 白名单文件不存在: $WHITELIST_FILE" >&2
    exit 2
fi

case "$BUILD_DIR" in
    /*) ;;
    *) BUILD_DIR="$ROOT/$BUILD_DIR" ;;
esac
APP="$BUILD_DIR/magtile_app"
DATA_DIR="$ROOT/data"
MODELS_DIR="$DATA_DIR/models"

PYTHON="$(command -v python3 || command -v python)"
if [ -z "$PYTHON" ]; then
    echo "错误: 需要 python3 (质检工具依赖)" >&2
    exit 2
fi

# ---- 自动构建 (与 tools/run_strict_audit.sh 同一约定) --------------
if [ ! -x "$APP" ]; then
    echo ">> magtile_app 不存在, 自动配置并构建 ($BUILD_DIR) ..."
    cmake -S "$ROOT" -B "$BUILD_DIR" -DCMAKE_BUILD_TYPE=Release || exit 2
    nproc_val="$( (command -v nproc >/dev/null && nproc) || sysctl -n hw.ncpu 2>/dev/null || echo 2)"
    cmake --build "$BUILD_DIR" -j "$nproc_val" --target magtile_app || exit 2
fi

# ---- 批次临时目录 (关卡 2/3 的目录口径输入) ------------------------
BATCH_DIR="$(mktemp -d /tmp/magtile_batch_review_XXXXXX)"
trap 'rm -rf "$BATCH_DIR"' EXIT
for model in "${MODEL_FILES[@]}"; do
    base="$(basename "$model")"
    if [ -e "$BATCH_DIR/$base" ]; then
        echo "错误: 批次文件重名: $base (同一文件请勿重复给出)" >&2
        exit 2
    fi
    cp "$model" "$BATCH_DIR/$base" || exit 2
done

# ---- 彩色输出 (与 run_release_gate.sh 同一约定) --------------------
if { [ -t 1 ] || [ -n "${FORCE_COLOR:-}" ]; } && [ -z "${NO_COLOR:-}" ]; then
    RED=$'\033[31m'; GREEN=$'\033[32m'; YELLOW=$'\033[33m'
    CYAN=$'\033[36m'; BOLD=$'\033[1m'; RESET=$'\033[0m'
else
    RED=""; GREEN=""; YELLOW=""; CYAN=""; BOLD=""; RESET=""
fi

STAGE_NAMES=()
STAGE_RESULTS=()
stage_index=0

# run_stage <关卡名> <命令/函数...>: 失败不中断 (一次报告给全)。
run_stage() {
    local name="$1"; shift
    stage_index=$((stage_index + 1))
    echo ""
    echo "${BOLD}${CYAN}==============================================================${RESET}"
    echo "${BOLD}${CYAN} 评审关卡 $stage_index: $name${RESET}"
    echo "${BOLD}${CYAN}==============================================================${RESET}"
    "$@"
    local status=$?
    STAGE_NAMES+=("$name")
    if [ "$status" -eq 0 ]; then
        STAGE_RESULTS+=("PASS")
        echo "${GREEN}${BOLD}[通过] $name${RESET}"
    else
        STAGE_RESULTS+=("FAIL")
        echo "${RED}${BOLD}[失败] $name (退出码 $status)${RESET}"
    fi
    return "$status"
}

# ---- 关卡 1: strict 物理校验 (零警告, 豁免白名单与全库审计共源) -----
mapfile -t WAIVERS < <(sed -n '/^WAIVERS=(/,/^)$/p' \
    "$ROOT/tools/audit_strict_physics.sh" | grep -oE '"[^"]+:[^"]+"' | tr -d '"')

is_waived() {
    local key="$1:$2" entry
    for entry in "${WAIVERS[@]:-}"; do
        [ "$entry" = "$key" ] && return 0
    done
    return 1
}

stage_validate_strict() {
    local failed=0 model id output status warn_lines blocking_warns line code count
    echo "逐文件 validate --profile strict (零警告政策, 共 ${#MODEL_FILES[@]} 个)"
    for model in "${MODEL_FILES[@]}"; do
        id="$(basename "$model" .json)"
        output="$("$APP" validate "$model" --data-dir "$DATA_DIR" --profile strict 2>&1)"
        status=$?
        warn_lines="$(printf '%s\n' "$output" | grep -F '[警告]' || true)"

        blocking_warns=""
        if [ -n "$warn_lines" ]; then
            while IFS= read -r line; do
                code="$(printf '%s' "$line" | grep -oE '\([a-z_]+\)$' | tr -d '()')"
                if [ -z "$code" ] || ! is_waived "$id" "$code"; then
                    blocking_warns="$blocking_warns$line"$'\n'
                fi
            done <<< "$warn_lines"
        fi

        if [ "$status" -ne 0 ]; then
            failed=$((failed + 1))
            echo "${RED}[失败]${RESET} $id (validate 退出码 $status)"
            printf '%s\n' "$output" | grep -E '\[(错误|警告)\]' | sed "s/^/        /"
        elif [ -n "$blocking_warns" ]; then
            failed=$((failed + 1))
            count="$(printf '%s' "$blocking_warns" | grep -c .)"
            echo "${YELLOW}[警告]${RESET} $id ($count 条严格档警告, 零警告政策按失败处理)"
            printf '%s' "$blocking_warns" | sed "s/^/        /"
        elif [ -n "$warn_lines" ]; then
            count="$(printf '%s\n' "$warn_lines" | wc -l)"
            echo "${YELLOW}[豁免]${RESET} $id ($count 条已豁免警告, 理由见 docs/STRICT_PHYSICS_AUDIT.md)"
            printf '%s\n' "$warn_lines" | sed "s/^/        /"
        else
            echo "${GREEN}[通过]${RESET} $id"
        fi
    done
    echo "小计: ${#MODEL_FILES[@]} 个批次文件, 失败 $failed"
    [ "$failed" -eq 0 ]
}

# ---- 关卡 2: 难度配额 D3 冻结闸门 ----------------------------------
stage_difficulty_quota() {
    local args=("$MODELS_DIR" --batch "$BATCH_DIR")
    [ -n "$WHITELIST_FILE" ] && args+=(--whitelist-file "$WHITELIST_FILE")
    "$PYTHON" "$ROOT/tools/check_difficulty_quota.py" "${args[@]}"
}

# ---- 关卡 5: 唯一性抽查 (全库 + 批次外文件) ------------------------
stage_uniqueness() {
    local extra=() model parent
    for model in "${MODEL_FILES[@]}"; do
        parent="$(cd "$(dirname "$model")" && pwd)"
        if [ "$parent" != "$MODELS_DIR" ]; then
            extra+=("$model")
        fi
    done
    "$PYTHON" "$ROOT/tests/test_library_uniqueness.py" "$MODELS_DIR" \
        ${extra[@]:+"${extra[@]}"} --catalog "$DATA_DIR/tile_catalog.json"
}

# ---- 关卡编排 ------------------------------------------------------
echo "${BOLD}=============================================================="
echo " MagTile Studio 内容批评审 (Content Batch Review)"
echo " 项目根: $ROOT"
echo " 批次文件: ${#MODEL_FILES[@]} 个"
printf '   - %s\n' "${MODEL_FILES[@]}"
[ -n "$WHITELIST_FILE" ] && echo " D3 豁免白名单: $WHITELIST_FILE"
echo "==============================================================${RESET}"

run_stage "strict 物理校验 (零警告)" stage_validate_strict
run_stage "难度配额 (D3 冻结闸门)" stage_difficulty_quota
run_stage "内容系列归类 (--strict)" \
    "$PYTHON" "$ROOT/tools/check_content_series.py" "$BATCH_DIR" \
    --map "$DATA_DIR/content_series_map.json" --strict
run_stage "片型分层 core-9 (--strict)" \
    "$PYTHON" "$ROOT/tools/check_core5_usage.py" "$MODELS_DIR" \
    --catalog "$DATA_DIR/tile_catalog.json" --strict
if [ "$SKIP_UNIQUENESS" -eq 1 ]; then
    echo ""
    echo "${YELLOW}[跳过] 唯一性抽查 (--skip-uniqueness; 入库前必须补跑)${RESET}"
else
    run_stage "唯一性抽查 (结构签名比对)" stage_uniqueness
fi

# ---- 总结报告 ------------------------------------------------------
pass_count=0; fail_count=0
echo ""
echo "${BOLD}=============================================================="
echo " 内容批评审报告"
echo "==============================================================${RESET}"
for i in "${!STAGE_NAMES[@]}"; do
    case "${STAGE_RESULTS[$i]}" in
        PASS) pass_count=$((pass_count + 1))
              printf '  %s%-6s%s %s\n' "$GREEN" "PASS" "$RESET" "${STAGE_NAMES[$i]}" ;;
        FAIL) fail_count=$((fail_count + 1))
              printf '  %s%-6s%s %s\n' "$RED" "FAIL" "$RESET" "${STAGE_NAMES[$i]}" ;;
    esac
done
echo "${BOLD}--------------------------------------------------------------${RESET}"
if [ "$fail_count" -gt 0 ]; then
    echo "${RED}${BOLD} 结论: $((pass_count + fail_count)) 个评审关卡中 $fail_count 个失败, 本批不可入库${RESET}"
    exit 1
fi
echo "${GREEN}${BOLD} 结论: 全部 $pass_count 个评审关卡通过${RESET}"
echo " 机器侧评审只是入库必要条件 —— 策展终审 (人工 10 项清单) 见"
echo " docs/CONTENT_STRATEGY.md 3.4 节; D4+ 另需实物复核 (4.3 节)。"
exit 0
