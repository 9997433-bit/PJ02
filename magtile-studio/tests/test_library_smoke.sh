#!/usr/bin/env bash
# =============================================================
# MagTile Studio - 商业版模型库 (library) 冒烟测试
#
# 检查项:
#   1. library CLI: 终端列出模型库并完成目录/模型文件对账;
#   2. library --dev-gui 无头渲染模型库界面 (优先 xvfb-run, 其次现有
#      DISPLAY), 渲染 5 帧并保存 PPM 截图, 校验格式与内容非纯色;
#   3. library --dev-gui --open <model>: 深链直接进入教程会话, 渲染数帧
#      后退出, 校验进度存档中确实建档 (库与教程/进度模块联动);
#   4. library --dev-gui --parent-gate: 渲染家长门界面 (算术题 + 中文
#      大写数字软键盘) 并截图, 校验非纯色 (家长门 UI 冒烟);
#   5. 无显示环境时 2/3/4 降级为链接检查 (--dev-gui 退出码不为 2)。
#
# 用法:
#   tests/test_library_smoke.sh <magtile_app 路径> <项目根>
# =============================================================
set -u

APP="${1:?用法: test_library_smoke.sh <magtile_app> <项目根>}"
ROOT="${2:?用法: test_library_smoke.sh <magtile_app> <项目根>}"
DATA_DIR="$ROOT/data"
MODEL_ID="castle_foundation_01"
WORK_DIR="$(mktemp -d /tmp/magtile_library_smoke_XXXXXX)"
SHOT="$WORK_DIR/library.ppm"
DB="$WORK_DIR/progress.db"
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

# ---- 1. library CLI: 列表 + 目录对账 ------------------------------
cli_output="$("$APP" library --data-dir "$DATA_DIR" --db "$DB" 2>&1)"
cli_exit=$?
if [[ "$cli_exit" -eq 0 ]] && grep -q "$MODEL_ID" <<<"$cli_output"; then
    pass "library CLI 列出模型库且目录对账通过"
else
    fail "library CLI 退出码 $cli_exit 或未列出 $MODEL_ID"
    printf '%s\n' "$cli_output" >&2
fi

# ---- 2/3. 无头图形渲染 --------------------------------------------
TIMEOUT_CMD=()
command -v timeout >/dev/null 2>&1 && TIMEOUT_CMD=(timeout 120)

RUNNER=()
if command -v xvfb-run >/dev/null 2>&1; then
    RUNNER=(xvfb-run -a -s "-screen 0 1600x1000x24")
elif [[ -n "${DISPLAY:-}" ]]; then
    RUNNER=()
else
    echo "[信息] 无 xvfb-run 也无 DISPLAY, 降级为链接检查..."
    "$APP" library --data-dir "$DATA_DIR" --db "$DB" --dev-gui --frames 1 >/dev/null 2>&1
    link_exit=$?
    if [[ "$link_exit" -eq 2 ]]; then
        fail "构建未包含渲染后端 (--dev-gui 退出码 2)"
    else
        pass "渲染后端已链接 (--dev-gui 退出码 $link_exit, 非 2; 无显示环境, 跳过实际渲染)"
    fi
    [[ "$failures" -eq 0 ]] && { echo; echo "模型库冒烟测试通过 (降级模式)"; exit 0; }
    exit 1
fi

# ---- 2. 模型库界面渲染 + 截图 --------------------------------------
echo "[信息] 无头渲染模型库界面 $FRAMES 帧..."
"${TIMEOUT_CMD[@]}" "${RUNNER[@]}" \
    "$APP" library --data-dir "$DATA_DIR" --db "$DB" \
    --dev-gui --frames "$FRAMES" --screenshot "$SHOT"
gui_exit=$?
if [[ "$gui_exit" -eq 0 ]]; then
    pass "模型库界面渲染 $FRAMES 帧后正常退出"
else
    fail "模型库界面渲染退出码 $gui_exit (期望 0)"
fi

if [[ -s "$SHOT" ]]; then
    header="$(head -c 32 "$SHOT" | head -n 2 | tr '\n' ' ')"
    if [[ "$header" == P6\ * ]]; then
        pass "模型库截图已生成 ($header)"
        distinct="$(tail -c 262144 "$SHOT" | od -An -v -tx1 | tr ' ' '\n' | sort -u | grep -c . || true)"
        if [[ "$distinct" -ge 2 ]]; then
            pass "截图内容非纯色 (采样到 $distinct 种字节值)"
        else
            fail "截图疑似纯色/空白 (采样仅 $distinct 种字节值)"
        fi
    else
        fail "截图不是 PPM (P6) 格式: $header"
    fi
else
    fail "未生成模型库截图 $SHOT"
fi

# ---- 3. --open 深链: 教程会话 + 进度建档 ---------------------------
echo "[信息] 深链进入 $MODEL_ID 教程会话并渲染数帧..."
"${TIMEOUT_CMD[@]}" "${RUNNER[@]}" \
    "$APP" library --data-dir "$DATA_DIR" --db "$DB" \
    --dev-gui --open "$MODEL_ID" --frames 8 >/dev/null 2>&1
open_exit=$?
if [[ "$open_exit" -eq 0 ]]; then
    pass "--open 深链教程会话渲染后正常退出"
else
    fail "--open 深链教程会话退出码 $open_exit (期望 0)"
fi

show_output="$("$APP" progress show "$MODEL_ID" --db "$DB" 2>&1)"
if [[ $? -eq 0 ]] && grep -q "$MODEL_ID" <<<"$show_output"; then
    pass "教程会话已写入进度存档 (progress show 有记录)"
else
    fail "进度存档中没有 $MODEL_ID 的记录 (库与进度模块联动失败)"
    printf '%s\n' "$show_output" >&2
fi

# ---- 4. --parent-gate: 家长门界面渲染 + 截图 ------------------------
GATE_SHOT="$WORK_DIR/parent_gate.ppm"
echo "[信息] 无头渲染家长门界面 $FRAMES 帧..."
"${TIMEOUT_CMD[@]}" "${RUNNER[@]}" \
    "$APP" library --data-dir "$DATA_DIR" --db "$DB" \
    --dev-gui --parent-gate --frames "$FRAMES" --screenshot "$GATE_SHOT"
gate_exit=$?
if [[ "$gate_exit" -eq 0 ]]; then
    pass "家长门界面渲染 $FRAMES 帧后正常退出"
else
    fail "家长门界面渲染退出码 $gate_exit (期望 0)"
fi

if [[ -s "$GATE_SHOT" ]]; then
    gate_header="$(head -c 32 "$GATE_SHOT" | head -n 2 | tr '\n' ' ')"
    if [[ "$gate_header" == P6\ * ]]; then
        distinct="$(tail -c 262144 "$GATE_SHOT" | od -An -v -tx1 | tr ' ' '\n' | sort -u | grep -c . || true)"
        if [[ "$distinct" -ge 2 ]]; then
            pass "家长门截图已生成且非纯色 (采样到 $distinct 种字节值)"
        else
            fail "家长门截图疑似纯色/空白 (采样仅 $distinct 种字节值)"
        fi
    else
        fail "家长门截图不是 PPM (P6) 格式: $gate_header"
    fi
else
    fail "未生成家长门截图 $GATE_SHOT"
fi

echo
if [[ "$failures" -eq 0 ]]; then
    echo "模型库冒烟测试通过"
    exit 0
fi
echo "模型库冒烟测试失败: $failures 项未通过" >&2
exit 1
