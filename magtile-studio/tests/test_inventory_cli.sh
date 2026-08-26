#!/usr/bin/env bash
# =============================================================
# MagTile Studio - 磁力片库存 CLI 测试 (ctest: inventory_cli)
#
# 检查项:
#   1. 空库 inventory show: 正常退出并提示尚未登记;
#   2. 空库 inventory match: 非零退出并提示先登记;
#   3. inventory set: 登记多种形状并回显清单与合计;
#      3b. 新核心片型 (大正方形/窗格方/门框方/车轮底座) 的标识被接受;
#   4. 跨进程持久化: 再次 inventory show 仍能读到;
#   5. 非法输入: 未知形状 / 非法数量必须非零退出;
#   6. inventory match: 满配库存下全库模型均能搭,
#      全 0 库存下能搭数为 0 且缺片清单按缺片数升序给出。
#
# 用法:
#   tests/test_inventory_cli.sh <magtile_app 路径> <项目根>
# =============================================================
set -u

APP="${1:?用法: test_inventory_cli.sh <magtile_app> <项目根>}"
ROOT="${2:?用法: test_inventory_cli.sh <magtile_app> <项目根>}"
DATA_DIR="$ROOT/data"
WORK_DIR="$(mktemp -d /tmp/magtile_inventory_cli_XXXXXX)"
DB="$WORK_DIR/progress.db"

failures=0
pass() { printf '[通过] %s\n' "$1"; }
fail() { printf '[失败] %s\n' "$1" >&2; failures=$((failures + 1)); }
cleanup() { rm -rf "$WORK_DIR"; }
trap cleanup EXIT

if [[ ! -x "$APP" ]]; then
    fail "找不到可执行文件 $APP"
    exit 1
fi

# ---- 1. 空库 show: 正常退出 + 提示 --------------------------------
output="$("$APP" inventory show --db "$DB" 2>&1)"
if [[ $? -eq 0 ]] && grep -q "尚未登记" <<<"$output"; then
    pass "空库 inventory show 正常退出并提示尚未登记"
else
    fail "空库 inventory show 行为异常"
    printf '%s\n' "$output" >&2
fi

# ---- 2. 空库 match: 非零退出 + 提示 --------------------------------
output="$("$APP" inventory match --data-dir "$DATA_DIR" --db "$DB" 2>&1)"
if [[ $? -ne 0 ]] && grep -q "尚未登记" <<<"$output"; then
    pass "空库 inventory match 非零退出并提示先登记"
else
    fail "空库 inventory match 行为异常 (应非零退出)"
    printf '%s\n' "$output" >&2
fi

# ---- 3. set: 登记并回显 --------------------------------------------
output="$("$APP" inventory set square 40 equilateral_triangle 24 hexagon 2 --db "$DB" 2>&1)"
if [[ $? -eq 0 ]] && grep -q "square" <<<"$output" && grep -q "合计: 66 片" <<<"$output"; then
    pass "inventory set 登记 3 种形状并回显合计 66 片"
else
    fail "inventory set 登记/回显异常"
    printf '%s\n' "$output" >&2
fi

# ---- 3b. 新核心片型标识被接受 (独立库, 不影响后续合计断言) ----------
CORE_DB="$WORK_DIR/core.db"
output="$("$APP" inventory set large_square 4 window_square 6 door_frame 8 wheel_base 10 --db "$CORE_DB" 2>&1)"
if [[ $? -eq 0 ]] && grep -q "大正方形.*x 4" <<<"$output" && \
   grep -q "窗格方.*x 6" <<<"$output" && grep -q "门框方.*x 8" <<<"$output" && \
   grep -q "车轮底座.*x 10" <<<"$output" && grep -q "合计: 28 片" <<<"$output"; then
    pass "新核心片型 large_square/window_square/door_frame/wheel_base 登记成功 (合计 28 片)"
else
    fail "新核心片型标识登记异常"
    printf '%s\n' "$output" >&2
fi

# ---- 4. 跨进程持久化 + 覆盖登记 ------------------------------------
output="$("$APP" inventory set square 30 --db "$DB" 2>&1)"
show_output="$("$APP" inventory show --db "$DB" 2>&1)"
if [[ $? -eq 0 ]] && grep -q "正方形.*x 30" <<<"$show_output" && \
   grep -q "合计: 56 片" <<<"$show_output"; then
    pass "覆盖登记生效且跨进程持久化 (合计 56 片)"
else
    fail "覆盖登记/持久化异常"
    printf '%s\n' "$show_output" >&2
fi

# ---- 5. 非法输入拒绝 -----------------------------------------------
if "$APP" inventory set not_a_shape 5 --db "$DB" >/dev/null 2>&1; then
    fail "未知形状标识未被拒绝"
else
    pass "未知形状标识被拒绝 (非零退出)"
fi
if "$APP" inventory set square abc --db "$DB" >/dev/null 2>&1; then
    fail "非法数量未被拒绝"
else
    pass "非法数量被拒绝 (非零退出)"
fi
if "$APP" inventory set square --db "$DB" >/dev/null 2>&1; then
    fail "缺数量的奇数参数未被拒绝"
else
    pass "形状/数量不成对被拒绝 (非零退出)"
fi

# ---- 6a. match: 满配库存下全库模型均能搭 ----------------------------
FULL_DB="$WORK_DIR/full.db"
"$APP" inventory set \
    square 999 large_square 999 window_square 999 door_frame 999 \
    equilateral_triangle 999 right_triangle 999 isosceles_triangle 999 \
    rectangle 999 wheel_base 999 rhombus 999 trapezoid 999 hexagon 999 sector 999 \
    --db "$FULL_DB" >/dev/null 2>&1
match_output="$("$APP" inventory match --data-dir "$DATA_DIR" --db "$FULL_DB" 2>&1)"
match_exit=$?
summary="$(grep -o '共 [0-9]* 个模型, 能搭 [0-9]* 个' <<<"$match_output" | head -n 1)"
total="$(grep -o '[0-9]*' <<<"$summary" | sed -n 1p)"
buildable="$(grep -o '[0-9]*' <<<"$summary" | sed -n 2p)"
if [[ "$match_exit" -eq 0 && -n "$total" && "$total" -gt 0 && "$total" == "$buildable" ]]; then
    pass "满配库存 match: 全库 $total 个模型均能搭"
else
    fail "满配库存 match 异常 (退出码 $match_exit, 摘要: $summary)"
    printf '%s\n' "$match_output" >&2
fi

# ---- 6b. match: 全 0 库存下能搭 0 个且给出缺片清单 -------------------
ZERO_DB="$WORK_DIR/zero.db"
"$APP" inventory set square 0 --db "$ZERO_DB" >/dev/null 2>&1
zero_output="$("$APP" inventory match --data-dir "$DATA_DIR" --db "$ZERO_DB" 2>&1)"
zero_exit=$?
if [[ "$zero_exit" -eq 0 ]] && grep -q "能搭 0 个" <<<"$zero_output" && \
   grep -q "还差一点的模型" <<<"$zero_output" && grep -q "还缺" <<<"$zero_output"; then
    pass "全 0 库存 match: 能搭 0 个并列出缺片清单"
else
    fail "全 0 库存 match 异常 (退出码 $zero_exit)"
    printf '%s\n' "$zero_output" >&2
fi

echo
if [[ "$failures" -eq 0 ]]; then
    echo "磁力片库存 CLI 测试通过"
    exit 0
fi
echo "磁力片库存 CLI 测试失败: $failures 项未通过" >&2
exit 1
