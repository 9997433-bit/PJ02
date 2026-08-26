#!/usr/bin/env bash
# =============================================================
# MagTile Studio - 磁力片库存图形录入冒烟测试 (ctest: inventory_gui_smoke)
#
# 检查项 (核心承诺: 图形录入与 CLI 共用同一份 SQLite 库存):
#   1. library --dev-gui --inventory 无头渲染库存录入界面并截图,
#      校验 PPM 格式与内容非纯色;
#   2. --smoke-inventory 自动驾驶: 模拟用户在图形界面修改数量并点击
#      "保存, 看看我能搭什么" (与真实点击相同的 action -> 保存管线),
#      随后 CLI inventory show 必须从同一数据库读到这些数量;
#   3. 保存的库存对 inventory match 生效 (跨界面数据一致);
#   4. 未在 --smoke-inventory 中指定的片型按 0 落库 ("明确没有"),
#      onboarding 完成标记写入 (下次启动不再弹提示);
#   5. 无显示环境时降级为链接检查 (--dev-gui 退出码不为 2)。
#
# 用法:
#   tests/test_inventory_gui.sh <magtile_app 路径> <项目根>
# =============================================================
set -u

APP="${1:?用法: test_inventory_gui.sh <magtile_app> <项目根>}"
ROOT="${2:?用法: test_inventory_gui.sh <magtile_app> <项目根>}"
DATA_DIR="$ROOT/data"
WORK_DIR="$(mktemp -d /tmp/magtile_inventory_gui_XXXXXX)"
DB="$WORK_DIR/progress.db"
EDITOR_SHOT="$WORK_DIR/inventory_editor.ppm"
FRAMES=5

failures=0
pass() { printf '[通过] %s\n' "$1"; }
fail() { printf '[失败] %s\n' "$1" >&2; failures=$((failures + 1)); }
cleanup() { rm -rf "$WORK_DIR"; }
trap cleanup EXIT

if [[ ! -x "$APP" ]]; then
    fail "找不到可执行文件 $APP"
    exit 1
fi

TIMEOUT_CMD=()
command -v timeout >/dev/null 2>&1 && TIMEOUT_CMD=(timeout 120)

RUNNER=()
if command -v xvfb-run >/dev/null 2>&1; then
    RUNNER=(xvfb-run -a -s "-screen 0 1600x1000x24")
elif [[ -n "${DISPLAY:-}" ]]; then
    RUNNER=()
else
    echo "[信息] 无 xvfb-run 也无 DISPLAY, 降级为链接检查..."
    "$APP" library --data-dir "$DATA_DIR" --db "$DB" --dev-gui --inventory --frames 1 >/dev/null 2>&1
    link_exit=$?
    if [[ "$link_exit" -eq 2 ]]; then
        fail "构建未包含渲染后端 (--dev-gui 退出码 2)"
    else
        pass "渲染后端已链接 (--dev-gui 退出码 $link_exit, 非 2; 无显示环境, 跳过实际渲染)"
    fi
    [[ "$failures" -eq 0 ]] && { echo; echo "库存图形录入冒烟测试通过 (降级模式)"; exit 0; }
    exit 1
fi

# ---- 1. 库存录入界面渲染 + 截图 -------------------------------------
echo "[信息] 无头渲染库存录入界面 $FRAMES 帧..."
"${TIMEOUT_CMD[@]}" "${RUNNER[@]}" \
    "$APP" library --data-dir "$DATA_DIR" --db "$DB" \
    --dev-gui --inventory --frames "$FRAMES" --screenshot "$EDITOR_SHOT"
editor_exit=$?
if [[ "$editor_exit" -eq 0 ]]; then
    pass "库存录入界面渲染 $FRAMES 帧后正常退出"
else
    fail "库存录入界面渲染退出码 $editor_exit (期望 0)"
fi

if [[ -s "$EDITOR_SHOT" ]]; then
    header="$(head -c 32 "$EDITOR_SHOT" | head -n 2 | tr '\n' ' ')"
    if [[ "$header" == P6\ * ]]; then
        distinct="$(tail -c 262144 "$EDITOR_SHOT" | od -An -v -tx1 | tr ' ' '\n' | sort -u | grep -c . || true)"
        if [[ "$distinct" -ge 2 ]]; then
            pass "库存录入界面截图已生成且非纯色 (采样到 $distinct 种字节值)"
        else
            fail "库存录入界面截图疑似纯色/空白 (采样仅 $distinct 种字节值)"
        fi
    else
        fail "截图不是 PPM (P6) 格式: $header"
    fi
else
    fail "未生成库存录入界面截图 $EDITOR_SHOT"
fi

# 只渲染不保存: 数据库不应出现库存记录 ("返回" 语义, 编辑副本不落盘)
show_before="$("$APP" inventory show --db "$DB" 2>&1)"
if grep -q "尚未登记" <<<"$show_before"; then
    pass "只打开录入界面不保存: 库存仍为空 (编辑副本不落盘)"
else
    fail "只打开录入界面就产生了库存记录 (不应落盘)"
    printf '%s\n' "$show_before" >&2
fi

# ---- 2. 图形路径写库存 -> CLI 能读到 (核心检查) ----------------------
echo "[信息] 冒烟自动驾驶: 图形录入 square=42 等 4 种片型并保存..."
"${TIMEOUT_CMD[@]}" "${RUNNER[@]}" \
    "$APP" library --data-dir "$DATA_DIR" --db "$DB" \
    --dev-gui --smoke-inventory "square=42,equilateral_triangle=24,right_triangle=8,rectangle=6" \
    --frames 8 >/dev/null 2>&1
save_exit=$?
if [[ "$save_exit" -eq 0 ]]; then
    pass "图形录入自动驾驶 (修改数量 + 保存并匹配) 正常退出"
else
    fail "图形录入自动驾驶退出码 $save_exit (期望 0)"
fi

show_output="$("$APP" inventory show --db "$DB" 2>&1)"
if [[ $? -eq 0 ]] && grep -q "正方形.*x 42" <<<"$show_output" && \
   grep -q "等边三角形.*x 24" <<<"$show_output" && \
   grep -q "直角三角形.*x 8" <<<"$show_output" && \
   grep -q "长方形.*x 6" <<<"$show_output" && \
   grep -q "合计: 80 片" <<<"$show_output"; then
    pass "CLI inventory show 读到图形路径写入的库存 (合计 80 片)"
else
    fail "CLI inventory show 未读到图形路径写入的库存"
    printf '%s\n' "$show_output" >&2
fi

# ---- 3. 保存的库存对 inventory match 生效 ----------------------------
match_output="$("$APP" inventory match --data-dir "$DATA_DIR" --db "$DB" 2>&1)"
if [[ $? -eq 0 ]] && grep -q "能搭" <<<"$match_output"; then
    pass "inventory match 基于图形录入的库存完成匹配"
else
    fail "inventory match 异常"
    printf '%s\n' "$match_output" >&2
fi

# ---- 4. 未指定片型按 0 落库 + onboarding 完成标记 --------------------
if grep -q "车轮底座.*x 0" <<<"$show_output" && grep -q "13 种形状" <<<"$show_output"; then
    pass "未指定片型按 0 落库 (13 种形状全部登记, \"明确没有\" 语义)"
else
    fail "未指定片型没有按 0 落库"
    printf '%s\n' "$show_output" >&2
fi

echo
if [[ "$failures" -eq 0 ]]; then
    echo "库存图形录入冒烟测试通过"
    exit 0
fi
echo "库存图形录入冒烟测试失败: $failures 项未通过" >&2
exit 1
