#!/usr/bin/env bash
# =============================================================
# MagTile Studio - 套装 → 模型匹配冒烟 (ctest: buildable_by_set)
#
# 检查项:
#   1. inventory apply-set standard_102 写入合并 BOM;
#   2. inventory match 能搭数量 > 0;
#   3. report_buildable_by_set.py 与 CLI match 摘要一致 (模型总数)。
#
# 用法:
#   tests/test_buildable_by_set.sh <magtile_app 路径> <项目根>
# =============================================================
set -u

APP="${1:?用法: test_buildable_by_set.sh <magtile_app> <项目根>}"
ROOT="${2:?用法: test_buildable_by_set.sh <magtile_app> <项目根>}"
DATA_DIR="$ROOT/data"
WORK_DIR="$(mktemp -d /tmp/magtile_buildable_by_set_XXXXXX)"
DB="$WORK_DIR/progress.db"
PYTHON="${PYTHON:-python3}"

failures=0
pass() { printf '[通过] %s\n' "$1"; }
fail() { printf '[失败] %s\n' "$1" >&2; failures=$((failures + 1)); }
cleanup() { rm -rf "$WORK_DIR"; }
trap cleanup EXIT

if [[ ! -x "$APP" ]]; then
    fail "找不到可执行文件 $APP"
    exit 1
fi

# ---- 1. apply-set standard_102 ------------------------------------
apply_out="$("$APP" inventory apply-set standard_102 --data-dir "$DATA_DIR" --db "$DB" 2>&1)"
apply_exit=$?
if [[ "$apply_exit" -eq 0 ]] && grep -q "已应用 1 个实物套装" <<<"$apply_out"; then
    pass "inventory apply-set standard_102 成功"
else
    fail "inventory apply-set standard_102 异常 (退出码 $apply_exit)"
    printf '%s\n' "$apply_out" >&2
fi

# ---- 2. inventory match: 能搭 > 0 ---------------------------------
match_out="$("$APP" inventory match --data-dir "$DATA_DIR" --db "$DB" 2>&1)"
match_exit=$?
summary="$(grep -o '共 [0-9]* 个模型, 能搭 [0-9]* 个' <<<"$match_out" | head -n 1)"
total="$(grep -o '[0-9]*' <<<"$summary" | sed -n 1p)"
buildable="$(grep -o '[0-9]*' <<<"$summary" | sed -n 2p)"
if [[ "$match_exit" -eq 0 && -n "$buildable" && "$buildable" -gt 0 ]]; then
    pass "standard_102 库存 match: 能搭 $buildable / $total 个模型"
else
    fail "standard_102 库存 match 异常 (退出码 $match_exit, 摘要: $summary)"
    printf '%s\n' "$match_out" >&2
fi

# ---- 3. report 脚本与 CLI 模型总数对账 ------------------------------
if [[ ! -f "$ROOT/tools/report_buildable_by_set.py" ]]; then
    fail "缺少 tools/report_buildable_by_set.py"
else
    report_out="$("$PYTHON" "$ROOT/tools/report_buildable_by_set.py" --json standard_102 2>&1)"
    report_exit=$?
    report_total="$(grep -o '"model_total": [0-9]*' <<<"$report_out" | grep -o '[0-9]*' | head -n 1)"
    report_buildable="$(grep -o '"buildable_count": [0-9]*' <<<"$report_out" | grep -o '[0-9]*' | head -n 1)"
    if [[ "$report_exit" -eq 0 && "$report_total" == "$total" && "$report_buildable" == "$buildable" ]]; then
        pass "report_buildable_by_set.py 与 CLI match 对账一致 ($report_buildable/$report_total)"
    else
        fail "report 与 CLI 不一致 (report $report_buildable/$report_total, CLI $buildable/$total)"
        printf '%s\n' "$report_out" >&2
    fi
fi

echo
if [[ "$failures" -eq 0 ]]; then
    echo "套装 → 模型匹配冒烟通过"
    exit 0
fi
echo "套装 → 模型匹配冒烟失败: $failures 项未通过" >&2
exit 1
