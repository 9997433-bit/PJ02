#!/usr/bin/env bash
# =============================================================
# MagTile Studio - 弱磁严格档物理审计 (全库零警告闸门)
#
# 用 --profile strict (strict_consumer 弱磁严格档: 悬挂额定 120g/
# 单位边长, 抗碰撞安全系数 70%) 逐一校验 data/models/ 下的每一个
# 模型 JSON, 并执行比常规质检更严的"零警告"政策:
#
#   [失败] validate 退出码非零           -> 存在 Error 级物理问题, 不可发布
#   [失败] 输出含任何 "[警告]" 行        -> Warning 级问题 (如
#          disconnected_assembly / single_point_of_failure /
#          hanging_chain_long / no_structural_redundancy) 同样拦截:
#          全库承诺 strict 档零警告 (见 docs/STRICT_PHYSICS_AUDIT.md)
#   [豁免] 极少数模型的特定警告代码在 WAIVERS 白名单中显式豁免
#          (必须在 docs/STRICT_PHYSICS_AUDIT.md 记录理由), 不拦截但照常展示
#   [通过] 退出码为零且零警告
#
# 结束时汇总: 通过/豁免/警告/失败模型数, 以及警告/错误代码 Top 榜
# (按括号内的 issue 代码聚合), 便于内容团队定位共性问题。
#
# CI 接入: 在流水线中于构建 magtile_app 之后调用本脚本即可, 例如
#   tests/run_full_qa.sh 之后追加  tools/audit_strict_physics.sh build
# 退出码: 0 = 全库零警告零错误; 1 = 存在警告或错误; 2 = 环境不满足
#
# 用法: tools/audit_strict_physics.sh [build_dir]   (默认 build)
# =============================================================
set -u

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
BUILD_DIR="${1:-$ROOT/build}"
case "$BUILD_DIR" in
    /*) ;;
    *) BUILD_DIR="$ROOT/$BUILD_DIR" ;;
esac
APP="$BUILD_DIR/magtile_app"
DATA_DIR="$ROOT/data"
MODELS_DIR="$DATA_DIR/models"

if [ ! -x "$APP" ]; then
    echo "错误: 找不到可执行文件 $APP (请先构建, 如 cmake --build build --target magtile_app)" >&2
    exit 2
fi

shopt -s nullglob
models=("$MODELS_DIR"/*.json)
shopt -u nullglob
if [ "${#models[@]}" -eq 0 ]; then
    echo "错误: $MODELS_DIR 下没有找到任何模型 JSON" >&2
    exit 1
fi

# ---- 彩色输出 (与 tests/run_full_qa.sh 同约定) --------------------
if { [ -t 1 ] || [ -n "${FORCE_COLOR:-}" ]; } && [ -z "${NO_COLOR:-}" ]; then
    RED=$'\033[31m'; GREEN=$'\033[32m'; YELLOW=$'\033[33m'; BOLD=$'\033[1m'; RESET=$'\033[0m'
else
    RED=""; GREEN=""; YELLOW=""; BOLD=""; RESET=""
fi

# ---- 警告豁免白名单 ------------------------------------------------
# 格式: "模型id:警告代码"。仅豁免指定模型的指定 Warning 代码, 其余
# 一律拦截。每一条豁免必须在 docs/STRICT_PHYSICS_AUDIT.md 记录结构
# 论证 (为什么该警告是设计使然而非缺陷)。
#
# suspension_bridge_01 / disconnected_assembly: 悬索桥的教学叙事是
# "东西两岸对称推进、主跨正中合龙" (真实悬索桥的施工顺序), 第 7~11 步
# 东岸子结构独立接地属预期分组; 校验器对该警告的建议是"在教程中明确
# 分组说明", 该模型第 7 步教程文案已显式说明分组 —— 判定为设计使然。
WAIVERS=(
    "suspension_bridge_01:disconnected_assembly"
)

is_waived() {
    # $1 = 模型 id, $2 = 警告代码
    local key="$1:$2" entry
    for entry in "${WAIVERS[@]}"; do
        [ "$entry" = "$key" ] && return 0
    done
    return 1
}

echo "=============================================================="
echo " 弱磁严格档物理审计: 共 ${#models[@]} 个模型 (--profile strict, 零警告政策)"
echo "=============================================================="

pass=0
waived=0
warned=0
failed=0
issue_lines=""          # 逐条警告/错误行 (含模型名), 汇总用

for model in "${models[@]}"; do
    id="$(basename "$model" .json)"
    output="$("$APP" validate "$model" --data-dir "$DATA_DIR" --profile strict 2>&1)"
    status=$?
    warn_lines="$(printf '%s\n' "$output" | grep -F '[警告]' || true)"

    # 从警告行提取代码并区分 已豁免/未豁免
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
        issue_lines="$issue_lines$(printf '%s\n' "$output" | grep -E '\[(错误|警告)\]' | sed "s/^/$id: /")"$'\n'
    elif [ -n "$blocking_warns" ]; then
        warned=$((warned + 1))
        count="$(printf '%s' "$blocking_warns" | grep -c .)"
        echo "${YELLOW}[警告]${RESET} $id ($count 条严格档警告)"
        printf '%s' "$blocking_warns" | sed "s/^/        /"
        issue_lines="$issue_lines$(printf '%s' "$blocking_warns" | sed "s/^/$id: /")"$'\n'
    elif [ -n "$warn_lines" ]; then
        waived=$((waived + 1))
        count="$(printf '%s\n' "$warn_lines" | wc -l)"
        echo "${YELLOW}[豁免]${RESET} $id ($count 条已豁免警告, 理由见 docs/STRICT_PHYSICS_AUDIT.md)"
        printf '%s\n' "$warn_lines" | sed "s/^/        /"
    else
        pass=$((pass + 1))
        echo "${GREEN}[通过]${RESET} $id"
    fi
done

echo ""
echo "=============================================================="
echo " 汇总: 通过 $pass / 豁免 $waived / 警告 $warned / 失败 $failed (共 ${#models[@]} 个模型)"

if [ -n "$issue_lines" ]; then
    echo ""
    echo " 问题代码 Top 榜 (按 issue 代码聚合):"
    printf '%s' "$issue_lines" | grep -oE '\([a-z_]+\)$' | sort | uniq -c | sort -rn \
        | sed 's/^/   /'
fi
echo "=============================================================="

if [ "$failed" -gt 0 ] || [ "$warned" -gt 0 ]; then
    echo "${BOLD}${RED} 结果: 严格档审计未达零警告标准${RESET}"
    exit 1
fi
if [ "$waived" -gt 0 ]; then
    echo "${BOLD}${GREEN} 结果: 全库 ${#models[@]} 个模型 strict 档零未豁免警告零错误 (含 $waived 个白名单豁免)${RESET}"
else
    echo "${BOLD}${GREEN} 结果: 全库 ${#models[@]} 个模型 strict 档零警告零错误${RESET}"
fi
exit 0
